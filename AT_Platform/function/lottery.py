import json
import requests
from datetime import datetime as dt
from datetime import timedelta
from AT_Platform.function import common

header = {
    'accept': "application/json, text/plain, */*",
    'accept-language': "zh-cn",
    'content-type': 'application/json',
    'origin': '',
    'referer': '',
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

def doFirst_step(keyName:str, data_dict:dict, login_form:dict) -> dict:
    result_dict = {
        "errorMsg": '',
        "token" : '',
        "openNum" : 'No record',
        "round" : ''
    }
    token = lottery_login(keyName=keyName, data_dict=data_dict, form_data=login_form)
    data_dict[keyName].update({'token' : token})
    if 'Error' not in token : 
        result_dict['token'] = token
        openData = get_lottery_record(keyName=keyName, data_dict=data_dict)
        if 'Error' not in openData:
            result_dict.update(openData)
        else : 
            result_dict["openNum"] = openData
    else:
        result_dict['errorMsg'] += token

    data_dict[keyName].update(result_dict)
    return data_dict[keyName]


def lottery_login(keyName:str, data_dict:dict, form_data:dict) -> str:
    myDataObj = data_dict[keyName]
    header = {
        'accept': "application/json, text/plain, */*",
        'accept-language': "zh-cn",
        'content-type': 'application/json',
        'origin': myDataObj['web_url'],
        'referer': myDataObj['web_url'] + "/",
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    url = f"{myDataObj['api_url']}/ig-lottery/adminapi/agent/login"
    payload = {
        "account": form_data['account'],
        "password": form_data['password'],
        "googleCode": ""
    }
    response = requests.post(url=url, json=payload, headers=header)
    result = response.json()
    if result['code'] == 1 and result['msg'] == 'ok':
        print(f"[{keyName}] login lottery success")
        return result['data']['token']
    else:
        print(url + str(header) + str(result))
        print(f"[{keyName}] login lottery fail")
        return ("[Error] 登入失敗，請確認帳號密碼 (" + result['msg'] + ")")

def get_lottery_record(keyName:str, data_dict:dict) -> str:
    myDataObj = data_dict[keyName]
    header.update({
        'origin': myDataObj['web_url'],
        'referer': myDataObj['web_url'] + "/",
        'x-access-token' : myDataObj['token']
    })
    # path 最後 "/8" 是 lotteryId 固定香港六合彩
    url = f"{myDataObj['api_url']}/ig-lottery/adminapi/lottery-open/{str(myDataObj['lottery_id'])}"
    payload = {
        'agentIDList': ','.join(str(x) for x in myDataObj['agentList']),
        'startTime': int(dt.strptime(dt.strftime(dt.now() + timedelta(days=-6), '%Y-%m-%d'), '%Y-%m-%d').timestamp()),
        'endTime': int(dt.strptime(dt.strftime(dt.now() + timedelta(days=1), '%Y-%m-%d'), '%Y-%m-%d').timestamp()),
        'pageIndex': 1
    }
    response = requests.get(url=url, params=payload, headers=header)
    result = response.json()
    if result['code'] == 1 and result['msg'] == 'ok':
        print("get lottery number success")
        target = None
        for obj in result['data']:
            # 0 未結算, 1 已結算, 2 已注銷, 3 已撤銷
            if obj['numbers'] != "" and (obj['status'] == 3 or obj['status'] == 0):     
                target = {"openNum" : obj['numbers'], "round": obj['round']}
                break
        if target is None:
            return {'openNum': 'No record', 'round': ''}
        else:
            return target
        # for test part
        # if keyName == '1.0' : 
        #     print({"openNum" : result['data'][1]['numbers'], "round": result['data'][1]['round']})
        #     return {"openNum" : result['data'][1]['numbers'], "round": result['data'][1]['round']}
        # else:
        #     print({"openNum" : result['data'][0]['numbers'], "round": result['data'][0]['round']})
        #     return {"openNum" : result['data'][0]['numbers'], "round": result['data'][0]['round']}
    else:
        print(f"get lottery numbers fail ({result['msg']})")
        return f"[Error] 取得開獎記錄錯誤 ({result['msg']})"

def do_openLottery(keyName:str, data_dict:dict, idx) -> str:
    myDataObj = data_dict[keyName]
    if myDataObj['round'] != '' and myDataObj['openNum'] != '' and myDataObj['openNum'] != 'No record':
        header.update({
            'origin': myDataObj['web_url'],
            'referer': myDataObj['web_url'] + "/",
            'x-access-token' : myDataObj['token']
        })
        url = f"{myDataObj['api_url']}/ig-lottery/adminapi/lottery-open/settlement"
        payload = {
            "lotteryID": myDataObj['lottery_id'],
            "round": myDataObj['round'],
            "agentIDList": list(myDataObj['agentList'])
        }

        response = requests.put(url=url, json=payload, headers=header)
        result = response.json()
        if result['code'] == 1 and result['msg'] == 'ok':
            print('lottery open success.')
            return '彩票結算成功'
        else:
            print('lottery open fail.')
            return "[Error] 彩票結算錯誤  (" + result['msg'] + ")"
