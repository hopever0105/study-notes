#%%
"""
[가치 투자 퀀트 전략]

마법공식은 가장 널리 알려진 '퀀트 전략'이다. 
마법공식은 우량한 기업을 저렴한 가격에 매수하는 초간단 주식투자법이다. 
재정 상태를 알아보기 위해 관련 데이터를 분석하는 방법을 기본 분석이라고 하는데, 
마법공식은 기본 분석의 정석이다.

[양적 가치 투자 철학]
① 유니버스(종목) 확인
② 아웃라이어(outliers) 제거
③ 가치(value) 찾기
④ 퀄리티(quality) 찾기
⑤ 신념을 가지고 투자하기

핵심은 자본 수익률과 이익 수익률 순위를 매겨 상위 종목의 기업을 선택하는 것이다. 
그 전에 종목을 구성할 때 다음의 두 조건으로 걸러낸다. 

첫째, 거래소에 상장된 개별 종목을 시가총액 순으로 나열한 다음 
일정 금액 이상의 종목을 기준으로 설정한다. 

둘째, 투자 종목을 선별할 때 이상치가 있는 종목을 제거한다. 
가령, 이익 수익률 지표가 마이너스(-)를 보인 종목은 제거한다. 
그다음 자본 수익률과 이익 수익률 두 가지 지표를 기준으로 순위를 매겨 투자할 종목을 선별한다.


[마법공식 워크플로]
1. 투자에 사용할 자금과 투자 대상 기업 규모를 설정한다.
2. 마법공식에 따른 순위를 나열한다.
   예를 들어, 코스피 200에서 자본수익률이 높은 기업에 대한 순위를 매기고, 
   동시에 이익수익률이 높은 기업을 순서대로 나열한다.
3. 자본 수익률 순위와 이익 수익률 순위를 더한다.
   예를 들면, 자본 수익률 순위 1위와 이익 수익률 순위 4위의 총합은 5이다.
   더한 값의 등수가 낮은 순으로 순위를 매긴다.
4. 등수가 가장 낮은 5~7개 기업을 매수한다.
   처음 투자 기간 1년 동안은 투자 금액의 20~30%만 매수한다.
5. 나머지 자금을 2~3개월마다 위 과정을 반복해 예정 투자금의 100%를 사용해 매수한다.
6. 매수가 완료된 주식을 1년 동안 보유한 후 매도한다.
7. 매도 이후 위 과정을 계속해서 반복한다.

자본 수익률은 투입된 자본 대비 수익을 얼마나 올릴 수 있는지를 판단하고, 
이익 수익률은 주가 대비 수익을 얼마나 올릴 수 있는지를 판단하는 지표다. 
일반 사용자는 각 수치를 계산하기가 어려우므로, 
대개 자본 수익률 대신 총자산 순이익률(ROA)과 
이익 수익률 대신 주가 수익률(PER)을 이용해 마법공식을 구성한다.

같은 방식으로 ROA가 높은 순으로 정렬해 우량한 주식을 결정하고
 PER이 낮은 순으로 정렬해 저렴한 주식을 결정한다.
 그다음 2개 지표 순위를 합산해 최종적으로 저렴하고 우량한 종목을 선별해 투자한다.
"""
#%%
from pathlib import Path
import pandas as pd
import pymysql

QUANT_DIR = Path(r'C:\Users\arlo0\OneDrive\바탕 화면\취업\quant')
env = {}
for line in (QUANT_DIR / '.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

conn = pymysql.connect(
    host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)),
    user=env['DB_USER'], password=env['DB_PASSWORD'],
    database=env['DB_NAME'], charset='utf8mb4'
)

# 1) DB 내 전체 테이블 목록 확인
tables = pd.read_sql("SHOW TABLES", conn)
print("=== [DB 테이블 목록] ===")
print(tables)

# 2) 재무제표 테이블(예: kor_fs)이 있다면 구조 확인
for tbl in tables.iloc[:, 0]:
    if tbl != 'kor_ticker':
        print(f"\n--- [{tbl} 샘플] ---")
        print(pd.read_sql(f"SELECT * FROM `{tbl}` LIMIT 5", conn))

conn.close()
#%%
"""
[데이터 수집 및 구조 확인]
파이썬으로 위 공식대로 종목을 선별하고, 매수 후 1년간 보유하는 방식으로 수익률을 계산.
FinanceDataReader API 사용

거래소에 상장된 종목 코드를 받아오기 위해 StockListing() 함수를 호출하고 Key 값으로 'KRX'를 전달.
'KRX'는 코스피(KOSPI), 코스닥(KOSDAQ), 코넥스(KONEX) 시장에 상장된 모든 종목을 가져온다.
종목 정보를 받아왔으면 이제 마법공식에 필요한 개별 종목의 재무제표 데이터를 받을 차례다.
PER, ROA 지표가 필요한데 재무제표 데이터는 네이버 금융, 다음 금융, 야후 파이낸스, FnGuide 등에서 받아올 수 있다.


"""
"""
import sys
from pathlib import Path

QUANT_DIR = Path(r'C:\Users\arlo0\OneDrive\바탕 화면\취업\quant')
if str(QUANT_DIR) not in sys.path:
    sys.path.insert(0, str(QUANT_DIR))

import krx_guard
krx_guard.install()          # KRX 요청 제한(2초 간격, 하루 500건, 연속 실패 3회 중지)
print('KRX 오늘 사용량:', krx_guard.status())

import FinanceDataReader as fdr

try:
    krx_all = fdr.StockListing('KRX')
    print(krx_all.head())
except krx_guard.KRXBlocked as e:
    print('KRX 요청 중지됨 → 재시도하지 않고 건너뜀:', e)
    krx_all = None"""

#%%
"""
[데이터 수집 및 구조 확인]
fdr.StockListing('KRX') 대신 MySQL stock_db.kor_ticker 최신 기준일 스냅샷을 쓴다. (KRX 요청 없음)
kor_ticker 컬럼: 종목코드, 종목명, 시장구분, 종가, 시가총액, 기준일, EPS, PER, BPS, 주당배당금, 종목구분
"""

from pathlib import Path
import pandas as pd
import pymysql

QUANT_DIR = Path(r'C:\Users\arlo0\OneDrive\바탕 화면\취업\quant')

# quant/.env 에서 DB 접속 정보 읽기
env = {}
for line in (QUANT_DIR / '.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

conn = pymysql.connect(host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)), user=env['DB_USER'],
                       password=env['DB_PASSWORD'], database=env['DB_NAME'], charset='utf8mb4')

sql = """
SELECT `종목코드`, `종목명`, `시장구분`, `종가`, `시가총액`, `EPS`, `PER`, `BPS`, `주당배당금`, `종목구분`, `기준일`
FROM kor_ticker
WHERE `기준일` = (SELECT MAX(`기준일`) FROM kor_ticker)
"""
krx_all = pd.read_sql(sql, conn)
conn.close()

print('기준일:', krx_all['기준일'].iloc[0], '/ 종목 수:', len(krx_all))
print(krx_all.head())

#%%
"""
[미리 받아놓은 PER과 ROA 지표 데이터 로드 및 전처리]
# --- 책 원본 CSV 로드 및 인코딩/결측치 처리 설명 ---
# df = pd.read_csv('../data/ch04/PER_ROA.csv', engine='python')
#
# 데이터를 살펴보게 되면 셋째 행에서 ROA가 결측치인 NaN으로 나타난 것을 확인할 수 있다.
# 삼성전자우(삼성전자 우선주)는 우선주 종목으로 일반 보통주와 성격이 다른 주식이다.
# 마법공식을 구현할 때는 보통주만을 대상으로 하므로 NaN을 보이는 데이터는 일단 제외한다.
#
# [주의! 에러가 발생한 경우]
# df = pd.read_csv('../data/ch04/PER_ROA.csv')
# -> UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc1 in position 0: invalid start byte
# 크롤링한 데이터를 저장하면서 인코딩 방식이 달라져 다시 읽을 때 못 읽거나 한글이 깨지는 경우가 있다.
# 그럴 때는 인코딩 설정에 맞춰 읽거나(encoding='cp949'), 다른 확장자로 다시 저장해 불러오면 된다.
#
# with open 구문을 이용한 방법
# import csv
# line_list = []
# with open('../data/ch04/PER_ROA.csv') as csv_file:
#     csv_reader = csv.reader(csv_file, delimiter=',')  # ',' 구분자로 파일을 읽는다
#     for row in csv_reader:
#         if '' in row:  # 한 줄씩 순회하는 중에 NaN이 포함된 행은 건너뛴다
#             pass
#         else:
#             line_list.append(row)  # 리스트에 추가
# df = pd.DataFrame(data=line_list[1:], columns=line_list[0])
"""

import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

# 윈도우 한글 폰트 (그래프 한글 깨짐 방지)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 200)

# 한국 주요 상장 종목 + 우선주 샘플 (yfinance 실시간 재무 지표 로드)
conn = pymysql.connect(host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)), user=env['DB_USER'],
                       password=env['DB_PASSWORD'], database=env['DB_NAME'], charset='utf8mb4')

# 1) 정상 종목명 마스터 로드 (fdr_kr_ticker 최신 기준일)
sql_name = """
SELECT `종목코드`, `종목명`
FROM fdr_kr_ticker
WHERE `기준일` = (SELECT MAX(`기준일`) FROM fdr_kr_ticker)
  AND `종목명` IS NOT NULL
"""
name_df = pd.read_sql(sql_name, conn).drop_duplicates(subset=['종목코드'])
krx_df = name_df.rename(columns={'종목코드': 'Symbol', '종목명': 'Name'}).copy()

# 2) DB(kor_fs)에서 연간('y') 최신 당기순이익, 자산 불러와 ROA 계산
sql_fs = """
SELECT `종목코드`, `계정`, `값`
FROM kor_fs
WHERE `공시구분` = 'y'
  AND `계정` IN ('당기순이익', '자산')
  AND (`종목코드`, `기준일`) IN (
      SELECT `종목코드`, MAX(`기준일`)
      FROM kor_fs
      WHERE `공시구분` = 'y'
      GROUP BY `종목코드`
  )
"""
fs_raw = pd.read_sql(sql_fs, conn)
conn.close()

fs_piv = fs_raw.pivot_table(index='종목코드', columns='계정', values='값', aggfunc='first')
fs_piv['ROA'] = (fs_piv['당기순이익'] / fs_piv['자산']) * 100

# 3) krx_all(시가총액, PER) + 정상 종목명 + ROA 결합
df = krx_all[['종목코드', '종가', '시가총액', 'PER']].merge(name_df, on='종목코드', how='inner')
df = df.merge(fs_piv[['ROA']], on='종목코드', how='left')
df['시가총액'] = (df['시가총액'] / 1e8).round(0)
df = df.rename(columns={'종가': '현재가'})
df = df[['종목코드', '종목명', '현재가', '시가총액', 'PER', 'ROA']]

# 결측치 및 무한대 제외
df = df[~df.isin([np.nan, np.inf, -np.inf]).any(axis=1)].copy()
df = df.reset_index(drop=True)
print(df.head())

"""
np.nan, np.inf, -np.inf 값이 하나라도 포함된(any(axis=1)) 행 데이터에 NOT(~) 연산자를 붙여 원하는 데이터만 필터링한다.
먼저 공통으로 사용할 수 있는 순위 계산 함수를 만든다.
"""

#%%
"""
[마법공식 순위 계산 함수 및 개별 지표 순위 산출]
"""

def sort_value(s_value, asc=True, standard=0):
    """
    description
        특정 지푯값을 정렬한다.

    parameters
        s_value : pandas Series
            정렬할 데이터를 받는다.

        asc : bool
            True : 오름차순
            False : 내림차순

        standard : int
            조건에 맞는 값을 True로 대체하기 위한 기준값
    returns
        s_value_mask_rank : pandas Series
            정렬된 순위
    """
    # 지표별 기준값 미만은 필터링한다.
    s_value_mask = s_value.mask(s_value < standard, np.nan)

    # 필터링된 종목에서 순위를 선정한다.
    s_value_mask_rank = s_value_mask.rank(ascending=asc, na_option="bottom")

    return s_value_mask_rank

per = pd.to_numeric(df['PER'])
roa = pd.to_numeric(df['ROA'])

# PER 지푯값을 기준으로 순위 정렬 및 0 미만 값 제거
per_rank = sort_value(per, asc=True, standard=0)
# ROA 지푯값을 기준으로 순위 정렬 및 0 미만 값 제거
roa_rank = sort_value(roa, asc=False, standard=0)

"""
1. 기준값 미만의 값은 mask()로 제거한다 (마법공식은 음수 지표를 사전에 제거).
2. rank()로 순위를 정렬한다.
3. 정렬된 데이터를 반환한다.
PER은 asc=True(오름차순), ROA는 asc=False(내림차순).
"""

print(per_rank.head())
print(roa_rank.head())

#%%
"""
[종합 순위 계산 및 마법공식 종목 선정]
"""

result_rank = per_rank + roa_rank                        # PER 순위 ROA 순위 합산
result_rank = sort_value(result_rank, asc=True)          # 합산 순위 정렬
result_rank = result_rank.where(result_rank <= 10, 0)    # 합산 순위 필터링
result_rank = result_rank.mask(result_rank > 0, 1)       # 순위 제거

"""
상위 10개 종목만 보이도록 where()에 10 이하 조건을 걸고 나머지는 0으로 대체.
순위를 보고 싶으면 넷째 줄 mask를 주석 처리한다.
"""

print(result_rank.head())
print("선정 종목 수 합계:", result_rank.sum())

mf_df = df.loc[result_rank > 0, ['종목명', '시가총액']].copy()  # 선택된 종목 데이터프레임 복사
mf_stock_list = df.loc[result_rank > 0, '종목명'].values        # 선택된 종목명 추출
print(mf_df)

#%%
"""
[종목 코드 결합 및 2025년도 마법공식 종목 수익률 확인]
재무 데이터에는 종목명만 있으므로 krx_df에서 종목 코드를 붙인다.
"""

mf_df['종목 코드'] = ''
for stock in mf_stock_list:
    matched = krx_df[krx_df['Name'] == stock]['Symbol'].values
    if len(matched) > 0:
        mf_df.loc[mf_df['종목명'] == stock, '종목 코드'] = matched[0]

print("\n--- [종목 코드 결합 후 mf_df] ---")
print(mf_df)

START = '2025-01-01'
END = '2025-12-31'

conn = pymysql.connect(host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)), user=env['DB_USER'],
                       password=env['DB_PASSWORD'], database=env['DB_NAME'], charset='utf8mb4')

codes_str = ",".join([f"'{c}'" for c in mf_df['종목 코드'].values if c != ''])
sql_price = f"""
SELECT `날짜`, `종목코드`, `종가`
FROM kor_price
WHERE `종목코드` IN ({codes_str})
  AND `날짜` BETWEEN '{START}' AND '{END}'
ORDER BY `날짜`
"""
price_2025 = pd.read_sql(sql_price, conn)
conn.close()

mf_df['2025_수익률'] = np.nan
for x in mf_df['종목 코드'].values:
    sub = price_2025[price_2025['종목코드'] == x]
    if sub.empty:
        print('가격 없음:', x)
        continue
    cum_ret = sub['종가'].iloc[-1] / sub['종가'].iloc[0] - 1
    mf_df.loc[mf_df['종목 코드'] == x, '2025_수익률'] = cum_ret

print("\n--- [2025년도 개별 누적 수익률 추가 결과] ---")
print(mf_df)

# 일별 누적 수익률 추이 (pct_change + cumprod)
price_piv = price_2025.pivot(index='날짜', columns='종목코드', values='종가')
code_to_name = dict(zip(mf_df['종목 코드'], mf_df['종목명']))
price_piv = price_piv.rename(columns=code_to_name)

mf_df_rtn = (1 + price_piv.pct_change()).cumprod()
print("\n--- [일별 누적 수익률 추이 (mf_df_rtn.tail())] ---")
print(mf_df_rtn.tail())

"""
[마법공식의 한계]
원래 마법공식은 EBIT 기반 지표(이익수익률·자본수익률)를 쓴다. 여기서는 PER·ROA로 단순화한 수정 마법공식이라
원래만큼의 수익률이 안 나올 수 있다. 공식은 출발점일 뿐이다.
"""



#%%
"""
[다년도 마법공식(Magic Formula) 연도별 리밸런싱 백테스트]
전년도(Y년) 결산 재무제표(ROA) + 연말 밸류에이션(PER) 기준 마법공식 Top 10 종목을
다음 해(Y+1년) 첫 거래일에 동일 비중 매수 -> 연말 매도했을 때의 연도별/누적 성과 분석
"""

import pandas as pd
import numpy as np
import pymysql
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

conn = pymysql.connect(
    host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)),
    user=env['DB_USER'], password=env['DB_PASSWORD'],
    database=env['DB_NAME'], charset='utf8mb4'
)

#%% [1단계] DB 연결 및 연도별 기초 데이터 로드
import pandas as pd
import numpy as np
import pymysql
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

QUANT_DIR = Path(r'C:\Users\arlo0\OneDrive\바탕 화면\취업\quant')
env = {}
for line in (QUANT_DIR / '.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

def sort_value(s_value, asc=True, standard=0):
    s_value_mask = s_value.mask(s_value < standard, np.nan)
    return s_value_mask.rank(ascending=asc, na_option="bottom")

conn = pymysql.connect(
    host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)),
    user=env['DB_USER'], password=env['DB_PASSWORD'],
    database=env['DB_NAME'], charset='utf8mb4'
)

# 보통주 종목명 마스터 로드
name_map_df = pd.read_sql("""
SELECT `종목코드`, `종목명`
FROM fdr_kr_ticker
WHERE `종목구분` = '보통주' AND `종목명` IS NOT NULL
GROUP BY `종목코드`, `종목명`
""", conn)
code_to_name = dict(zip(name_map_df['종목코드'], name_map_df['종목명']))
common_codes = set(name_map_df['종목코드'])

# 연간 재무제표(당기순이익, 자산) 로드
fs_all = pd.read_sql("""
SELECT `종목코드`, CAST(LEFT(`기준일`, 4) AS UNSIGNED) AS `연도`, `계정`, `값`
FROM kor_fs
WHERE `공시구분` = 'y'
  AND `계정` IN ('당기순이익', '자산')
""", conn)

# 연말 시가총액 및 수정주가 역산용 기준 데이터 로드
mcap_raw = pd.read_sql("""
SELECT a.`종목코드`, CAST(LEFT(a.`날짜`, 4) AS UNSIGNED) AS `연도`, a.`시가총액`
FROM kor_ohlcv_raw a
INNER JOIN (
    SELECT LEFT(`날짜`, 4) AS yr, MAX(`날짜`) AS max_dt
    FROM kor_ohlcv_raw
    GROUP BY LEFT(`날짜`, 4)
) b ON a.`날짜` = b.max_dt
""", conn)

latest_mcap = pd.read_sql("""
SELECT `종목코드`, `시가총액` AS `최신시가총액`
FROM kor_ticker
WHERE `기준일` = (SELECT MAX(`기준일`) FROM kor_ticker)
  AND `시가총액` IS NOT NULL
""", conn).set_index('종목코드')['최신시가총액']

year_end_close = pd.read_sql("""
SELECT a.`종목코드`, CAST(LEFT(a.`날짜`, 4) AS UNSIGNED) AS `연도`, a.`종가`
FROM kor_price a
INNER JOIN (
    SELECT LEFT(`날짜`, 4) AS yr, MAX(`날짜`) AS max_dt
    FROM kor_price
    GROUP BY LEFT(`날짜`, 4)
) b ON a.`날짜` = b.max_dt
""", conn)

latest_close = pd.read_sql("""
SELECT `종목코드`, `종가` AS `최신종가`
FROM kor_price
WHERE `날짜` = (SELECT MAX(`날짜`) FROM kor_price)
""", conn).set_index('종목코드')['최신종가']

conn.close()

# 백테스트 가능한 (결산연도 Y, 투자연도 Y+1) 구간 계산
fs_years = sorted(fs_all['연도'].unique())
pr_years = set(year_end_close['연도'].unique())
valid_pairs = [(int(y), int(y) + 1) for y in fs_years if (int(y) + 1) in pr_years]

print(f"데이터 로드 완료 | 백테스트 구간: {valid_pairs[0][0]}년 결산({valid_pairs[0][1]}년 투자) ~ {valid_pairs[-1][0]}년 결산({valid_pairs[-1][1]}년 투자)")

#%% [2단계] 연도별 마법공식 Top 10 선정 및 리밸런싱 수익률 계산
conn = pymysql.connect(
    host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)),
    user=env['DB_USER'], password=env['DB_PASSWORD'],
    database=env['DB_NAME'], charset='utf8mb4'
)

yearly_records = []
daily_port_returns = []
daily_mkt_returns = []

for fs_yr, hold_yr in valid_pairs:
    sub_fs = fs_all[fs_all['연도'] == fs_yr]
    piv_fs = sub_fs.pivot_table(index='종목코드', columns='계정', values='값', aggfunc='last')
    if '당기순이익' not in piv_fs.columns or '자산' not in piv_fs.columns:
        continue

    fac = piv_fs[piv_fs.index.isin(common_codes)].copy()
    fac['ROA'] = (fac['당기순이익'] / fac['자산']) * 100

    sub_mc = mcap_raw[mcap_raw['연도'] == fs_yr].set_index('종목코드')['시가총액']
    if len(sub_mc) > 100:
        fac['시가총액'] = sub_mc
    else:
        yr_cls = year_end_close[year_end_close['연도'] == fs_yr].set_index('종목코드')['종가']
        fac['시가총액'] = latest_mcap * (yr_cls / latest_close)

    fac['시가총액_억'] = fac['시가총액'] / 1e8
    fac['PER'] = fac['시가총액_억'] / fac['당기순이익']
    fac = fac.replace([np.inf, -np.inf], np.nan).dropna(subset=['PER', 'ROA', '시가총액_억'])

    # 소형주 하위 20% 제외 후 PER·ROA 순위 산정
    fac = fac[fac['시가총액_억'] >= fac['시가총액_억'].quantile(0.2)]
    p_rank = sort_value(fac['PER'], asc=True, standard=0)
    r_rank = sort_value(fac['ROA'], asc=False, standard=0)
    tot_rank = sort_value((p_rank + r_rank).dropna(), asc=True)

    top10_codes = list(tot_rank.nsmallest(10).index)
    if len(top10_codes) < 5:
        continue

    # 다음 해 보유 주가 조회
    codes_sql = ",".join([f"'{c}'" for c in top10_codes])
    pr_df = pd.read_sql(f"""
        SELECT `날짜`, `종목코드`, `종가`
        FROM kor_price
        WHERE `종목코드` IN ({codes_sql})
          AND `날짜` BETWEEN '{hold_yr}-01-01' AND '{hold_yr}-12-31'
        ORDER BY `날짜`
    """, conn)
    if pr_df.empty:
        continue

    pr_piv = pr_df.pivot(index='날짜', columns='종목코드', values='종가').ffill().bfill()
    norm_piv = pr_piv.div(pr_piv.iloc[0])
    port_daily_idx = norm_piv.mean(axis=1)
    port_daily_ret = port_daily_idx.pct_change().fillna(port_daily_idx.iloc[0] - 1)
    daily_port_returns.append(port_daily_ret)

    # 벤치마크(해당 연도 전체 종목 동일가중 평균)
    mkt_raw = pd.read_sql(f"""
        SELECT `날짜`, `종목코드`, `종가`
        FROM kor_price
        WHERE `날짜` BETWEEN '{hold_yr}-01-01' AND '{hold_yr}-12-31'
    """, conn)
    mkt_piv = mkt_raw.pivot(index='날짜', columns='종목코드', values='종가')
    mkt_ret_mat = mkt_piv.pct_change(fill_method=None)
    mkt_ret_mat = mkt_ret_mat.where(mkt_ret_mat.abs() < 0.35)
    mkt_df = mkt_ret_mat.mean(axis=1).fillna(0)
    daily_mkt_returns.append(mkt_df)

    yr_ret = (port_daily_idx.iloc[-1] - 1) * 100
    mkt_yr_ret = ((1 + mkt_df).cumprod().iloc[-1] - 1) * 100
    yr_mdd = ((port_daily_idx / port_daily_idx.cummax()) - 1).min() * 100
    top10_names = [code_to_name.get(c, c) for c in top10_codes]

    yearly_records.append({
        '투자연도': f"{hold_yr}년",
        '기준결산': f"{fs_yr}말",
        '마법공식(%)': round(yr_ret, 2),
        '시장평균(%)': round(mkt_yr_ret, 2),
        '초과수익(%p)': round(yr_ret - mkt_yr_ret, 2),
        '연중MDD(%)': round(yr_mdd, 2),
        '선정종목(Top10)': ", ".join(top10_names)
    })

conn.close()
print(f"백테스트 연산 완료: 총 {len(yearly_records)}개 연도 처리됨")

#%% [3단계] 연도별 성과 요약표 및 전체 기간 종합 성적표 출력
res_table = pd.DataFrame(yearly_records)
all_port_ret = pd.concat(daily_port_returns)
all_mkt_ret = pd.concat(daily_mkt_returns).reindex(all_port_ret.index).fillna(0)

cum_port = (1 + all_port_ret).cumprod()
cum_mkt = (1 + all_mkt_ret).cumprod()

res_table['누적배수(배)'] = [
    round(cum_port[cum_port.index.astype(str).str.startswith(row['투자연도'][:4])].iloc[-1], 2)
    for _, row in res_table.iterrows()
]

pd.set_option('display.max_colwidth', 120)
print("=== [연도별 마법공식 리밸런싱 성과 요약표] ===")
print(res_table[['투자연도', '기준결산', '마법공식(%)', '시장평균(%)', '초과수익(%p)', '연중MDD(%)', '누적배수(배)', '선정종목(Top10)']].to_string(index=False))

n_years = len(res_table)
total_ret = (cum_port.iloc[-1] - 1) * 100
cagr = (cum_port.iloc[-1] ** (1 / n_years) - 1) * 100
total_mdd = ((cum_port / cum_port.cummax()) - 1).min() * 100
win_rate = (res_table['마법공식(%)'] > 0).mean() * 100
beat_rate = (res_table['초과수익(%p)'] > 0).mean() * 100

print("\n=== [전체 기간 종합 성적표] ===")
print(f"• 테스트 기간 : {res_table['투자연도'].iloc[0]} ~ {res_table['투자연도'].iloc[-1]} ({n_years}년)")
print(f"• 누적 수익률 : {total_ret:,.2f}% (최종 {cum_port.iloc[-1]:.2f}배)  |  시장평균: {(cum_mkt.iloc[-1]-1)*100:,.2f}% ({cum_mkt.iloc[-1]:.2f}배)")
print(f"• 연평균(CAGR): {cagr:.2f}%  |  전체 MDD: {total_mdd:.2f}%")
print(f"• 플러스 연도 승률: {win_rate:.1f}%  |  시장 초과수익 승률: {beat_rate:.1f}%")

#%% [4단계] 누적 수익률 및 연도별 수익률 비교 그래프
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [1.3, 1]})

cum_port.index = pd.to_datetime(cum_port.index)
cum_mkt.index = pd.to_datetime(cum_mkt.index)

ax1.plot(cum_port.index, cum_port.values, color='royalblue', linewidth=2.2, label=f'마법공식 Top 10 누적배수 (CAGR {cagr:.1f}%)')
ax1.plot(cum_mkt.index, cum_mkt.values, color='dimgray', linewidth=1.6, linestyle='--', label='시장 동일가중 평균')
ax1.set_title('전년도 결산 기준 마법공식 Top 10 매년 리밸런싱 누적 수익률 추이', fontsize=13, fontweight='bold')
ax1.set_ylabel('누적 자산 배수 (시작=1.0)')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)

x = np.arange(len(res_table))
width = 0.38
bars1 = ax2.bar(x - width/2, res_table['마법공식(%)'], width, color='royalblue', label='마법공식 Top 10 (%)')
bars2 = ax2.bar(x + width/2, res_table['시장평균(%)'], width, color='lightgray', edgecolor='gray', label='시장평균 (%)')
ax2.axhline(0, color='black', linewidth=0.9)
ax2.set_title('연도별 수익률 비교 (마법공식 vs 시장평균)', fontsize=12, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(res_table['투자연도'])
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
ax2.legend(loc='upper left')
ax2.grid(True, axis='y', alpha=0.3)

for bar in bars1:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, h + (1.5 if h >= 0 else -4.0),
             f'{h:.1f}%', ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='navy')

plt.tight_layout()
plt.show()
#%%
import pandas as pd
import pymysql

conn = pymysql.connect(
    host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)),
    user=env['DB_USER'], password=env['DB_PASSWORD'],
    database=env['DB_NAME'], charset='utf8mb4'
)

# 1. 미국 재무제표(tv_us_fs, global_fs) 연도 범위 및 순이익/자산 계정명 확인
print("=== [1. tv_us_fs 연도 및 계정 샘플] ===")
print(pd.read_sql("""
    SELECT MIN(date) AS min_dt, MAX(date) AS max_dt, COUNT(DISTINCT ticker) AS n_tickers
    FROM tv_us_fs WHERE value IS NOT NULL
""", conn))
print(pd.read_sql("""
    SELECT DISTINCT account FROM tv_us_fs
    WHERE value IS NOT NULL AND (account LIKE '%Income%' OR account LIKE '%Asset%' OR account LIKE '%Share%')
    LIMIT 30
""", conn))

print("\n=== [2. global_fs 연도 및 계정 샘플] ===")
print(pd.read_sql("""
    SELECT MIN(date) AS min_dt, MAX(date) AS max_dt, COUNT(DISTINCT ticker) AS n_tickers
    FROM global_fs WHERE value IS NOT NULL
""", conn))
print(pd.read_sql("""
    SELECT DISTINCT account FROM global_fs
    WHERE value IS NOT NULL AND (account LIKE '%Income%' OR account LIKE '%Asset%' OR account LIKE '%Share%')
    LIMIT 30
""", conn))

# 2. 미국 주가(us_price, global_price) 연도 범위 확인
print("\n=== [3. 미국 주가 테이블 연도 범위] ===")
print(pd.read_sql("SELECT 'us_price' AS tbl, MIN(`날짜`) AS min_dt, MAX(`날짜`) AS max_dt FROM us_price", conn))
print(pd.read_sql("SELECT 'global_price' AS tbl, MIN(`Date`) AS min_dt, MAX(`Date`) AS max_dt FROM global_price", conn))

conn.close()

#%% [미국 1단계] DB에서 미국 31개 종목 재무제표(global_fs) 및 주가(us_price) 로드
import pandas as pd
import numpy as np
import pymysql
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

QUANT_DIR = Path(r'C:\Users\arlo0\OneDrive\바탕 화면\취업\quant')
env = {}
for line in (QUANT_DIR / '.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

def sort_value(s_value, asc=True, standard=0):
    s_value_mask = s_value.mask(s_value < standard, np.nan)
    return s_value_mask.rank(ascending=asc, na_option="bottom")

us_tickers = [
    'SPY',
    'AAPL', 'MSFT', 'NVDA', 'AMZN', 'SPCX', 'GOOGL', 'META', 'AVGO', 'TSLA', 'WMT',
    'AMD', 'MU', 'ASML', 'COST', 'PLTR', 'CSCO', 'INTC', 'AMAT', 'TXN', 'LRCX',
    'PANW', 'AMGN', 'NFLX', 'LIN', 'CRWD', 'GILD', 'PEP', 'SHOP', 'KLAC', 'ARM'
]
stock_universe = [t for t in us_tickers if t not in ['SPY', 'SPCX']]
tickers_sql = ",".join([f"'{t}'" for t in stock_universe])

conn = pymysql.connect(
    host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)),
    user=env['DB_USER'], password=env['DB_PASSWORD'],
    database=env['DB_NAME'], charset='utf8mb4'
)

# 연간 재무제표 로드 (순이익, 총자산, 발행주식수)
us_fs_all = pd.read_sql(f"""
SELECT `ticker`, CAST(LEFT(`date`, 4) AS UNSIGNED) AS `연도`, `account`, `value`
FROM global_fs
WHERE `ticker` IN ({tickers_sql})
  AND `freq` = 'y'
  AND `value` IS NOT NULL
  AND `account` IN ('NetIncome', 'TotalAssets', 'OrdinarySharesNumber', 'DilutedAverageShares')
""", conn)

# 미국 29개 개별 종목 일별 주가 로드 (2021년 이후)
us_price_all = pd.read_sql(f"""
SELECT `날짜`, `티커`, `종가`, `수정종가`
FROM us_price
WHERE `티커` IN ({tickers_sql})
  AND `날짜` >= '2021-01-01'
ORDER BY `날짜`
""", conn)

# 벤치마크 SPY 주가 로드 (us_price 우선 -> 없으면 sample_etf 또는 yfinance)
spy_df = pd.read_sql("""
SELECT `날짜`, `수정종가` AS `SPY`
FROM us_price
WHERE `티커` = 'SPY' AND `날짜` >= '2021-01-01'
ORDER BY `날짜`
""", conn)

if spy_df.empty:
    spy_df = pd.read_sql("""
    SELECT `Date` AS `날짜`, `SPY`
    FROM sample_etf
    WHERE `Date` >= '2021-01-01' AND `SPY` IS NOT NULL
    ORDER BY `Date`
    """, conn)

conn.close()

if spy_df.empty:
    spy_raw = yf.download('SPY', start='2021-01-01', auto_adjust=False, progress=False)
    if isinstance(spy_raw.columns, pd.MultiIndex):
        spy_raw.columns = spy_raw.columns.get_level_values(0)
    spy_df = spy_raw[['Adj Close']].reset_index()
    spy_df.columns = ['날짜', 'SPY']
    spy_df['날짜'] = spy_df['날짜'].astype(str).str[:10]

spy_series = spy_df.set_index('날짜')['SPY'].astype(float)
us_price_all['연도'] = us_price_all['날짜'].astype(str).str[:4].astype(int)

fs_years = sorted(us_fs_all['연도'].unique())
pr_years = set(us_price_all['연도'].unique())
us_valid_pairs = [(int(y), int(y) + 1) for y in fs_years if (int(y) + 1) in pr_years]

print(f"미국 데이터 로드 완료 | 백테스트 구간: {us_valid_pairs[0][0]}년 결산({us_valid_pairs[0][1]}년 투자) ~ {us_valid_pairs[-1][0]}년 결산({us_valid_pairs[-1][1]}년 투자)")

#%% [미국 2단계] 연도별 마법공식 Top 10 선정 및 리밸런싱 수익률 계산
us_yearly_records = []
us_daily_port_returns = []
us_daily_spy_returns = []

for fs_yr, hold_yr in us_valid_pairs:
    sub_fs = us_fs_all[us_fs_all['연도'] == fs_yr]
    piv_fs = sub_fs.pivot_table(index='ticker', columns='account', values='value', aggfunc='last')
    if 'NetIncome' not in piv_fs.columns or 'TotalAssets' not in piv_fs.columns:
        continue

    shares = piv_fs['OrdinarySharesNumber'] if 'OrdinarySharesNumber' in piv_fs.columns else pd.Series(np.nan, index=piv_fs.index)
    if 'DilutedAverageShares' in piv_fs.columns:
        shares = shares.fillna(piv_fs['DilutedAverageShares'])

    # 전년도 말 종가 기준 시가총액 및 PER, ROA 계산
    yr_pr = us_price_all[us_price_all['연도'] == fs_yr]
    year_end_cls = yr_pr.groupby('티커')['종가'].last()

    fac = pd.DataFrame(index=piv_fs.index)
    fac['NetIncome'] = piv_fs['NetIncome']
    fac['TotalAssets'] = piv_fs['TotalAssets']
    fac['Shares'] = shares
    fac['YearEndClose'] = year_end_cls
    fac['MarketCap'] = fac['YearEndClose'] * fac['Shares']
    fac['PER'] = fac['MarketCap'] / fac['NetIncome']
    fac['ROA'] = (fac['NetIncome'] / fac['TotalAssets']) * 100

    fac = fac.replace([np.inf, -np.inf], np.nan).dropna(subset=['PER', 'ROA'])

    # 마법공식 순위 산정 (PER > 0 오름차순, ROA > 0 내림차순)
    p_rank = sort_value(fac['PER'], asc=True, standard=0)
    r_rank = sort_value(fac['ROA'], asc=False, standard=0)
    tot_rank = sort_value((p_rank + r_rank).dropna(), asc=True)

    top10_tickers = list(tot_rank.nsmallest(10).index)
    if len(top10_tickers) < 5:
        continue

    # 다음 해(hold_yr) 1년간 수정종가 기준 동일 비중 보유 수익률 계산
    hold_pr = us_price_all[(us_price_all['연도'] == hold_yr) & (us_price_all['티커'].isin(top10_tickers))]
    if hold_pr.empty:
        continue

    pr_piv = hold_pr.pivot(index='날짜', columns='티커', values='수정종가').ffill().bfill()
    norm_piv = pr_piv.div(pr_piv.iloc[0])
    port_daily_idx = norm_piv.mean(axis=1)
    port_daily_ret = port_daily_idx.pct_change().fillna(port_daily_idx.iloc[0] - 1)
    us_daily_port_returns.append(port_daily_ret)

    # 벤치마크 SPY 동일 기간 수익률
    spy_hold = spy_series[spy_series.index.astype(str).str.startswith(str(hold_yr))].reindex(pr_piv.index).ffill().bfill()
    spy_norm = spy_hold / spy_hold.iloc[0]
    spy_daily_ret = spy_norm.pct_change().fillna(spy_norm.iloc[0] - 1)
    us_daily_spy_returns.append(spy_daily_ret)

    yr_ret = (port_daily_idx.iloc[-1] - 1) * 100
    spy_yr_ret = (spy_norm.iloc[-1] - 1) * 100
    yr_mdd = ((port_daily_idx / port_daily_idx.cummax()) - 1).min() * 100

    us_yearly_records.append({
        '투자연도': f"{hold_yr}년",
        '기준결산': f"{fs_yr}말",
        '마법공식(%)': round(yr_ret, 2),
        'SPY(%)': round(spy_yr_ret, 2),
        '초과수익(%p)': round(yr_ret - spy_yr_ret, 2),
        '연중MDD(%)': round(yr_mdd, 2),
        '선정종목(Top10)': ", ".join(top10_tickers)
    })

print(f"미국 백테스트 연산 완료: 총 {len(us_yearly_records)}개 연도 처리됨")

#%% [미국 3단계] 연도별 성과 요약표 및 전체 기간 종합 성적표 출력
us_res_table = pd.DataFrame(us_yearly_records)
us_all_port_ret = pd.concat(us_daily_port_returns)
us_all_spy_ret = pd.concat(us_daily_spy_returns).reindex(us_all_port_ret.index).fillna(0)

us_cum_port = (1 + us_all_port_ret).cumprod()
us_cum_spy = (1 + us_all_spy_ret).cumprod()

us_res_table['누적배수(배)'] = [
    round(us_cum_port[us_cum_port.index.astype(str).str.startswith(row['투자연도'][:4])].iloc[-1], 2)
    for _, row in us_res_table.iterrows()
]

pd.set_option('display.max_colwidth', 120)
print("=== [미국 나스닥 Top 30 대상 마법공식 리밸런싱 성과 요약표] ===")
print(us_res_table[['투자연도', '기준결산', '마법공식(%)', 'SPY(%)', '초과수익(%p)', '연중MDD(%)', '누적배수(배)', '선정종목(Top10)']].to_string(index=False))

n_years = len(us_res_table)
total_ret = (us_cum_port.iloc[-1] - 1) * 100
cagr = (us_cum_port.iloc[-1] ** (1 / n_years) - 1) * 100
total_mdd = ((us_cum_port / us_cum_port.cummax()) - 1).min() * 100
win_rate = (us_res_table['마법공식(%)'] > 0).mean() * 100
beat_rate = (us_res_table['초과수익(%p)'] > 0).mean() * 100

print("\n=== [미국 전체 기간 종합 성적표] ===")
print(f"• 테스트 기간 : {us_res_table['투자연도'].iloc[0]} ~ {us_res_table['투자연도'].iloc[-1]} ({n_years}년)")
print(f"• 누적 수익률 : {total_ret:,.2f}% (최종 {us_cum_port.iloc[-1]:.2f}배)  |  SPY: {(us_cum_spy.iloc[-1]-1)*100:,.2f}% ({us_cum_spy.iloc[-1]:.2f}배)")
print(f"• 연평균(CAGR): {cagr:.2f}%  |  전체 MDD: {total_mdd:.2f}%")
print(f"• 플러스 연도 승률: {win_rate:.1f}%  |  SPY 초과수익 승률: {beat_rate:.1f}%")

#%% [미국 4단계] 미국 마법공식 Top 10 vs SPY 누적 수익률 및 연도별 그래프
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [1.3, 1]})

us_cum_port.index = pd.to_datetime(us_cum_port.index)
us_cum_spy.index = pd.to_datetime(us_cum_spy.index)

ax1.plot(us_cum_port.index, us_cum_port.values, color='royalblue', linewidth=2.2, label=f'미국 마법공식 Top 10 누적배수 (CAGR {cagr:.1f}%)')
ax1.plot(us_cum_spy.index, us_cum_spy.values, color='crimson', linewidth=1.8, linestyle='--', label='SPY (S&P 500 벤치마크)')
ax1.set_title('전년도 결산 기준 미국 마법공식 Top 10 매년 리밸런싱 누적 수익률 추이', fontsize=13, fontweight='bold')
ax1.set_ylabel('누적 자산 배수 (시작=1.0)')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)

x = np.arange(len(us_res_table))
width = 0.38
bars1 = ax2.bar(x - width/2, us_res_table['마법공식(%)'], width, color='royalblue', label='마법공식 Top 10 (%)')
bars2 = ax2.bar(x + width/2, us_res_table['SPY(%)'], width, color='lightgray', edgecolor='gray', label='SPY (%)')
ax2.axhline(0, color='black', linewidth=0.9)
ax2.set_title('연도별 수익률 비교 (미국 마법공식 vs SPY)', fontsize=12, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(us_res_table['투자연도'])
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
ax2.legend(loc='upper left')
ax2.grid(True, axis='y', alpha=0.3)

for bar in bars1:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, h + (1.5 if h >= 0 else -4.0),
             f'{h:.1f}%', ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='navy')

plt.tight_layout()
plt.show()
#%% [미국 전체 1단계] DB에서 미국 전체 종목 재무제표(global_fs) 및 주가(us_price) 로드
import pandas as pd
import numpy as np
import pymysql
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

QUANT_DIR = Path(r'C:\Users\arlo0\OneDrive\바탕 화면\취업\quant')
env = {}
for line in (QUANT_DIR / '.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

def sort_value(s_value, asc=True, standard=0):
    s_value_mask = s_value.mask(s_value < standard, np.nan)
    return s_value_mask.rank(ascending=asc, na_option="bottom")

conn = pymysql.connect(
    host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)),
    user=env['DB_USER'], password=env['DB_PASSWORD'],
    database=env['DB_NAME'], charset='utf8mb4'
)

# 1) 미국 종목명 마스터 로드 (global_ticker)
us_name_df = pd.read_sql("""
SELECT `Symbol`, MAX(`Name`) AS `Name`
FROM global_ticker
WHERE `country` = 'United States' AND `Name` IS NOT NULL
GROUP BY `Symbol`
""", conn)
us_code_to_name = dict(zip(us_name_df['Symbol'], us_name_df['Name']))

# 2) 미국 전체 종목 연간 재무제표 로드 (순이익, 총자산, 발행주식수)
us_fs_all = pd.read_sql("""
SELECT `ticker`, CAST(LEFT(`date`, 4) AS UNSIGNED) AS `연도`, `account`, `value`
FROM global_fs
WHERE `freq` = 'y'
  AND `value` IS NOT NULL
  AND `account` IN ('NetIncome', 'TotalAssets', 'OrdinarySharesNumber', 'DilutedAverageShares')
""", conn)

# 3) 미국 전체 종목 연말 종가 로드 (연말 시가총액 = 연말종가 * 발행주식수 계산용)
us_year_end_close = pd.read_sql("""
SELECT a.`티커`, CAST(LEFT(a.`날짜`, 4) AS UNSIGNED) AS `연도`, a.`종가`
FROM us_price a
INNER JOIN (
    SELECT LEFT(`날짜`, 4) AS yr, MAX(`날짜`) AS max_dt
    FROM us_price
    WHERE `날짜` >= '2021-01-01'
    GROUP BY LEFT(`날짜`, 4)
) b ON a.`날짜` = b.max_dt
""", conn)

# 4) 벤치마크 SPY 주가 로드 (us_price -> sample_etf -> yfinance 순)
spy_df = pd.read_sql("""
SELECT `날짜`, `수정종가` AS `SPY`
FROM us_price
WHERE `티커` = 'SPY' AND `날짜` >= '2021-01-01'
ORDER BY `날짜`
""", conn)

if spy_df.empty:
    spy_df = pd.read_sql("""
    SELECT `Date` AS `날짜`, `SPY`
    FROM sample_etf
    WHERE `Date` >= '2021-01-01' AND `SPY` IS NOT NULL
    ORDER BY `Date`
    """, conn)

conn.close()

if spy_df.empty:
    spy_raw = yf.download('SPY', start='2021-01-01', auto_adjust=False, progress=False)
    if isinstance(spy_raw.columns, pd.MultiIndex):
        spy_raw.columns = spy_raw.columns.get_level_values(0)
    spy_df = spy_raw[['Adj Close']].reset_index()
    spy_df.columns = ['날짜', 'SPY']
    spy_df['날짜'] = spy_df['날짜'].astype(str).str[:10]

spy_series = spy_df.set_index('날짜')['SPY'].astype(float)

fs_years = sorted(us_fs_all['연도'].unique())
pr_years = set(us_year_end_close['연도'].unique())
us_valid_pairs = [(int(y), int(y) + 1) for y in fs_years if (int(y) + 1) in pr_years]

print(f"미국 전체 데이터 로드 완료 (재무 종목수: {us_fs_all['ticker'].nunique()}개)")
print(f"백테스트 구간: {us_valid_pairs[0][0]}년 결산({us_valid_pairs[0][1]}년 투자) ~ {us_valid_pairs[-1][0]}년 결산({us_valid_pairs[-1][1]}년 투자)")

#%% [미국 전체 2단계] 연도별 마법공식 Top 10 선정 및 리밸런싱 수익률 계산
conn = pymysql.connect(
    host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)),
    user=env['DB_USER'], password=env['DB_PASSWORD'],
    database=env['DB_NAME'], charset='utf8mb4'
)

us_yearly_records = []
us_daily_port_returns = []
us_daily_spy_returns = []

for fs_yr, hold_yr in us_valid_pairs:
    sub_fs = us_fs_all[us_fs_all['연도'] == fs_yr]
    piv_fs = sub_fs.pivot_table(index='ticker', columns='account', values='value', aggfunc='last')
    if 'NetIncome' not in piv_fs.columns or 'TotalAssets' not in piv_fs.columns:
        continue

    shares = piv_fs['OrdinarySharesNumber'] if 'OrdinarySharesNumber' in piv_fs.columns else pd.Series(np.nan, index=piv_fs.index)
    if 'DilutedAverageShares' in piv_fs.columns:
        shares = shares.fillna(piv_fs['DilutedAverageShares'])

    yr_cls = us_year_end_close[us_year_end_close['연도'] == fs_yr].set_index('티커')['종가']

    fac = pd.DataFrame(index=piv_fs.index)
    fac['NetIncome'] = piv_fs['NetIncome']
    fac['TotalAssets'] = piv_fs['TotalAssets']
    fac['Shares'] = shares
    fac['YearEndClose'] = yr_cls
    fac['MarketCap'] = fac['YearEndClose'] * fac['Shares']
    fac['PER'] = fac['MarketCap'] / fac['NetIncome']
    fac['ROA'] = (fac['NetIncome'] / fac['TotalAssets']) * 100

    fac = fac.replace([np.inf, -np.inf], np.nan).dropna(subset=['PER', 'ROA', 'MarketCap'])

    # 초소형주(시가총액 하위 20%) 제외 후 마법공식 순위 산정
    fac = fac[fac['MarketCap'] >= fac['MarketCap'].quantile(0.2)]
    p_rank = sort_value(fac['PER'], asc=True, standard=0)
    r_rank = sort_value(fac['ROA'], asc=False, standard=0)
    tot_rank = sort_value((p_rank + r_rank).dropna(), asc=True)

    # 주가 데이터 누락 대비 상위 15개 후보 조회 후 실제 거래 데이터 있는 상위 10개 확정
    cand_tickers = list(tot_rank.nsmallest(15).index)
    if len(cand_tickers) < 5:
        continue

    cand_sql = ",".join([f"'{t}'" for t in cand_tickers])
    hold_pr = pd.read_sql(f"""
        SELECT `날짜`, `티커`, `수정종가`
        FROM us_price
        WHERE `티커` IN ({cand_sql})
          AND `날짜` BETWEEN '{hold_yr}-01-01' AND '{hold_yr}-12-31'
        ORDER BY `날짜`
    """, conn)
    if hold_pr.empty:
        continue

    avail_tickers = [t for t in cand_tickers if t in set(hold_pr['티커'])][:10]
    hold_pr = hold_pr[hold_pr['티커'].isin(avail_tickers)]

    pr_piv = hold_pr.pivot(index='날짜', columns='티커', values='수정종가').ffill().bfill()
    norm_piv = pr_piv.div(pr_piv.iloc[0])
    port_daily_idx = norm_piv.mean(axis=1)
    port_daily_ret = port_daily_idx.pct_change().fillna(port_daily_idx.iloc[0] - 1)
    us_daily_port_returns.append(port_daily_ret)

    # 벤치마크 SPY 동일 기간 수익률
    spy_hold = spy_series[spy_series.index.astype(str).str.startswith(str(hold_yr))].reindex(pr_piv.index).ffill().bfill()
    spy_norm = spy_hold / spy_hold.iloc[0]
    spy_daily_ret = spy_norm.pct_change().fillna(spy_norm.iloc[0] - 1)
    us_daily_spy_returns.append(spy_daily_ret)

    yr_ret = (port_daily_idx.iloc[-1] - 1) * 100
    spy_yr_ret = (spy_norm.iloc[-1] - 1) * 100
    yr_mdd = ((port_daily_idx / port_daily_idx.cummax()) - 1).min() * 100

    us_yearly_records.append({
        '투자연도': f"{hold_yr}년",
        '기준결산': f"{fs_yr}말",
        '대상종목수': len(fac),
        '마법공식(%)': round(yr_ret, 2),
        'SPY(%)': round(spy_yr_ret, 2),
        '초과수익(%p)': round(yr_ret - spy_yr_ret, 2),
        '연중MDD(%)': round(yr_mdd, 2),
        '선정종목(Top10)': ", ".join(avail_tickers)
    })

conn.close()
print(f"미국 전체 종목 백테스트 연산 완료: 총 {len(us_yearly_records)}개 연도 처리됨")

#%% [미국 전체 3단계] 연도별 성과 요약표 및 전체 기간 종합 성적표 출력
us_res_table = pd.DataFrame(us_yearly_records)
us_all_port_ret = pd.concat(us_daily_port_returns)
us_all_spy_ret = pd.concat(us_daily_spy_returns).reindex(us_all_port_ret.index).fillna(0)

us_cum_port = (1 + us_all_port_ret).cumprod()
us_cum_spy = (1 + us_all_spy_ret).cumprod()

us_res_table['누적배수(배)'] = [
    round(us_cum_port[us_cum_port.index.astype(str).str.startswith(row['투자연도'][:4])].iloc[-1], 2)
    for _, row in us_res_table.iterrows()
]

pd.set_option('display.max_colwidth', 120)
print("=== [미국 전체 종목 대상 마법공식 리밸런싱 성과 요약표] ===")
print(us_res_table[['투자연도', '기준결산', '대상종목수', '마법공식(%)', 'SPY(%)', '초과수익(%p)', '연중MDD(%)', '누적배수(배)', '선정종목(Top10)']].to_string(index=False))

n_years = len(us_res_table)
total_ret = (us_cum_port.iloc[-1] - 1) * 100
cagr = (us_cum_port.iloc[-1] ** (1 / n_years) - 1) * 100
total_mdd = ((us_cum_port / us_cum_port.cummax()) - 1).min() * 100
win_rate = (us_res_table['마법공식(%)'] > 0).mean() * 100
beat_rate = (us_res_table['초과수익(%p)'] > 0).mean() * 100

print("\n=== [미국 전체 종목 종합 성적표] ===")
print(f"• 테스트 기간 : {us_res_table['투자연도'].iloc[0]} ~ {us_res_table['투자연도'].iloc[-1]} ({n_years}년)")
print(f"• 누적 수익률 : {total_ret:,.2f}% (최종 {us_cum_port.iloc[-1]:.2f}배)  |  SPY: {(us_cum_spy.iloc[-1]-1)*100:,.2f}% ({us_cum_spy.iloc[-1]:.2f}배)")
print(f"• 연평균(CAGR): {cagr:.2f}%  |  전체 MDD: {total_mdd:.2f}%")
print(f"• 플러스 연도 승률: {win_rate:.1f}%  |  SPY 초과수익 승률: {beat_rate:.1f}%")

#%% [미국 전체 4단계] 미국 전체 마법공식 Top 10 vs SPY 누적 수익률 및 연도별 그래프
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [1.3, 1]})

us_cum_port.index = pd.to_datetime(us_cum_port.index)
us_cum_spy.index = pd.to_datetime(us_cum_spy.index)

ax1.plot(us_cum_port.index, us_cum_port.values, color='royalblue', linewidth=2.2, label=f'미국 전체 마법공식 Top 10 누적배수 (CAGR {cagr:.1f}%)')
ax1.plot(us_cum_spy.index, us_cum_spy.values, color='crimson', linewidth=1.8, linestyle='--', label='SPY (S&P 500 벤치마크)')
ax1.set_title('전년도 결산 기준 미국 전체 종목 마법공식 Top 10 매년 리밸런싱 누적 수익률 추이', fontsize=13, fontweight='bold')
ax1.set_ylabel('누적 자산 배수 (시작=1.0)')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)

x = np.arange(len(us_res_table))
width = 0.38
bars1 = ax2.bar(x - width/2, us_res_table['마법공식(%)'], width, color='royalblue', label='마법공식 Top 10 (%)')
bars2 = ax2.bar(x + width/2, us_res_table['SPY(%)'], width, color='lightgray', edgecolor='gray', label='SPY (%)')
ax2.axhline(0, color='black', linewidth=0.9)
ax2.set_title('연도별 수익률 비교 (미국 전체 마법공식 vs SPY)', fontsize=12, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(us_res_table['투자연도'])
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
ax2.legend(loc='upper left')
ax2.grid(True, axis='y', alpha=0.3)

for bar in bars1:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, h + (1.5 if h >= 0 else -4.0),
             f'{h:.1f}%', ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='navy')

plt.tight_layout()
plt.show()

#%% [한국 장기 1단계] dart_fs(2013~2025) 기반 한국 전체 마법공식 13년치 백테스트 연산
import pandas as pd
import numpy as np
import pymysql
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

QUANT_DIR = Path(r'C:\Users\arlo0\OneDrive\바탕 화면\취업\quant')
env = {}
for line in (QUANT_DIR / '.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

def sort_value(s_value, asc=True, standard=0):
    s_value_mask = s_value.mask(s_value < standard, np.nan)
    return s_value_mask.rank(ascending=asc, na_option="bottom")

conn = pymysql.connect(
    host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)),
    user=env['DB_USER'], password=env['DB_PASSWORD'],
    database=env['DB_NAME'], charset='utf8mb4'
)

# 1) 보통주 종목명 마스터 로드
kr_name_df = pd.read_sql("""
SELECT `종목코드`, `종목명`
FROM fdr_kr_ticker
WHERE `종목구분` = '보통주' AND `종목명` IS NOT NULL
GROUP BY `종목코드`, `종목명`
""", conn)
kr_code_to_name = dict(zip(kr_name_df['종목코드'], kr_name_df['종목명']))
kr_common_codes = set(kr_name_df['종목코드'])

# 2) dart_fs 자산('assets') 및 당기순이익('ni') 로드 (12월 결산, 억원 단위)
dart_fs_all = pd.read_sql("""
SELECT `종목코드`, CAST(LEFT(`기준일`, 4) AS UNSIGNED) AS `연도`, `계정`, `값`
FROM dart_fs
WHERE MONTH(`기준일`) = 12
  AND `계정` IN ('assets', 'ni')
  AND `값` IS NOT NULL
""", conn)

# 3) 연말 시가총액(kor_ohlcv_raw) 및 보완용 기준 주가 로드
mcap_hist = pd.read_sql("""
SELECT a.`종목코드`, CAST(LEFT(a.`날짜`, 4) AS UNSIGNED) AS `연도`, a.`시가총액`
FROM kor_ohlcv_raw a
INNER JOIN (
    SELECT LEFT(`날짜`, 4) AS yr, MAX(`날짜`) AS max_dt
    FROM kor_ohlcv_raw
    GROUP BY LEFT(`날짜`, 4)
) b ON a.`날짜` = b.max_dt
""", conn)

latest_mcap = pd.read_sql("""
SELECT `종목코드`, `시가총액` AS `최신시가총액`
FROM kor_ticker
WHERE `기준일` = (SELECT MAX(`기준일`) FROM kor_ticker)
  AND `시가총액` IS NOT NULL
""", conn).set_index('종목코드')['최신시가총액']

year_end_close = pd.read_sql("""
SELECT a.`종목코드`, CAST(LEFT(a.`날짜`, 4) AS UNSIGNED) AS `연도`, a.`종가`
FROM kor_price a
INNER JOIN (
    SELECT LEFT(`날짜`, 4) AS yr, MAX(`날짜`) AS max_dt
    FROM kor_price
    GROUP BY LEFT(`날짜`, 4)
) b ON a.`날짜` = b.max_dt
""", conn)

latest_close = pd.read_sql("""
SELECT `종목코드`, `종가` AS `최신종가`
FROM kor_price
WHERE `날짜` = (SELECT MAX(`날짜`) FROM kor_price)
""", conn).set_index('종목코드')['최신종가']

dart_years = sorted(dart_fs_all['연도'].unique())
pr_years = set(year_end_close['연도'].unique())
dart_valid_pairs = [(int(y), int(y) + 1) for y in dart_years if (int(y) + 1) in pr_years]

print(f"한국 장기 백테스트 구간: {dart_valid_pairs[0][0]}년 결산({dart_valid_pairs[0][1]}년 투자) ~ {dart_valid_pairs[-1][0]}년 결산({dart_valid_pairs[-1][1]}년 투자)")

kr_long_records = []
kr_long_daily_port = []
kr_long_daily_mkt = []

for fs_yr, hold_yr in dart_valid_pairs:
    sub_fs = dart_fs_all[dart_fs_all['연도'] == fs_yr]
    piv_fs = sub_fs.pivot_table(index='종목코드', columns='계정', values='값', aggfunc='last')
    if 'ni' not in piv_fs.columns or 'assets' not in piv_fs.columns:
        continue

    fac = piv_fs[piv_fs.index.isin(kr_common_codes)].copy()
    fac['ROA'] = (fac['ni'] / fac['assets']) * 100

    sub_mc = mcap_hist[mcap_hist['연도'] == fs_yr].set_index('종목코드')['시가총액']
    if len(sub_mc) > 100:
        fac['시가총액'] = sub_mc
    else:
        yr_cls = year_end_close[year_end_close['연도'] == fs_yr].set_index('종목코드')['종가']
        fac['시가총액'] = latest_mcap * (yr_cls / latest_close)

    # dart_fs 값은 억원 단위이므로 시가총액(원)을 1e8로 나누어 PER 계산
    fac['시가총액_억'] = fac['시가총액'] / 1e8
    fac['PER'] = fac['시가총액_억'] / fac['ni']
    fac = fac.replace([np.inf, -np.inf], np.nan).dropna(subset=['PER', 'ROA', '시가총액_억'])

    # 소형주 하위 20% 제외 후 순위 산정
    fac = fac[fac['시가총액_억'] >= fac['시가총액_억'].quantile(0.2)]
    p_rank = sort_value(fac['PER'], asc=True, standard=0)
    r_rank = sort_value(fac['ROA'], asc=False, standard=0)
    tot_rank = sort_value((p_rank + r_rank).dropna(), asc=True)

    # 거래정지·상장폐지 대비 상위 15개 후보 조회 후 실제 주가 존재하는 상위 10개 확정
    cand_codes = list(tot_rank.nsmallest(15).index)
    if len(cand_codes) < 5:
        continue

    codes_sql = ",".join([f"'{c}'" for c in cand_codes])
    pr_df = pd.read_sql(f"""
        SELECT `날짜`, `종목코드`, `종가`
        FROM kor_price
        WHERE `종목코드` IN ({codes_sql})
          AND `날짜` BETWEEN '{hold_yr}-01-01' AND '{hold_yr}-12-31'
        ORDER BY `날짜`
    """, conn)
    if pr_df.empty:
        continue

    avail_codes = [c for c in cand_codes if c in set(pr_df['종목코드'])][:10]
    pr_df = pr_df[pr_df['종목코드'].isin(avail_codes)]

    pr_piv = pr_df.pivot(index='날짜', columns='종목코드', values='종가').ffill().bfill()
    norm_piv = pr_piv.div(pr_piv.iloc[0])
    port_daily_idx = norm_piv.mean(axis=1)
    port_daily_ret = port_daily_idx.pct_change().fillna(port_daily_idx.iloc[0] - 1)
    kr_long_daily_port.append(port_daily_ret)

    # 해당 연도 시장 동일가중 평균 수익률
    mkt_raw = pd.read_sql(f"""
        SELECT `날짜`, `종목코드`, `종가`
        FROM kor_price
        WHERE `날짜` BETWEEN '{hold_yr}-01-01' AND '{hold_yr}-12-31'
    """, conn)
    mkt_mat = mkt_raw.pivot(index='날짜', columns='종목코드', values='종가').pct_change(fill_method=None)
    mkt_df = mkt_mat.where(mkt_mat.abs() < 0.35).mean(axis=1).fillna(0)
    kr_long_daily_mkt.append(mkt_df)

    yr_ret = (port_daily_idx.iloc[-1] - 1) * 100
    mkt_yr_ret = ((1 + mkt_df).cumprod().iloc[-1] - 1) * 100
    yr_mdd = ((port_daily_idx / port_daily_idx.cummax()) - 1).min() * 100
    top10_names = [kr_code_to_name.get(c, c) for c in avail_codes]

    kr_long_records.append({
        '투자연도': f"{hold_yr}년",
        '기준결산': f"{fs_yr}말",
        '대상종목수': len(fac),
        '마법공식(%)': round(yr_ret, 2),
        '시장평균(%)': round(mkt_yr_ret, 2),
        '초과수익(%p)': round(yr_ret - mkt_yr_ret, 2),
        '연중MDD(%)': round(yr_mdd, 2),
        '선정종목(Top10)': ", ".join(top10_names)
    })

conn.close()
print(f"한국 장기 백테스트 연산 완료: 총 {len(kr_long_records)}개 연도 처리됨")

#%% [한국 장기 2단계] 한국 장기(2014~2026) 성과 요약표 및 누적 수익률 그래프
kr_long_table = pd.DataFrame(kr_long_records)
kr_long_port_ret = pd.concat(kr_long_daily_port)
kr_long_mkt_ret = pd.concat(kr_long_daily_mkt).reindex(kr_long_port_ret.index).fillna(0)

kr_long_cum_port = (1 + kr_long_port_ret).cumprod()
kr_long_cum_mkt = (1 + kr_long_mkt_ret).cumprod()

kr_long_table['누적배수(배)'] = [
    round(kr_long_cum_port[kr_long_cum_port.index.astype(str).str.startswith(row['투자연도'][:4])].iloc[-1], 2)
    for _, row in kr_long_table.iterrows()
]

pd.set_option('display.max_colwidth', 120)
print("=== [한국 전체(dart_fs 장기) 마법공식 연도별 성과 요약표] ===")
print(kr_long_table[['투자연도', '기준결산', '대상종목수', '마법공식(%)', '시장평균(%)', '초과수익(%p)', '연중MDD(%)', '누적배수(배)', '선정종목(Top10)']].to_string(index=False))

n_yrs = len(kr_long_table)
tot_r = (kr_long_cum_port.iloc[-1] - 1) * 100
cagr_kr_long = (kr_long_cum_port.iloc[-1] ** (1 / n_yrs) - 1) * 100
mdd_kr_long = ((kr_long_cum_port / kr_long_cum_port.cummax()) - 1).min() * 100
win_r = (kr_long_table['마법공식(%)'] > 0).mean() * 100
beat_r = (kr_long_table['초과수익(%p)'] > 0).mean() * 100

print("\n=== [한국 장기(2014~2026) 종합 성적표] ===")
print(f"• 테스트 기간 : {kr_long_table['투자연도'].iloc[0]} ~ {kr_long_table['투자연도'].iloc[-1]} ({n_yrs}년)")
print(f"• 누적 수익률 : {tot_r:,.2f}% (최종 {kr_long_cum_port.iloc[-1]:.2f}배)  |  시장평균: {(kr_long_cum_mkt.iloc[-1]-1)*100:,.2f}% ({kr_long_cum_mkt.iloc[-1]:.2f}배)")
print(f"• 연평균(CAGR): {cagr_kr_long:.2f}%  |  전체 MDD: {mdd_kr_long:.2f}%")
print(f"• 플러스 연도 승률: {win_r:.1f}%  |  시장 초과수익 승률: {beat_r:.1f}%")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [1.3, 1]})
kr_long_cum_port.index = pd.to_datetime(kr_long_cum_port.index)
kr_long_cum_mkt.index = pd.to_datetime(kr_long_cum_mkt.index)

ax1.plot(kr_long_cum_port.index, kr_long_cum_port.values, color='forestgreen', linewidth=2.2, label=f'한국 장기 마법공식 Top 10 (CAGR {cagr_kr_long:.1f}%)')
ax1.plot(kr_long_cum_mkt.index, kr_long_cum_mkt.values, color='dimgray', linewidth=1.6, linestyle='--', label='한국 시장 동일가중 평균')
ax1.set_title('한국 전체 종목 마법공식 장기 리밸런싱 누적 수익률 추이 (2014~2026)', fontsize=13, fontweight='bold')
ax1.set_ylabel('누적 자산 배수 (시작=1.0)')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)

x = np.arange(len(kr_long_table))
w = 0.38
bars1 = ax2.bar(x - w/2, kr_long_table['마법공식(%)'], w, color='forestgreen', label='한국 장기 마법공식 (%)')
bars2 = ax2.bar(x + w/2, kr_long_table['시장평균(%)'], w, color='lightgray', edgecolor='gray', label='시장평균 (%)')
ax2.axhline(0, color='black', linewidth=0.9)
ax2.set_title('연도별 수익률 비교 (한국 장기 마법공식 vs 시장평균)', fontsize=12, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(kr_long_table['투자연도'])
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
ax2.legend(loc='upper left')
ax2.grid(True, axis='y', alpha=0.3)

for bar in bars1:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, h + (1.5 if h >= 0 else -4.5),
             f'{h:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold', color='darkgreen')

plt.tight_layout()
plt.show()

#%% [최종 4개 비교 1단계] 4개 전략 일별 수익률 수집 및 통합 정리
conn = pymysql.connect(
    host=env['DB_HOST'], port=int(env.get('DB_PORT', 3306)),
    user=env['DB_USER'], password=env['DB_PASSWORD'],
    database=env['DB_NAME'], charset='utf8mb4'
)

# ① 미국 31종목 일별 수익률 계산
us_31_list = [
    'AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'AVGO', 'TSLA', 'WMT',
    'AMD', 'MU', 'ASML', 'COST', 'PLTR', 'CSCO', 'INTC', 'AMAT', 'TXN', 'LRCX',
    'PANW', 'AMGN', 'NFLX', 'LIN', 'CRWD', 'GILD', 'PEP', 'SHOP', 'KLAC', 'ARM'
]
us_fs_all = pd.read_sql("""
SELECT `ticker`, CAST(LEFT(`date`, 4) AS UNSIGNED) AS `연도`, `account`, `value`
FROM global_fs WHERE `freq` = 'y' AND `value` IS NOT NULL
  AND `account` IN ('NetIncome', 'TotalAssets', 'OrdinarySharesNumber', 'DilutedAverageShares')
""", conn)
us_ye_close = pd.read_sql("""
SELECT a.`티커`, CAST(LEFT(a.`날짜`, 4) AS UNSIGNED) AS `연도`, a.`종가`
FROM us_price a
INNER JOIN (SELECT LEFT(`날짜`, 4) AS yr, MAX(`날짜`) AS max_dt FROM us_price WHERE `날짜` >= '2021-01-01' GROUP BY LEFT(`날짜`, 4)) b
ON a.`날짜` = b.max_dt
""", conn)

spy_df = pd.read_sql("SELECT `날짜`, `수정종가` AS `SPY` FROM us_price WHERE `티커` = 'SPY' AND `날짜` >= '2021-01-01' ORDER BY `날짜`", conn)
if spy_df.empty:
    spy_df = pd.read_sql("SELECT `Date` AS `날짜`, `SPY` FROM sample_etf WHERE `Date` >= '2021-01-01' AND `SPY` IS NOT NULL ORDER BY `Date`", conn)
if spy_df.empty:
    spy_raw = yf.download('SPY', start='2021-01-01', auto_adjust=False, progress=False)
    if isinstance(spy_raw.columns, pd.MultiIndex):
        spy_raw.columns = spy_raw.columns.get_level_values(0)
    spy_df = spy_raw[['Adj Close']].reset_index()
    spy_df.columns = ['날짜', 'SPY']
    spy_df['날짜'] = spy_df['날짜'].astype(str).str[:10]
spy_series = spy_df.set_index('날짜')['SPY'].astype(float)

us31_rets, us31_yr_map = [], {}
for fs_yr in sorted(us_fs_all['연도'].unique()):
    hold_yr = int(fs_yr) + 1
    if hold_yr not in set(us_ye_close['연도'].unique()):
        continue
    sub_fs = us_fs_all[(us_fs_all['연도'] == fs_yr) & (us_fs_all['ticker'].isin(us_31_list))]
    piv_fs = sub_fs.pivot_table(index='ticker', columns='account', values='value', aggfunc='last')
    if 'NetIncome' not in piv_fs.columns or 'TotalAssets' not in piv_fs.columns:
        continue
    shares = piv_fs['OrdinarySharesNumber'] if 'OrdinarySharesNumber' in piv_fs.columns else pd.Series(np.nan, index=piv_fs.index)
    if 'DilutedAverageShares' in piv_fs.columns:
        shares = shares.fillna(piv_fs['DilutedAverageShares'])
    yr_cls = us_ye_close[us_ye_close['연도'] == fs_yr].set_index('티커')['종가']
    fac = pd.DataFrame(index=piv_fs.index)
    fac['MarketCap'] = yr_cls * shares
    fac['PER'] = fac['MarketCap'] / piv_fs['NetIncome']
    fac['ROA'] = (piv_fs['NetIncome'] / piv_fs['TotalAssets']) * 100
    fac = fac.replace([np.inf, -np.inf], np.nan).dropna(subset=['PER', 'ROA', 'MarketCap'])
    tot_rank = sort_value((sort_value(fac['PER'], True, 0) + sort_value(fac['ROA'], False, 0)).dropna(), True)
    cands = list(tot_rank.nsmallest(10).index)
    if len(cands) < 5:
        continue
    cands_sql = ",".join([f"'{t}'" for t in cands])
    hold_pr = pd.read_sql(f"SELECT `날짜`, `티커`, `수정종가` FROM us_price WHERE `티커` IN ({cands_sql}) AND `날짜` BETWEEN '{hold_yr}-01-01' AND '{hold_yr}-12-31' ORDER BY `날짜`", conn)
    if hold_pr.empty:
        continue
    pr_piv = hold_pr.pivot(index='날짜', columns='티커', values='수정종가').ffill().bfill()
    idx_s = pr_piv.div(pr_piv.iloc[0]).mean(axis=1)
    us31_rets.append(idx_s.pct_change().fillna(idx_s.iloc[0] - 1))
    us31_yr_map[f"{hold_yr}년"] = round((idx_s.iloc[-1] - 1) * 100, 2)

ret_us31 = pd.concat(us31_rets)

# ② 미국 전체 (앞 셀 결과 연결)
ret_usall = us_all_port_ret.copy()
usall_yr_map = dict(zip(us_res_table['투자연도'], us_res_table['마법공식(%)']))

# ③ 한국 단기 kor_fs (앞 셀 결과 연결)
ret_kr_short = all_port_ret.copy()
kr_short_yr_map = dict(zip(res_table['투자연도'], res_table['마법공식(%)']))

# ④ 한국 장기 dart_fs (방금 계산한 결과 연결)
ret_kr_long = kr_long_port_ret.copy()
kr_long_yr_map = dict(zip(kr_long_table['투자연도'], kr_long_table['마법공식(%)']))
kr_mkt_yr_map = dict(zip(kr_long_table['투자연도'], kr_long_table['시장평균(%)']))

conn.close()
print("4개 전략 일별 수익률 통합 완료!")
print(f"1. 미국 31종목       : {str(ret_us31.index.min())[:10]} ~ {str(ret_us31.index.max())[:10]}")
print(f"2. 미국 전체         : {str(ret_usall.index.min())[:10]} ~ {str(ret_usall.index.max())[:10]}")
print(f"3. 한국 전체(kor_fs) : {str(ret_kr_short.index.min())[:10]} ~ {str(ret_kr_short.index.max())[:10]}")
print(f"4. 한국 전체(dart_fs): {str(ret_kr_long.index.min())[:10]} ~ {str(ret_kr_long.index.max())[:10]}")

#%% [최종 4개 비교 2단계] 4개 전략 퀀트 지표 종합 비교표 및 3단 시각화
common_start = max(
    str(ret_us31.index.min())[:10],
    str(ret_usall.index.min())[:10],
    str(ret_kr_short.index.min())[:10],
    str(ret_kr_long.index.min())[:10]
)
common_end = min(
    str(ret_us31.index.max())[:10],
    str(ret_usall.index.max())[:10],
    str(ret_kr_short.index.max())[:10],
    str(ret_kr_long.index.max())[:10]
)

def slice_period(s, st, ed):
    idx_str = s.index.astype(str).str[:10]
    return s[(idx_str >= st) & (idx_str <= ed)]

c_us31 = slice_period(ret_us31, common_start, common_end)
c_usall = slice_period(ret_usall, common_start, common_end)
c_kr_short = slice_period(ret_kr_short, common_start, common_end)
c_kr_long = slice_period(ret_kr_long, common_start, common_end)

spy_sub = slice_period(spy_series, common_start, common_end)
c_spy = spy_sub.pct_change().fillna(0)

spy_yr_map = {}
for y_str in sorted(set(spy_series.index.astype(str).str[:4])):
    sub = spy_series[spy_series.index.astype(str).str.startswith(y_str)]
    if len(sub) > 1:
        spy_yr_map[f"{y_str}년"] = round((sub.iloc[-1] / sub.iloc[0] - 1) * 100, 2)

def eval_strategy(label, ret_s, yr_map, bm_map, rf=0.03):
    cum = (1 + ret_s).cumprod()
    years = len(ret_s) / 252.0
    tot_ret = (cum.iloc[-1] - 1) * 100
    cagr = (cum.iloc[-1] ** (1 / years) - 1) * 100
    vol = ret_s.std() * np.sqrt(252) * 100

    down_s = ret_s[ret_s < 0]
    down_vol = down_s.std() * np.sqrt(252) * 100 if len(down_s) > 0 else np.nan
    sharpe = (cagr / 100 - rf) / (vol / 100) if vol > 0 else np.nan
    sortino = (cagr / 100 - rf) / (down_vol / 100) if down_vol > 0 else np.nan

    dd = (cum / cum.cummax()) - 1
    mdd = dd.min() * 100
    calmar = cagr / abs(mdd) if mdd != 0 else np.nan

    c_yrs = [y for y in yr_map if y in bm_map and int(y[:4]) >= int(common_start[:4])]
    y_vals = np.array([yr_map[y] for y in c_yrs])
    b_vals = np.array([bm_map[y] for y in c_yrs])
    win_rate = (y_vals > 0).mean() * 100 if len(y_vals) > 0 else np.nan
    beat_rate = (y_vals > b_vals).mean() * 100 if len(y_vals) > 0 else np.nan
    alpha = np.mean(y_vals - b_vals) if len(y_vals) > 0 else np.nan

    return {
        '전략/유니버스': label,
        '누적수익(%)': round(tot_ret, 2),
        '최종배수': round(cum.iloc[-1], 2),
        'CAGR(%)': round(cagr, 2),
        '연변동성(%)': round(vol, 2),
        'MDD(%)': round(mdd, 2),
        '샤프지수': round(sharpe, 2),
        '소르티노': round(sortino, 2),
        '칼마지수': round(calmar, 2),
        '연도승률(%)': round(win_rate, 1),
        'BM승률(%)': round(beat_rate, 1),
        '평균알파(%p)': round(alpha, 2)
    }, cum, dd

m1, cum1, dd1 = eval_strategy('1. 미국 31종목', c_us31, us31_yr_map, spy_yr_map)
m2, cum2, dd2 = eval_strategy('2. 미국 전체', c_usall, usall_yr_map, spy_yr_map)
m3, cum3, dd3 = eval_strategy('3. 한국 전체(kor_fs)', c_kr_short, kr_short_yr_map, kr_mkt_yr_map)
m4, cum4, dd4 = eval_strategy('4. 한국 전체(dart_fs)', c_kr_long, kr_long_yr_map, kr_mkt_yr_map)
m_bm, cum_bm, dd_bm = eval_strategy('[벤치마크] SPY', c_spy, spy_yr_map, spy_yr_map)

summary_4way = pd.DataFrame([m1, m2, m3, m4, m_bm])
print(f"\n=== [4개 마법공식 전략 종합 퀀트 지표 비교 (공통기간: {common_start} ~ {common_end}, Rf=3.0%)] ===")
print(summary_4way.to_string(index=False))

all_years = sorted(set(us31_yr_map) | set(usall_yr_map) | set(kr_short_yr_map) | set(kr_long_yr_map))
yr_rows = []
for y in all_years:
    yr_rows.append({
        '투자연도': y,
        '미국 31종목(%)': us31_yr_map.get(y, np.nan),
        '미국 전체(%)': usall_yr_map.get(y, np.nan),
        'SPY(%)': spy_yr_map.get(y, np.nan),
        '한국(kor_fs)(%)': kr_short_yr_map.get(y, np.nan),
        '한국(dart_fs)(%)': kr_long_yr_map.get(y, np.nan),
        '한국 시장평균(%)': kr_mkt_yr_map.get(y, np.nan)
    })
yr_4way_df = pd.DataFrame(yr_rows)
print("\n=== [전체 기간 연도별 수익률 가로 비교표 (2014~2026)] ===")
print(yr_4way_df.to_string(index=False))

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 14), gridspec_kw={'height_ratios': [1.35, 0.9, 1.15]})

for s in [cum1, cum2, cum3, cum4, cum_bm, dd1, dd2, dd3, dd4]:
    s.index = pd.to_datetime(s.index)

ax1.plot(cum1.index, cum1.values, color='royalblue', linewidth=2.3, label=f"1. 미국 31종목 (CAGR {m1['CAGR(%)']}%, Sharpe {m1['샤프지수']})")
ax1.plot(cum2.index, cum2.values, color='darkorange', linewidth=2.3, label=f"2. 미국 전체 (CAGR {m2['CAGR(%)']}%, Sharpe {m2['샤프지수']})")
ax1.plot(cum3.index, cum3.values, color='mediumseagreen', linewidth=2.1, linestyle='-.', label=f"3. 한국 전체 kor_fs (CAGR {m3['CAGR(%)']}%, Sharpe {m3['샤프지수']})")
ax1.plot(cum4.index, cum4.values, color='darkgreen', linewidth=2.3, label=f"4. 한국 전체 dart_fs (CAGR {m4['CAGR(%)']}%, Sharpe {m4['샤프지수']})")
ax1.plot(cum_bm.index, cum_bm.values, color='dimgray', linewidth=1.6, linestyle='--', label=f"SPY 벤치마크 (CAGR {m_bm['CAGR(%)']}%)")
ax1.set_title(f'4개 마법공식 유니버스 누적 수익률 비교 (공통기간: {common_start} ~ {common_end})', fontsize=13, fontweight='bold')
ax1.set_ylabel('누적 자산 배수 (시작=1.0)')
ax1.legend(loc='upper left', ncol=2)
ax1.grid(True, alpha=0.3)

ax2.plot(dd1.index, dd1.values * 100, color='royalblue', linewidth=1.5, label=f"1. 미국 31종목 (MDD {m1['MDD(%)']}%)")
ax2.plot(dd2.index, dd2.values * 100, color='darkorange', linewidth=1.5, label=f"2. 미국 전체 (MDD {m2['MDD(%)']}%)")
ax2.plot(dd3.index, dd3.values * 100, color='mediumseagreen', linewidth=1.3, linestyle='-.', label=f"3. 한국 kor_fs (MDD {m3['MDD(%)']}%)")
ax2.plot(dd4.index, dd4.values * 100, color='darkgreen', linewidth=1.5, label=f"4. 한국 dart_fs (MDD {m4['MDD(%)']}%)")
ax2.set_title('전고점 대비 낙폭(Drawdown) 추이 비교', fontsize=12, fontweight='bold')
ax2.set_ylabel('낙폭 (%)')
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
ax2.legend(loc='lower left', ncol=2)
ax2.grid(True, alpha=0.3)

common_yr_df = yr_4way_df[yr_4way_df['투자연도'].str[:4].astype(int) >= int(common_start[:4])].reset_index(drop=True)
x = np.arange(len(common_yr_df))
w = 0.20
ax3.bar(x - 1.5*w, common_yr_df['미국 31종목(%)'].fillna(0),  w, color='royalblue', label='1. 미국 31종목')
ax3.bar(x - 0.5*w, common_yr_df['미국 전체(%)'].fillna(0),    w, color='darkorange', label='2. 미국 전체')
ax3.bar(x + 0.5*w, common_yr_df['한국(kor_fs)(%)'].fillna(0), w, color='mediumseagreen', label='3. 한국(kor_fs)')
ax3.bar(x + 1.5*w, common_yr_df['한국(dart_fs)(%)'].fillna(0),w, color='darkgreen', label='4. 한국(dart_fs)')
ax3.axhline(0, color='black', linewidth=0.9)
ax3.set_title('공통기간 연도별 수익률 비교 (4개 유니버스)', fontsize=12, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(common_yr_df['투자연도'])
ax3.yaxis.set_major_formatter(mtick.PercentFormatter())
ax3.legend(loc='upper left', ncol=4)
ax3.grid(True, axis='y', alpha=0.3)

plt.tight_layout()
plt.show()
