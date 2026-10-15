# 이상치 처리와 퀄리티-밸류-모멘텀 멀티팩터
#%% 공통 import 및 DB 연결 설정
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from scipy.stats import zscore
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

#%% 계정 이름 통일 + 재무제표 불러오기 함수 load_fs
acc_map = {
    '자산': '자산총계',
    '자본': '자본총계',
    '매출액(수익)': '매출액',
    '유형자산감가상각비': '감가상각비',
    '유형자산등감가상각비': '감가상각비',
}
acc_prior = {'자산': 1, '자본': 1, '유형자산등감가상각비': 1}

def load_fs(accounts, freq='q'):
    raw = [k for k, v in acc_map.items() if v in accounts]
    in_str = "','".join(sorted(set(accounts) | set(raw)))
    sql = f"""
    select 종목코드, 계정, 기준일, 값
    from kor_fs
    where 계정 in ('{in_str}')
    and 공시구분 = '{freq}';
    """
    df = pd.read_sql(sql, con=engine).dropna(subset=['값'])
    df['우선순위'] = df['계정'].map(acc_prior).fillna(0)
    df['계정'] = df['계정'].replace(acc_map)
    df = df.sort_values(['종목코드', '계정', '기준일', '우선순위'])
    df = df.drop_duplicates(['종목코드', '계정', '기준일'], keep='first')
    df = df.drop(columns='우선순위')
    return df.sort_values(['종목코드', '계정', '기준일']).reset_index(drop=True)

#%% 재무제표 계정 이름 확인
need_acc = ['당기순이익', '매출총이익', '영업활동으로인한현금흐름', '자산총계', '자본총계']
acc_db = {acc_map.get(a, a) for a in
          pd.read_sql("select distinct 계정 from kor_fs;", con=engine)['계정']}
print('없는 계정:', [a for a in need_acc if a not in acc_db])

#%% PBR 이상치 확인
value_sql = """
select * from kor_value
where 기준일 = (select max(기준일) from kor_value);
"""
value_list = pd.read_sql(value_sql, con=engine)
value_pivot = value_list.pivot(index='종목코드', columns='지표', values='값')

value_pivot['PBR'].plot.hist(bins=100, figsize=(10, 6))
plt.show()

q_low = value_pivot['PBR'].quantile(0.01)
q_hi = value_pivot['PBR'].quantile(0.99)
print(q_low, q_hi)

#%% 이상치 처리 - 트림
value_trim = value_pivot['PBR'][(value_pivot['PBR'] > q_low) &
                                (value_pivot['PBR'] < q_hi)]
value_trim.plot.hist(bins=100, figsize=(10, 6))
plt.show()

#%% 이상치 처리 - 윈저라이징
value_winsor = value_pivot['PBR'].clip(lower=q_low, upper=q_hi)
value_winsor.plot.hist(bins=100, figsize=(10, 6))
plt.show()

#%% 팩터 결합 - 순위 분포
value_rank = value_pivot[['PBR']].rank()
value_rank['PBR'].plot.hist(bins=100, figsize=(10, 6))
plt.show()

print(value_rank['PBR'].isna().sum())

#%% 팩터 결합 - Z-score 정규화
value_z = value_pivot[['PBR']].rank().apply(zscore, nan_policy='omit')
value_z['PBR'].plot.hist(bins=100, figsize=(10, 6))
plt.show()

#%% 데이터 불러오기 - 종목, 재무제표, 가치지표, 주가, 섹터
ticker_sql = """
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker)
and 종목구분 = '보통주';
"""
ticker_list = pd.read_sql(ticker_sql, con=engine)

fs_list = load_fs(['당기순이익', '매출총이익', '영업활동으로인한현금흐름', '자산총계', '자본총계'])

value_sql = """
select * from kor_value
where 기준일 = (select max(기준일) from kor_value);
"""
value_list = pd.read_sql(value_sql, con=engine)

price_sql = """
select 날짜, 종가, 종목코드
from kor_price
where 날짜 >= (select date_sub(max(날짜), interval 1 year) from kor_price);
"""
price_list = pd.read_sql(price_sql, con=engine)

sector_sql = """
select * from kor_sector
where 기준일 = (select max(기준일) from kor_sector);
"""
sector_list = pd.read_sql(sector_sql, con=engine)
print(sector_list.columns.tolist())

#%% 퀄리티 지표 계산
fs_list['ttm'] = fs_list.groupby(['종목코드', '계정'])['값'].transform(
    lambda x: x.rolling(window=4, min_periods=4).sum()
)
fs_list['ttm'] = np.where(fs_list['계정'].isin(['자산총계', '자본총계']),
                          fs_list['ttm'] / 4, fs_list['ttm'])

fs_list_clean = fs_list.dropna(subset=['ttm']).groupby(['종목코드', '계정']).tail(1)
fs_list_pivot = fs_list_clean.pivot(index='종목코드', columns='계정', values='ttm')

data_QUALITY = pd.DataFrame(index=fs_list_pivot.index)
data_QUALITY['ROE'] = fs_list_pivot['당기순이익'] / fs_list_pivot['자본총계']
data_QUALITY['GPA'] = fs_list_pivot['매출총이익'] / fs_list_pivot['자산총계']
data_QUALITY['CFO'] = fs_list_pivot['영업활동으로인한현금흐름'] / fs_list_pivot['자산총계']
data_QUALITY = data_QUALITY.reset_index()

#%% 밸류 지표 정리
value_pivot = value_list.pivot(index='종목코드', columns='지표', values='값')
value_pivot = value_pivot[['PBR', 'PCR', 'PER', 'PSR', 'DY']].reset_index()

#%% 모멘텀 - 12M 수익률, K-Ratio
price_pivot = price_list.pivot(index='날짜', columns='종목코드', values='종가')

ret_list = (price_pivot.iloc[-1] / price_pivot.iloc[0] - 1).to_frame('12M')
ret_list = ret_list.reset_index()

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

#%% 테이블 합치기 - data_bind
data_bind = ticker_list[['종목코드', '종목명']].copy()
data_bind = data_bind.merge(
    sector_list[['CMP_CD', 'SEC_NM_KOR']],
    left_on='종목코드', right_on='CMP_CD', how='left'
).drop(columns='CMP_CD')
data_bind = data_bind.merge(data_QUALITY, on='종목코드', how='left')
data_bind = data_bind.merge(value_pivot, on='종목코드', how='left')
data_bind = data_bind.merge(ret_list, on='종목코드', how='left')
data_bind = data_bind.merge(k_ratio_bind, on='종목코드', how='left')

data_bind.head()

#%% 팩터별 정리 함수 col_clean
def col_clean(df, cutoff=0.01, asc=False):
    q_low = df.quantile(cutoff)
    q_hi = df.quantile(1 - cutoff)

    df_trim = df[(df > q_low) & (df < q_hi)]

    if asc == False:
        df_rank = df_trim.rank(axis=0, ascending=False)
    else:
        df_rank = df_trim.rank(axis=0, ascending=True)

    df_z_score = pd.Series(zscore(df_rank, nan_policy='omit'), index=df_rank.index)

    return df_z_score

#%% data_bind_group - 팩터 묶음 만들기
data_bind_group = data_bind.set_index(['종목코드', '종목명']).loc[
    :, ['ROE', 'GPA', 'CFO', 'PBR', 'PCR', 'PER', 'PSR', 'DY', '12M', 'K_ratio']]
data_bind_group.head()

#%% z_quality, z_value, z_momentum
z_quality = data_bind_group[['ROE', 'GPA', 'CFO']].apply(
    col_clean, cutoff=0.01, asc=False)

z_value_low = data_bind_group[['PBR', 'PCR', 'PER', 'PSR']].apply(
    col_clean, cutoff=0.01, asc=True)
z_value_dy = data_bind_group[['DY']].apply(col_clean, cutoff=0.01, asc=False)
z_value = pd.concat([z_value_low, z_value_dy], axis=1)

z_momentum = data_bind_group[['12M', 'K_ratio']].apply(
    col_clean, cutoff=0.01, asc=False)

#%% 분포 확인
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
z_quality.sum(axis=1, skipna=False).plot.hist(bins=50, ax=axes[0], title='quality')
z_value.sum(axis=1, skipna=False).plot.hist(bins=50, ax=axes[1], title='value')
z_momentum.sum(axis=1, skipna=False).plot.hist(bins=50, ax=axes[2], title='momentum')
plt.show()

#%% 재정규화 - data_bind_final
z_quality_summ = z_quality.sum(axis=1, skipna=False).to_frame('z_quality')
z_value_summ = z_value.sum(axis=1, skipna=False).to_frame('z_value')
z_momentum_summ = z_momentum.sum(axis=1, skipna=False).to_frame('z_momentum')

data_bind_final = pd.concat([z_quality_summ, z_value_summ, z_momentum_summ], axis=1)
data_bind_final = data_bind_final.apply(zscore, nan_policy='omit')
data_bind_final.head()

#%% 팩터 간 상관관계
mask = np.triu(np.ones_like(data_bind_final.corr(), dtype=bool))
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(data_bind_final.corr(), annot=True, mask=mask, fmt='.2f',
            cmap=sns.color_palette('coolwarm', as_cmap=True), ax=ax)
plt.show()

#%% 최종 포트폴리오 - 가중합과 20종목 선정
wts = [0.3, 0.3, 0.3]
data_bind_final_sum = (data_bind_final * wts).sum(axis=1, skipna=False).to_frame()
data_bind_final_sum.columns = ['qvm']

port_qvm = data_bind.merge(data_bind_final_sum, on=['종목코드'])
port_qvm['invest'] = np.where(port_qvm['qvm'].rank() <= 20, 'Y', 'N')

port_qvm[port_qvm['invest'] == 'Y'].round(4)

#%% plot_rank 함수와 melt 데이터
def plot_rank(df):
    ax = sns.displot(data=df, x='rank', col='variable', col_wrap=3,
                     facet_kws={'sharey': False, 'sharex': True},
                     bins=20, height=3, aspect=1.2)
    ax.set_titles('{col_name}')
    plt.subplots_adjust(top=0.85)
    plt.show()

invest_codes = port_qvm.loc[port_qvm['invest'] == 'Y', '종목코드']
data_rank = data_bind.set_index('종목코드')[
    ['ROE', 'GPA', 'CFO', 'PBR', 'PCR', 'PER', 'PSR', 'DY', '12M', 'K_ratio']
].rank(pct=True)
data_rank = data_rank.loc[invest_codes]

data_melt = data_rank.reset_index().melt(id_vars='종목코드')
data_melt = data_melt.rename(columns={'value': 'rank'})

#%% hist_quality, hist_value, hist_momentum
hist_quality = data_melt[data_melt['variable'].isin(['ROE', 'GPA', 'CFO'])]
plot_rank(hist_quality)

hist_value = data_melt[data_melt['variable'].isin(['PBR', 'PCR', 'PER', 'PSR', 'DY'])].copy()
hist_value.loc[hist_value['variable'] == 'DY', 'rank'] = \
    1 - hist_value.loc[hist_value['variable'] == 'DY', 'rank']
plot_rank(hist_value)

hist_momentum = data_melt[data_melt['variable'].isin(['12M', 'K_ratio'])]
plot_rank(hist_momentum)

#%% 엑셀로 저장
port_qvm[port_qvm['invest'] == 'Y']['종목코드'].to_excel('model.xlsx', index=False)
