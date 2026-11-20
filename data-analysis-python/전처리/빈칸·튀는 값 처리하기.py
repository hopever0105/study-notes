# -*- coding: utf-8 -*-
# 빈칸·튀는 값 처리하기 (3-1 결측치와 이상치 처리)
# 1부: 책 원본 따라 치기 / 2부: 금융 데이터(prices.csv + delisted.csv)로 같은 처리 연습
# Spyder: F5 전체 실행 / Ctrl+Enter 현재 셀 실행 / F9 선택 줄 실행
#
# 언제 쓰나: 모델에 넣기 전, 빈칸(NaN)과 튀는 값을 정리할 때.
# 금융에서 꼭 기억할 것 두 가지
#   ① 빈칸을 '미래 값'으로 채우면 안 된다 (bfill, 전체 기간 평균 → 미래정보 누수)
#   ② 주식 수익률의 튀는 값은 대부분 '진짜 사건'이다 → 지우지 말고 눌러 준다(winsorize)

# =====================================================================
# 1부. 책 원본
# =====================================================================

# %% 데이터 가져오기
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_wine

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

wine_load = load_wine()
wine = pd.DataFrame(wine_load.data, columns=wine_load.feature_names)
wine['Class'] = wine_load.target
wine['Class'] = wine['Class'].map({0: 'class_0', 1: 'class_1', 2: 'class_2'})

# %% 상자그림으로 튀는 값 눈으로 보기
plt.boxplot(wine['color_intensity'], whis=1.5)
plt.title('color_intensity')
plt.show()

# %% IQR 방식으로 이상치 찾기
# Q1 = 하위 25% 값, Q3 = 하위 75% 값, IQR = Q3 - Q1
# Q1 - 1.5×IQR 보다 작거나 Q3 + 1.5×IQR 보다 크면 이상치
def outliers_iqr(df, col, whisker=1.5):
    q1, q3 = np.percentile(df[col], [25, 75])
    iqr = q3 - q1
    lower = q1 - whisker * iqr
    upper = q3 + whisker * iqr
    return df[(df[col] < lower) | (df[col] > upper)][[col]]

outliers = outliers_iqr(wine, 'color_intensity')
print(outliers)

# %% 방법 1: 이상치 행 삭제
drop_outliers = wine.drop(index=outliers.index)
print('Original :', wine.shape)
print('Drop outliers :', drop_outliers.shape)

# %% 방법 2: 이상치를 NaN으로 바꾼 뒤 평균으로 채우기
wine.loc[outliers.index, 'color_intensity'] = np.nan
wine['color_intensity'] = wine['color_intensity'].fillna(wine['color_intensity'].mean())
print(wine.loc[outliers.index, 'color_intensity'])


# =====================================================================
# 2부. 금융판
# =====================================================================

# %% 데이터: 살아 있는 50종목 + 상장폐지 10종목 종가를 한 표로
BASE = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터'
prices = pd.read_csv(BASE + r'\prices.csv', dtype={'code': str}, parse_dates=['date'], encoding='utf-8-sig')
delisted = pd.read_csv(BASE + r'\delisted.csv', dtype={'code': str}, parse_dates=['date'], encoding='utf-8-sig')

both = pd.concat([prices[['date', 'code', 'close']], delisted], ignore_index=True)
close = both.pivot(index='date', columns='code', values='close')   # 행=날짜, 열=종목
print(close.shape)   # (거래일 수, 60종목)

# %% 1) 빈칸이 얼마나 있나
na_cnt = close.isna().sum().sort_values(ascending=False)
print(na_cnt.head(15))
print('전체 빈칸 비율:', round(close.isna().mean().mean() * 100, 2), '%')

# %% 2) 빈칸이 '왜' 생겼는지부터 나눈다 — 이유마다 처리법이 다름
# (a) 상장 전 / (b) 상장폐지 후 / (c) 중간에 비는 날(거래정지 등)
first = close.apply(lambda s: s.first_valid_index())   # 처음 값이 있는 날
last = close.apply(lambda s: s.last_valid_index())     # 마지막 값이 있는 날

rows = []
for code in close.columns:
    s = close[code]
    before = s.loc[:first[code]].isna().sum()            # 상장 전
    after = s.loc[last[code]:].isna().sum()              # 폐지 후
    middle = s.loc[first[code]:last[code]].isna().sum()  # 중간 공백
    rows.append([code, before, middle, after])
na_type = pd.DataFrame(rows, columns=['code', '상장전', '중간', '폐지후']).set_index('code')
print(na_type[(na_type.sum(axis=1) > 0)].sort_values('중간', ascending=False).head(15))
# 결과: 이 데이터엔 '상장전'(늦게 상장)과 '폐지후'만 있고 '중간' 공백은 없음

# %% 3) 중간 공백: 직전 값으로 채우기(ffill) — 단, 길게 채우지 않는다
# 연습용으로 한 종목에 거래정지 8거래일을 일부러 만든다 (원본 close는 그대로 두고 사본에서)
code_gap = prices['code'].iloc[0]
close_demo = close.copy()
stop_days = close_demo.loc['2024-03-04':].index[:8]
close_demo.loc[stop_days, code_gap] = np.nan

# 거래가 없던 날의 '알 수 있는 가장 최신 가격'은 직전 종가 → ffill은 미래를 보지 않음
# limit=5: 5일까지만 채우고 그 뒤는 NaN으로 둠 (긴 거래정지를 가짜 '보합'으로 만들지 않기)
filled = close_demo[code_gap].ffill(limit=5)
print(code_gap, '중간 빈칸 수 - 전:', close_demo[code_gap].isna().sum(), '/ 후:', filled.isna().sum())
print(pd.DataFrame({'원래': close_demo[code_gap], 'ffill(limit=5)': filled}).loc[stop_days[0] - pd.Timedelta(days=3):stop_days[-1] + pd.Timedelta(days=3)])

# 폐지 후는 채우지 않는다: ffill(limit 없이)하면 망한 종목이 마지막 가격으로 계속 '살아 있게' 됨
# → 생존편향의 반대 실수(폐지 손실이 안 잡힘)

# %% 4) 하면 안 되는 채우기 두 가지 — 숫자로 확인
s = close_demo[code_gap].copy()
gap_days = stop_days[:3]
print('빈 날:', list(gap_days.date))
print('ffill(직전 값)  :', s.ffill().loc[gap_days].values)
print('bfill(다음 값)  :', s.bfill().loc[gap_days].values, '← 그날엔 알 수 없던 미래 가격')
print('전체 평균으로   :', round(s.mean(), 0), '← 2026년 가격까지 섞인 평균 (책의 fillna(mean)을 그대로 쓰면 이렇게 됨)')

# %% 5) 수익률을 만든 뒤의 빈칸
# 수익률은 종가 2개가 다 있어야 계산됨 → 첫날·공백 다음날은 NaN
ret = close.pct_change(fill_method=None)   # fill_method=None: pandas가 몰래 ffill 하지 않게
print('수익률 빈칸 수(상위 5종목):')
print(ret.isna().sum().sort_values(ascending=False).head())
# 수익률 빈칸은 0으로 채우지 않는다 (0 = '보합이었다'는 거짓 정보). 그 종목·그 날만 빼고 계산

# %% 6) 튀는 값: 책의 IQR 방식을 수익률에 그대로 쓰면?
long_ret = ret.stack().rename('ret').reset_index()     # 다시 긴 표로 (날짜, 종목, 수익률)
q1, q3 = np.percentile(long_ret['ret'], [25, 75])
iqr = q3 - q1
iqr_out = long_ret[(long_ret['ret'] < q1 - 1.5 * iqr) | (long_ret['ret'] > q3 + 1.5 * iqr)]
print(f'IQR 이상치: {len(iqr_out):,}개 / 전체 {len(long_ret):,}개 = {len(iqr_out) / len(long_ret) * 100:.1f}%')
print('잘리는 기준:', round(q1 - 1.5 * iqr, 4), '~', round(q3 + 1.5 * iqr, 4))
# 하루 ±5% 남짓만 넘어도 이상치가 됨 → 지우면 급등락일(가장 중요한 날)을 통째로 버리는 셈

# %% 7) 진짜 '오류' 찾기: 가격제한폭 ±30%를 넘는 수익률
# 한국 주식은 하루 ±30%까지만 움직임 → 넘으면 액면분할 미반영·데이터 오류일 가능성
err = long_ret[long_ret['ret'].abs() > 0.3001]
print('±30% 초과:', len(err), '건')
print(err.sort_values('ret').head(5))   # 가장 많이 떨어진 쪽
print(err.sort_values('ret').tail(5))   # 가장 많이 오른 쪽 (+3,900% 같은 값)
print('그중 상장폐지 종목:', err['code'].isin(delisted['code']).sum(), '건')
# 34건 전부 상장폐지 종목에서 나옴 (살아 있는 50종목은 수정주가라 ±30% 안)
# - 2026년 폐지 직전 -90%대: 정리매매(가격제한 없음) → 진짜 사건
# - 2024년 +3,900%(=39.0) 같은 값: 주식 병합(감자)이 반영 안 된 '수정 전 가격'일 가능성 → 데이터 오류 쪽
# → 진짜든 오류든 모델 학습에 그대로 넣으면 한 줄이 결과를 좌우함 → 확인 후 제외하거나 아래처럼 눌러 줌

# %% 8) 지우지 말고 눌러 주기: 날짜별 winsorize (단면)
# 매일 그날 60종목 수익률의 1%·99% 분위수 밖을 그 분위수 값으로 바꿈
# 날짜별로 하는 이유: 그날 알 수 있는 정보만 씀 (전체 기간 분위수 = 미래 섞임)
def winsorize_by_date(df, col, lo=0.01, hi=0.99):
    q_lo = df.groupby('date')[col].transform(lambda s: s.quantile(lo))
    q_hi = df.groupby('date')[col].transform(lambda s: s.quantile(hi))
    return df[col].clip(lower=q_lo, upper=q_hi)

long_ret['ret_w'] = winsorize_by_date(long_ret, 'ret')
print(long_ret[['ret', 'ret_w']].describe().round(4))
print('바뀐 값 비율:', round((long_ret['ret'] != long_ret['ret_w']).mean() * 100, 2), '%')
# 최댓값이 39.0 → 16.0 정도로만 줄어듦: 하루 종목이 60개뿐이라 99% 분위수가 거의 '두 번째로 큰 값'
# → 종목 수가 적을 땐 ±30% 초과(오류 의심)를 먼저 빼고 winsorize 하거나, 아래 z점수 자르기를 씀

# %% 9) 다른 방식: 날짜별 z점수로 ±3 넘으면 ±3으로 자르기
# z = (값 - 그날 평균) / 그날 표준편차
g = long_ret.groupby('date')['ret']
long_ret['z'] = (long_ret['ret'] - g.transform('mean')) / g.transform('std')
long_ret['z_clip'] = long_ret['z'].clip(-3, 3)
print('|z| > 3 비율:', round((long_ret['z'].abs() > 3).mean() * 100, 2), '%')

# %% 10) MAD(중앙값 절대편차) 방식: 튀는 값에 덜 휘둘리는 기준
# 평균·표준편차는 튀는 값 하나에 끌려감 → 중앙값 기반은 덜 끌려감
# MAD = |값 - 중앙값|의 중앙값, 1.4826×MAD ≈ 정규분포일 때 표준편차
med = g.transform('median')
mad = (long_ret['ret'] - med).abs().groupby(long_ret['date']).transform('median') * 1.4826
long_ret['robust_z'] = (long_ret['ret'] - med) / mad
print('|robust z| > 5 비율:', round((long_ret['robust_z'].abs() > 5).mean() * 100, 2), '%')

# %% 11) 그림으로 비교: 처리 전 / 날짜별 winsorize 후
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].boxplot(long_ret['ret'], whis=1.5)
ax[0].set_title('원래 일간 수익률')
ax[1].boxplot(long_ret['ret_w'], whis=1.5)
ax[1].set_title('날짜별 1%·99% winsorize 후')
plt.show()

# %% 12) 정리: 상황별 처리법
summary = pd.DataFrame({
    '상황': ['중간 거래정지로 빈 가격', '상장 전·폐지 후', '수익률 첫날 NaN', '급등락 수익률', '±30% 초과 수익률', '모델 입력 변수의 튀는 값'],
    '처리': ['ffill(limit=며칠)', '채우지 않음(그 기간 제외)', '그 행만 제외', '지우지 않음(진짜 사건)', '원자료 확인(분할·오류)', '날짜별 winsorize 또는 z점수 자르기'],
    '하면 안 되는 것': ['bfill·전체 평균', '마지막 값으로 계속 채우기', '0으로 채우기', 'IQR로 삭제', '그냥 두기', '전체 기간 분위수로 자르기'],
})
print(summary.to_string(index=False))
