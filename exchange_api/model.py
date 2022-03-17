# -*- coding: utf-8 -*-
"""
Created on Wed Apr 14 03:44:03 2021

@author: kmwh0
"""
'''
send price data to price_queue 

method:
    run_tracking()
    
    while True:
        if not self.price_queue.empty():
            data = price_queue.get() //receive json data
            print(data)
'''
from multiprocessing import Process
import multiprocessing as mp
import threading
import datetime
import time
from . import upbit as upbit
import asyncio
import os

uuid_list = []


process = None
price_queue = None

def producer(q,t): #멀티프로세서
    proc = mp.current_process()
    print("Process Name: ", proc.name)
    print(" __name__ : ",__name__)
    print("Thread Name: ", threading.currentThread().getName())
    try:
        asyncio.run(upbit.upbit_websocket(q,t))
    except:
        print("소켓문제: 멀티프로세서 재구동")
        time.sleep(10)
        producer(q,t)

'''
run to get coin price
params: ticker list
'''
def run_tracking(tickers,queue=None):
    global process,price_queue
    if process == None:
        #producer process
        price_queue = queue
        process = Process(name="droducer", target=producer, args=(queue,tickers), daemon=True)
        process.start()
    else:
        process.terminate()
        process = None
        #producer process
        process = Process(name="droducer", target=producer, args=(price_queue,tickers), daemon=True)
        process.start()

'''
get coin name list
params: ticker list
'''
def get_timing_level():
    return upbit.get_timing_level()

def set_timing_level(level):
    return upbit.set_timing_level(level)

def setKey(access,secret):
    return upbit.setKey(access,secret)

def get_coinlist():
    return upbit.get_upbit_coinlist()

def get_orderlist():
    return upbit.get_orderlist()

def order(name,price,count):
    return upbit.order(name,price,count)

def get_purchased(uuid):
    return upbit.check_purchased(uuid)

#return dataframe
def get_analyze(coinlist):
    return upbit.get_analyze(coinlist)

#return dataframe
def get_analyze_scalping(coinlist):
    return upbit.get_analyze_scalping(coinlist)

def get_target(coinname:str, interval:str , k, count):
    return upbit.get_target(coinname,interval,k,count)

def get_average(coinlist,interval,count):
    return upbit.get_average(coinlist,interval,count)

def get_realtiming():
    return upbit.real_timing

def get_timingname():
    return upbit.timing

def get_start_time(interval):
    return upbit.get_start_time(interval)

def get_purchased_count():
    return upbit.get_purchased_count()


def buy_crypto(name,price=None,volume=None):
    return upbit.buy_crypto(name,price,volume)

def sell_crypto(name):
    return upbit.sell_crypto(name)

def get_market_price(name,unit="1"):
    return upbit.get_market_price(name,unit)

if __name__ == '__main__':
    run_tracking([["KRW-XRP"]])
    print("나는 부모")
    time.sleep(5)
    os.system("pause")