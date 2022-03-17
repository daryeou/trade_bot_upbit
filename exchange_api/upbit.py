# -*- coding: utf-8 -*-
'''
ticker에 interval 값 추가하고 사용자가 타임주기 선택할 수 있도록
갑자기 물량 흔들리는 경우를 대비해서 3초간 모은 웹소켓 데이터를 리스트에 3담아서 평균내서 화면에 표시하고 초기화
'''
"""
Created on Wed Apr 14 03:41:10 2021

@author: kmwh0
"""
import os

fixed_IP=""
_AccessKey=""
_SecretKey=""

def setKey(access,secret):
    global _AccessKey, _SecretKey
    _AccessKey=access
    _SecretKey=secret
    os.environ['UPBIT_OPEN_API_ACCESS_KEY'] = _AccessKey
    os.environ['UPBIT_OPEN_API_SECRET_KEY'] = _SecretKey
    
os.environ['UPBIT_OPEN_API_SERVER_URL'] = "https://api.upbit.com"

import pyupbit
import asyncio
import requests
import json
import websockets
import numpy as np
import traceback
from decimal import Decimal
import collections
from pandas import DataFrame
import pandas as pd
from deprecated import deprecated

@deprecated
def print_price():
    # tickers = pyupbit.get_tickers(fiat="KRW")
    # print(tickers)
    # price = pyupbit.get_current_price(["KRW-XRP","KRW-ETH"])
    # price_name = list(price.keys())
    # price_list = list(price.values())
    # print(f'{price_name[0]}:{price_list[0]}원')
    # print(f'{price_name[1]}:{price_list[1]}원')
    pass

@deprecated
def save_excel(coinname):
    df = pyupbit.get_ohlcv(coinname,interval="minute1",count=200)
    df.to_excel(f"{coinname}.xlsx")
    

'''
params: tickers list
return coinlist dict
{'market': ... , 'korean_name':..., 'english_name':...}
'''
def get_upbit_coinlist(market_name="KRW"):
    url = "https://api.upbit.com/v1/market/all"
    querystring = {"isDetails":"false"}
    json_coinlist = requests.request("GET", url, params=querystring)
    coinlist = json.loads(json_coinlist.text)
    coinlist = [x for x in coinlist if market_name in x['market'] ] #한화 마켓을 기본값으로
    return coinlist



'''실시간 웹소켓으로 시세 수신'''
async def upbit_ws_client(q,t):
    uri = "wss://api.upbit.com/websocket/v1"

    async with websockets.connect(uri) as websocket:
        subscribe_fmt = [ 
            {"ticket":"test"},
            {
                "type": "ticker",
                "codes": t, #coin names list #TODO 수정할것!!!!
                "isOnlyRealtime": True
            },
            {
                "type":"orderbook",
                "codes":[f'{x}.1' for x in t]
            },
            {"format":"SIMPLE"}
        ]
        subscribe_data = json.dumps(subscribe_fmt)        
        await websocket.send(subscribe_data)

        while True:
            data = await websocket.recv()
            #await asyncio.sleep(1)
            data = json.loads(data)
            q.put(data)


async def upbit_websocket(q,t):
    await upbit_ws_client(q,t)


'''chance order'''
import os
import jwt
import uuid
import hashlib
import datetime
from urllib.parse import urlencode

uuid_list = []

def buy_crypto(name,price=None,volume=None):
    global uuid_list
    try:
        access_key = os.environ['UPBIT_OPEN_API_ACCESS_KEY']
        secret_key = os.environ['UPBIT_OPEN_API_SECRET_KEY']
        server_url = os.environ['UPBIT_OPEN_API_SERVER_URL']
        qeury=None
        
        # if price == None:
        #     query = {
        #         'market': name,
        #         'side': "bid",
        #         'price': price,
        #         'ord_type': "price",
        #     }
        # else:
        #     query = {
        #         'market': name,
        #         'side': "bid",
        #         'volume':volume,
        #         'price': price,
        #         'ord_type': "limit",
        #     }
        
        query = {
                'market': name,
                'side': "bid",
                'price': price,
                'ord_type': "price",
            }
            
        query_string = urlencode(query).encode()
        
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
        
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
        
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
        
        res = requests.post(server_url + "/v1/orders", params=query, headers=headers, timeout=3)
        print(res.status_code)
        if (res.status_code == 200) | (res.status_code == 201):
            print("purchase registered")
            uuid_list.append(res.json()["uuid"])
            print(json.loads(res.text))
        else:
            print("purchase failed : ",json.loads(res.text))
        return [res.status_code,json.loads(res.text)]
    except:
        return [400,"error"]

def sell_crypto(name):
    global uuid_list
    try:
        access_key = os.environ['UPBIT_OPEN_API_ACCESS_KEY']
        secret_key = os.environ['UPBIT_OPEN_API_SECRET_KEY']
        server_url = os.environ['UPBIT_OPEN_API_SERVER_URL']
        
        data=get_orderlist()
        info = [x for x in data if f'{x["unit_currency"]}-{x["currency"]}'== name][0]
        print(info)
        
        query = {
            'market': name,
            'side': "ask",
            'volume': info["balance"],
            'ord_type': "market",
        }
        query_string = urlencode(query).encode()
        
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
        
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
        
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
        
        res = requests.post(server_url + "/v1/orders", params=query, headers=headers, timeout=3)
        print(res.status_code)
        if (res.status_code == 200) | (res.status_code == 201):
            print("purchase registered")
            uuid_list.append(res.json()["uuid"])
        else:
            print("purchase failed",json.loads(res.text))
        return [res.status_code,json.loads(res.text)]
    except:
        return [400,"error"]
    
def get_purchased_count():
    return len(uuid_list)
        
def get_orderlist():
    access_key = os.environ['UPBIT_OPEN_API_ACCESS_KEY']
    secret_key = os.environ['UPBIT_OPEN_API_SECRET_KEY']
    server_url = os.environ['UPBIT_OPEN_API_SERVER_URL']
    
    payload = {
    'access_key': access_key,
    'nonce': str(uuid.uuid4()),
    }
    
    jwt_token = jwt.encode(payload, secret_key)
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}
    
    res = requests.get(server_url + "/v1/accounts", headers=headers)
    
    return(res.json())

def check_purchased(uuid):
    access_key = os.environ['UPBIT_OPEN_API_ACCESS_KEY']
    secret_key = os.environ['UPBIT_OPEN_API_SECRET_KEY']
    server_url = os.environ['UPBIT_OPEN_API_SERVER_URL']
    
    query = {
        'uuid': uuid,
    }
    query_string = urlencode(query).encode()
    
    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()
    
    payload = {
        'access_key': access_key,
        'nonce': str(uuid.uuid4()),
        'query_hash': query_hash,
        'query_hash_alg': 'SHA512',
    }
    
    jwt_token = jwt.encode(payload, secret_key)
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}
    
    res = requests.get(server_url + "/v1/order", params=query, headers=headers)
    
    return(res.json())
    
    
def get_start_time(interval):
    try:
        ticker="KRW-BTC"
        df = pyupbit.get_ohlcv(ticker,interval=interval,count=1)
        return df.index[-1]
    except:
        return get_start_time(interval)
    
def calc_unit(value):
        if value >= 2000000:
            return 1000
        elif value >= 1000000:
            return 500
        elif value >= 500000:
            return 100
        elif value >= 100000:
            return 50
        elif value >= 10000:
            return 10
        elif value >= 1000:
            return 5
        elif value >= 100:
            return 1
        elif value >= 10:
            return 0.1
        else:
            return 0.01
            

analyze_data =[]
timing_level = 7
interval_list=["minute1","minute3","minute5","minute10","minute15","minute30","minute60","minute240","day"]
realtime_list=[60,180,300,600,900,1800,3600,14400,86400]
timing= "minute60" #테스트용으로 수정할것
real_timing=None
count_limit = 1000

def get_timing_level():
    global timing_level
    return timing_level

def set_timing_level(level):
    global timing_level,timing,real_timing
    timing_level = level
    timing=interval_list[timing_level] #글로벌 타이밍 설정
    real_timing=realtime_list[timing_level]

def get_ror_scalping(df: DataFrame, GAP, k: float, window: int, cancel_per:float):
    df['range'] = (df["rate_of_change"]) * k
    df['target'] = 0
    if window==0:
        df['moving_average'] = 0
    else:
        df['moving_average'] = df['close'].rolling(window=window).mean().shift(1) #이동평균선 window=기간
    df['target'] = df['open'] + df['range'].shift(1)
    df['target'] = np.where(df['target']>df['moving_average'], df['target'], df['moving_average']) #이동 평균을 타겟에 포함할 것인지
    df['target'] = (df['target'] - (df['target']%GAP) + GAP)
    #df['bull'] = df['open'] >= df['moving_average']
    #df['bull'] = df['low'] >= df['moving_average']
    
    df['ror'] = 1
    df['purchase'] = 0
    df['high_sub'] = 0
    #df['low_sub'] = 0
    #df['cancel_price']=0
    for i in range(window,len(df)):
        if df.iloc[i-1]["purchase"] == 0:
            if (df.iloc[i]['high'] >= df.iloc[i]['target']) :
                df.iloc[i,df.columns.get_loc('high_sub')] = (df.iloc[i]['high'])
                # if df.iloc[i]['close'] < cancel_price:
                #     df.iloc[i,df.col파이썬 파라미터 소수점umns.get_loc('purchase')] = -1
                #     df.iloc[i,df.columns.get_loc('ror')] = ( (cancel_price) / (df.iloc[i]['target']*1.0005) )*0.9995 #중간에 매도할 경우
                # else:
                df.iloc[i,df.columns.get_loc('purchase')] = 1
                df.iloc[i,df.columns.get_loc('ror')] = (df.iloc[i]['close'] / df.iloc[i]['target'] )*0.9995
            else:
                # df.iloc[i,df.columns.get_loc('ror')] = 1
                # df.iloc[i,df.columns.get_loc('purchase')] = 0
                pass #속도를 위해 생략
        elif df.iloc[i-1]["purchase"] == 1:
            df.iloc[i,df.columns.get_loc('high_sub')] = (df.iloc[i-1]['high_sub'] if (df.iloc[i-1]['high_sub']>df.iloc[i]['high']) else df.iloc[i]['high'])
            cancel_price = (df.iloc[i]['high_sub'] - (df.iloc[i-1]['rate_of_change']*cancel_per))
            cancel_price = (cancel_price - (cancel_price%GAP) - GAP)
            #df.iloc[i,df.columns.get_loc('cancel_price')] = cancel_price - (cancel_price%GAP) - GAP #only using for Debugging
            '''and df.iloc[i]['close'] < df.iloc[i-1]['moving_average']  이동평균을 매도점에 포함할 것인지'''
            if df.iloc[i]['close'] <= cancel_price: 
                df.iloc[i,df.columns.get_loc('ror')] = ((df.iloc[i]['close']) / df.iloc[i-1]['close'])*0.9995 #종가에 팔 경우
                #df.iloc[i,df.columns.get_loc('ror')] = ( cancel_price / df.iloc[i-1]['close'] )*0.9995 #calcel_price에 팔 경우
                df.iloc[i,df.columns.get_loc('purchase')] = 0
            else:
                df.iloc[i,df.columns.get_loc('ror')] = (df.iloc[i]['close']) / df.iloc[i-1]['close']
                df.iloc[i,df.columns.get_loc('purchase')] = 1
                
   
    '''------------------------------------------------테스트문구-----------------------------------------------------------'''
 
    '''------------------------------------------------테스트문구------------------------------------------------------------'''
    
    # df['ror'] = np.where((df['ror'].shift(1) == 1.0) & (df['ror'] != 1.0), (df['ror']*0.9995),df['ror']) #슬리피지 감안하여 0.995가 아닌 0.990을 곱함!!
    # df['ror'] = np.where((df['ror'].shift(1) != 1.0) & (df['ror'] == 1.0), (df['ror']*0.9995),df['ror'])

    ror = df['ror'].cumprod()[-2]
    return ror

#params : coinname:str, interval: dataframeInterval['day','minute5...], count:<200, window:이동평균 몇일?
def calc_df_scalping(coinname: str):
    try:
        global timing, count_limit
        final_ror = 0
        final_k = 0.50
        final_window=3
        final_cancel_percent=0.83
        
        df = pyupbit.get_ohlcv(coinname,interval=timing,count=count_limit)
        GAP = calc_unit(df['open'][-1])
        #df.loc[df.index[-1]+datetime.timedelta(hours=24)]=[0,0,0,0,0] #열 추가인데 필요없음..
        df["rate_of_change"] = df['high']-df['low']
        
        counter = collections.Counter(df["rate_of_change"].tolist())
        unit_k = 1/((max([x[0] for x in counter.most_common(1)]))/GAP) 
        unit_k = (unit_k if unit_k >= 0.2 else 0.2) #최소단위 0.2 즉 20%
        for k in np.arange(0.0,2.0,unit_k): #k값 지정
            for window in np.arange(3,8,1): #window 표준데이터 수 개수 지정
                for cancel_per in np.arange(2.0,0.0,unit_k*(-1)):
                    print(f"calculating {coinname}:k={k:.1f},{window=},cancel_per={cancel_per:.1f}")
                    result_ror = get_ror_scalping(df,GAP,k,window,cancel_per)
                    if result_ror > final_ror:
                        final_ror = result_ror
                        final_k = k
                        final_window = window
                        final_cancel_percent=cancel_per

        final_ror = get_ror_scalping(df,GAP,final_k,final_window,final_cancel_percent) #df를 수정

        roc_mean = (df["rate_of_change"].mean()) #rateofchange 는 하락변동폭 방지를 위한 값. 
        df['holding_period_return'] = df['ror'].cumprod() #holding period return 누적곱셈사용, final_ror값과 같음
        df['maximum_draw_down'] = ((df['holding_period_return'].cummax() - df['holding_period_return'] )/df['holding_period_return'].cummax()) #누적맥스사용
        
        try:
            df.to_excel(f'{coinname}.xlsx')
            print("저장")
        except:
            #traceback.print_exc(limit=None,chain=True)
            print("저장실패")
        result=({"name":coinname,"k":final_k,"window":final_window,"cancel_per":final_cancel_percent,"MDD":df['maximum_draw_down'].max(), "HPR":df['holding_period_return'][-2],"ROC_mean":roc_mean,"GAP":GAP})
        print(f'--{coinname} : Profit:{final_ror:.4f}, {final_k:.2f} {final_window} {final_cancel_percent:.2f}--')
        #print(df['2021'])
        return result
    except:
        traceback.print_exc(limit=None,chain=True)
        return 1
#최대 안정성 및 수익 (단타,장타용) bull을 이용하여 판단
def get_analyze_scalping(coinname):
    data=calc_df_scalping(coinname) #여기선 5일 이동 평균..변경할것
    # sorted_hprs = sorted(data ,key=lambda x: x["HPR"], reverse=True)
    # print(dict(zip([x["name"] for x in sorted_hprs],[x["HPR"] for x in sorted_hprs])))
    return data

''' 이동평균선만 분석 '''
#params interval:주기 count:평균에 사용할 지표수
def get_average(coinname,interval,count):
    try:
        print("전달 받은 값",coinname,interval,count)
        # if interval == None:
        #     global analyze_data, timing
        #     info = next((item for item in analyze_data if item['name']==coinname),None)
        #     interval = timing
        #     count=info["window"]+1
        df = pyupbit.get_ohlcv(coinname,interval=interval,count=count+1)
        close = df['close']
        if(count <= 0):
            close_mean = 0
        else:
            close_mean=close.rolling(window=count).mean()[-2]
        return [coinname,close_mean]
    except:
        traceback.print_exc(limit=None,chain=True)



'''db.py의 Coin_database instance를 넘김->analyze_data'''
def get_target(coinname:str, interval, k, count):
    try:
        df = pyupbit.get_ohlcv(coinname,interval=interval,count=count+2)
        df["rate_of_change"] = df['high']-df['low']
        df['range'] = (df["rate_of_change"]) * k
        #df['target'] = df['open'] + df['range'].shift(1)
    
        if count==0:
            df['moving_average'] = 0
        else:
            df['moving_average'] = df['close'].rolling(window=count).mean().shift(1) #이동평균선 window=기간
            
        # df['compare_target'] = np.where(df['target'].replace(np.nan,float('inf')) > df['moving_average'].replace(np.nan,float('inf')), 
        #                                 df['target'].replace(np.nan,float('inf')),df['moving_average'].replace(np.nan,float('inf')))
        #거래 취소 구간, 타겟 값, bull판단을 위한 이동평균값:0일 경우 무시
        
        try:
            #df.to_excel(f'{coinname}-temp.xlsx')
            print("저장")
        except:
            traceback.print_exc(limit=None,chain=True)
            print("저장실패")
                
        return [coinname,df['open'][-1],df['close'][-2],df['range'][-2],df["rate_of_change"][-2],df['moving_average'][-1]]
    except:
        print("타겟을 얻어오는데 실패했습니다. 재시도합니다.")
        return get_target(coinname, interval, k, count)

def get_market_price(coinname:str, unit = "1" , count = "5"):
    try:
        url = "https://api.upbit.com/v1/candles/minutes/1"
        querystring = {"unit":"1","market":"KRW-XRP","count":"5"}
        response = requests.request("GET", url, params=querystring)
        return(response.json())
    except:
        print("마켓 가격 조회 실패. 재수행합니다.")
        return get_market_price(coinname, unit)
    
def second_smallest_num(arr):
    second = smallest = float('inf')
    for n in arr:
        if n < smallest:
            second = smallest
            smallest = n
        elif second > n > smallest:
            second = n
    return second
        
    

if __name__ == '__main__':
    print ("test")
    print(get_market_price("KRW-MED","30","2"))
    #get_analyze(["KRW-BTC"])
    #get_analyze(["KRW-BTC","KRW-XRP","KRW-BTT"])
    get_analyze_scalping(["KRW-QTUM"])
    # print(analyze_data)
    # print(get_target("KRW-XRP"))
    #buy_crypto("KRW-BTC",1)
    os.system("pause")

    
'''데이터 수집 비동기화. 약 3초정도 단축.
async def try_get_ohlcv(loop,coinname,interval="day",count=30):
    df = await loop.run_in_executor(None,pyupbit.get_ohlcv,*[coinname,interval,count])
    if type(df) is not DataFrame:
        await asyncio.sleep(1.1)
        return await try_get_ohlcv(loop,coinname,interval,count)
    return df
#params : coinname:str, fee :float(percent)
async def calc_df(loop, coinname: str,fee : float):
    try:
        df = await try_get_ohlcv(loop,coinname)
        final_ror =0
        final_k = 0
        final_fee = fee * 0.01
        for k in np.arange(0.1,1.0,0.01):
            result_ror = get_ror(df,k,fee)
            if result_ror > final_ror:
                final_ror = result_ror
                final_k = k
            #print(f'{k:.2f} {result_ror:.2f}')
        df['moving_average5'] = df['close'].rolling(window=5).mean().shift(1) #이동평균선 window=기간
        df['range'] = (df['high'] - df['low']) * final_k
        df['target'] = df['open'] + df['range'].shift(1)
        df['bull'] = df['open'] > df['moving_average5']
        df['rate_of_returns'] = np.where(df['high'] > df['target'], 
                             (df['close']-df['close']*final_fee) / (df['target']+df['target']*final_fee),1) #TODO Check the mathematical expression
        df['holding_period_return'] = df['rate_of_returns'].cumprod() #holding period return 누적곱셈사용
        df['maximum_draw_down'] = (df['holding_period_return'].cummax() - df['holding_period_return'] )/df['holding_period_return'].cummax() * 100 #누적맥스사용
        print("Maximum Draw Down(%) : ",df['maximum_draw_down'].max())
        print("Holding Period Return(%) : ",df['holding_period_return'][-2])
        print(f'--{final_k:.2f} {final_ror:.2f}--')
        await loop.run_in_executor(None,df.to_excel,(f'{coinname}.xlsx'))
        return df['holding_period_return'][-2]
    except:
        return 1
    
async def get_analyze(coinlist,loop):
    hprs = []
    list = coinlist
    print(list)
    futures = [calc_df(loop,ticker,0.05) for ticker in list]
    hprs = {name:value for name,value in zip(list,await asyncio.gather(*futures))}
    sorted_hprs = sorted(hprs,key=lambda x: x[1], reverse=True)
    print(sorted_hprs[:5])
    return sorted_hprs[:5]

def get_analyze_run(coinlist):
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(get_analyze(coinlist,loop))
    loop.close()
    print(result)
        
if __name__ == '__main__':
    print ("test")
    get_analyze_run()
'''
