# 한국투자증권 Open API 연결, 주문, 잔고조회, 스케줄링
import os
#%% APP Key 저장 (keyring)
import keyring
from getpass import getpass


print(len(keyring.get_password('mock_app_key', 'user')),
      len(keyring.get_password('mock_app_secret', 'user')))


#%% 접근 토큰 발급받기
import requests
import json
import keyring

app_key = keyring.get_password('mock_app_key', 'user')
app_secret = keyring.get_password('mock_app_secret', 'user')

if app_key is None or app_secret is None:
    raise RuntimeError("keyring 에서 모의 APP Key / Secret 을 읽지 못했다. 저장 셀과 User Name 을 확인할 것.")

url_base = "https://openapivts.koreainvestment.com:29443"

headers = {"content-type": "application/json"}
path = "oauth2/tokenP"
body = {
    "grant_type": "client_credentials",
    "appkey": app_key,
    "appsecret": app_secret
}

url = f"{url_base}/{path}"
print(url)


#%% 접근 토큰 요청
res = requests.post(url, headers=headers, data=json.dumps(body))

if 'access_token' not in res.json():
    raise RuntimeError(f"토큰 발급 실패: {res.text}")

access_token = res.json()['access_token']
print('토큰 발급 완료')


#%% 해시키 발급받기
def hashkey(datas):
    path = "uapi/hashkey"
    url = f"{url_base}/{path}"
    headers = {
        'content-Type': 'application/json',
        'appKey': app_key,
        'appSecret': app_secret,
    }
    res = requests.post(url, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]

    return hashkey


#%% 주식 현재가 시세 조회하기
path = "uapi/domestic-stock/v1/quotations/inquire-price"
url = f"{url_base}/{path}"

headers = {
    "Content-Type": "application/json",
    "authorization": f"Bearer {access_token}",
    "appKey": app_key,
    "appSecret": app_secret,
    "tr_id": "FHKST01010100"
}

params = {"fid_cond_mrkt_div_code": "J",
          "fid_input_iscd": "005930"}

res = requests.get(url, headers=headers, params=params)

if res.json().get('rt_cd') != '0':
    raise RuntimeError(f"현재가 조회 실패: {res.text}")

res.json()['output']['stck_prpr']


#%% 매수 주문

CANO = os.environ['KIS_CANO']
ACNT_PRDT_CD = "01"

assert 'openapivts' in url_base, "모의투자 domain 이 아니다. url_base 확인"
assert CANO.isdigit() and len(CANO) == 8, "CANO 는 숫자 8자리여야 한다"

path = "uapi/domestic-stock/v1/trading/order-cash"
url = f"{url_base}/{path}"

data = {
    "CANO": CANO,
    "ACNT_PRDT_CD": ACNT_PRDT_CD,
    "PDNO": "005930",
    "ORD_DVSN": "01",
    "ORD_QTY": "10",
    "ORD_UNPR": "0"
}

headers = {
    "Content-Type": "application/json",
    "authorization": f"Bearer {access_token}",
    "appKey": app_key,
    "appSecret": app_secret,
    "tr_id": "VTTC0802U",
    "custtype": "P",
    "hashkey": hashkey(data)
}

res = requests.post(url, headers=headers, data=json.dumps(data))
res.json()


#%% 정정 주문
path = "uapi/domestic-stock/v1/trading/order-cash"
url = f"{url_base}/{path}"

data = {
    "CANO": CANO,
    "ACNT_PRDT_CD": ACNT_PRDT_CD,
    "PDNO": "005930",
    "ORD_DVSN": "00",
    "ORD_QTY": "10",
    "ORD_UNPR": "50000"
}

headers = {
    "Content-Type": "application/json",
    "authorization": f"Bearer {access_token}",
    "appKey": app_key,
    "appSecret": app_secret,
    "tr_id": "VTTC0802U",
    "custtype": "P",
    "hashkey": hashkey(data)
}

res = requests.post(url, headers=headers, data=json.dumps(data))
res.json()


#%% 미체결 주문의 번호 확인

if res.json().get('rt_cd') != '0':
    raise RuntimeError(f"주문 실패: {res.text}")

KRX_FWDG_ORD_ORGNO = res.json()["output"][
    "KRX_FWDG_ORD_ORGNO"]
ODNO = res.json()["output"]["ODNO"]

print(KRX_FWDG_ORD_ORGNO, ODNO)


#%% 미체결 주문을 최유리 지정가로 정정
path = "uapi/domestic-stock/v1/trading/order-rvsecncl"
url = f"{url_base}/{path}"

data = {
    "CANO": CANO,
    "ACNT_PRDT_CD": ACNT_PRDT_CD,
    "KRX_FWDG_ORD_ORGNO": KRX_FWDG_ORD_ORGNO,
    "ORGN_ODNO": ODNO,
    "ORD_DVSN": "03",
    "RVSE_CNCL_DVSN_CD": "01",
    "ORD_QTY": "10",
    "ORD_UNPR": "0",
    "QTY_ALL_ORD_YN": "Y"
}

headers = {
    "Content-Type": "application/json",
    "authorization": f"Bearer {access_token}",
    "appKey": app_key,
    "appSecret": app_secret,
    "tr_id": "VTTC0803U",
    "custtype": "P",
    "hashkey": hashkey(data)
}

res = requests.post(url, headers=headers, data=json.dumps(data))
res.json()


#%% 매도 주문
path = "uapi/domestic-stock/v1/trading/order-cash"
url = f"{url_base}/{path}"

data = {
    "CANO": CANO,
    "ACNT_PRDT_CD": ACNT_PRDT_CD,
    "PDNO": "005930",
    "ORD_DVSN": "01",
    "ORD_QTY": "10",
    "ORD_UNPR": "0"
}

headers = {
    "Content-Type": "application/json",
    "authorization": f"Bearer {access_token}",
    "appKey": app_key,
    "appSecret": app_secret,
    "tr_id": "VTTC0801U",
    "custtype": "P",
    "hashkey": hashkey(data)
}

res = requests.post(url, headers=headers, data=json.dumps(data))
res.json()


#%% 주식 잔고조회
path = "uapi/domestic-stock/v1/trading/inquire-balance"
url = f"{url_base}/{path}"

headers = {
    "Content-Type": "application/json",
    "authorization": f"Bearer {access_token}",
    "appKey": app_key,
    "appSecret": app_secret,
    "tr_id": "VTTC8434R"
}

params = {
    "CANO": CANO,
    "ACNT_PRDT_CD": ACNT_PRDT_CD,
    "AFHR_FLPR_YN": "N",
    "OFL_YN": "",
    "INQR_DVSN": "01",
    "UNPR_DVSN": "01",
    "FUND_STTL_ICLD_YN": "N",
    "FNCG_AMT_AUTO_RDPT_YN": "N",
    "PRCS_DVSN": "00",
    "CTX_AREA_FK100": "",
    "CTX_AREA_NK100": ""
}

res = requests.get(url, headers=headers, params=params)

if res.json().get('rt_cd') != '0':
    raise RuntimeError(f"잔고조회 실패: {res.text}")


#%% 보유 종목 정보
res.json()['output1']


#%%
import pandas as pd

ap = pd.DataFrame.from_records(res.json()['output1'])
ap


#%% 계좌잔고 확인
res.json()['output2']


#%% 스케줄링
import datetime

def job():
    print(datetime.datetime.now().strftime('%H:%M:%S'))
    print("====================")


#%%
import schedule

schedule.every(3).seconds.do(job)


#%% 등록된 스케줄 확인
schedule.get_jobs()


#%% 스케줄 실행
while True:
    schedule.run_pending()


#%% 시간 지정하기
import pandas as pd
from datetime import timedelta

schedule.clear()

startDt = datetime.datetime.now() + timedelta(seconds=60)
endDt = datetime.datetime.now() + timedelta(seconds=80)
time_list = pd.date_range(startDt, endDt, periods=5)

print(time_list)


#%% 스케줄러 등록용 시:분:초 형태로 변환
time_list_sec = [i.strftime('%H:%M:%S') for i in time_list]

time_list_sec


#%% 위 시간에 job() 이 실행되도록 스케줄 등록
[schedule.every().day.at(i).do(job) for i in time_list_sec]


#%% 실행 결과 확인
while True:
    schedule.run_pending()
    if datetime.datetime.now() > endDt:
        print('End')
        schedule.clear()
        break


#%%

import requests
import json
import keyring
import pandas as pd
import time
import numpy as np
import datetime
from datetime import timedelta
import schedule

app_key = keyring.get_password('mock_app_key', 'user')
app_secret = keyring.get_password('mock_app_secret', 'user')

if app_key is None or app_secret is None:
    raise RuntimeError("keyring 에서 모의 APP Key / Secret 을 읽지 못했다. 저장 셀과 User Name 을 확인할 것.")

url_base = "https://openapivts.koreainvestment.com:29443"


assert CANO.isdigit() and len(CANO) == 8, "CANO 는 숫자 8자리여야 한다"

headers = {"content-type": "application/json"}
path = "oauth2/tokenP"
url = f"{url_base}/{path}"
body = {
    "grant_type": "client_credentials",
    "appkey": app_key,
    "appsecret": app_secret
}
res = requests.post(url, headers=headers, data=json.dumps(body))

if 'access_token' not in res.json():
    raise RuntimeError(f"토큰 발급 실패: {res.text}")

access_token = res.json()['access_token']


def hashkey(datas):
    path = "uapi/hashkey"
    url = f"{url_base}/{path}"
    headers = {
        'content-Type': 'application/json',
        'appKey': app_key,
        'appSecret': app_secret,
    }
    res = requests.post(url, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]
    return hashkey


#%%

def get_price(ticker):
    path = "uapi/domestic-stock/v1/quotations/inquire-price"
    url = f"{url_base}/{path}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appKey": app_key,
        "appSecret": app_secret,
        "tr_id": "FHKST01010100"
    }
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": ticker
    }
    res = requests.get(url, headers=headers, params=params)

    if res.json().get('rt_cd') != '0':
        raise RuntimeError(f"현재가 조회 실패({ticker}): {res.text}")

    price = int(res.json()['output']['stck_prpr'])
    time.sleep(0.1)

    return price


get_price('005930')


#%%

def trading(ticker, tr_id):
    path = "uapi/domestic-stock/v1/trading/order-cash"
    url = f"{url_base}/{path}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": ticker,
        "ORD_DVSN": "03",
        "ORD_QTY": "1",
        "ORD_UNPR": "0"
    }
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appKey": app_key,
        "appSecret": app_secret,
        "tr_id": tr_id,
        "custtype": "P",
        "hashkey": hashkey(data)
    }
    res = requests.post(url, headers=headers, data=json.dumps(data))
    time.sleep(0.1)

    return res


#%%

def check_account():
    output1 = []
    CTX_AREA_NK100 = ''

    while True:
        path = "uapi/domestic-stock/v1/trading/inquire-balance"
        url = f"{url_base}/{path}"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {access_token}",
            "appKey": app_key,
            "appSecret": app_secret,
            "tr_id": "VTTC8434R"
        }
        params = {
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "01",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": CTX_AREA_NK100
        }
        res = requests.get(url, headers=headers, params=params)

        if res.json().get('rt_cd') != '0':
            raise RuntimeError(f"잔고조회 실패: {res.text}")

        output1.append(pd.DataFrame.from_records(res.json()['output1']))

        CTX_AREA_NK100 = res.json()['ctx_area_nk100'].strip()

        if CTX_AREA_NK100 == '':
            output2 = res.json()['output2']
            break

        time.sleep(0.1)

    if not output1[0].empty:
        res1 = (pd.concat(output1)[['pdno', 'hldg_qty']]
                .rename(columns={'pdno': '종목코드', 'hldg_qty': '보유수량'})
                .reset_index(drop=True))
    else:
        res1 = pd.DataFrame(columns=['종목코드', '보유수량'])

    res2 = output2[0]

    return [res1, res2]


ap, account = check_account()
print(ap)
print(account['tot_evlu_amt'])


#%%

mp = pd.DataFrame({'종목코드': ['005930', '373220', '000660', '207940', '051910',
                              '035420', '005380', '006400', '035720', '105560']})

ap, account = check_account()

invest_per_stock = int(account['tot_evlu_amt']) * 0.98 / len(mp)

target = mp.merge(ap, on='종목코드', how='outer')

target['보유수량'] = pd.to_numeric(target['보유수량']).fillna(0)

target['현재가'] = target['종목코드'].apply(get_price)

target['목표수량'] = np.where(target['종목코드'].isin(mp['종목코드'].tolist()),
                          round(invest_per_stock / target['현재가']),
                          0)

target['투자수량'] = target['목표수량'] - target['보유수량']
target['투자수량'] = target['투자수량'].astype(int)

target


#%%

startDt = datetime.datetime.now() + timedelta(minutes=1)
endDt = datetime.datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)

if startDt >= endDt:
    raise RuntimeError("종료 시각(오후 3시)이 이미 지났다. 장중에 실행할 것.")

for i in range(0, len(target)):

    ticker = target.loc[i, '종목코드']
    n = target.loc[i, '투자수량']

    if n == 0:
        continue

    position = 'VTTC0802U' if n > 0 else 'VTTC0801U'

    time_list = pd.date_range(startDt, endDt, periods=abs(n))
    time_list_sec = time_list.round(freq='s').tolist()
    time_list_sec = [t.strftime('%H:%M:%S') for t in time_list_sec]

    for t in time_list_sec:
        schedule.every().day.at(t).do(trading, ticker, position)

print(len(schedule.get_jobs()))


#%%

while True:
    schedule.run_pending()
    time.sleep(1)

    if datetime.datetime.now() > endDt + timedelta(minutes=1):
        break

schedule.clear()


#%%

ap_after, account_after = check_account()
ap_after.columns = ['종목코드', '매매후수량']
ap_after[['매매후수량']] = ap_after[['매매후수량']].apply(pd.to_numeric)

target_after = target.merge(ap_after, on='종목코드', how='left')
target_after['매매후수량'] = target_after['매매후수량'].fillna(0)
target_after['차이'] = target_after['목표수량'] - target_after['매매후수량']

target_after


#%%

mp = pd.read_excel('model.xlsx', dtype=str)

ap, account = check_account()

invest_per_stock = int(account['tot_evlu_amt']) * 0.98 / len(mp)

target = mp.merge(ap, on='종목코드', how='outer')
target['보유수량'] = pd.to_numeric(target['보유수량']).fillna(0)

target['현재가'] = target['종목코드'].apply(get_price)
target['목표수량'] = np.where(target['종목코드'].isin(mp['종목코드'].tolist()),
                          round(invest_per_stock / target['현재가']),
                          0)
target['투자수량'] = (target['목표수량'] - target['보유수량']).astype(int)

target


#%%

startDt = datetime.datetime.now() + timedelta(minutes=1)
endDt = datetime.datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)

if startDt >= endDt:
    raise RuntimeError("종료 시각(오후 3시)이 이미 지났다. 장중에 실행할 것.")

for i in range(0, len(target)):

    ticker = target.loc[i, '종목코드']
    n = target.loc[i, '투자수량']

    if n == 0:
        continue

    position = 'VTTC0802U' if n > 0 else 'VTTC0801U'

    time_list = pd.date_range(startDt, endDt, periods=abs(n))
    time_list_sec = time_list.round(freq='s').tolist()
    time_list_sec = [t.strftime('%H:%M:%S') for t in time_list_sec]

    for t in time_list_sec:
        schedule.every().day.at(t).do(trading, ticker, position)

print(len(schedule.get_jobs()))

while True:
    schedule.run_pending()
    time.sleep(1)

    if datetime.datetime.now() > endDt + timedelta(minutes=1):
        break

schedule.clear()


#%%

ap_after, account_after = check_account()
ap_after.columns = ['종목코드', '매매후수량']
ap_after[['매매후수량']] = ap_after[['매매후수량']].apply(pd.to_numeric)

target_after = target.merge(ap_after, on='종목코드', how='left')
target_after['매매후수량'] = target_after['매매후수량'].fillna(0)
target_after['차이'] = target_after['목표수량'] - target_after['매매후수량']

target_after


#%%

real_app_key = keyring.get_password('real_app_key', 'user')
real_app_secret = keyring.get_password('real_app_secret', 'user')

if real_app_key is None or real_app_secret is None:
    raise RuntimeError("keyring 에서 실전 APP Key / Secret 을 읽지 못했다. 저장 셀의 실전 부분을 먼저 실행할 것.")

app_key = real_app_key
app_secret = real_app_secret

url_base = "https://openapi.koreainvestment.com:9443"

CANO = os.environ['KIS_REAL_CANO']
ACNT_PRDT_CD = "01"

assert CANO.isdigit() and len(CANO) == 8, "실계좌번호 앞 8자리로 CANO 를 바꿀 것"

headers = {"content-type": "application/json"}
path = "oauth2/tokenP"
url = f"{url_base}/{path}"
body = {
    "grant_type": "client_credentials",
    "appkey": app_key,
    "appsecret": app_secret
}
res = requests.post(url, headers=headers, data=json.dumps(body))

if 'access_token' not in res.json():
    raise RuntimeError(f"토큰 발급 실패: {res.text}")

access_token = res.json()['access_token']


#%%

def check_account():
    output1 = []
    CTX_AREA_NK100 = ''

    while True:
        path = "uapi/domestic-stock/v1/trading/inquire-balance"
        url = f"{url_base}/{path}"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {access_token}",
            "appKey": app_key,
            "appSecret": app_secret,
            "tr_id": "TTTC8434R"
        }
        params = {
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "01",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": CTX_AREA_NK100
        }
        res = requests.get(url, headers=headers, params=params)

        if res.json().get('rt_cd') != '0':
            raise RuntimeError(f"잔고조회 실패: {res.text}")

        output1.append(pd.DataFrame.from_records(res.json()['output1']))

        CTX_AREA_NK100 = res.json()['ctx_area_nk100'].strip()

        if CTX_AREA_NK100 == '':
            output2 = res.json()['output2']
            break

        time.sleep(0.1)

    if not output1[0].empty:
        res1 = (pd.concat(output1)[['pdno', 'hldg_qty']]
                .rename(columns={'pdno': '종목코드', 'hldg_qty': '보유수량'})
                .reset_index(drop=True))
    else:
        res1 = pd.DataFrame(columns=['종목코드', '보유수량'])

    res2 = output2[0]

    return [res1, res2]


ap, account = check_account()
print(ap)
print(account['tot_evlu_amt'])


#%%

mp = pd.DataFrame({'종목코드': ['005930', '000660', '005380', '035720', '105560',
                              '001120', '003380', '003650', '009160', '009970']})

ap, account = check_account()

invest_per_stock = int(account['tot_evlu_amt']) * 0.98 / len(mp)

target = mp.merge(ap, on='종목코드', how='outer')
target['보유수량'] = pd.to_numeric(target['보유수량']).fillna(0)

target['현재가'] = target['종목코드'].apply(get_price)
target['목표수량'] = np.where(target['종목코드'].isin(mp['종목코드'].tolist()),
                          round(invest_per_stock / target['현재가']),
                          0)
target['투자수량'] = (target['목표수량'] - target['보유수량']).astype(int)

target


#%%

def trading(ticker, tr_id):
    path = "uapi/domestic-stock/v1/trading/order-cash"
    url = f"{url_base}/{path}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": ticker,
        "ORD_DVSN": "03",
        "ORD_QTY": "1",
        "ORD_UNPR": "0"
    }
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appKey": app_key,
        "appSecret": app_secret,
        "tr_id": tr_id,
        "custtype": "P",
        "hashkey": hashkey(data)
    }
    res = requests.post(url, headers=headers, data=json.dumps(data))
    time.sleep(0.1)

    return res


startDt = datetime.datetime.now() + timedelta(minutes=1)
endDt = datetime.datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)

if startDt >= endDt:
    raise RuntimeError("종료 시각(오후 3시)이 이미 지났다. 장중에 실행할 것.")

for i in range(0, len(target)):

    ticker = target.loc[i, '종목코드']
    n = target.loc[i, '투자수량']

    if n == 0:
        continue

    position = 'TTTC0802U' if n > 0 else 'TTTC0801U'

    time_list = pd.date_range(startDt, endDt, periods=abs(n))
    time_list_sec = time_list.round(freq='s').tolist()
    time_list_sec = [t.strftime('%H:%M:%S') for t in time_list_sec]

    for t in time_list_sec:
        schedule.every().day.at(t).do(trading, ticker, position)

print(len(schedule.get_jobs()))

while True:
    schedule.run_pending()
    time.sleep(1)

    if datetime.datetime.now() > endDt + timedelta(minutes=1):
        break

schedule.clear()


#%%

ap_after, account_after = check_account()
ap_after.columns = ['종목코드', '매매후수량']
ap_after[['매매후수량']] = ap_after[['매매후수량']].apply(pd.to_numeric)

target_after = target.merge(ap_after, on='종목코드', how='left')
target_after['매매후수량'] = target_after['매매후수량'].fillna(0)
target_after['차이'] = target_after['목표수량'] - target_after['매매후수량']

target_after
