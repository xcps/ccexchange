#!/usr/bin/python3
import urllib.request
import urllib.parse
import simplejson as json


class RPCCaller:

    _req_id = 0
    opener = None

    def __init__(self, username=None, password=None, url=None):
        if username and password and url:
            self.init(username, password, url)

    def init(self, username, password, url):
        self._req_id = 0
        self.url = url
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.url, username, password)
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        self.opener = urllib.request.build_opener(handler)

    def _get_request_id(self):
        self._req_id += 1
        return self._req_id

    def check_received(self, address):
        return self.rpc_request('getreceivedbyaddress', [address,])

    def get_info(self):
        return self.rpc_request('getinfo', [])

    def get_mining_info(self):
        return self.rpc_request('getmininginfo', [])

    def get_network_hashes(self):
        return self.rpc_request('getnetworkhashps', [])

    def get_balance(self):
        return self.rpc_request('getbalance', [])

    def create_new_address(self):
        return self.rpc_request('getnewaddress', [])

    def get_transactions(self, count=100):
        return self.rpc_request('listtransactions', ["", count])

    def send_coins(self, address, amount, passphrase):
        import logging;logging.error(address, amount, passphrase)
        if passphrase:
            self.rpc_request('walletpassphrase', [passphrase, 5,])
        return self.rpc_request('sendtoaddress', [address, amount,])

    def is_address_valid(self, address):
        is_valid = False
        response = self.rpc_request('validateaddress', [address,])
        if response['isvalid'] == True:
            is_valid = True
        return is_valid

    def rpc_request(self, method, params):

        values = {
            'method': method,
            'params': params,
            'id': self._get_request_id(),
        }
        data = '{}\n'.format(json.dumps(values))
        import logging;logging.error(data)
        try:
            req = urllib.request.Request(self.url,
                                        data.encode('utf-8'))
            # response = urllib.request.urlopen(req)
            response = self.opener.open(req)
        except Exception as ex:
            import logging;logging.error(ex.read())
            print('error {}'.format(ex))
            raise ex
        result = json.loads(response.read().decode())['result']
        return result

def run(username, password):
    rpc = RPCCaller(username, password, 'http://127.0.0.1:9376')
    print(rpc.get_transactions())

if __name__ == "__main__":
    import sys
    run(sys.argv[1], sys.argv[2])
