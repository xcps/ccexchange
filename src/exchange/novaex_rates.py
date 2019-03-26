#!/usr/bin/python3
import json
import requests

RATES_API_URL = "https://novaexchange.com/remote/v2/market/openorders/BTC_ANC/BOTH/"
proxies = {
    "http":"socks5://localhost:9050",
    "https":"socks5://localhost:9050"
}

def get_data_from_novaex():
    response = requests.get(RATES_API_URL, proxies=proxies)
    raw_result = response.text
    data = json.loads(raw_result)
    return data

def get_ancbtc_rate():
    return get_data_from_novaex()

if __name__ == '__main__':
    print(get_ancbtc_rate())
