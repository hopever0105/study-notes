#바이앤 홀드 전략
# 주식을 매수 후 장기 보유 
# 장기적 우상향 경제 성장 믿는 투자철학에서의 합리적


#%% 데이터불러오기 
import pandas as pd
import numpy as np

#%%1. 국내 주식, 데이터 시세 
import FinanceDataReader as fdr

df = fdr.DataReader('NAVER:005930', '2024-01-01', '2026-11-17')   # 삼성전자
print(df.tail())

#%%2. 미국 주식 야후 
import yfinance as yf
df = yf.download('SPY', start='2024-01-01')
print(df.tail())

# 여러 개를 한 번에 받을 때
df = yf.download(['AAPL', 'NVDA', 'QQQ'], start='2024-01-01')['Close']


#%% 3. 전 종목 티커 목록 (KRX에 요청)

import sys
sys.path.append(r'C:\Users\arlo0\OneDrive\바탕 화면\취업')
from quant.krx_guard import install
install()                      # 반드시 다른 import보다 먼저

import FinanceDataReader as fdr
tickers = fdr.StockListing('KRX')        # 코드, 종목명, 시장, 시가총액 등
print(tickers[['Code', 'Name', 'Market']].head())

# 종목명으로 코드 찾기
print(tickers[tickers['Name'] == '삼성전자'])

#%% 4. 나의 sql
import pandas as pd
import pymysql
from pathlib import Path

# 접속 정보 (quant/.env)
env = {}
for line in Path(r'C:\Users\arlo0\OneDrive\바탕 화면\취업\quant\.env').read_text(encoding='utf-8').splitlines():
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

conn = pymysql.connect(host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)),
                       user=env['DB_USER'], password=env['DB_PASSWORD'],
                       database=env['DB_NAME'], charset='utf8mb4')

# 1) 국내 종목 목록 (가장 최근 기준일)
tickers = pd.read_sql("""
    SELECT 종목코드, 종목명, 시장구분, 종가, 시가총액, PER, BPS, 종목구분
    FROM kor_ticker
    WHERE 기준일 = (SELECT MAX(기준일) FROM kor_ticker)
""", conn)

# 종목명으로 코드 찾기
print(tickers[tickers['종목명'].str.contains('삼성전자')])

# 2) 국내 일별 시세 (한 종목)
kr = pd.read_sql("""
    SELECT 날짜, 시가, 고가, 저가, 종가, 거래량
    FROM kor_price
    WHERE 종목코드 = '005930' AND 날짜 >= '2024-01-01'
    ORDER BY 날짜
""", conn, index_col='날짜')

# 3) 미국 일별 시세 (S&P500 종목 + 주요 ETF)
us = pd.read_sql("""
    SELECT 날짜, 티커, 종가, 수정종가, 거래량
    FROM us_price
    WHERE 티커 IN ('SPY', 'QQQ', 'AAPL') AND 날짜 >= '2024-01-01'
""", conn)
us_close = us.pivot(index='날짜', columns='티커', values='수정종가')   # 날짜 × 티커 표

conn.close()
print(kr.tail())
print(us_close.tail())
# 경고문구는 무시 가능 


#%% 다시 
df = yf.download(['XOM'], start='1990-01-01')
#print(df)
print(df.head())
print(df.info())
# DATE가 인덱스로 설정되며 시가, 고가, 저가,종가, 수정종가, 거래량으로 구성
#%% 결측치
import numpy as np

print(df.isnull().sum())
# or 
print(df[df.isin([np.nan, np.inf, -np.inf]).any(axis=1)])


#%% 데이터 슬라이싱
price_df = df.loc[:,['Close']].copy()
price_df.plot(figsize=(16,9))

from_date = '1990-01-01'
to_date = '2020-06-30'
price_df.loc[from_date:to_date].plot(figsize=(16,9))

# 최고점 대비 현재까지 하락한 비율 중 최대학률을 낙폭을 MDD라고한다. 

#%% 일별 수익률 계산
price_df['daily_rtn'] = price_df['Close'].pct_change()
price_df.head(10)

# 바이앤 홀드에서 일변 수익률 계산이유
# 매수시점부터 매도시점가지 보유할 때 일변수익률 누적 곱하는 것이
# 최종적으로 매수 시점 대비 매도 시점 종가 수익률임 (기하평균수익률)

#%% 바이앤홀드 전략 누적 곱 계싼
""" pd.cumprod() 함수 이용"""
price_df['st_rtn'] = (1+price_df['daily_rtn']).cumprod()
print(df.head(10))
# 1990년에 샀으면 45배수익 

#%% 
price_df['st_rtn'].plot(figsize=(16,9))

#%% 다른 시점 기준으로 수익률 계산하기 
base_date = '2011-01-03'
tmp_df = price_df.loc[base_date:,['st_rtn']]/price_df.loc[base_date,['st_rtn']]
last_date = tmp_df.index[-1]
print('누적수익: ',tmp_df.loc[last_date,'st_rtn'])
tmp_df.plot(figsize= (16,9))
