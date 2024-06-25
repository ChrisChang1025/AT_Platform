import requests, random, json, uuid, time, pytz
from datetime import datetime as dt

class sport :

    header = None
    api_url = None
    platform_url = None
    stoken = None
    env = None

    def __init__(self,env=str, api_url=None, platform_url=None, stoken=None):
        self.env = env
        self.api_url = api_url
        self.platform_url = platform_url
        self.stoken = stoken

    @property
    def stoken(self):
        return self.__stoken

    @stoken.setter
    def stoken(self,value):
        self.set_sport_header(value)
        self.__stoken = value  

    def get_match_info(self,sid, iid, inplay):
        if inplay == True:
            path = self.api_url + f"/product/business/sport/inplay/match?sid={sid}&iid={iid}"
        else:
            path = self.api_url + f"/product/business/sport/prematch/match?sid={sid}&iid={iid}"
            
        try:
            response = requests.get(path, headers=self.header)
            response.raise_for_status()  # Raises an exception for HTTP errors (status codes >= 400)
            data = response.json()
            
            if data.get('code') == 0 and 'data' in data and 'data' in data['data'] and 'market' in data['data']['data']:
                retval = data['data']['data']
            else:
                print(f"Unexpected response structure or code: {data.get('code')}")
        
        except json.JSONDecodeError as json_error:
            print(f"JSON decoding error: {json_error}")
        except requests.RequestException as request_error:
            print(f"Request error: {request_error}")
        except Exception as e:
            print(f"Exception : {e}")

        return retval

    def bet_process(self, params):
        fail_msg = ''
        sid = params['sid']
        inplay = params['inplay']
        iid_list = params['iid'].split(',')
        bet_market_list = dict()
        property_dict = self.get_score_type()
        for idx in range(0, len(iid_list)):
            iid = iid_list[idx]
            try:
                if inplay == True or inplay == 'True':
                    match_data = self.get_match_info(sid=sid, iid=iid, inplay=True)
                else:
                    match_data = self.get_match_info(sid=sid, iid=iid, inplay=False)
            except Exception as e :
                fail_msg = "Can't get correct match info"
                continue
                
            if 'market' in match_data and len(match_data['market']) > 0 :                    
                markets = match_data['market']
                for mk, mk_value in markets.items():                        
                    if 'bet_market' in params and params['bet_market'] !='None' and mk not in params['bet_market']:
                        continue
                    score_type= property_dict[str(sid)][mk]['mkScoreType']                        
                    if 'detail' in match_data and score_type in match_data['detail']:
                        score = match_data['detail'][score_type]
                    else:
                        score = '0-0'
                        
                    oddslist = self.parse_odds(mk_value)                            

                    for i in range(len(oddslist)):   
                        tmp = oddslist[random.choice(range(len(oddslist)))]                         
                        if tmp['beton'] == 'absK': 
                            continue
                                
                        if float(tmp['odds']) > 0:
                            new_odds = tmp['odds']
                            tickets=[{
                                    "sid": sid,
                                    "iid": iid,
                                    "tid": match_data['tid'],
                                    "beton": tmp['beton'],        
                                    "inp": inplay,
                                    "k": tmp['k'],
                                    "market": mk,
                                    "odds": new_odds,
                                    "score": score,
                                    "outright": "false",
                                    "vd": match_data['vd']
                                }]

                            try:
                                if float(new_odds) > 0 and (params['market'].lower() == 'all' or mk in params['market'].split(',')):
                                    if mk in bet_market_list : 
                                        bet_market_list[mk].append(tickets[0])
                                    else:
                                        bet_market_list[mk] = tickets                            
                                                    
                            except Exception as e:                                    
                                print(f"Bet process exception : {e}")
                                
            generate_data = lambda num: [{
                                "idx": idx,
                                "ante": params['ante'],
                                "transId": params['account'] + '_' + str(uuid.uuid4()).replace('-', '') + str(time.time())
                            } for idx in range(num)]
            result_list = []
            pass_count = 0
            fail_count = 0        
            for market in bet_market_list.keys():
                length = len(bet_market_list[market]) if len(bet_market_list[market]) < 10 else 10
                singles = generate_data(length)
                bet_payload = {
                                "marketType": "EU",
                                "currency": params['currency'],
                                "outrights": [],
                                "parlays": [],
                                "singles": singles,
                                "tickets": bet_market_list[market][:length]
                             }                
                bet_results, p_count, f_count, msg = self.bet(bet_payload)
                pass_count+=p_count
                fail_count+= f_count
                fail_msg+=f"\n{msg}"
                for bet_result in bet_results:
                    bet_result.insert(0,len(result_list)+1)
                    result_list.append(bet_result)
                time.sleep(1)
            return result_list, pass_count, fail_count, fail_msg

    def bet(self, bet_payload) -> list:
        path = self.api_url + f"/product/game/bet"
        pass_count = 0
        fail_count = 0
        fail_msg = ''
        result = [] #["投注時間","賽事代號","盤口代號","投注項","K值","賠率","注單號","投注結果"]]
        try :            
            bet_time = dt.now().astimezone(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')
            response = requests.post(path, headers=self.header,json=bet_payload)
            response.raise_for_status()  
            data = response.json()
            if data.get('code') == 0:
                # print(f"pass : {data['data']['submitted']['singles']} , fail : {data['data']['failed']['singles']}")
                if 'submitted' in data['data'] and 'singles' in data['data']['submitted'] and len(data['data']['submitted']['singles']) > 0:
                    for i in  data["data"]["submitted"]["singles"]:
                        bet_info = bet_payload['tickets'][i['idx']]
                        result.append([bet_time,bet_info['iid'],bet_info['market'],bet_info['beton'],bet_info['k'],bet_info['odds'],i['orderno'],"OK"])
                        pass_count+=1

                if 'failed' in data['data'] and 'singles' in data['data']['failed']  and len(data['data']['failed']['singles']) > 0:
                    for i in  data["data"]["failed"]["singles"]:
                        bet_info = bet_payload['tickets'][i['idx']]
                        result.append([bet_time,bet_info['iid'],bet_info['market'],bet_info['beton'],bet_info['k'],bet_info['odds'],i['subCode'],"Fail"])
                        fail_count+=1
            else:       
                 for i in  range(len(bet_payload['tickets'])):
                    bet_info = bet_payload['tickets'][i]
                    result.append([bet_time,bet_info['iid'],bet_info['market'],bet_info['beton'],bet_info['k'],bet_info['odds'],data.get('code'),"Fail"])
                    fail_count+=1
            
        except json.JSONDecodeError as json_error:
            fail_msg= f"bet JSON decoding error: {json_error}"
        except requests.RequestException as request_error:
            for i in  range(len(bet_payload['tickets'])):
                bet_info = bet_payload['tickets'][i]
                result.append([bet_time,bet_info['iid'],bet_info['market'],bet_info['beton'],bet_info['k'],bet_info['odds'],response.status_code,"Fail"])
                fail_count+=1
        except Exception as e:
            fail_msg = f"bet Exception : {e}"
        finally:
            return result, pass_count, fail_count, fail_msg
                    
    def get_score_type(self):
        
        try:
            if self.env == 'pre-prod':            
                path = f'{self.api_url}/platform/systatus/proxy/sports/prod/Java/json/zh-cn/market_property_setting'
            else:
                path = f'{self.api_url}/platform/systatus/proxy/sports/{self.env}/Java/json/zh-cn/market_property_setting'
            
            response = requests.request("GET", path).json()
            response['1'] = response.pop('football')
            response['2'] = response.pop('basketball')
            response['3'] = response.pop('tennis')
            response['4'] = response.pop('baseball')
            return response
        except Exception as e:
            print('get_score_type error: %s'%e)
            return {'1':{},'2':{},'3':{},'4':{}}

    def parse_odds(self , odds_set):
        odds_lists = []

        if type(odds_set) is dict:
            k=''
            odds_info={}
            for tmpKey, tmpValue in odds_set.items():
                if tmpKey == 'k':
                    k=tmpValue
                else :
                    beton=tmpKey
                    odds=tmpValue
                    odds_info = {
                            'k': k,
                            'beton' : beton,
                            'odds': odds
                        }
                    odds_lists.append(odds_info)
        elif type(odds_set) is list:
            for i in range(0,len(odds_set)):
                k=''
                beton=''
                odds=''                
                
                for tmpKey, tmpValue in odds_set[i].items():
                    odds_info={} # 紀錄整理完的賠率組合
                    if tmpKey=='k' and len(odds_set[i])>2 :
                        k=tmpValue
                    elif tmpKey=='k' and len(odds_set[i])==2 :
                        beton=tmpValue
                    elif tmpKey=='o' and len(odds_set[i])==2 :
                        odds=tmpValue
                        odds_info = {
                            'k': k,
                            'beton' : beton,
                            'odds': odds
                        }
                        if beton != "absK" :
                            odds_lists.append(odds_info)
                    else :
                        beton = tmpKey
                        odds = tmpValue                        
                        if beton == "a":
                            betk = k.replace("-", "+") if k[0] == "-" else k.replace("+", "-")
                        else :
                            betk = k
                        
                        odds_info = {
                            'k': betk,
                            'beton' : beton,
                            'odds': odds
                        }
                        if beton != "absK" :
                            odds_lists.append(odds_info)
        
        return odds_lists

    def set_sport_header(self,stoken=None):
        self.header= {
                "origin": self.platform_url,
                "referer": self.platform_url,
                "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4044.141 Safari/537.36",
                "devicemode": "Pixel 5",            
                "apptype": "2",
                "device":"mobile",
                "content-type": "application/json;charset=UTF-8",
                "currency": "CNY"
                # "cks" : str(get_cks(vend, account))
            }

        if stoken is not None:
            self.header.update({"authorization": "Bearer " + str(stoken)})

    def chashout(self, orderno):
        path = self.api_url + f"/product/cashout/amount"
        payload = {"orderId": orderno}
        try:
            response = requests.post(path, headers=self.header,json=payload)            
            assert(response.json()['code'] == 0), f"Can't cashout : {response.json()}"
            data = response.json()
            uniKey = data['data']['uniKey']
            amount = data['data']['amount']
            path = self.api_url + f"/product/cashout/confirm" 
            payload = {"uniKey": uniKey}
            response = requests.post(path, headers=self.header,json=payload)
            assert(response.json()['code'] == 0), f"Call cashout confirm error : {response.json()}"
            data = response.json()
            return amount
        except Exception as e :
            return str(e)