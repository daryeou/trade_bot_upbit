# -*- coding: utf-8 -*-
"""
2021-02-26
Cyptocurrency investment bot
ver. 0.1

This application is Automatic investment programe for UPBIT
"""
from log_module.logging2 import *
from log_module.file import *
from exchange_api.model import *
from repository.db import *
import sys
import traceback
from PyQt5.QtCore import *
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import QSound
import requests
import datetime 
import math
import numpy as np
import os
import jwt
import uuid
import hashlib
from urllib.parse import urlencode
import websockets
import asyncio
from multiprocessing import Queue
from collections import deque
import multiprocessing
from itertools import chain, repeat
from functools import partial

#TODO 교차봇 구현 방법: 최고점 최저점 찍는 사이 시간 간격을 파악 후, count를 이용하여 재진입 여부를 파악하고 기존의 정보를 활용하여 일정시간안에 상승이 없으면 재매 

form_class = uic.loadUiType("mywindow.ui")[0]

tickers = ["KRW-XRP"]

my_money=0;

purchase_price = 0 # 매수시 사용할 가격.

is_loading=1 # analyze전에 매수 매도 되는것을 방지.. 1이면 target과 cancel값 미완성 상태

calc_time = 3 # 1봉 주기(초)

break_time_limit = 0 # 봉이 이 횟수만큼 돌때까지 재매수 금지.

_AccessKey = ""
_SecretKey = ""

class Refresh(QThread):
    timeout = pyqtSignal(object,object)
    
    update_log = pyqtSignal(object)
    update_average = pyqtSignal()
    
    def __init__(self, price_queue, parent=None):
        super().__init__(parent)
        self.is_run=True
        self.q = price_queue
        
    def run(self):
        global is_loading, my_money
        
        coin_db = Coin_database()
        
        while is_loading == 1:
            self.sleep(1)
        
        while self.is_run:
            if not self.q.empty():
                data = self.q.get() #receive json data
                if data['ty'] == 'ticker':

                    coin_db.update_price(data['cd'],data['tp']) # 가격 큐에 삽입
                    
                elif data['ty'] == 'orderbook':
                    coin_db.set_orderbook(data['cd'],data)
                
                else:
                    pass
            else:
                self.sleep(1)
            
    def stop(self):
        self.is_run=False
        
class Refresh_any(QThread):
    update_log = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__()
        self.is_run=True
        
    def run(self):
        global my_money, is_loading
        
        while is_loading == 1:
            self.sleep(1)

        while self.is_run:
            # lists=[]
            # for coinname in tickers:
            #     lists.append(get_average(coinname,'day',5))
            # self.update_average.emit(lists)
            # now = datetime.datetime.now()
            # starttime = get_start_time("day") + datetime.timedelta(days=1)
            # starttime = starttime.replace(hour=9,minute=1)
            # sleep_time = starttime - now
            # self.sleep(int(float(sleep_time.total_seconds())))

            sleep_time = datetime.timedelta(seconds=60)
            self.sleep(int(float(sleep_time.total_seconds())))

            
    def stop(self):
        self.is_run=False

        
class Analyze(QThread):
    global tickers
    update_average = pyqtSignal()
    update_log = pyqtSignal(object)
    all_sell = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__()
        self.is_run=True
        self.pool = multiprocessing.Pool() #(processes=(4)) 멀티프로세서 생성
        
    def run(self):
        global is_loading, my_money
        
        
        coin_db = Coin_database()
        
        all_ticker = [x['market'] for x in get_coinlist()]
        for x in tickers:
            if x not in all_ticker:
                self.update_log.emit("잘못된 ticker가 있습니다.")
                exit(-1)
        
            
        while self.is_run:
            try:
                self.update_log.emit("차트 분석 중입니다. 종료될 때 까지 다른버튼은 누르지마시고 기다려주세요. 폴더에 저장되는 xlxs파일은 프로그램 동작중에 실행하지 마십시오.")
                #정밀분석 데이터 갱신
                precise_analyze(self.update_log,self.pool)
                for x in tickers:
                    re_analyze(self.update_log,coin_db,x)
                    self.update_average.emit() #테이블 업데이트 내용 반영
                self.update_log.emit("----------------------")
               
                is_loading=0; #데이터 갱신을 차단 해제
                
                starttime = get_start_time(get_timingname()) + datetime.timedelta(seconds=get_realtiming())
                starttime = starttime.replace(second=8)
                now = datetime.datetime.now()
                sleep_time = starttime - now
                self.update_log.emit(f"정밀 분석 타이머: {sleep_time} {starttime} {now}")
               
                self.sleep(int(float(sleep_time.total_seconds())))
                
                # self.update_log.emit(f"{now} 전부 매도합니다.  (장타모드) ")
                # self.all_sell.emit(0)     
                
            except:
                traceback.print_exc(limit=None,chain=True)
                self.update_log.emit("차트 정밀분석 불러오기 에러. 재호출 합니다..")
                
    def stop(self):
        self.pool.close()
        self.pool.join()
        self.is_run=False
        
class Tick(QThread):
    global tickers
    update_log = pyqtSignal(object)
    timeout = pyqtSignal(object,object)
    update_average = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__()
        self.is_run=True
        self.coin_db = Coin_database()
        self.notes = {
            'buy': QSound("buy.wav"),
            'sell': QSound("sell.wav")
        }
        
        
    def run(self):
        global my_money, calc_time, tickers, purchase_price
        
        coin_db = Coin_database()
        
        while is_loading == 1:
            self.sleep(calc_time)
        self.update_log.emit(f"---{break_time_limit*calc_time}초 후에 매수,매도 시작합니다. Purchase System lock---")
        
        while self.is_run:
            try:
                my_info=get_orderlist()
                my_money = int(float([x for x in my_info if f'{x["unit_currency"]}-{x["currency"]}'== "KRW-KRW"][0]["balance"]))
                self.update_log.emit(f"현재 사용가능 자산:{my_money}원")
                for ticker in tickers:
                    self.coin_db.maintain_count(ticker)
                    
                    
                    ''' 지정된 초(calc_time)마다 분석 후 매수 매도 결정'''
                    price_now = coin_db.get_price(ticker) #최근 number_of_samples개를 평균으로 현재값 계산
                    if price_now == 0: #선진입 방지!!
                           continue
                    self.timeout.emit(ticker,price_now) #현재 가격 차트에 업데이트
                    self.update_average.emit() #타겟, 취소가 차트 계속해서 업데이트 (cancel 등..)
                    
                    coininfo = coin_db.get(ticker)
                    
                    if coin_db.is_lock(ticker)==1 :
                        self.update_log.emit(f'Selling Condition Check: {ticker}:{price_now} target:{coininfo["cancel"]=} {coininfo["cancel2"]=} {coininfo["before_target"]=} updated:{coininfo["updated"]}')
                        if (price_now<=coininfo['cancel'] or ( (coininfo["updated"] == 1) and price_now<=coininfo['before_target'] ) or ( (price_now<=coininfo['cancel2']) ) ) : #매도 조건 and로 한 이유:upbit.py 참 '''(coininfo["updated"] == 1) and'''
                            if coin_db.is_trading(ticker)==1 :
                                
                                result = sell_crypto(ticker) 
                                if result[0] == 200 | result[0] == 201:
                                    self.update_log.emit(f"{ticker}매도 완료 {result}")
                                else:
                                    result = sell_crypto(ticker)
                                    self.update_log.emit(f"{ticker}재매도 시도 결과 {result}")
                                coin_db.set_trading(ticker,0)
                                self.update_average.emit()
                                self.notes['sell'].play()
                            
                    elif coin_db.is_lock(ticker)==0 :  
                                
                        self.update_log.emit(f'Purchase Condition Check: {ticker}:{price_now} target:{coininfo["target"]} avg:{coininfo["movingavg"]} breakTime:{coininfo["break_time"]}')
                        if ( (price_now>=coininfo['target']) or ( (coininfo['ap']>(coininfo['target']-coininfo['GAP'])) and (coininfo['as'] < coininfo['bs']*0.33) and (coininfo['ap']<=coininfo['target']) ) ) and price_now>=coininfo['movingavg'] and coininfo["break_time"] > break_time_limit:
                            self.update_log.emit(f'매수 : {ticker=} {price_now=} {coininfo["target"]=} {coininfo["movingavg"] =} {coininfo["speed"] =} {coininfo["break_time"]=}')
                            price = purchase_price
                            result = None
                            #result = buy_crypto(ticker,coininfo['ap'],float(price)/coininfo['ap']) #지정가로 구매
                            if purchase_price == 0: #TODO : 매번 if문으로 하지말고 코루틴 yield로 변경할 것!!!!! 또는 if문을 밖으로 꺼낼것..연산낭비 
                                temp = math.floor(my_money/(len(tickers)-get_purchased_count()))*0.95
                                print(f"--결제금액 자동연산 {ticker}: {temp}원에 결제--")
                                if temp > 5010:
                                    self.update_log.emit(f'{temp=}')
                                    result = buy_crypto(ticker,temp) #시장가로 구매
                                else:
                                    print("최소 금액 (5000원) 미도달로 결제 실패")
                            else:
                                if my_money < purchase_price:
                                    print(f"{ticker} : 잔액이 부족합니다. 결제를 취소합니다.")
                                    continue
                            
                            self.update_average.emit()
                            print(result)
                            if result[0] == 200 | result[0] == 201:
                                self.update_log.emit(f"{ticker}매수 완료 {result}")
                                #------------uuid추가함!!TODO 이제 제때 매수 안된 코인들 관리하도록 만들자.-------------------
                                #------------TODO 매도 후 코인정보에 매도시간을 기록하여 datatime과 비교해서 다음 분기까지 분석 연산을 금지하거나 일정값(cancel보다 아래)아래로 떨어지면 다시 연산가능하게 만들것 ---------
                                #------------업비트의 경우 9시에 매도량이 늘어나기때문에 그전에 대피할것
                                coin_db.add_uuid(ticker, result[1]['uuid']) 
                                #re_analyze(self.update_log,coin_db,ticker) #구매후 리벨런싱
                                coin_db.set_trading(ticker,1)
                                coin_db.set_lock(ticker)
                                self.notes['buy'].play()
                                
                                #리스트 맨 앞으로 추가
                                #TODO 연산 낭비가 심하므로 db에서 name을 ID값으로 하는 딕셔너리로 수정할 것.
                                tickers.remove(ticker)
                                tickers.insert(0,ticker)
                                
                            else:
                                self.update_log.emit(f"{ticker}매수 실패! {result}\n ")
                                
                
                            # if price_now>(coininfo['target']):
                            #     pass
                            # elif price_now<coininfo['cancel']:
                            #     pass
                        
                    
                sleep_time = datetime.timedelta(seconds=calc_time)
                self.sleep(int(float(sleep_time.total_seconds())))
            except:
                self.update_log.emit(f"네트워크 연결에 문제가 있습니다.")
                self.sleep(calc_time)
                traceback.print_exc(limit=None,chain=True)
            
    def stop(self):
        self.is_run=False
        
def precise_analyze(update_log,pool):
    global tickers
    
    coin_db = Coin_database()
    try:
        update_log.emit("정밀 차트 분석 시작.")
        
        pool.daemon = True
        update_log.emit("멀티프로세서 생성.")
        timing_level = get_timing_level()
        # result = pool.map(partial(analyze_worker,timing_level),tickers)
        result = pool.starmap(analyze_worker, zip(repeat(timing_level),tickers))
        for data in result:
            update_log.emit(f"정밀 차트 적용 {data['name']}")
            coin_db.adddata(data["name"], data["k"], data["window"], data["cancel_per"], data["MDD"], data["HPR"], data["ROC_mean"],data["GAP"])
        update_log.emit("정밀 차트 분석 종료.")   
    except:
        update_log.emit("정밀 차트 분석 에러. 재시작")
        traceback.print_exc(limit=None,chain=True)
        coin_db.reset()
        precise_analyze(update_log)
        return
    finally:
        #pool.terminate()
        # pool.close()
        # pool.join()
        pass

    return
    
def analyze_worker(timing_level,ticker):
    try:
        print("작업 중: "+ticker)
        set_timing_level(timing_level) #멀티프로세서 문제로 타이밍레벨을 다시 설정해주어야 함.!!!
        data = get_analyze_scalping(ticker) #차트 분석 TODO 주기적으로 되도록 만들 것
        return data
    except:
        print(f"{ticker} : 차트 분석 에러. 다시시도합니다.")
        analyze_worker(coin_db,ticker)
    

def re_analyze(update_log,coin_db,x):
    try:
        update_log.emit(f"{x}차트 분석 중")
        coin_db.addtarget(*get_target(x,get_timingname(),coin_db.get(x)["k"],coin_db.get(x)["window"]))
        update_log.emit(f"{x}이동평균 분석 중")              
        real_avg = get_average(x,get_timingname(),coin_db.get(x)["window"])
        coin_db.addavg(*real_avg)
        update_log.emit(f"{x} 완료") 
    except:
        traceback.print_exc(limit=None,chain=True)
        print("불러오기 에러. 재가동")
        #return re_analyze(update_log,coin_db,x)
        
# def buying_analyze(update_log,coin_db,name):
#     try:
#         update_log.emit(f"{name} 고점 분석")
#         open = float(get_market_price(name,1)["opening_price"])
#         coin_db.update_cancel_open(name,open)

#         update_log.emit(f"{name} 완료") 
#     except:
#         traceback.print_exc(limit=None,chain=True)
#         print("매수 중 코인 분석 에러. 고점계산이 불가능합니다. 재연산 실행")
#         return buying_analyze(update_log,coin_db,name)
    
# import inspect
"""
param: uic.loadUiType
"""
class MyWindow(QMainWindow,form_class):
    def __init__(self,log):
        self.log = log
        super().__init__()
        self.setupUi(self)
        #self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        #self.setGeometry(100, 200, 300, 400)
        self.center()
        self.setWindowTitle("코린이봇 New V5.0 (Cryptocurrency investment Manager)")
        self.setWindowIcon(QIcon("icon.png"))
        
        self.coin_db = Coin_database()

        #make queue to communicate with model.py
        price_queue = Queue()
        self.price_queue = price_queue
        
        #setting tables
        global tickers
        tickers=[x['market'] for x in get_coinlist()]
        self.table_reload()
        
        self.menuInfo.triggered.connect(self.menu_info)
        self.menuExit.triggered.connect(self.menu_exit)
        
        self.optimizationButton.clicked.connect(self.edit_tickers)
        self.sell_bt.clicked.connect(self.all_sell)
        self.timeLevel.setText(str(get_timing_level()))
        self.AccessKey.setText(str(_AccessKey))
        self.SecretKey.setText(str(_SecretKey))
        self.purchasePrice.setText(str(0))
        # r = requests.get("https://api.korbit.co.kr/v1/ticker/detailed?currency_pair=btc_krw")
        # print(r.text)
        # self.timer = QTimer(self)
        # self.timer.start(1000000)
        # self.timer.timeout.connect(self.timeout)

        
    def closeEvent(self, e):
        try:
            if self.analyze.isRunning():  # 쓰레드가 돌아가고 있다면 
               self.analyze.stop()
               self.analyze.terminate()  # 현재 돌아가는 thread 를 중지시킨다
               #self.analyze.wait()       # 새롭게 thread를 대기한후
               #self.analyze.start()      # 다시 처음부터 시작
        except:
             print("None analyze thread")
        try:
            if self.refresh_any.isRunning():  # 쓰레드가 돌아가고 있다면 
               self.refresh_any.stop()
               self.refresh_any.terminate()  # 현재 돌아가는 thread 를 중지시킨다
               #self.refresh_any.wait()       # 새롭게 thread를 대기한후
               #self.refresh_any.start()      # 다시 처음부터 시작
        except:
             print("None refresh_any thread")
        try:
            if self.refresh_list.isRunning():  # 쓰레드가 돌아가고 있다면 
               self.refresh_list.stop()
               self.refresh_list.terminate()  # 현재 돌아가는 thread 를 중지시킨다
               #self.refresh_list.wait()       # 새롭게 thread를 대기한후
               #self.refresh_list.start()      # 다시 처음부터 시작
        except:
            print("None refresh_list thread")
        try:
            if self.tick.isRunning():  # 쓰레드가 돌아가고 있다면 
               self.tick.stop()
               self.tick.terminate()  # 현재 돌아가는 thread 를 중지시킨다
               #self.tick.wait()       # 새롭게 thread를 대기한후
               #self.tick.start()      # 다시 처음부터 시작
        except:
            print("None tick thread")       
           
    def runEvent(self):
        self.tick = Tick()
        self.tick.update_log.connect(self.log_update)
        self.tick.timeout.connect(self.table_update)
        self.tick.update_average.connect(self.short_update)
        self.tick.start()
        
        self.refresh_list = Refresh(self.price_queue, self)
        self.refresh_list.timeout.connect(self.table_update)
        self.refresh_list.update_log.connect(self.log_update)
        self.refresh_list.update_average.connect(self.short_update)
        self.refresh_list.start()
        
        self.refresh_any = Refresh_any()
        self.refresh_any.update_log.connect(self.log_update)
        self.refresh_any.start()
        
        self.analyze = Analyze()
        self.analyze.update_average.connect(self.short_update)
        self.analyze.update_log.connect(self.log_update)
        self.analyze.all_sell.connect(self.all_sell)
        self.analyze.start()
        
        # self.Periodic_analyze = Periodic_analyze()
        # self.Periodic_analyze.update_log.connect(self.log_update)
        # self.Periodic_analyze.start()
    '''
    init method
    setting tables
    '''       
    def table_reload(self):
        #table column update
        self.coinPriceWidget.setRowCount(len(tickers))
        self.purchasedList.setRowCount(len(tickers))
        self.coinNameLine.setText(','.join(tickers))
        #self.coinNameLine.adjustSize() #if use it, size is too small
        #coin name list column update
        coinNameList = get_coinlist()
        self.marketInfoWidget.setRowCount(len(coinNameList))
       
        coinNameList = sorted(coinNameList, key = lambda item: item['market'])
        for index,lists in enumerate(coinNameList):
            ticker_item00 = QTableWidgetItem(lists['market'])
            ticker_item01 = QTableWidgetItem(lists['korean_name'])
            self.marketInfoWidget.setItem(index, 0, ticker_item00)
            self.marketInfoWidget.setItem(index, 1, ticker_item01)
            
        for index,x in enumerate(tickers):
            ticker_item10 = QTableWidgetItem(str(""))
            ticker_item11 = QTableWidgetItem(str("-------------------"))
            ticker_item12 = QTableWidgetItem(str("---------------"))
            ticker_item13 = QTableWidgetItem(str(""))
            ticker_item14 = QTableWidgetItem(str(""))
            ticker_item15 = QTableWidgetItem(str(""))
            ticker_item16 = QTableWidgetItem(str("------------"))
            ticker_item17 = QTableWidgetItem(str(""))
            ticker_item18 = QTableWidgetItem(str(""))
            ticker_item19 = QProgressBar(self.coinPriceWidget)
            ticker_item19.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            ticker_item19.setStyleSheet("""
                   QProgressBar {background-color : rgba(0, 0, 0, 0%);border : 1}
                   QProgressBar::Chunk {background-color : rgba(255, 0, 0, 50%);border : 1}
                   """)
            ticker_item20 = QProgressBar(self.coinPriceWidget)
            ticker_item20.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            ticker_item20.setStyleSheet("""
                   QProgressBar {background-color : rgba(0, 0, 0, 0%);border : 1}
                   QProgressBar::Chunk {background-color : rgba(0, 255, 0, 50%);border : 1}
                   """)

            ticker_item21 = QTableWidgetItem(str("------"))
            self.coinPriceWidget.setItem(index,0,ticker_item10)
            self.coinPriceWidget.setItem(index,1,ticker_item11)
            self.coinPriceWidget.setItem(index,2,ticker_item12)
            self.coinPriceWidget.setItem(index,3,ticker_item13)
            self.coinPriceWidget.setItem(index,4,ticker_item14)
            self.coinPriceWidget.setItem(index,5,ticker_item15)
            self.coinPriceWidget.setItem(index,6,ticker_item16)
            self.coinPriceWidget.setItem(index,7,ticker_item17)
            self.coinPriceWidget.setItem(index,8,ticker_item18)
            self.coinPriceWidget.setCellWidget(index,9,ticker_item19)
            self.coinPriceWidget.setCellWidget(index,10,ticker_item20)
            self.coinPriceWidget.setItem(index,11,ticker_item21)
            
        for index,x in enumerate(tickers):
            purchased_item0 = QTableWidgetItem(str(""))
            purchased_item1 = QTableWidgetItem(str(""))
            self.purchasedList.setItem(index, 0, purchased_item0)
            self.purchasedList.setItem(index, 1, purchased_item1)
            
        
        
        
    #view information
    @pyqtSlot()
    def menu_info(self):
        msg = QMessageBox()
        msg.setWindowTitle("정보")
        msg.setText(f'twitter.com/daryeou  \n제작 : @daryeou')
        msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        result = msg.exec_()
        if result == QMessageBox.Cancel:
            pass
            #self.send_valve_popup_signal.emit(False)
        elif result == QMessageBox.Ok:
            pass
            #self.send_valve_popup_signal.emit(True)
        
    #exit menu
    @pyqtSlot()
    def menu_exit(self):
        pass
    
    '''
    emit   
    '''
    
    @pyqtSlot(object)
    def log_update(self,log):
        try:
            cur_time = QTime.currentTime()
            str_time = cur_time.toString("로그 업데이트 시간 hh:mm:ss.zzz")
            self.log.debug(log)
            self.statusBar().showMessage(str_time)
            self.logWidget.appendPlainText(log)
        except:
            self.log.debug("failed to attach log")
            
            
    @pyqtSlot(object,object)
    def table_update(self,coinname,price_now): 
        try:
            cur_time = QTime.currentTime()
            str_time = cur_time.toString("리스트 업데이트 시간 hh:mm:ss.zzz")
            self.statusBar().showMessage(str_time)
            
            for index, ticker in enumerate(tickers):
                if coinname == ticker:
                    purchased_item0 = self.purchasedList.item(index,0)
                    purchased_item1 = self.purchasedList.item(index,1)
                    #purchased chart update
                    #체결된 거래 표시
                    if self.coin_db.is_trading(ticker)==1:
                        purchased_item0.setText(str(ticker))
                        purchased_item1.setText("매수")
                    else:
                        purchased_item0.setText("- - -")
                        purchased_item1.setText("- - -")
                    
                    #Center Chart update
                    #메인 정보 표시 
                    data = self.coin_db.get(ticker)
                    ticker_item0 = self.coinPriceWidget.item(index,0)
                    ticker_item1 = self.coinPriceWidget.item(index,1)
                    ticker_item2 = self.coinPriceWidget.item(index,2)
                    ticker_item8 = self.coinPriceWidget.item(index,8)
                    ticker_item9 = self.coinPriceWidget.cellWidget(index,9)
                    ticker_item10 = self.coinPriceWidget.cellWidget(index,10)
                    ticker_item11 = self.coinPriceWidget.item(index,11)
                    ticker_item0.setText(ticker)
                    ticker_item1.setText(str(f'{data["speed"]:.0f} , Adv:{data["profit"]*100:.1f}%'))
                    ticker_item2.setText(str(f"{price_now:.2f}"))
                    maxTradingValue = int(float(max([data['as'],data['bs']])))
                    ticker_item8.setText(str(data['ap'])) #현재 매도 호가
                    ticker_item9.setRange(0, maxTradingValue)
                    ticker_item9.setFormat(f"{data['as']:.2f}")
                    ticker_item9.setValue(int(float(data['as'])))
                    ticker_item10.setRange(0, maxTradingValue)
                    ticker_item10.setFormat(f"{data['bs']:.2f}")
                    ticker_item10.setValue(int(float(data['bs'])))
                    if data["is_trading"] == 1:
                        ticker_item0.setBackground(QBrush(QColor(140, 220, 220)))
                    else:
                        ticker_item0.setBackground(QBrush(QColor(255, 255, 255)))
                    try:
                        now_value = float(self.coinPriceWidget.item(index,2).text())
                        avg =  float(self.coinPriceWidget.item(index,4).text())
                    except:
                        ticker_item11.setText(f'대기중')
                        continue
                    if avg == 0:
                        ticker_item11.setText(f'이동평균제외')
                    elif now_value>avg:
                        ticker_item11.setText(f'상승장')
                    elif now_value<=avg:
                        ticker_item11.setText(f'하락장')                
                                
        except:
            traceback.print_exc(limit=None,chain=True)
            self.log.debug("failed to attach table")
            
            
    @pyqtSlot()
    def short_update(self):
        global tickers #tickers 코인이름들을 가져와서 db에서 데이터 추출
        try:
            cur_time = QTime.currentTime()
            str_time = cur_time.toString("이동평균 업데이트 시간 hh:mm:ss.zzz")
            self.statusBar().showMessage(str_time)
            for index, coinname in enumerate(tickers): #데이터 가져오기
                item = self.coin_db.get(coinname)
                ticker_item3 = self.coinPriceWidget.item(index,3)
                ticker_item4 = self.coinPriceWidget.item(index,4)
                ticker_item5 = self.coinPriceWidget.item(index,5)
                ticker_item6 = self.coinPriceWidget.item(index,6)
                ticker_item7 = self.coinPriceWidget.item(index,7)
                ticker_item3.setText(str(f"range:{item['range']:.2f},window:{item['window']}"))
                ticker_item4.setText(str(f"{item['movingavg']:.2f}"))
                ticker_item5.setText(str(f"{item['target']:.2f}"))
                ticker_item6.setText(str(f"{(item['cancel_per']*100):.1f}% {item['cancel']:.2f},{item['cancel2']:.2f},이전타겟:{item['before_target']:.2f}"))
                ticker_item7.setText(str(f"{item['ROC_mean']:.2f}"))

        except:
            self.log.debug("failed to load table")
            traceback.print_exc(limit=None,chain=True)
            
    @pyqtSlot()   
    def all_sell(self,stop=1):
        global is_loading
        try:
            global tickers
            
            for ticker in tickers:
                try:
                    result = sell_crypto(ticker) #판매 후 리벨런싱
                    self.update_log.emit(f"{ticker}매도 완료 {result}")
                    self.coin_db.set_trading(ticker,0)
                except:
                    print("보유하지 않은 코인 건너뜀")
                    pass
        except:
            pass
        for index, ticker in enumerate(tickers):
            purchased_item0 = self.purchasedList.item(index,0)
            purchased_item1 = self.purchasedList.item(index,1)
            purchased_item0.setText("- - -")
            purchased_item1.setText("- - -")
        print("매도 완료")
        if stop == 1:
            print("-프로그램 정지- 최적화를 누르면 다시 시작합니다.")
            is_loading = 1

    '''
    if clicked '최적화'    
    '''
    @pyqtSlot()   
    def edit_tickers(self):
        try:
            global tickers, is_loading, purchase_price
            
            
            is_loading = 1
            set_timing_level(int(self.timeLevel.text()))
            purchase_price = float(self.purchasePrice.text())
            print("API키 :", self.AccessKey.text(),self.SecretKey.text())
            setKey(self.AccessKey.text(),self.SecretKey.text())
            coinnameList = self.coinNameLine.text()
            tickers = coinnameList.split(',')
            self.table_reload()
            
            #reload price list
            run_tracking(tickers,self.price_queue)
            try:
                self.closeEvent(None)
            except:
                pass
            coin = Coin_database()
            coin.reset()
            coin.init(tickers) #코인DB 초기화 작업
            self.runEvent()
        except:
            traceback.print_exc(limit=None,chain=True)
            print("Edit Ticker 에러. 버튼을 다시 눌러주세요.")
        
        
    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2) 
    
    @pyqtSlot()
    def btn_clicked(self):
         print("bt click")
         self.lineEdit.setText(str("hello"))
         
    
def main(log):
    
    #Execute multiple processes to obtain coin prices
    
    app = QApplication(sys.argv)
    window = MyWindow(log)
    window.show()
    app.exec_()

'''
get Attribute from arguments
arg: sys.argv[1]
result:
'''

'''
Make ticket price Log file in json
arg: ticket name, 
result: 
'''

if __name__ == '__main__':
    try:
        log_init()
        log = Log(1) #load debugger
        main(log)
    except Exception as e:
        print("--- Exception Occured ---")
        log.debug(traceback.format_exc(limit=None,chain=True))
        traceback.print_exc(limit=None,chain=True)
    finally:
        log.clear()
        sys.exit(0)
        
    
