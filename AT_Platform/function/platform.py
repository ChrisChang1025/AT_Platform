import requests, string, random
from AT_Platform.function import common


class platform :

    header = None
    api_url = None
    platform_url = None
    token = None

    def __init__(self, api_url=None, platform_url=None, token=None):
        self.api_url = api_url
        self.platform_url = platform_url
        self.token = token

    @property
    def token(self):
        return self.__token

    @token.setter
    def token(self, value):
        self.set_platform_header(token=value)
        self.__token = value

    def platform_login(self,account:str, password:str) -> bool:
        url = f'{self.api_url}/platform/user/token'
        payload = {
            "account": account,
            "password": common.login_pw_encrypt(password).decode("utf-8"),
            "clientNonce": None,
            "device": "pc"
        }
        response = requests.request("POST", url, headers=self.header, json=payload).json()
        if not response.get('data'):
            print('登入失敗: %s'%str(response))
            return False
        elif  response['data']['token']  == '':
            print('登入失敗: %s  , header : %s , payload: %s '% ( str(response) , self.header , payload )    )
            return False

        else:
            self.token = response['data']['token']
            return True
        
    def sport_login(self) -> str:
        url = f'{self.api_url}/platform/thirdparty/game/entry'
        Param = {
            "providerCode": 1,
            "device": "pc"
        }
        response = requests.request("GET", url, headers=self.header, params=Param).json()
        if not response.get('data'):
            print(f"Sport login fail : {response.get('msg')}")
            return None #response.get('msg')
        else:
            return response['data']['token']
        
    def getwallet(self,currency:str) -> str:
        url = f'{self.api_url}/platform/payment/wallets/list'# info 改成 list
        response = requests.get(url, headers=self.header).json()
        for currency_wallet in response['data']['wallets']:# #抓出的response wallet 是一個 List ,裡面包 各個 currency 的字典
            if currency == currency_wallet['currency']: # 找到 帶入 的currency 參數
                return currency_wallet['amount']# string 
        return None

    def set_platform_header(self,token=None, x_uuid=None):
        characters = string.ascii_letters + string.digits
        self.header= {
            "origin": self.platform_url,
            "referer": self.platform_url,
            "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4044.141 Safari/537.36",
            "devicemode": "Pixel 5",
            "apptype": "2",
            "device":"mobile",
            "content-type": "application/json;charset=UTF-8",
            "x-uuid":''.join(random.choice(characters) for i in range(20))
        }
        
        if token is not None:
            self.header.update({"authorization": "Bearer " + str(token)})


