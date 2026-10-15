# KRX/WICS/네이버/FnGuide 국내 주식 데이터 수집, MySQL 저장, 가치지표 계산
#%% 로그인 정보 설정 확인
import os
print('KRX_ID 설정됨:', os.environ.get('KRX_ID') is not None)
print('KRX_PW 설정됨:', os.environ.get('KRX_PW') is not None)

#%% 영업일 기준 데이터 받기 - 최근 영업일 구하기 방법 1: pykrx가 가까운 영업일을 계산
from pykrx import stock
from datetime import datetime, timedelta

today = datetime.today().strftime('%Y%m%d')
last_biz = stock.get_nearest_business_day_in_a_week(today)
print('방법1:', last_biz)

#%% 최근 영업일 구하기 방법 2: 삼성전자 일봉의 마지막 날짜
start = (datetime.today() - timedelta(days=10)).strftime('%Y%m%d')
df = stock.get_market_ohlcv(start, today, '005930')
last_biz2 = df.index[-1].strftime('%Y%m%d')
print('방법2:', last_biz2)


#%%


import requests as rq
from io import BytesIO
import pandas as pd
from pykrx.website.comm.auth import get_auth_session

krx = get_auth_session()
print('로그인 세션:', krx is not None)


gen_otp_url = 'https://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'
gen_otp_stk = {
    'mktId': 'STK',
    'trdDd': last_biz,
    'money': '1',
    'csvxls_isNo': 'false',
    'name': 'fileDown',
    'url': 'dbms/MDC/STAT/standard/MDCSTAT03901'
}

headers = {'Referer': 'https://data.krx.co.kr/contents/MDC/MDI/mdiLoader'}


otp_stk = krx.post(gen_otp_url, headers=headers, data=gen_otp_stk).text
print(otp_stk[:100])

down_url = 'https://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'
down_sector_stk = krx.post(down_url, headers=headers, data={'code': otp_stk})

sector_stk = pd.read_csv(BytesIO(down_sector_stk.content), encoding='EUC-KR')
sector_stk.head()


#%% 업종분류 현황 - 코스닥
gen_otp_ksq = {
    'mktId': 'KSQ',
    'trdDd': last_biz,
    'money': '1',
    'csvxls_isNo': 'false',
    'name': 'fileDown',
    'url': 'dbms/MDC/STAT/standard/MDCSTAT03901'
}

otp_ksq = krx.post(gen_otp_url, headers=headers, data=gen_otp_ksq).text
down_sector_ksq = krx.post(down_url, headers=headers, data={'code': otp_ksq})
sector_ksq = pd.read_csv(BytesIO(down_sector_ksq.content), encoding='EUC-KR', dtype={'종목코드': str})
sector_ksq.head()

#%% 코스피 + 코스닥 합치기
krx_sector = pd.concat([sector_stk, sector_ksq], ignore_index=True)
krx_sector['종목명'] = krx_sector['종목명'].str.strip()
krx_sector['기준일'] = last_biz

krx_sector.head()


#%%

import requests as rq
from io import BytesIO
import pandas as pd
from datetime import datetime, timedelta


gen_otp_ind = {
    'searchType': '1',
    'mktId': 'ALL',
    'trdDd': last_biz,
    'csvxls_isNo': 'false',
    'name': 'fileDown',
    'url': 'dbms/MDC/STAT/standard/MDCSTAT03501'
}

headers = {'Referer': 'https://data.krx.co.kr/contents/MDC/MDI/mdiLoader'}


otp_ind = krx.post(gen_otp_url, headers=headers, data=gen_otp_ind).text
print(otp_ind[:100])

down_ind = krx.post(down_url, headers=headers, data={'code': otp_ind})

krx_ind = pd.read_csv(BytesIO(down_ind.content), encoding='EUC-KR')
krx_ind['종목명'] = krx_ind['종목명'].str.strip()
krx_ind['기준일'] = last_biz

krx_ind.head()

#%%
diff = list(set(krx_sector['종목명']).symmetric_difference(set(krx_ind['종목명'])))
print(diff)

kor_ticker = pd.merge(krx_sector,
                      krx_ind,
                      on= krx_sector.columns.intersection(
                          krx_ind.columns).tolist(),
                      how = 'outer')

kor_ticker.head()


print(kor_ticker[kor_ticker['종목명'].str.contains('스팩|제[0-9]+호')]['종목명'].values)

print(kor_ticker[kor_ticker['종목코드'].str[-1:]!='0']['종목명'].values)

print(kor_ticker[kor_ticker['종목명'].str.endswith('리츠')]['종목명'].values)


import numpy as np

kor_ticker['종목구분'] = np.where(kor_ticker['종목명'].str.contains('스팩|제[0-9]+호'),'스팩',
                              np.where(kor_ticker['종목코드'].str[-1:]!='0','우선주',
                                     np.where(kor_ticker['종목명'].str.endswith('리츠'),'리츠',
                                              np.where(kor_ticker['종목명'].isin(diff),'기타',
                                                       '보통주'))))

kor_ticker = kor_ticker.reset_index(drop=True)
kor_ticker.colums = kor_ticker.columns.str.replace(' ','')
kor_ticker = kor_ticker[['종목코드','종목명','시장구분','종가','시가총액','기준일','EPS',
                         'PER','BPS','주당배당금','종목구분']]
kor_ticker = kor_ticker.replace({np.nan:None})
kor_ticker['기준일'] = pd.to_datetime(kor_ticker['기준일'])

#%%
"""
create database stock_db;

use stock_db;

create table kor_ticker

(
     종목코드 varchar(6) not null,
     종목명 varchar(20),
     시장구분 varchar(6),
     종가 float,
     시가총액 float,
     기준일 date,
     EPS float,
     PER float,
     BPS float,
     주당배당금 float,
     종목구분 varchar(5),
     primary key(종목코드, 기준일)
);
"""

#%%
import pymysql

con = pymysql.connect(user='root',
                      passwd=os.environ['DB_PW'],
                      host='127.0.0.1',
                      db='stock_db',
                      charset='utf8')

mycursor = con.cursor()
query = f"""
    insert into kor_ticker(종목코드,종목명,시장구분,종가,시가총액,기준일,EPS,PER,BPS,주당배당금, 종목구분)
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) as new
    on duplicate key update
    종목명 = new.종목명, 시장구분 = new.시장구분, 종가 = new.종가, 시가총액 = new.시가총액, EPS =new.EPS, PER= new.PER, BPS = new.BPS, 주당배당금=new.주당배당금, 종목구분=new.종목구분;
"""

args = kor_ticker.values.tolist()

mycursor.executemany(query,args)
con.commit()

con.close()


#%%
import json
import requests as rq
import pandas as pd

url = f'''https://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&dt=20261008&sec_cd=G10 '''

data = rq.get(url).json()

type(data)


print(data.keys())

data['list'][0]
data['sector']

#%%
data_pd = pd.json_normalize(data['list'])
data_pd.head()

#%%
import time
import json
import requests as rq
import pandas as pd
from tqdm import tqdm

sector_code = [
    'G25','G35','G50','G40','G10','G20','G55','G30','G15','G45'
    ]

data_sector = []

for i in tqdm(sector_code):
    url = f'''https://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&dt=20261008&sec_cd={i}'''
    data = rq.get(url).json()
    data_pd = pd.json_normalize(data['list'])

    data_sector.append(data_pd)

    time.sleep(2)

sector = pd.concat(data_sector, axis=0)
sector = sector[['IDX_CD', 'CMP_CD', 'CMP_KOR', 'SEC_NM_KOR']].copy()
sector['기준일'] = last_biz
sector['기준일'] = pd.to_datetime(sector['기준일'])


#%% sql 코드
"""
use stock_db;

create table kor_sector
(
    IDX_CD varchar(3),
    CMP_CD varchar(6),
    CMP_KOR varchar(20),
    SEC_NM_KOR varchar(10),
    기준일 date,
    primary key(CMP_CD, 기준일)
);
"""

#%% 국내 섹터 들어갈 테이블 만들기
import pymysql

con = pymysql.connect(user='root',
                      passwd=os.environ['DB_PW'],
                      host='127.0.0.1',
                      db='stock_db',
                      charset = 'utf8')

mycursor=con.cursor()
query = f"""
    insert into kor_sector (IDX_CD, CMP_CD, CMP_KOR, SEC_NM_KOR, 기준일)
    values(%s,%s,%s,%s,%s) as new
    on duplicate key update
    IDX_CD = new.IDX_CD, CMP_KOR = new.CMP_KOR, SEC_NM_KOR = new.SEC_NM_KOR
"""

args = sector.values.tolist()

mycursor.executemany(query,args)
con.commit()

con.close()


#%%

from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")

query = """
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker)
    and 종목구분 = '보통주' ;
"""

ticker_list = pd.read_sql(query, con=engine)
engine.dispose()

ticker_list.head()


#%% 위에서 살펴본 주가 데이터 페이지 크롤링 하기
from dateutil.relativedelta import relativedelta
import requests as rq
from io import BytesIO
from datetime import date

i=0
ticker = ticker_list['종목코드'][i]

fr = (date.today() + relativedelta(years=-5)).strftime("%Y%m%d")
to = (date.today()).strftime("%Y%m%d")

url = f'''https://fchart.stock.naver.com/siseJson.nhn?symbol={ticker}&requestType=1&startTime={fr}&endTime={to}&timeframe=day'''

data = rq.get(url).content

data_price = pd.read_csv(BytesIO(data))
data_price.head()


#%%
import re
import pandas as pd
price = data_price.iloc[:, 0:6]
price.columns = ['날짜','시가','고가','저가','종가','거래량']
price = price.dropna()
price['날짜'] = price['날짜'].str.extract('(\d+)')
price['날짜'] = pd.to_datetime(price['날짜'])
price['종목코드'] = ticker

price.head()


#%% 전종목 주가 크롤링
"""
use stock_db;

create table kor_price
(
     날짜 date,
     시가 double,
     고가 double,
     저가 double,
     종가 double,
     거래량 double,
     종목코드 varchar(6),
     primary key(날짜, 종목코드)
) ;
"""

import pymysql
from sqlalchemy import create_engine
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import requests as rq
import time
from tqdm import tqdm
from io import BytesIO

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")
con= pymysql.connect (user= 'root',
                      passwd=os.environ['DB_PW'],
                      host = '127.0.0.1',
                      db='stock_db',
                      charset = 'utf8')

mycursor = con.cursor()

ticker_list = pd.read_sql("""
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker)
    and 종목구분 = '보통주';
""", con=engine)


query = """
    insert into kor_price(날짜, 시가, 고가, 저가, 종가, 거래량, 종목코드)
    values(%s,%s,%s,%s,%s,%s,%s) as new
    on duplicate key update
    시가 = new.시가, 고가 = new.고가, 저가 = new.저가,
    종가 = new.종가, 거래량 = new.거래량;
"""

error_list = []

for i in tqdm(range(0,len(ticker_list))):


    ticker = ticker_list['종목코드'][i]


    fr = (date.today() + relativedelta(years=-5)).strftime("%Y%m%d")
    to = (date.today()).strftime("%Y%m%d")


    try:

        url = f'''https://fchart.stock.naver.com/siseJson.nhn?symbol={ticker}&requestType=1&startTime={fr}&endTime={to}&timeframe=day'''


        data= rq.get(url).content
        data_price = pd.read_csv(BytesIO(data))


        price = data_price.iloc[:, 0:6]
        price.columns = ['날짜','시가','고가','저가','종가','거래량']
        price = price.dropna()
        price['날짜'] = price['날짜'].str.extract('(\d+)')
        price['날짜'] = pd.to_datetime(price['날짜'])
        price['종목코드'] = ticker


        args = price.values.tolist()
        mycursor.executemany(query,args)
        con.commit()


    except:

        print(ticker)
        error_list.append(ticker)


engine.dispose()
con.close()


#%%


from sqlalchemy import create_engine
import pandas as pd
import requests as rq
from bs4 import BeautifulSoup
import re
import time
from tqdm import tqdm

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")
query = """
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker)
    and 종목구분 = '보통주';
"""
ticker_list = pd.read_sql(query, con=engine)
engine.dispose()

i = 0
ticker = ticker_list['종목코드'][i]

url = f'https://wcomp.fnguide.com/CompanyInfo/Finance?c_id=AA&menu_type=01&cmp_cd={ticker}'

fnguide_headers = {'User-Agent': 'Mozilla/5.0'}

def fnguide_fs(name, ticker, freq):
    u = f'https://wcomp.fnguide.com/CompanyInfo/{name}'
    r = rq.get(u, params={'cmp_cd': ticker, 'freq_typ': freq, 'consol_typ': 'C'}, headers=fnguide_headers)
    o = r.json()['dataset']

    if isinstance(o, list) and len(o) > 0 and 'data' in o[0]:
        o = o[0]

    if not (isinstance(o, dict) and 'data' in o and 'header' in o):
        print(type(o), (list(o.keys()) if isinstance(o, dict) else str(o)[:300]))
        raise ValueError(f'{name} {freq}: 구조 확인 필요')

    df = pd.DataFrame(o['data'])
    rename = {h['CD']: h['YYMM'].replace(' (최근분기)', '') for h in o['header']}
    df = df.rename(columns=rename)
    df['NAME'] = df['NAME'].str.strip()
    df = df[['NAME'] + list(rename.values())]
    df = df.rename(columns={'NAME': 'IFRS(연결)'})
    for c in rename.values():
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def fnguide_tables(ticker):
    return [fnguide_fs('getFinIncome', ticker, 'Y'),
            fnguide_fs('getFinIncome', ticker, 'Q'),
            fnguide_fs('getFinBalance', ticker, 'Y'),
            fnguide_fs('getFinBalance', ticker, 'Q'),
            fnguide_fs('getFinCashFlow', ticker, 'Y'),
            fnguide_fs('getFinCashFlow', ticker, 'Q')]

data = fnguide_tables(ticker)

[item.head(3) for item in data]


#%% 연간 재무제표 합치기
print(data[0].columns.tolist(), '\n',
      data[2].columns.tolist(), '\n',
      data[4].columns.tolist()
      )

data_fs_y = pd.concat(
    [data[0].iloc[:, ~data[0].columns.str.contains('전년동기')], data[2], data[4]])
data_fs_y = data_fs_y.rename(columns={data_fs_y.columns[0]: "계정"})

data_fs_y.head()


#%% 결산월 찾기

page_data = rq.get(url, headers=fnguide_headers)
page_data_html = BeautifulSoup(page_data.content, 'html.parser')

fiscal_data = page_data_html.select('div.corp_group1 > h2')

if len(fiscal_data) > 1:
    fiscal_data_text = fiscal_data[1].text
    fiscal_data_text = re.findall('[0-9]+', fiscal_data_text)
else:
    fiscal_data_text = list({c[-2:] for c in data[2].columns[1:] if re.fullmatch(r'\d{4}/\d{2}', str(c))})
print(fiscal_data_text)

data_fs_y = data_fs_y.loc[:, (data_fs_y.columns == '계정') | (
    data_fs_y.columns.str[-2:].isin(fiscal_data_text))]

data_fs_y.head()


#%% 클렌징이 필요한 부분 확인
data_fs_y[data_fs_y.loc[:, ~data_fs_y.columns.isin(['계정'])].isna().all(axis=1)].head()

data_fs_y['계정'].value_counts(ascending=False).head()


#%% 재무제표 클렌징 함수
def clean_fs(df, ticker, frequency):

    df = df[~df.loc[:, ~df.columns.isin(['계정'])].isna().all(axis=1)]
    df = df.drop_duplicates(['계정'], keep='first')
    df = pd.melt(df, id_vars='계정', var_name='기준일', value_name='값')
    df = df[~pd.isnull(df['값'])]
    df['계정'] = df['계정'].replace({'계산에 참여한 계정 펼치기': ''}, regex=True)
    df['기준일'] = pd.to_datetime(df['기준일'],
                               format='%Y/%m') + pd.tseries.offsets.MonthEnd()
    df['종목코드'] = ticker
    df['공시구분'] = frequency

    return df


#%% 연간 / 분기 클렌징 후 합치기
data_fs_y_clean = clean_fs(data_fs_y, ticker, 'y')
data_fs_y_clean.head()

data_fs_q = pd.concat(
    [data[1].iloc[:, ~data[1].columns.str.contains('전년동기')], data[3], data[5]])
data_fs_q = data_fs_q.rename(columns={data_fs_q.columns[0]: "계정"})
data_fs_q_clean = clean_fs(data_fs_q, ticker, 'q')

data_fs_q_clean.head()

data_fs_bind = pd.concat([data_fs_y_clean, data_fs_q_clean])


#%% . 전 종목 재무제표 크롤링
"""
use stock_db;

create table kor_fs
(
    계정 varchar(30),
    기준일 date,
    값 float,
    종목코드 varchar(6),
    공시구분 varchar(1),
    primary key(계정, 기준일, 종목코드, 공시구분)
);
"""

#%% 전 종목 재무제표 크롤링
import pymysql
from sqlalchemy import create_engine
import pandas as pd
import requests as rq
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import time

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")
con = pymysql.connect(user='root',
                      passwd=os.environ['DB_PW'],
                      host='127.0.0.1',
                      db='stock_db',
                      charset='utf8')
mycursor = con.cursor()

ticker_list = pd.read_sql("""
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker)
    and 종목구분 = '보통주';
""", con=engine)

query = """
    insert into kor_fs (계정, 기준일, 값, 종목코드, 공시구분)
    values (%s,%s,%s,%s,%s) as new
    on duplicate key update
    값=new.값
"""

error_list = []


for i in tqdm(range(0, len(ticker_list))):

    ticker = ticker_list['종목코드'][i]

    try:

        url = f'https://wcomp.fnguide.com/CompanyInfo/Finance?c_id=AA&menu_type=01&cmp_cd={ticker}'

        data = fnguide_tables(ticker)

        data_fs_y = pd.concat([
            data[0].iloc[:, ~data[0].columns.str.contains('전년동기')], data[2],
            data[4]
        ])
        data_fs_y = data_fs_y.rename(columns={data_fs_y.columns[0]: "계정"})

        page_data = rq.get(url, headers=fnguide_headers)
        page_data_html = BeautifulSoup(page_data.content, 'html.parser')

        fiscal_data = page_data_html.select('div.corp_group1 > h2')
        if len(fiscal_data) > 1:
            fiscal_data_text = fiscal_data[1].text
            fiscal_data_text = re.findall('[0-9]+', fiscal_data_text)
        else:
            fiscal_data_text = list({c[-2:] for c in data[2].columns[1:] if re.fullmatch(r'\d{4}/\d{2}', str(c))})

        data_fs_y = data_fs_y.loc[:, (data_fs_y.columns == '계정') | (
            data_fs_y.columns.str[-2:].isin(fiscal_data_text))]

        data_fs_y_clean = clean_fs(data_fs_y, ticker, 'y')

        data_fs_q = pd.concat([
            data[1].iloc[:, ~data[1].columns.str.contains('전년동기')], data[3],
            data[5]
        ])
        data_fs_q = data_fs_q.rename(columns={data_fs_q.columns[0]: "계정"})

        data_fs_q_clean = clean_fs(data_fs_q, ticker, 'q')

        data_fs_bind = pd.concat([data_fs_y_clean, data_fs_q_clean])

        args = data_fs_bind.values.tolist()
        mycursor.executemany(query, args)
        con.commit()

    except:

        print(ticker)
        error_list.append(ticker)


engine.dispose()
con.close()


#%% 삼성전자 가치지표 - 데이터 불러오기
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")

ticker_list = pd.read_sql("""
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker)
      and 종목구분 = '보통주';
""", con=engine)

sample_fs = pd.read_sql("""
select * from kor_fs
where 공시구분 = 'q'
and 종목코드 = '005930'
and 계정 in ('당기순이익', '자본총계', '영업활동으로인한현금흐름', '매출액(수익)');
""", con=engine)

sample_fs['계정'] = sample_fs['계정'].replace({'매출액(수익)': '매출액', '자본총계': '자본'})

engine.dispose()


#%% 재무제표 정렬 (종목코드, 계정, 기준일 순)
sample_fs = sample_fs.sort_values(['종목코드', '계정', '기준일'])

sample_fs.head()


#%% TTM 구하기
sample_fs['ttm'] = sample_fs.groupby(
    ['종목코드', '계정'], as_index=False)['값'].rolling(window=4,
                                                      min_periods=4).sum()['값']

sample_fs


#%% 자본은 평균, 최근 데이터만 선택
import numpy as np

sample_fs['ttm'] = np.where(sample_fs['계정'] == '자본',
                            sample_fs['ttm'] / 4, sample_fs['ttm'])
sample_fs = sample_fs.groupby(['계정', '종목코드']).tail(1)

sample_fs.head()


#%% 시가총액과 합치기
sample_fs_merge = sample_fs[['계정', '종목코드', 'ttm']].merge(
    ticker_list[['종목코드', '시가총액', '기준일']], on='종목코드')
sample_fs_merge['시가총액'] = sample_fs_merge['시가총액'] / 100000000

sample_fs_merge.head()


#%% 가치지표 계산
sample_fs_merge['value'] = sample_fs_merge['시가총액'] / sample_fs_merge['ttm']
sample_fs_merge['지표'] = np.where(
    sample_fs_merge['계정'] == '매출액', 'PSR',
    np.where(
        sample_fs_merge['계정'] == '영업활동으로인한현금흐름', 'PCR',
        np.where(sample_fs_merge['계정'] == '자본', 'PBR',
                 np.where(sample_fs_merge['계정'] == '당기순이익', 'PER', None))))

sample_fs_merge


#%% 배당수익률 (삼성전자)
ticker_list_sample = ticker_list[ticker_list['종목코드'] == '005930'].copy()
ticker_list_sample['DY'] = ticker_list_sample['주당배당금'] / ticker_list_sample['종가']

ticker_list_sample.head()


#%% . 전 종목 가치지표 계산 - SQL
"""
use stock_db;

create table kor_value
(
    종목코드 varchar(6),
    기준일 date,
    지표 varchar(3),
    값 double,
    primary key (종목코드, 기준일, 지표)
);
"""


#%% 전 종목: 재무 데이터를 이용해 가치지표 계산
import pymysql
from sqlalchemy import create_engine
import pandas as pd
import numpy as np

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")
con = pymysql.connect(user='root',
                      passwd=os.environ['DB_PW'],
                      host='127.0.0.1',
                      db='stock_db',
                      charset='utf8')
mycursor = con.cursor()

kor_fs = pd.read_sql("""
select * from kor_fs
where 공시구분 = 'q'
and 계정 in ('당기순이익', '자본총계', '영업활동으로인한현금흐름', '매출액(수익)');
""", con=engine)
kor_fs['계정'] = kor_fs['계정'].replace({'매출액(수익)': '매출액', '자본총계': '자본'})

ticker_list = pd.read_sql("""
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker)
and 종목구분 = '보통주';
""", con=engine)

engine.dispose()


#%% TTM 구하기
kor_fs = kor_fs.sort_values(['종목코드', '계정', '기준일'])
kor_fs['ttm'] = kor_fs.groupby(['종목코드', '계정'], as_index=False)['값'].rolling(
    window=4, min_periods=4).sum()['값']

kor_fs['ttm'] = np.where(kor_fs['계정'] == '자본', kor_fs['ttm'] / 4,
                         kor_fs['ttm'])
kor_fs = kor_fs.groupby(['계정', '종목코드']).tail(1)


#%% 가치지표 계산
kor_fs_merge = kor_fs[['계정', '종목코드',
                       'ttm']].merge(ticker_list[['종목코드', '시가총액', '기준일']],
                                     on='종목코드')
kor_fs_merge['시가총액'] = kor_fs_merge['시가총액'] / 100000000

kor_fs_merge['value'] = kor_fs_merge['시가총액'] / kor_fs_merge['ttm']
kor_fs_merge['value'] = kor_fs_merge['value'].round(4)
kor_fs_merge['지표'] = np.where(
    kor_fs_merge['계정'] == '매출액', 'PSR',
    np.where(
        kor_fs_merge['계정'] == '영업활동으로인한현금흐름', 'PCR',
        np.where(kor_fs_merge['계정'] == '자본', 'PBR',
                 np.where(kor_fs_merge['계정'] == '당기순이익', 'PER', None))))

kor_fs_merge.rename(columns={'value': '값'}, inplace=True)
kor_fs_merge = kor_fs_merge[['종목코드', '기준일', '지표', '값']]

kor_fs_merge = kor_fs_merge.replace([np.inf, -np.inf], np.nan)
kor_fs_merge = kor_fs_merge.astype(object).where(kor_fs_merge.notna(), None)

kor_fs_merge.head(4)


#%% 계산된 가치지표를 데이터베이스에 저장
query = """
    insert into kor_value (종목코드, 기준일, 지표, 값)
    values (%s,%s,%s,%s) as new
    on duplicate key update
    값=new.값
"""

args_fs = kor_fs_merge.values.tolist()
mycursor.executemany(query, args_fs)
con.commit()


#%% 배당수익률(DY) 계산 후 저장
ticker_list['값'] = ticker_list['주당배당금'] / ticker_list['종가']
ticker_list['값'] = ticker_list['값'].round(4)
ticker_list['지표'] = 'DY'
dy_list = ticker_list[['종목코드', '기준일', '지표', '값']]
dy_list = dy_list.replace([np.inf, -np.inf], np.nan)
dy_list = dy_list.astype(object).where(dy_list.notna(), None)
dy_list = dy_list[dy_list['값'] != 0]

dy_list.head()

args_dy = dy_list.values.tolist()
mycursor.executemany(query, args_dy)
con.commit()

engine.dispose()
con.close()
