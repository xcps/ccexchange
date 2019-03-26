#!/usr/bin/python3
import json
import urllib.request

RATES_API_URL = "http://nvspc.i2p/api/dummy/getstockglass?t=3&c=30"
PROXY_URL = 'http://localhost:4444'

def get_data_from_nvspc():
    proxy_handler = urllib.request.ProxyHandler({
        'http': PROXY_URL
    })
    opener = urllib.request.build_opener(proxy_handler)
    response = opener.open(RATES_API_URL)
    raw_result = response.read().decode()
    data = json.loads(raw_result)['data']
    return data

def decide_myrates(data, percent=10):
    sell_ = 0
    amount = 0
    for sell in reversed(data['Sell']):
        amount += sell['amount']
        if amount > 1000:
            sell_ = sell['cost']
            break

    buy = 0
    amount = 0
    for sell in data['Buy']:
        amount += sell['amount']
        if amount > 1000:
            buy = sell['cost']
            break
    print('sell', sell_, 'buy', buy)
    print('sell', (sell_*(percent+100)/100), 1/(sell_*(percent+100)/100), 'buy', buy/(((percent+100)/100)))
    

def get_gstbtc_rate():
    return decide_myrates(get_data_from_nvspc(), 20)


if __name__ == '__main__':
    get_gstbtc_rate()
