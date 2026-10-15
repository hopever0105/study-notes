# 퀄리티 팩터와 마법공식
#%% 공통 import 및 DB 연결 설정
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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


#%% 계정 이름 통일 + 재무제표 불러오기 함수 load_fs
acc_map = {
    '자산': '자산총계',
    '자본': '자본총계',
    '부채총계': '부채',
    '매출액(수익)': '매출액',
    '유형자산감가상각비': '감가상각비',
    '유형자산등감가상각비': '감가상각비',
}
acc_prior = {'자산': 1, '자본': 1, '부채': 1, '유형자산등감가상각비': 1}

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
need_acc = ['당기순이익', '매출총이익', '영업활동으로인한현금흐름', '자산총계', '자본총계',
            '법인세비용', '이자비용', '현금및현금성자산', '부채',
            '유동부채', '유동자산', '비유동자산', '감가상각비']
acc_db = {acc_map.get(a, a) for a in
          pd.read_sql("select distinct 계정 from kor_fs;", con=engine)['계정']}
print('없는 계정:', [a for a in need_acc if a not in acc_db])

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

#%% 수익성별 포트 수익률
url = 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_OP_CSV.zip'
df_op = pd.read_csv(url, skiprows=24, encoding='cp1252')

df_op.rename(columns={df_op.columns[0]: 'date'}, inplace=True)
is_ym = df_op['date'].astype(str).str.strip().str.fullmatch(r'\d{6}')
end_point = (~is_ym).values.argmax()
df_op = df_op.iloc[:end_point].copy()
df_op['date'] = pd.to_datetime(df_op['date'].astype(str).str.strip(), format='%Y%m')
df_op = df_op.set_index('date').astype(float)

df_op_vw = df_op[['Lo 20', 'Qnt 2', 'Qnt 3', 'Qnt 4', 'Hi 20']]
(1 + df_op_vw / 100).cumprod().plot(figsize=(10, 6), logy=True,
                                    title='수익성별 누적수익률')
plt.show()

factor_stat(df_op_vw)

#%% 우량성 포트 - 재무제표 TTM 계산
fs_list = load_fs(['당기순이익', '매출총이익', '영업활동으로인한현금흐름', '자산총계', '자본총계'])

fs_list['ttm'] = fs_list.groupby(['종목코드', '계정'])['값'].transform(
    lambda x: x.rolling(window=4, min_periods=4).sum()
)

fs_list['ttm'] = np.where(fs_list['계정'].isin(['자산총계', '자본총계']),
                          fs_list['ttm'] / 4, fs_list['ttm'])

fs_list_clean = fs_list.dropna(subset=['ttm']).groupby(['종목코드', '계정']).tail(1)
fs_list_pivot = fs_list_clean.pivot(index='종목코드', columns='계정', values='ttm')

#%% 우량성 포트 - ROE, GPA, CFO
data_QUALITY = pd.DataFrame(index=fs_list_pivot.index)
data_QUALITY['ROE'] = fs_list_pivot['당기순이익'] / fs_list_pivot['자본총계']
data_QUALITY['GPA'] = fs_list_pivot['매출총이익'] / fs_list_pivot['자산총계']
data_QUALITY['CFO'] = fs_list_pivot['영업활동으로인한현금흐름'] / fs_list_pivot['자산총계']
data_QUALITY.head()

#%% 우량성 포트 - 상관관계
quality_rank = data_QUALITY.rank(ascending=False, axis=0)

mask = np.triu(np.ones_like(quality_rank.corr(), dtype=bool))
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(quality_rank.corr(), annot=True, mask=mask, fmt='.2f',
            cmap=sns.color_palette('coolwarm', as_cmap=True), ax=ax)
plt.show()

#%% 우량성 포트 - 종목 선정
quality_sum = quality_rank.sum(axis=1, skipna=False).rank()

ticker_sql = """
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker)
and 종목구분 = '보통주';
"""
ticker_list = pd.read_sql(ticker_sql, con=engine)

data_QUALITY['invest'] = np.where(quality_sum <= 20, 'Y', 'N')
port_quality = ticker_list.merge(data_QUALITY.reset_index(), on='종목코드')
port_quality = port_quality[port_quality['invest'] == 'Y']
port_quality[['종목코드', '종목명', 'ROE', 'GPA', 'CFO']]

#%% 퀄리티와 밸류의 관계
value_sql = """
select * from kor_value
where 기준일 = (select max(기준일) from kor_value);
"""
value_list = pd.read_sql(value_sql, con=engine)
value_pivot = value_list.pivot(index='종목코드', columns='지표', values='값')

data_bind = pd.DataFrame({
    'PBR_rank': value_pivot['PBR'].rank(),
    'GPA_rank': data_QUALITY['GPA'].rank(ascending=False)
}).dropna()

print(data_bind.corr(method='spearman'))

#%% 퀄리티와 밸류 - 분위수 막대그래프
data_bind['PBR_q'] = pd.qcut(data_bind['PBR_rank'], q=5, labels=False)
data_bind['GPA_mean'] = data_QUALITY['GPA']

data_bind.groupby('PBR_q')['GPA_mean'].mean().plot.bar(figsize=(8, 5))
plt.show()

#%% 퀄리티와 밸류 결합 포트 (BEME x OP 5x5)
import re
url = 'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/25_Portfolios_BEME_OP_5x5_CSV.zip'
raw = pd.read_csv(url, header=None, names=range(30), encoding='cp1252',
                  skip_blank_lines=False)

is_ym = raw[0].astype(str).str.strip().str.fullmatch(r'\d{6}').values
start = is_ym.argmax()
end = start + (~is_ym[start:]).argmax()
header = raw.iloc[start - 1].dropna().astype(str).str.strip().tolist()

df_25 = raw.iloc[start:end, :len(header) + 1].copy()
df_25.columns = ['date'] + header
df_25['date'] = pd.to_datetime(df_25['date'].astype(str).str.strip(), format='%Y%m')
df_25 = df_25.set_index('date').astype(float)
df_25 = df_25.replace([-99.99, -999], np.nan)
print(df_25.columns.tolist())

def bm_op(c):
    c = c.replace('LoBM', 'BM1').replace('HiBM', 'BM5')
    c = c.replace('LoOP', 'OP1').replace('HiOP', 'OP5')
    m = re.search(r'BM\s*(\d).*?OP\s*(\d)', c)
    return (int(m.group(1)), int(m.group(2))) if m else None

pos = {c: bm_op(c) for c in df_25.columns}
if None in pos.values():
    raise ValueError(f'컬럼명 형식이 다릅니다. 위에 출력된 컬럼명을 확인하세요: {df_25.columns.tolist()}')

col_quality = [c for c, (b, o) in pos.items() if o == 5]
col_value = [c for c, (b, o) in pos.items() if b == 5]
col_worst = [c for c, (b, o) in pos.items() if b == 1 and o == 1]
col_best = [c for c, (b, o) in pos.items() if b == 5 and o == 5]
print(len(col_quality), len(col_value), len(col_worst), len(col_best))

df_cmp = pd.DataFrame({
    'Quality': df_25[col_quality].mean(axis=1),
    'Value': df_25[col_value].mean(axis=1),
    'Worst': df_25[col_worst].mean(axis=1),
    'Best': df_25[col_best].mean(axis=1),
})

(1 + df_cmp / 100).cumprod().plot(figsize=(10, 6), logy=True,
                                  title='퀄리티/밸류 조합 누적수익률')
plt.show()

factor_stat(df_cmp)

#%% 마법 공식 포트 - 데이터
fs_magic = load_fs(['당기순이익', '법인세비용', '이자비용', '현금및현금성자산', '부채',
                    '유동부채', '유동자산', '비유동자산', '감가상각비'])

fs_magic['ttm'] = fs_magic.groupby(['종목코드', '계정'])['값'].transform(
    lambda x: x.rolling(window=4, min_periods=4).sum()
)

fs_magic_last = fs_magic.groupby(['종목코드', '계정']).tail(1)
last_pivot = fs_magic_last.pivot(index='종목코드', columns='계정', values='값')

fs_magic_ttm = fs_magic.dropna(subset=['ttm']).groupby(['종목코드', '계정']).tail(1)
ttm_pivot = fs_magic_ttm.pivot(index='종목코드', columns='계정', values='ttm')

print(last_pivot.notna().sum())
print(ttm_pivot.notna().sum())

#%% 마법 공식 포트 - EBIT, EV, 이익수익률
ticker_sql = """
select * from kor_ticker
where 기준일 = (select max(기준일) from kor_ticker)
and 종목구분 = '보통주';
"""
ticker_list = pd.read_sql(ticker_sql, con=engine)

magic_ebit = ttm_pivot['당기순이익'] + ttm_pivot['법인세비용'] + ttm_pivot['이자비용']

magic_cap = ticker_list.set_index('종목코드')['시가총액'] / 100000000
magic_debt = last_pivot['부채']

magic_excess_cash = (last_pivot['유동부채'] - last_pivot['유동자산']
                     + last_pivot['현금및현금성자산'])
magic_excess_cash_final = magic_excess_cash.clip(lower=0)

magic_ev = magic_cap + magic_debt - magic_excess_cash_final
magic_ey = magic_ebit / magic_ev

#%% 마법 공식 포트 - 투하자본수익률
magic_ic = ((last_pivot['유동자산'] - last_pivot['유동부채'])
            + (last_pivot['비유동자산'] - last_pivot['감가상각비']))
magic_roc = magic_ebit / magic_ic

#%% 마법 공식 포트 - 종목 선정
data_magic = pd.DataFrame({'magic_ey': magic_ey, 'magic_roc': magic_roc})
data_magic.index.name = '종목코드'
data_magic = data_magic.replace([np.inf, -np.inf], np.nan)

magic_rank = data_magic.rank(ascending=False, axis=0)
data_magic['magic_rank'] = magic_rank.sum(axis=1, skipna=False).rank()
data_magic['invest'] = np.where(data_magic['magic_rank'] <= 20, 'Y', 'N')

port_magic = ticker_list.merge(data_magic.reset_index(), on='종목코드')
port_magic[port_magic['invest'] == 'Y'][['종목코드', '종목명', 'magic_ey', 'magic_roc']]

#%% 마법 공식 포트 - 산점도
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=data_magic.dropna(), x='magic_ey', y='magic_roc',
                hue='invest', alpha=0.6, ax=ax)
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 3)
plt.show()
