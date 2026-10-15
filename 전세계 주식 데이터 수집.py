# 미국 주식 티커, 주가, 재무제표 수집 및 가치지표 계산
import os

#%% 토큰 저장
import keyring


api_key = keyring.get_password('tiingo', 'user')


#%% . 데이터 다운로드
from tiingo import TiingoClient
import pandas as pd
import keyring

api_key = keyring.get_password('tiingo', 'user')
config = {}
config['session'] = True
config['api_key'] = api_key
client = TiingoClient(config)


#%% 티커 정보 확인
tickers = client.list_stock_tickers()
tickers_df = pd.DataFrame.from_records(tickers)


#%% list_stock_tickers() 메서드를 통해 티커 정보를 받아 올 수 있다.
tickers_df.head()


#%% 거래소와 통화별 종목이 몇 개 있는지 확인해 보자.
tickers_df.groupby(['exchange', 'priceCurrency'])['ticker'].count()


#%% 각 종목의 상세 정보 (애플 AAPL)
ticker_metadata = client.get_ticker_metadata("AAPL")
print(ticker_metadata)


#%% 주가 받기
historical_prices = client.get_dataframe("AAPL",
                                         startDate='2026-10-04',
                                         frequency='daily')

historical_prices.head()


#%% 일별 가치지표
fundamentals_daily = client.get_fundamentals_daily('AAPL')
fundamentals_daily_df = pd.DataFrame.from_records(fundamentals_daily)

fundamentals_daily_df.head()


#%% 재무제표 받기
fundamentals_stmnts = client.get_fundamentals_statements(
    'AAPL', startDate='2019-01-01', asReported=True, fmt='csv')

df_fs = pd.DataFrame([x.split(',') for x in fundamentals_stmnts.split('\n')])
df_fs.columns = df_fs.iloc[0]
df_fs = df_fs[1:]
df_fs.set_index('date', drop=True, inplace=True)
df_fs = df_fs[df_fs.index != '']

df_fs.head()


#%% 티커 수집하기
from tradingview_screener import Query, Column
import pandas as pd

count, all_data_df = (Query()
    .set_markets('america')
    .select('name', 'description', 'exchange', 'sector', 'industry', 'market_cap_basic')
    .where(Column('type') == 'stock')
    .order_by('market_cap_basic', ascending=False)
    .limit(10000)
    .get_scanner_data())

print(count, len(all_data_df))
all_data_df.head()


#%% 열 이름으로 맞추기
all_data_df_bind = all_data_df.rename(columns={
    'name': 'Symbol',
    'description': 'Name',
    'exchange': 'Exchange',
    'sector': 'Sector',
    'industry': 'Industry',
    'market_cap_basic': 'Market Cap'})
all_data_df_bind = all_data_df_bind[['Symbol', 'Name', 'Exchange', 'Sector', 'Industry', 'Market Cap']]

all_data_df_bind = all_data_df_bind[all_data_df_bind['Exchange'].isin(['NASDAQ', 'NYSE', 'AMEX'])]

all_data_df_bind['Symbol'] = all_data_df_bind['Symbol'].str.replace('.', '-', regex=False)

all_data_df_bind['country'] = 'United States'
all_data_df_bind['date'] = pd.Timestamp.today().strftime('%Y-%m-%d')
all_data_df_bind = all_data_df_bind.reset_index(drop=True)

all_data_df_bind.head()


#%% global_ticker 테이블 생성
"""
use stock_db;

create table global_ticker
(
    Symbol varchar(20),
    Name varchar(255),
    Exchange varchar(20),
    Sector varchar(255),
    Industry varchar(255),
    `Market Cap` double,
    country varchar(30),
    date date,
    primary key (Symbol, country, date)
);
"""


#%% global_ticker 저장
from sqlalchemy import create_engine
import pymysql
import numpy as np

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")
con = pymysql.connect(user='root', passwd=os.environ['DB_PW'], host='127.0.0.1', db='stock_db', charset='utf8')
mycursor = con.cursor()

data_save = all_data_df_bind.astype(object).where(all_data_df_bind.notna(), None)

query = """
    insert into global_ticker (Symbol, Name, Exchange, Sector, Industry, `Market Cap`, country, date)
    values (%s,%s,%s,%s,%s,%s,%s,%s) as new
    on duplicate key update
    Name=new.Name, Exchange=new.Exchange, Sector=new.Sector, Industry=new.Industry, `Market Cap`=new.`Market Cap`
"""
args = data_save.values.tolist()
mycursor.executemany(query, args)
con.commit()

engine.dispose()
con.close()


#%% .3 주가 다운로드 (yfinance)
import yfinance as yf

data = yf.download('AAPL', progress=False, auto_adjust=False)
data.head()

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)
data.head()

data_jp = yf.download('8035.T', progress=False, auto_adjust=False)
if isinstance(data_jp.columns, pd.MultiIndex):
    data_jp.columns = data_jp.columns.get_level_values(0)
data_jp.head()


#%% . global_price 테이블 생성
"""
use stock_db;

create table global_price
(
    Date date,
    High double,
    Low double,
    Open double,
    Close double,
    Volume double,
    `Adj Close` double,
    ticker varchar(20),
    primary key (Date, ticker)
);
"""


#%% . 전 종목 주가 저장
from sqlalchemy import create_engine
import pymysql
import pandas as pd
import yfinance as yf
import time
from tqdm import tqdm
import numpy as np

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")
con = pymysql.connect(user='root', passwd=os.environ['DB_PW'], host='127.0.0.1', db='stock_db', charset='utf8')
mycursor = con.cursor()

ticker_list = pd.read_sql("""
select * from global_ticker
where date = (select max(date) from global_ticker) and country = 'United States';
""", con=engine)

query = """
    insert into global_price (Date, High, Low, Open, Close, Volume, `Adj Close`, ticker)
    values (%s,%s,%s,%s,%s,%s,%s,%s) as new
    on duplicate key update
    High=new.High, Low=new.Low, Open=new.Open, Close=new.Close, Volume=new.Volume, `Adj Close`=new.`Adj Close`
"""

error_list = []

for i in tqdm(range(0, len(ticker_list))):
    ticker = ticker_list['Symbol'][i]

    try:
        price = yf.download(ticker, progress=False, auto_adjust=False)
        if isinstance(price.columns, pd.MultiIndex):
            price.columns = price.columns.get_level_values(0)

        price = price.reset_index()
        price['ticker'] = ticker
        price = price[['Date', 'High', 'Low', 'Open', 'Close', 'Volume', 'Adj Close', 'ticker']]
        price['Date'] = price['Date'].dt.strftime('%Y-%m-%d')
        price = price.astype(object).where(price.notna(), None)

        args = price.values.tolist()
        mycursor.executemany(query, args)
        con.commit()

    except:
        print(ticker)
        error_list.append(ticker)


engine.dispose()
con.close()


#%% .4 재무제표 다운로드 (yahooquery)
from yahooquery import Ticker
import numpy as np

data = Ticker('AAPL')

data.asset_profile

#%%
data.summary_detail

#%%
data.history()


#%% 연간 재무제표
data_y = data.all_financial_data(frequency='a')

data_y.reset_index(inplace=True)
data_y = data_y.loc[:, ~data_y.columns.isin(['periodType', 'currencyCode'])]
data_y = data_y.melt(id_vars=['symbol', 'asOfDate'])
data_y = data_y.replace([np.nan], None)
data_y['freq'] = 'y'
data_y.columns = ['ticker', 'date', 'account', 'value', 'freq']
data_y.head()


#%% 분기 재무제표 인자만 q로 나머지 동일
data_q = data.all_financial_data(frequency='q')
data_q.reset_index(inplace=True)
data_q = data_q.loc[:, ~data_q.columns.isin(['periodType', 'currencyCode'])]
data_q = data_q.melt(id_vars=['symbol', 'asOfDate'])
data_q = data_q.replace([np.nan], None)
data_q['freq'] = 'q'
data_q.columns = ['ticker', 'date', 'account', 'value', 'freq']
data_q.head()


#%% . global_fs 테이블 생성
"""
use stock_db;

create table global_fs
(
    ticker varchar(20),
    date date,
    account varchar(100),
    value double,
    freq varchar(1),
    primary key (ticker, date, account, freq)
);
"""


#%% 전 종목 재무제표 저장
from sqlalchemy import create_engine
import pymysql
import pandas as pd
from yahooquery import Ticker
import time
from tqdm import tqdm
import numpy as np

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")
con = pymysql.connect(user='root', passwd=os.environ['DB_PW'], host='127.0.0.1', db='stock_db', charset='utf8')
mycursor = con.cursor()

ticker_list = pd.read_sql("""
select * from global_ticker
where date = (select max(date) from global_ticker) and country = 'United States';
""", con=engine)


query_fs = """
    insert into global_fs (ticker, date, account, value, freq)
    values (%s,%s,%s,%s,%s) as new
    on duplicate key update
    value = new.value;
"""

error_list = []


for i in tqdm(range(0, len(ticker_list))):


    ticker = ticker_list['Symbol'][i]


    try:

        data = Ticker(ticker)


        data_y = data.all_financial_data(frequency='a')
        data_y.reset_index(inplace=True)
        data_y = data_y.loc[:, ~data_y.columns.isin(['periodType', 'currencyCode'])]
        data_y = data_y.melt(id_vars=['symbol', 'asOfDate'])
        data_y = data_y.replace([np.nan], None)
        data_y['freq'] = 'y'
        data_y.columns = ['ticker', 'date', 'account', 'value', 'freq']


        data_q = data.all_financial_data(frequency='q')
        data_q.reset_index(inplace=True)
        data_q = data_q.loc[:, ~data_q.columns.isin(['periodType', 'currencyCode'])]
        data_q = data_q.melt(id_vars=['symbol', 'asOfDate'])
        data_q = data_q.replace([np.nan], None)
        data_q['freq'] = 'q'
        data_q.columns = ['ticker', 'date', 'account', 'value', 'freq']


        data_fs = pd.concat([data_y, data_q], axis=0)
        data_fs = data_fs.astype(object).where(data_fs.notna(), None)


        args = data_fs.values.tolist()
        mycursor.executemany(query_fs, args)
        con.commit()

    except:

        print(ticker)
        error_list.append(ticker)


engine.dispose()
con.close()

#%% global_fs 에 실제로 저장된 계정 이름
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")
check = pd.read_sql("""
select distinct account from global_fs
where account in ('NetIncome', 'StockholdersEquity', 'OperatingCashFlow', 'TotalRevenue', 'CashDividendsPaid');
""", con=engine)
print(check['account'].tolist())
engine.dispose()


#%% 애플 가치지표 - 데이터 불러오기
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(f"mysql+pymysql://root:{os.environ['DB_PW']}@127.0.0.1:3306/stock_db")

ticker_list = pd.read_sql("""
select * from global_ticker
where date = (select max(date) from global_ticker)
      and country = 'United States';
""", con=engine)
ticker_list = ticker_list.rename(columns={'Symbol': '종목코드', 'Market Cap': '시가총액', 'date': '기준일'})

sample_fs = pd.read_sql("""
select * from global_fs
where freq = 'q'
and ticker = 'AAPL'
and account in ('NetIncome', 'StockholdersEquity', 'OperatingCashFlow', 'TotalRevenue', 'CashDividendsPaid');
""", con=engine)

sample_fs = sample_fs.rename(columns={'ticker': '종목코드', 'date': '기준일', 'account': '계정',
                                      'value': '값', 'freq': '공시구분'})
sample_fs['계정'] = sample_fs['계정'].replace({'NetIncome': '당기순이익',
                                              'StockholdersEquity': '자본',
                                              'OperatingCashFlow': '영업활동으로인한현금흐름',
                                              'TotalRevenue': '매출액',
                                              'CashDividendsPaid': '배당금'})

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

sample_fs_merge.head()


#%% 가치지표 계산
sample_fs_merge['value'] = np.where(sample_fs_merge['계정'] == '배당금',
                                    -sample_fs_merge['ttm'] / sample_fs_merge['시가총액'],
                                    sample_fs_merge['시가총액'] / sample_fs_merge['ttm'])
sample_fs_merge['지표'] = np.where(
    sample_fs_merge['계정'] == '매출액', 'PSR',
    np.where(
        sample_fs_merge['계정'] == '영업활동으로인한현금흐름', 'PCR',
        np.where(sample_fs_merge['계정'] == '자본', 'PBR',
                 np.where(sample_fs_merge['계정'] == '당기순이익', 'PER',
                          np.where(sample_fs_merge['계정'] == '배당금', 'DY', None)))))

sample_fs_merge


#%% 미국 전 종목 가치지표 계산 - SQL
"""
use stock_db;

create table global_value
(
    종목코드 varchar(20),
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

global_fs = pd.read_sql("""
select * from global_fs
where freq = 'q'
and account in ('NetIncome', 'StockholdersEquity', 'OperatingCashFlow', 'TotalRevenue', 'CashDividendsPaid');
""", con=engine)
global_fs = global_fs.rename(columns={'ticker': '종목코드', 'date': '기준일', 'account': '계정',
                                      'value': '값', 'freq': '공시구분'})
global_fs['계정'] = global_fs['계정'].replace({'NetIncome': '당기순이익',
                                              'StockholdersEquity': '자본',
                                              'OperatingCashFlow': '영업활동으로인한현금흐름',
                                              'TotalRevenue': '매출액',
                                              'CashDividendsPaid': '배당금'})

ticker_list = pd.read_sql("""
select * from global_ticker
where date = (select max(date) from global_ticker)
and country = 'United States';
""", con=engine)
ticker_list = ticker_list.rename(columns={'Symbol': '종목코드', 'Market Cap': '시가총액', 'date': '기준일'})

engine.dispose()


#%% TTM 구하기
global_fs = global_fs.sort_values(['종목코드', '계정', '기준일'])
global_fs['ttm'] = global_fs.groupby(['종목코드', '계정'], as_index=False)['값'].rolling(
    window=4, min_periods=4).sum()['값']

global_fs['ttm'] = np.where(global_fs['계정'] == '자본', global_fs['ttm'] / 4,
                            global_fs['ttm'])
global_fs = global_fs.groupby(['계정', '종목코드']).tail(1)


#%% 가치지표 계산
global_fs_merge = global_fs[['계정', '종목코드',
                             'ttm']].merge(ticker_list[['종목코드', '시가총액', '기준일']],
                                           on='종목코드')

global_fs_merge['value'] = np.where(global_fs_merge['계정'] == '배당금',
                                    -global_fs_merge['ttm'] / global_fs_merge['시가총액'],
                                    global_fs_merge['시가총액'] / global_fs_merge['ttm'])
global_fs_merge['value'] = global_fs_merge['value'].round(4)
global_fs_merge['지표'] = np.where(
    global_fs_merge['계정'] == '매출액', 'PSR',
    np.where(
        global_fs_merge['계정'] == '영업활동으로인한현금흐름', 'PCR',
        np.where(global_fs_merge['계정'] == '자본', 'PBR',
                 np.where(global_fs_merge['계정'] == '당기순이익', 'PER',
                          np.where(global_fs_merge['계정'] == '배당금', 'DY', None)))))

global_fs_merge.rename(columns={'value': '값'}, inplace=True)
global_fs_merge = global_fs_merge[['종목코드', '기준일', '지표', '값']]

global_fs_merge = global_fs_merge[~((global_fs_merge['지표'] == 'DY') &
                                    (global_fs_merge['값'].fillna(0) == 0))]

global_fs_merge = global_fs_merge.replace([np.inf, -np.inf], np.nan)
global_fs_merge = global_fs_merge.astype(object).where(global_fs_merge.notna(), None)

global_fs_merge.head(4)


#%% 계산된 가치지표를 데이터베이스에 저장
query = """
    insert into global_value (종목코드, 기준일, 지표, 값)
    values (%s,%s,%s,%s) as new
    on duplicate key update
    값=new.값
"""

args_fs = global_fs_merge.values.tolist()
mycursor.executemany(query, args_fs)
con.commit()

engine.dispose()
con.close()
