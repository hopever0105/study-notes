# -*- coding: utf-8 -*-
# 글자 범주를 숫자로 바꾸기 (3-2 범주형 데이터 인코딩)
# 1부: 책 원본 따라 치기 / 2부: 금융 데이터(prices.csv)로 같은 인코딩 연습
# Spyder: F5 전체 실행 / Ctrl+Enter 현재 셀 실행 / F9 선택 줄 실행
#
# 언제 쓰나: 모델은 숫자만 받는다. '월요일', '상승장', '대형주' 같은 글자 범주를 숫자로 바꿀 때.
#   - map            : 내가 정한 규칙대로 바꾸기 (묶기·순서 매기기)
#   - factorize      : 범주마다 번호 붙이기 (0, 1, 2, ...)
#   - cut / qcut     : 숫자를 구간으로 잘라 범주 만들기
#   - get_dummies    : 범주마다 0/1 열 하나씩 (원-핫 인코딩)

# =====================================================================
# 1부. 책 원본
# =====================================================================

# %%
import pandas as pd
from sklearn.datasets import load_iris

iris_load = load_iris()
iris = pd.DataFrame(iris_load.data, columns=iris_load.feature_names)
iris['Class'] = iris_load.target

# 숫자 레이블을 문자열 범주로 변환
iris['Class'] = iris['Class'].map({0: 'Setosa', 1: 'Versicolor', 2: 'Virginica'})

# 나중에 쓰려고 사본 저장
iris_origin = iris.copy()

# %% map: 범주 묶기
class_group = {'Setosa': 'Group_A', 'Versicolor': 'Group_B', 'Virginica': 'Group_B'}
iris['Class_group'] = iris['Class'].map(class_group)
print(iris[['Class', 'Class_group']].head())

# %% factorize: 처음 나온 순서대로 0, 1, 2 번호
iris['Class_label2'] = pd.factorize(iris['Class'])[0]
print(iris[['Class', 'Class_label2']].head())

# %% 문자열 첫 글자로 묶기
iris['Class_initial'] = iris['Class'].str[0]
print(iris[['Class', 'Class_initial']].head())

# %% cut: 숫자를 정해진 경계로 잘라 범주로
iris['petal_length_group'] = pd.cut(iris['petal length (cm)'],
                                    bins=[0, 2, 5, 10],
                                    labels=['Short', 'Medium', 'Long'])
print(iris[['petal length (cm)', 'petal_length_group']].head())

# %% get_dummies: 원-핫 인코딩 (범주 3개 → 0/1 열 3개)
iris_dummy = pd.get_dummies(iris_origin, columns=['Class'])
print(iris_dummy.head())

# %% drop_first=True: 첫 범주 열을 빼서 2개만 (나머지 둘이 0이면 첫 범주라는 뜻)
iris_onehot = pd.get_dummies(iris_origin, columns=['Class'], drop_first=True)
print(iris_onehot.head())


# =====================================================================
# 2부. 금융판
# =====================================================================

# %% 데이터 + 기본 열
import numpy as np
import statsmodels.formula.api as smf

PATH = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터\prices.csv'
df = pd.read_csv(PATH, dtype={'code': str}, parse_dates=['date'], encoding='utf-8-sig')
df = df.sort_values(['code', 'date']).reset_index(drop=True)
df['ret'] = df.groupby('code')['close'].pct_change()
df = df.dropna(subset=['ret']).reset_index(drop=True)

# %% 1) 날짜에서 범주 뽑기: 요일·월
weekday_kr = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금'}
df['weekday'] = df['date'].dt.weekday.map(weekday_kr)    # map: 숫자 → 글자
df['month'] = df['date'].dt.month
print(df[['date', 'weekday', 'month']].head())

# %% 2) map으로 묶기 (책의 class_group과 같은 방식)
week_part = {'월': '주초', '화': '주초', '수': '주중', '목': '주말쪽', '금': '주말쪽'}
df['week_part'] = df['weekday'].map(week_part)
print(df.groupby('week_part')['ret'].mean().round(5))

# %% 3) factorize: 종목코드에 번호 붙이기
df['code_id'] = pd.factorize(df['code'])[0]
print(df[['code', 'code_id']].drop_duplicates().head())
# 주의: code_id 3이 1보다 '크다'는 뜻은 없음. 그런데 선형회귀·로지스틱에 숫자로 넣으면
#       "번호가 클수록 수익률이 높다/낮다"는 엉뚱한 관계를 학습함
#       → 선형 모델엔 원-핫, 트리 모델(의사결정나무·LightGBM)은 번호로 넣어도 비교적 괜찮음

# %% 4) cut: 정해진 경계로 자르기 — 가격대
df['price_band'] = pd.cut(df['close'], bins=[0, 10_000, 50_000, 200_000, np.inf],
                          labels=['1만 미만', '1~5만', '5~20만', '20만 이상'])
print(df['price_band'].value_counts())

# %% 5) qcut: 개수가 같게 자르기 — 거래대금 5분위
# 틀린 방법: 전체 기간을 한 번에 qcut → 2021년 행을 2026년 거래대금까지 보고 나눔(미래정보)
#            게다가 시장 전체 거래대금이 커진 해는 전부 상위 분위로 몰림
df['amt_q_wrong'] = pd.qcut(df['amount'], 5, labels=False)

# 맞는 방법: 날짜마다 그날 50종목 안에서 5분위 (단면 분위)
df['amt_q'] = df.groupby('date')['amount'].transform(lambda s: pd.qcut(s, 5, labels=False))

check = pd.crosstab(df['date'].dt.year, df['amt_q_wrong'], normalize='index').round(2)
print('전체 기간 qcut - 연도별 분위 비율 (한 해에 몰림):\n', check)
print('날짜별 qcut - 연도별 분위 비율 (매년 20%씩):\n',
      pd.crosstab(df['date'].dt.year, df['amt_q'], normalize='index').round(2))

# %% 6) 순서가 있는 범주 = 순서형 인코딩: 시장 국면
# 시장 = 그날 50종목 평균 수익률, 직전 20일 누적으로 국면 판단 (shift(1): 오늘 값은 안 씀)
mkt = df.groupby('date')['ret'].mean()
mkt_20 = (1 + mkt).rolling(20).apply(np.prod, raw=True).shift(1) - 1
regime = pd.cut(mkt_20, bins=[-np.inf, -0.03, 0.03, np.inf], labels=['하락', '횡보', '상승'])
df['regime'] = df['date'].map(regime)
# 하락 < 횡보 < 상승 순서가 의미 있음 → 0, 1, 2로 바꿔도 됨
df['regime_ord'] = df['regime'].map({'하락': 0, '횡보': 1, '상승': 2}).astype(float)
print(df['regime'].value_counts(dropna=False))

# %% 7) 원-핫 인코딩: 요일
dummies = pd.get_dummies(df['weekday'], prefix='wd', dtype=int)
print(dummies.head())
# 다섯 열을 더하면 항상 1 → 상수항(절편)이 있는 회귀에 다섯 개를 다 넣으면
# 상수항과 완전히 겹쳐 계수가 하나로 정해지지 않음 (더미 변수 함정)
print('행마다 합:', dummies.sum(axis=1).unique())

dummies_drop = pd.get_dummies(df['weekday'], prefix='wd', drop_first=True, dtype=int)
print('drop_first 후 열:', list(dummies_drop.columns), '← 빠진 하나가 기준 범주')

# %% 8) 더미로 회귀하면 계수가 무슨 뜻인가: 수익률 ~ 요일
# C(weekday, Treatment('월')): 요일을 범주로 보고 월요일을 기준으로 둠
model = smf.ols("ret ~ C(weekday, Treatment('월'))", data=df).fit()
print(model.params.round(5))
print('요일별 평균:\n', df.groupby('weekday')['ret'].mean().round(5))
# 절편 = 월요일 평균, 각 계수 = (그 요일 평균 - 월요일 평균)
# 숫자로 확인: 절편 + 화 계수 = 화요일 평균
print('절편 + 화 계수:', round(model.params.iloc[0] + model.params.filter(like='화').iloc[0], 5))

# %% 9) 범주가 많을 때: 타깃 인코딩 (범주 → 그 범주의 과거 평균 타깃)
# 예: 종목코드 50개를 원-핫하면 50열 → 대신 '그 종목의 과거 평균 수익률' 한 열로
# 반드시 '어제까지'의 평균만 씀: expanding().mean() 뒤 shift(1)
df['code_te'] = df.groupby('code')['ret'].transform(lambda s: s.expanding().mean().shift(1))
# 틀린 방법: 전체 기간 평균 → 오늘 수익률이 평균에 이미 들어가 있음
df['code_te_wrong'] = df.groupby('code')['ret'].transform('mean')
print(df[['code', 'date', 'ret', 'code_te', 'code_te_wrong']].head(6))

# 숫자로 차이 보기: 다음날 수익률과의 상관 (틀린 쪽이 그럴듯하게 높게 나옴)
df['next_ret'] = df.groupby('code')['ret'].shift(-1)
print('어제까지 평균 vs 다음날 수익률 상관:', round(df['code_te'].corr(df['next_ret']), 4))
print('전체 평균     vs 다음날 수익률 상관:', round(df['code_te_wrong'].corr(df['next_ret']), 4))

# %% 10) 정리: 무엇을 언제
summary = pd.DataFrame({
    '방법': ['map', 'factorize', 'cut', 'qcut', 'get_dummies', '타깃 인코딩'],
    '금융 예시': ['요일 → 주초/주말', '종목코드 → 번호', '가격대 구간', '거래대금 5분위', '요일 0/1 열', '종목 → 과거 평균 수익률'],
    '주의': ['규칙은 내가 정함', '번호 크기에 의미 없음(선형 모델 X)', '경계를 미래 데이터로 정하지 않기',
             '날짜별로 자르기', '상수항 있으면 drop_first', '어제까지만(shift(1))'],
})
print(summary.to_string(index=False))
