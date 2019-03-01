import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import configparser

# config
config = configparser.ConfigParser()
config.read('./config.txt') # you should create config.txt
accountID = config['oanda']['account_id']
access_token = config['oanda']['api_key']

import json
from oandapyV20 import API
from oandapyV20.exceptions import V20Error
from oandapyV20.endpoints.pricing import PricingStream
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.trades as trades

# OANDAのデモ口座へのAPI接続
api = API(access_token=access_token, environment="practice")

import time

ps = PricingStream(accountID=accountID, params={'instruments': 'EUR_USD'})
profit = 0.0001
loss = 0.0020
units = 10000
opentrades_req = trades.OpenTrades(accountID=accountID)

if __name__ == '__main__':
    while True:
        bt = api.request(opentrades_req)
        for s in api.request(ps):
            keys = s.keys()
            if ('bids' in keys) and ('asks' in keys):
                bid = float(s['bids'][0]['price'])
                ask = float(s['asks'][0]['price'])

                #-----------------#
                price = bid
                direct = -1
                #-----------------#

                deal_order = orders.OrderCreate(accountID, data={
                                                  "order": {
                                                      "price":f"{price}",
                                                    "instrument": "EUR_USD",
                                                    "units": f"{direct*units}",
                                                    "type": "LIMIT",
                                                    "positionFill": "DEFAULT",
                                                    'takeProfitOnFill': {
                                                       'timeInForce': 'GTC',
                                                       'price': f'{price+direct*profit:.5f}'},
                                                    'stopLossOnFill': {
                                                       'timeInForce': 'GTC',
                                                       'price': f'{price-direct*loss:.5f}'}
                                                  }})
                res = api.request(deal_order)
                limit_time = 5
                start = time.time()
                at = api.request(opentrades_req)
                while len(at['trades'])<=len(bt['trades']) and not (time.time()-start)>limit_time:
                    at = api.request(opentrades_req)
                if (time.time()-start)>limit_time:
                    #注文が通らなかった
                    print('注文が通らなかった')
                    r = orders.OrdersPending(accountID)
                    api.request(r)
                    cancel_req = orders.OrderCancel(accountID=accountID, orderID=r.response['orders'][0]['id'])
                    api.request(cancel_req)
                    time.sleep(5)
                    break
                #注文が通った
                print('注文が通った', price)
                bt = at

                #指値が通るのを待つ
                limit_time = 60*60*4
                start = time.time()
                at = api.request(opentrades_req)
                while len(at['trades'])>=len(bt['trades']) and not (time.time()-start)>limit_time:
                    at = api.request(opentrades_req)
                if (time.time()-start)>limit_time:
                    #時間切れで決済
                    print('時間切れで決済')
                    trade_id = at['trades'][0]['id']
                    r = trades.TradeClose(accountID=accountID, tradeID=trade_id, data={'units':str(units)})
                    api.request(r)
                    time.sleep(5)
                    break
                else:
                    #指値が通った
                    print('指値が通った')
                    break

            else:
                continue
