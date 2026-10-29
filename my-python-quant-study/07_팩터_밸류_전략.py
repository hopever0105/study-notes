# 베타 회귀와 밸류 팩터 포트폴리오
#%% 공통 import 및 DB 연결 설정
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import yfinance as yf
import pandas_datareader.data as web
from matplotlib import cm
from sqlalchemy import create_engine, inspect, text

db_pw = os.environ['DB_PW']
engine_url = f'mysql+pymysql://root:{db_pw}@127.0.0.1:3306/stock_db'
engine = create_engine(engine_url)

#%% 한글 폰트 설정
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns

plt.rc('font', family='Malgun Gothic')
mpl.rcParams['axes.unicode_minus'] = False

#%% 필요한 테이블이 DB에 있는지 확인
need_tables = ['kor_ticker', 'kor_sector', 'kor_price', 'kor_fs', 'kor_value']
exist_tables = inspect(engine).get_table_names()

for t in need_tables:
    if t not in exist_tables:
        raise RuntimeError(f'{t} 테이블이 없습니다. 국내 주식 데이터 수집.py 를 먼저 실행하세요.')
    with engine.connect() as con:
        cnt = con.execute(text(f'select count(*) from {t}')).scalar()
    if cnt == 0:
        raise RuntimeError(f'{t} 테이블이 비어 있습니다. 국내 주식 데이터 수집.py 를 먼저 실행하세요.')
    print(t, cnt)

#%% 공통 함수 factor_stat
def factor_stat(df):
    n = len(df)
    ret_ari = (df.mean() * 12).round(2)
    ret_geo = (((1 + df / 100).prod() ** (12 / n) - 1) * 100).round(2)
    vol = (df.std() * np.sqrt(12)).round(2)
    sharp = (ret_ari / vol).round(2)
    stat = pd.concat([ret_ari, ret_geo, vol, sharp], axis=1)
    stat.columns = ['아리스메틱 수익률(%)', '지오메트릭 수익률(%)', '변동성(%)', '샤프지수']
    return stat

#%% 베타 계산
ticker = ['^KS11', '039490.KS']
data = yf.download(ticker, start='2016-01-01', auto_adjust=False)['Adj Close']
data = data[ticker]
data = data.dropna()

return_df = data.pct_change().dropna()
return_df.columns = ['KOSPI', 'SEC']

x = sm.add_constant(return_df['KOSPI'])
y = return_df['SEC']

reg = sm.OLS(y, x).fit()
print(reg.summary())

beta = reg.params['KOSPI']
alpha = reg.params['const']
print(beta, alpha)

t_val = reg.params['KOSPI'] / reg.bse['KOSPI']
print(float(t_val))

#%% DataReader 로 팩터 데이터 불러오기
df_pbr = web.DataReader('Portfolios_Formed_on_BE-ME', 'famafrench',
                        start='1900-01-01')
print(df_pbr['DESCR'])

df_pbr_vw = df_pbr[0].copy()
print(df_pbr_vw.columns)

#%% PBR별 포트폴리오 수익률
df_pbr_vw = df_pbr_vw[['Lo 20', 'Qnt 2', 'Qnt 3', 'Qnt 4', 'Hi 20']]
df_pbr_vw.columns = ['Low PBR', 'PBR2', 'PBR3', 'PBR4', 'High PBR']
df_pbr_vw.index = df_pbr_vw.index.to_timestamp()

(1 + df_pbr_vw / 100).cumprod().plot(figsize=(10, 6), title='PBR별 누적수익률')
plt.show()

(1 + df_pbr_vw / 100).cumprod().plot(figsize=(10, 6), logy=True,
                                     title='PBR별 누적수익률(로그)')
plt.show()

factor_stat(df_pbr_vw)

#%% PER, PCR 누적수익률
for name in ['Portfolios_Formed_on_E-P', 'Portfolios_Formed_on_CF-P']:
    df_tmp = web.DataReader(name, 'famafrench', start='1900-01-01')[0]
    df_tmp = df_tmp[['Lo 20', 'Qnt 2', 'Qnt 3', 'Qnt 4', 'Hi 20']]
    df_tmp.index = df_tmp.index.to_timestamp()
    (1 + df_tmp / 100).cumprod().plot(figsize=(10, 6), logy=True, title=name)
    plt.show()
    print(factor_stat(df_tmp))

#%% 밸류 포트폴리오 - 데이터 불러오기
ticker_sql = """
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker)
and 종목구분 = '보통주';
"""
ticker_list = pd.read_sql(ticker_sql, con=engine)

value_sql = """
select * from kor_value
where 기준일 = (select max(기준일) from kor_value);
"""
value_list = pd.read_sql(value_sql, con=engine)
value_list.head()

#%% 밸류 포트폴리오 - 저PER, 저PBR 20종목
value_pivot = value_list.pivot(index='종목코드', columns='지표', values='값')

value_rank = value_pivot[['PER', 'PBR']].rank(axis=0)
value_sum = value_rank.sum(axis=1, skipna=False).rank()
value_pivot['invest'] = np.where(value_sum <= 20, 'Y', 'N')

port_value = ticker_list.drop(columns=['PER']).merge(value_pivot.reset_index(), on='종목코드')
port_value = port_value[port_value['invest'] == 'Y']
port_value[['종목코드', '종목명', 'PER', 'PBR']]

#%% 개 지표 결합 - 상관관계
value_pivot = value_list.pivot(index='종목코드', columns='지표', values='값')
value_pivot = value_pivot[['PER', 'PBR', 'PCR', 'PSR', 'DY']]

value_rank = value_pivot.rank(axis=0)
value_rank['DY'] = value_pivot['DY'].rank(ascending=False)

mask = np.triu(np.ones_like(value_rank.corr(), dtype=bool))
fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(value_rank.corr(), annot=True, mask=mask, fmt='.2f',
            cmap=sns.color_palette('coolwarm', as_cmap=True), ax=ax)
plt.show()

#%% 개 지표 결합 - 종합 순위
value_sum = value_rank.sum(axis=1, skipna=False).rank()
value_pivot['invest'] = np.where(value_sum <= 20, 'Y', 'N')

port_value5 = ticker_list.drop(columns=['PER']).merge(value_pivot.reset_index(), on='종목코드')
port_value5 = port_value5[port_value5['invest'] == 'Y']
port_value5[['종목코드', '종목명', 'PER', 'PBR', 'PCR', 'PSR', 'DY']]
