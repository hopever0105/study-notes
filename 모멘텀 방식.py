# 모멘텀, K-Ratio, 섹터 중립
#%% 공통 import 및 DB 연결 설정
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
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

#%% 모멘텀별 포트 수익률
df_mom = web.DataReader('10_Portfolios_Prior_12_2', 'famafrench',
                        start='1900-01-01')
df_mom_vw = df_mom[0].copy()
df_mom_vw.index = df_mom_vw.index.to_timestamp()
print(df_mom_vw.columns)

(1 + df_mom_vw / 100).cumprod().plot(figsize=(10, 6), logy=True,
                                     title='모멘텀 10분위 누적수익률')
plt.show()

factor_stat(df_mom_vw)

#%% 모멘텀 포트 - 데이터 불러오기
ticker_sql = """
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker)
and 종목구분 = '보통주';
"""
ticker_list = pd.read_sql(ticker_sql, con=engine)

price_sql = """
select 날짜, 종가, 종목코드
from kor_price
where 날짜 >= (select date_sub(max(날짜), interval 1 year) from kor_price);
"""
price_list = pd.read_sql(price_sql, con=engine)
price_list.head()

#%% 모멘텀 포트 - 12개월 수익률
price_pivot = price_list.pivot(index='날짜', columns='종목코드', values='종가')

ret_list = (price_pivot.iloc[-1] / price_pivot.iloc[0] - 1)
ret_list = ret_list.to_frame('12M')

ticker_list_mom = ticker_list.merge(ret_list.reset_index(), on='종목코드')
ticker_list_mom['모멘텀순위'] = ticker_list_mom['12M'].rank(ascending=False)

ticker_list_mom[ticker_list_mom['모멘텀순위'] <= 20][['종목코드', '종목명', '12M']]

#%% 모멘텀 포트 - 그래프
mom_top = ticker_list_mom[ticker_list_mom['모멘텀순위'] <= 20]['종목코드'].tolist()
price_mom = price_pivot[mom_top]
price_mom = price_mom / price_mom.iloc[0] * 100

price_melt = price_mom.reset_index().melt(id_vars='날짜', var_name='종목코드',
                                          value_name='지수')
price_melt = price_melt.merge(ticker_list[['종목코드', '종목명']], on='종목코드')

g = sns.relplot(data=price_melt, x='날짜', y='지수', col='종목명',
                col_wrap=5, kind='line', height=2.5, aspect=1.3,
                facet_kws={'sharey': False, 'sharex': True})
g.set_xticklabels(rotation=45)
g.fig.set_size_inches(16, 10)
g.fig.subplots_adjust(hspace=0.5, wspace=0.3)
plt.show()

#%% K-Ratio 계산 (한 종목 예시)
ticker_one = price_pivot.columns[0]

ret = price_pivot[[ticker_one]].pct_change().dropna()
ret_cum = np.log(1 + ret).cumsum()

x = np.array(range(len(ret)))
y = ret_cum[ticker_one].values

reg = sm.OLS(y, x).fit()
k_ratio_one = float(reg.params[0] / reg.bse[0])
print(ticker_one, k_ratio_one)

#%% K-Ratio 전종목 계산
ret = price_pivot.pct_change().iloc[1:]
ret_cum = np.log(1 + ret).cumsum()

x = np.array(range(len(ret)))
k_ratio = {}

for i in range(len(price_pivot.columns)):
    ticker = price_pivot.columns[i]
    try:
        y = ret_cum[ticker]
        reg = sm.OLS(y, x).fit()
        res = float(reg.params.iloc[0] / reg.bse.iloc[0])
    except Exception:
        res = np.nan
    k_ratio[ticker] = res

k_ratio_bind = pd.DataFrame.from_dict(k_ratio, orient='index').reset_index()
k_ratio_bind.columns = ['종목코드', 'K_ratio']
k_ratio_bind.head()

#%% K-Ratio 종목 선정
ticker_list_k = ticker_list.merge(k_ratio_bind, on='종목코드')
ticker_list_k['K_ratio순위'] = ticker_list_k['K_ratio'].rank(ascending=False)

k_top = ticker_list_k[ticker_list_k['K_ratio순위'] <= 20]
k_top[['종목코드', '종목명', 'K_ratio']]

#%% K-Ratio 그래프
k_codes = k_top['종목코드'].tolist()
price_k = price_pivot[k_codes]
price_k = price_k / price_k.iloc[0] * 100

price_k_melt = price_k.reset_index().melt(id_vars='날짜', var_name='종목코드',
                                          value_name='지수')
price_k_melt = price_k_melt.merge(ticker_list[['종목코드', '종목명']], on='종목코드')

g = sns.relplot(data=price_k_melt, x='날짜', y='지수', col='종목명',
                col_wrap=5, kind='line', height=2.5, aspect=1.3,
                facet_kws={'sharey': False, 'sharex': True})
g.set_xticklabels(rotation=45)
g.fig.set_size_inches(16, 10)
g.fig.subplots_adjust(hspace=0.5, wspace=0.3)
plt.show()

#%% 섹터 중립 - 데이터 불러오기
sector_sql = """
select * from kor_sector
where 기준일 = (select max(기준일) from kor_sector);
"""
sector_list = pd.read_sql(sector_sql, con=engine)

data_bind = ticker_list[['종목코드', '종목명']].merge(
    sector_list[['CMP_CD', 'SEC_NM_KOR']],
    left_on='종목코드', right_on='CMP_CD', how='left'
).drop(columns='CMP_CD')

data_bind = data_bind.merge(ret_list.reset_index(), on='종목코드')
data_bind = data_bind.merge(k_ratio_bind, on='종목코드')
data_bind.head()

#%% 섹터 쏠림 확인
top20 = data_bind.sort_values('12M', ascending=False).head(20)
top20['SEC_NM_KOR'].value_counts().sort_values().plot.barh(figsize=(8, 5))
plt.show()

#%% 섹터 중립 - 섹터 내 Z-score
data_bind['z_score'] = data_bind.groupby('SEC_NM_KOR', dropna=False)['12M'].transform(
    lambda x: (x - x.mean()) / x.std()
)

top20_neutral = data_bind.sort_values('z_score', ascending=False).head(20)
top20_neutral['SEC_NM_KOR'].value_counts().sort_values().plot.barh(figsize=(8, 5))
plt.show()
