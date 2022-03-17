# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 13:28:18 2021

@author: kmwh0
"""
from collections import deque
import numpy as np

#TODO 리스트로 된 db를 딕셔너리로 바꿀 것!! 
# db = ["KRW-XRP":{"up_temp":0,"updated":0,...},"KRW-BTC":{"up_temp":0,"updated":0,...}] 이런식으로

class Singleton(type):
    #_instance = WeakValueDictionary()
    _instance = {}
    def __call__(cls,*args,**kwargs):
        print("-------singleton created--------")
        if cls not in cls._instance:
            cls._instance[cls] = super(Singleton,cls).__call__(*args,**kwargs)
        return cls._instance[cls]

class Coin_database(metaclass = Singleton):
    db =[]
        
    def __init__(self):
        pass
    
    def init(self,tickers):
        for coinname in tickers:
            price_queue = deque(maxlen=30)
            self.db.append({"name":coinname,"up_temp":0,"updated":0,"volume":0,"maintain_count":0,"break_time":0,"uuid":[],"closed":0,"speed":0,"profit":0,"ap":0,"bp":0,"as":1000,"bs":1000,"price": price_queue,"open":float("inf"),"mean":None,"before_mean_max":0,"mean_max":0,"mean_min":0,"lock":0,"is_trading":0,"avg":None,"before_target":0,"original_target":0,"now_target":0,"target":0,"cancel":0,"cancel2":0,"before_movingavg":0,"movingavg":float('inf'),"k":None,"window":None,"cancel_per":None,"MDD":None, "HPR":None, "ROC_mean":None,"ROC_last":None,"GAP":None})
    
    def update_price(self,coinname,price):
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                self.db[index]["volume"] = self.db[index]["volume"]+1
                self.db[index]["price"].append(float(price))
                mean = np.array(self.db[index]["price"]).mean()
                self.db[index]["mean"] = mean #평균 갱신
                
                temp_ = (self.db[index]["target"] if self.db[index]["target"]>self.db[index]["movingavg"] else self.db[index]["movingavg"])
                temp_ = (temp_ - (temp_%self.db[index]['GAP']) + self.db[index]['GAP'])
                #self.db[index]["profit"] = ((mean - temp_)/temp_)
                self.db[index]["profit"] = (((mean - (mean%self.db[index]['GAP'])) - temp_)/temp_)
                self.db[index]["speed"] = self.db[index]["speed"]*99/100
                if mean < float(price):
                    self.db[index]["speed"] = self.db[index]["speed"] + 1
                else:
                    self.db[index]["speed"] = self.db[index]["speed"] - 1
                    
                if mean < self.db[index]["now_target"]-self.db[index]["range"]: #매도 후 재진입 할 수 있도록 기존 타겟값보다 현재값이 낮으면 매도 후 수정된 타겟값에서 기존 타겟값으로 복원
                    self.db[index]["target"] = self.db[index]["now_target"]
                    
                #print(coinname, self.db[index]["range"], self.db[index]["GAP"])
                break
                        
    def maintain_count(self,coinname):
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                mean = np.array(self.db[index]["price"]).mean()
                
                if self.db[index]["is_trading"]==0:
                    
                    self.db[index]["mean_max"] = mean
                    self.db[index]["before_mean_max"] = mean
                    self.db[index]["maintain_count"] = 0
                    self.db[index]['up_temp']=0
                    
                    self.db[index]["cancel"] = mean * 0.95           #   취소점1
                    self.db[index]["cancel2"] = self.db[index]["mean_max"] - (self.db[index]["ROC_last"]*self.db[index]["cancel_per"])   #   취소점2.
                    # self.db[index]["cancel"] = max([temp1,temp2])
                    
                    
                    #최저점 찾기 
                    if self.db[index]["mean_min"] == 0:
                        self.db[index]["mean_min"] = mean #최저점 찾기
                    elif self.db[index]["mean_min"] > mean:
                        temp = (self.db[index]["mean_min"] - mean) * 1 #타겟보다 n배만큼 하향하기
                        self.db[index]["mean_min"] = mean
                        #TODO 새로추가한 기능. 하한선 제한. 매도 후 3번정도 교차하므로 파악해서 사용할것!!!
                        # if self.db[index]["target"] > self.db[index]["movingavg"] + self.db[index]["range"] :
                        #     self.db[index]["target"] = self.db[index]["target"] - temp
                        #     print(f'{coinname} 저점이 하향합니다. 타겟이 하향합니다.') #저점에 따라 타겟이 하향하는 기능
                elif self.db[index]["is_trading"]==1:
                        self.db[index]["mean_min"] = mean
                        
                        if self.db[index]["mean_max"] == 0:
                            self.db[index]["mean_max"] = mean #고점 찾기
                        elif self.db[index]["mean_max"] < mean:
                            self.db[index]['up_temp'] = (mean - self.db[index]["mean_max"]) * 1.0 #하한선 n배 만큼 상향하기
                            self.db[index]["mean_max"] = mean
                            self.db[index]["cancel"] = self.db[index]["cancel"] + self.db[index]['up_temp'] #+ self.db[index]["range"]/(cycle/calctime)#하한선 가중치
                            self.db[index]["cancel2"] = self.db[index]["mean_max"] - (self.db[index]["ROC_last"]*self.db[index]["cancel_per"])
                            print(f'하한선이 상승합니다 {coinname} {self.db[index]["up_temp"]=} {self.db[index]["cancel_per"]=} {self.db[index]["cancel"]=} {self.db[index]["cancel2"]=} ')
                            
                            
                if (self.db[index]["is_trading"]==1): #매도한계시간이 흘러감
                    if self.db[index]["mean_max"] == self.db[index]["before_mean_max"]:
                        self.db[index]["maintain_count"] = self.db[index]["maintain_count"]  + 1
                    elif self.db[index]["mean_max"] > self.db[index]["before_mean_max"]:
                        self.db[index]["before_mean_max"] = self.db[index]["mean_max"]
                        self.db[index]["maintain_count"] = 0
                    print(f'유지 시간 {coinname} {self.db[index]["maintain_count"]}')
                else: #매수중이 아닐 떄
                    self.db[index]["break_time"] = self.db[index]["break_time"] + 1
                #print(f'초당 거래율 {coinname} {self.db[index]["volume"]}')
                self.db[index]["volume"] = 0
                return self.db[index]["maintain_count"]

    def get_price(self,coinname):
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                #self.db[index]["price"].clear() #tick주기에 따라 큐 clear
                return self.db[index]["mean"]
            
    def set_orderbook(self,coinname,data):
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                self.db[index]["as"] = float(data['obu'][0]['as'])
                self.db[index]["bs"] = float(data['obu'][0]['bs'])
                self.db[index]["ap"] = float(data['obu'][0]['ap'])
                self.db[index]["bp"] = float(data['obu'][0]['bp'])
                    
                if not self.db[index]["uuid"]: #uuid값 유무 확인 
                    self.db[index]["is_trading"] = 0
                
                break
    
  
    
    def addavg(self,coinname,avg):
        # list = (item for item in self.db if item['name']==coinname)
        # db_list = next(list,False)
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                self.db[index]["avg"] = avg
                break
                
    def addtarget(self,coinname,open,closed,range,ROC_last,movingavg):
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                self.db[index]["range"] = range
                self.db[index]["ROC_last"] = ROC_last
                self.db[index]["speed"] = 0

                self.db[index]["before_target"] = self.db[index]["target"]    
                try:
                    self.db[index]["target"] = self.db[index]["mean"] + range
                except:
                    self.db[index]["mean"] = open
                    self.db[index]["target"] = open + range #타겟은 소수점자리수때문에 매수시 값보다 비싸게사게 되므로 실거래에선 gap을빼서 판단. 
                self.db[index]['now_target'] = self.db[index]['target']
                self.db[index]["closed"] = closed
                
                self.db[index]["before_movingavg"] = self.db[index]["movingavg"]
                self.db[index]["movingavg"] = movingavg
                # self.db[index]["price"].clear()
                # self.db[index]["price"].append(open)
                # if self.db[index]["is_trading"]==0:
                #     self.db[index]["before_mean_max"] = open
                #     self.db[index]["mean_max"] =open
                
                self.db[index]["open"] = open
                    
                self.db[index]["mean_min"] =open
                if (self.db[index]["HPR"] <= 1.000) : #수익률이 마이너스면 차단
                    print(coinname, "은 수익률이 낮아 주의를 요합니다.", f'HPR = {self.db[index]["HPR"]}, Range = {self.db[index]["range"]}, GAP = {self.db[index]["GAP"]}')
                    #self.db[index]["target"] = float('inf')
                
                    
                if self.db[index]["is_trading"] == 0:
                    self.db[index]["mean_min"] = 0
                    self.db[index]["mean_max"] = 0
                    self.db[index]["lock"] = 0  #이미 매수해서 잠겼던 코인을 해제 
                    self.db[index]["updated"]=0
                else:
                    self.db[index]["updated"]=1
                
                break

    # def update_cancel_open(self,coinname,open):
    #     for index,item in enumerate(self.db):
    #         if item['name']==coinname:
    #             if self.db[index]["is_trading"]==1: 
    #                 '''-----------------TODO movingavg로 할지 high값으로 할지 open으로 할지 고민중..!!!--------------------'''
    #                 if open > self.db[index]["open"]:  
    #                     self.db[index]["cancel"] = float(self.db[index]["cancel"]) + (open - float(self.db[index]["open"]))
    #                     self.db[index]["open"] = open
    #                     print("---하한선이 상승합니다.---")
    #                     return True
    #                 else:
    #                     pass
                    
            
    def adddata(self,coinname,k,window,cancel_per,MDD,HPR,ROC_mean,GAP):
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                self.db[index]["k"] = k
                self.db[index]["window"] = window
                self.db[index]["cancel_per"] = cancel_per
                self.db[index]["MDD"] = MDD
                self.db[index]["HPR"] = HPR
                self.db[index]["ROC_mean"] = ROC_mean
                self.db[index]["GAP"] = GAP
                print(self.db[index])
                break
        
    def set_trading(self,coinname,value:int):
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                self.db[index]["updated"]=0
                if value == 1:
                    self.db[index]['now_target'] = self.db[index]['target']
                    self.db[index]["before_target"] = self.db[index]["target"]  
                    self.db[index]["original_target"] = self.db[index]["target"]  
                    self.db[index]["break_time"] = 0
                    self.db[index]["is_trading"] = 1
                if value == 0:
                    self.db[index]["uuid"] = []
                    self.db[index]["target"] = self.db[index]["target"] + self.db[index]["range"] +  self.db[index]["ROC_mean"] #타겟 제거/ 버그때문에 float('inf')에서 수정 
                    print(f'타겟 삭제.')
                    self.db[index]["mean_min"] = 0
                    self.db[index]["mean_max"] = 0
                    self.db[index]["is_trading"] = 0
                    self.db[index]["lock"] = 0  #이미 매수해서 잠겼던 코인을 해제 
                #매수한 상품을 상단으로
                # sorted_list = sorted(self.db ,key=lambda x: x["is_trading"], reverse=True)
                # self.db = sorted_list
                
                break
                
    def add_uuid(self,coinname,value:int):
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                self.db[index]["uuid"].append(value)
                break
                
    def is_trading(self,coinname):
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                return self.db[index]["is_trading"]
        
    def set_lock(self,coinname):
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                self.db[index]["lock"] = 1
                break
                    
    def is_lock(self,coinname):
        for index,item in enumerate(self.db):
            if item['name']==coinname:
                return self.db[index]["lock"]
        
    def get(self,coinname):
        list = (item for item in self.db if item['name']==coinname)
        db_list = next(list,False)
        return db_list
    
    def reset(self):
        self.db=[]
        

if __name__ == '__main__':
    coin = Coin_database()
    coin.init(["test","KRW"])
    coin.addavg("KRW",10)
    print(coin.get("KRW"))
    coin.reset()
    coin2 = Coin_database()
    coin.init(["test","KRWw"])
    print(coin2.get("KRWw"))