# DART, FRED, 공포탐욕지수 수집
import os


#%% API Key 저장
import keyring


#%% 고유번호 다운로드

import keyring
import requests as rq
from io import BytesIO
import zipfile

api_key = keyring.get_password('dart_api_key', 'user')
codezip_url = f'''https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}'''
codezip_data = rq.get(codezip_url)
codezip_data.headers


#%% 첨부파일 확인
codezip_data.headers['Content-Disposition']

codezip_file = zipfile.ZipFile(BytesIO(codezip_data.content))
codezip_file.namelist()


#%% CORPCODE.xml 불러오기
import xmltodict
import json
import pandas as pd

code_data = codezip_file.read('CORPCODE.xml').decode('utf-8')
data_odict = xmltodict.parse(code_data)
data_dict = json.loads(json.dumps(data_odict))
data = data_dict.get('result').get('list')
corp_list = pd.DataFrame(data)

corp_list.head()


#%% 종목 수 확인과 비상장 종목 제거
len(corp_list)

corp_list[corp_list['stock_code'].isin([None])].head()


#%% 고유번호 DB 저장
import pymysql
from sqlalchemy import create_engine

corp_list = corp_list[~corp_list.stock_code.isin(
    [None])].reset_index(drop=True)

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")
corp_list.to_sql(name='dart_code', con=engine, index=True, if_exists='replace')
engine.dispose()


#%% . 공시 데이터

from datetime import date
from dateutil.relativedelta import relativedelta

bgn_date = (date.today() + relativedelta(days=-7)).strftime("%Y%m%d")
end_date = (date.today()).strftime("%Y%m%d")

notice_url = f'''https://opendart.fss.or.kr/api/list.json?crtfc_key={api_key}&bgn_de={bgn_date}&end_de={end_date}&page_no=1&page_count=100'''

notice_data = rq.get(notice_url)
notice_data_df = notice_data.json().get('list')
notice_data_df = pd.DataFrame(notice_data_df)

notice_data_df.tail()


#%% . 특정 기업의 공시 데이터 수집

corp_list[corp_list['corp_name'] == '삼성전자']

bgn_date = (date.today() + relativedelta(days=-30)).strftime("%Y%m%d")
end_date = (date.today()).strftime("%Y%m%d")
corp_code = '00126380'

notice_url_ss = f'''https://opendart.fss.or.kr/api/list.json?crtfc_key={api_key}&corp_code={corp_code}&bgn_de={bgn_date}&end_de={end_date}&page_no=1&page_count=100'''

notice_data_ss = rq.get(notice_url_ss)
notice_data_ss_df = notice_data_ss.json().get('list')
notice_data_ss_df = pd.DataFrame(notice_data_ss_df)

notice_data_ss_df.tail()


#%% 공시 원문 URL 만들기
notice_url_exam = notice_data_ss_df.loc[0, 'rcept_no']
notice_dart_url = f'http://dart.fss.or.kr/dsaf001/main.do?rcpNo={notice_url_exam}'

print(notice_dart_url)


#%% . 사업보고서 주요 정보

corp_code = '00126380'
bsns_year = '2025'
reprt_code = '11011'

url_div = f'''https://opendart.fss.or.kr/api/alotMatter.json?crtfc_key={api_key}&corp_code={corp_code}&bsns_year={bsns_year}&reprt_code={reprt_code}'''

div_data_ss = rq.get(url_div)
div_data_ss_df = div_data_ss.json().get('list')
div_data_ss_df = pd.DataFrame(div_data_ss_df)

div_data_ss_df.head()


#%% 장단기 금리차 다운로드
import pandas_datareader as web
import pandas as pd

t10y2y = web.DataReader('T10Y2Y', 'fred', start='1990-01-01')
t10y3m = web.DataReader('T10Y3M', 'fred', start='1990-01-01')

rate_diff = pd.concat([t10y2y, t10y3m], axis=1)
rate_diff.columns = ['10Y - 2Y', '10Y - 3M']

rate_diff.tail()


#%% 장단기 금리차와 S&P500 지수 비교
import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf

sp = yf.download('^GSPC', start='1990-01-01', progress=False, auto_adjust=False)
if isinstance(sp.columns, pd.MultiIndex):
    sp.columns = sp.columns.get_level_values(0)

plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)

fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.plot(t10y2y, color='black', linewidth=0.5, label='10Y-2Y')
ax1.plot(t10y3m, color='gray', linewidth=0.5, label='10Y-3M')
ax1.axhline(y=0, color='r', linestyle='dashed')
ax1.set_ylabel('장단기 금리차')
ax1.legend(loc='lower right')

ax2 = ax1.twinx()
ax2.plot(np.log(sp['Close']), label='S&P500')
ax2.set_ylabel('S&P500 지수(로그)')
ax2.legend(loc='upper right')

plt.show()


#%% . 기대 인플레이션

import pandas_datareader as web
import pandas as pd

bei = web.DataReader('T10YIE', 'fred', start='1990-01-01')

bei.tail()


#%% 기대 인플레이션 그래프
import matplotlib.pyplot as plt

bei.plot(figsize=(10, 6), grid=True)
plt.axhline(y=2, color='r', linestyle='-')

plt.show()


#%% .3 Fear & Greed Index

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(url='https://edition.cnn.com/markets/fear-and-greed')
idx = driver.find_element(By.CLASS_NAME,
                          value='market-fng-gauge__dial-number-value').text
driver.close()
idx = int(idx)

print(idx)
