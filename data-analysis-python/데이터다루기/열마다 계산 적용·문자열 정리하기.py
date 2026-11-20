# -*- coding: utf-8 -*-
# 열마다 계산 적용·문자열 정리하기 (2-4 함수 적용·특수데이터: apply, 문자열, 날짜)
# 1부: 책 원본 따라 치기 / 2부: 금융 데이터(연습데이터 prices.csv)로 같은 기능 연습
# Spyder: F5 전체 실행 / Ctrl+Enter 현재 셀 실행 / F9 선택 줄 실행

# %%
import pandas as pd
import numpy as np

score = {'학년':[1, 1, 1, 1, 2, 2],
         '반':['A', 'A', 'B', 'B', 'C', 'C'],
         '성별':['여자', '남자', '여자', '남자', '여자', '남자'],
         '성적': [76, 88, 85, 72, 68, 70]}
score = pd.DataFrame(score)
score = score.pivot_table(index=['학년', '반'], columns='성별', values='성적')
print(score)
# %%
"""
DataFrame.apply(func,axis-0)
func: 적용할 함수
axis: 0이면 열단위로 함수적용, 1이면 행단위로 함수 적용 """
# apply: 열마다 함수 적용 (axis=0은 열 방향)
score.apply(np.sqrt, axis=0)

# %%
score.apply(np.max, axis=0)
# 남자 열에서 최고치, 여자 열에서 최고치를 
# 행별로 표현한다. 
# %%
def plus_five(val):
    return val + 5

score.apply(plus_five)

# %%
# apply: 행마다 함수 적용 (axis=1은 행 방향)
from math import ceil
def class_avg(df):
    return ceil((df['남자'] + df['여자'])/2)

score.apply(class_avg, axis=1)

# %% map 
"""map 함수
Series.map(func)
- 시리즈의 각 원소의 값을 반환 즉, 데이터프레임 전체가 아니라 단일 컬럼에 대해서 동작
"""
score['남자'].map(lambda x: x + 5)
# lamda랑 자주 사용함 
# %% 문자열 데이터 처리 
# 문자열 (.str)
landmark = pd.DataFrame({'name':['광화문','호미곶', '첨성대'],
                         'location':['서울 종로구 사직로 161',
                                     '경북 포항시 남구 호미곶면 대보리 150',
                                     '경북 경주시 인왕동 839-1']})
landmark['location'].str[3:6]

# %% 
landmark['location'].str.split(" ", expand=True)

# %%
landmark['loc_1'] = landmark['location'].str.split(" ").str[0]
landmark

# %%
landmark['location'].str.startswith('서울')

# %%
landmark['location'].str.endswith('1')

# %%
landmark['location'].str.contains('1')

# %%
# 날짜: 책 원본
from datetime import datetime, timedelta
datetime.today()

# %%
datetime.strptime('2021-12-25 00:00:00', '%Y-%m-%d %H:%M:%S')

# %%
time = datetime.today()
time.strftime('%Y-%m-%d %H:%M:%S')

# %%
time + timedelta(days=100)

# %%
# ===== 2부: 금융 데이터 버전 =====
# %%
PATH = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터\prices.csv'
prices = pd.read_csv(PATH, dtype={'code': str}, parse_dates=['date'], encoding='utf-8-sig')
prices = prices.sort_values(['code', 'date']).reset_index(drop=True)
prices.head()

# %%
# 열마다 apply: 가격 열들의 최댓값 (숫자 열만 골라서)
prices[['open', 'high', 'low', 'close']].apply(np.max, axis=0)

# %%
# 행마다 apply: 하루 가격 범위를 종가 대비 %로 (고가 - 저가) / 종가 x 100
prices['range_pct'] = prices.apply(lambda r: (r['high'] - r['low']) / r['close'] * 100, axis=1)
prices[['date', 'code', 'range_pct']].head()

# %%
# 함수 만들고 apply: 종가 구간 이름 붙이기
def price_band(close):
    if close < 10000:
        return '1만원 미만'
    elif close < 50000:
        return '1만~5만원'
    else:
        return '5만원 이상'

prices['band'] = prices['close'].apply(price_band)
prices['band'].value_counts()

# %%
# 종목별로 계산할 때 (groupby + transform): 전일 대비 수익률(%)
prices['ret'] = prices.groupby('code')['close'].transform(lambda s: s.pct_change() * 100)
prices[['date', 'code', 'close', 'ret']].head()

# %%
# 날짜 열: 연·월·요일
prices['year'] = prices['date'].dt.year
prices['month'] = prices['date'].dt.month
prices['weekday'] = prices['date'].dt.dayofweek.map({0:'월', 1:'화', 2:'수', 3:'목', 4:'금', 5:'토', 6:'일'})
prices[['date', 'year', 'month', 'weekday']].head()

# %%
# 날짜 계산: 기준일 + 30일, 기간 자르기
base = pd.Timestamp('2025-01-02')
base + timedelta(days=30)

# %%
jan_2025 = prices[(prices['date'] >= '2025-01-01') & (prices['date'] < '2025-02-01')]
print('2025년 1월 행 수:', len(jan_2025))

# %%
# 문자열: 종목코드 자리수·앞자리 확인 (코드는 반드시 문자열로 읽어야 0이 안 사라짐)
prices['code'].str.len().value_counts()

# %%
prices['code'].str[:2].value_counts().head()

# %%
prices['code'].str.startswith('0').sum()

# %%
# 문자열 채우기: 숫자 100을 6자리 코드로 (0 채우기)
pd.Series([100, 5930]).astype(str).str.zfill(6)

# %%
# 결측 확인
prices.isna().sum()
