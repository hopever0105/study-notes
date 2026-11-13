# -*- coding: utf-8 -*-
# 표 합치기·그룹별 요약·모양 바꾸기
# 언제 쓰나: 여러 달 체결 기록 이어 붙이기, 체결 기록에 종목명 붙이기, 종목별·연도별 수익률 요약표 만들기
# 책 예제(인사표·상품주문·iris·성적표)와 같은 순서로, 소재만 주식으로 바꿈
# Spyder: 구역(# %%)마다 Ctrl+Enter → 결과는 print로 확인

import pandas as pd

# ================================================================
# 1. concat: 표를 위아래(행) 또는 옆으로(열) 이어 붙이기
# ================================================================

# %% 1-1. 위아래로 붙이기 (axis=0): 10월 체결 + 11월 체결
# 열 이름만 같으면 열 순서가 달라도 이름 기준으로 맞춰 붙음
oct_trades = pd.DataFrame({
    '종목': ['삼성전자', 'NAVER'],
    '방향': ['매수', '매도'],
    '수량': [10, 3]
})
nov_trades = pd.DataFrame({
    '종목': ['카카오', '삼성전자'],
    '수량': [5, 4],              # 열 순서가 다름
    '방향': ['매수', '매도']
})
print(pd.concat([oct_trades, nov_trades], axis=0))
# 행 번호(index)가 0, 1, 0, 1 → 겹침

# %% 1-2. 행 번호 새로 매기기 (ignore_index=True) + 없는 열은 NaN
nov_trades2 = pd.DataFrame({
    '종목': ['카카오', '삼성전자'],
    '방향': ['매수', '매도'],
    '체결가': [52000, 71000]     # 10월 표엔 없는 열
})
print(pd.concat([oct_trades, nov_trades2], axis=0, ignore_index=True))
# 행 번호 0, 1, 2, 3 / 10월 행의 체결가, 11월 행의 수량은 NaN(빈칸)

# %% 1-3. 옆으로 붙이기 (axis=1): 행 번호가 같은 줄끼리 붙음
fee = pd.Series({1: 150}, name='수수료')     # 행 번호 1에만 값
print(pd.concat([oct_trades, fee], axis=1))
# 0번 행 수수료는 NaN (fee에 0번이 없어서)

# %% 1-4. 길이가 다르면 남는 줄은 NaN으로 채워짐
fee3 = pd.DataFrame({'수수료': [150, 90, 200]})
print(pd.concat([oct_trades, fee3], axis=1))
# 2번 행: 종목·방향·수량은 NaN, 수수료만 200

# ================================================================
# 2. merge: 공통 열(키)로 두 표 연결하기 (SQL의 JOIN)
# ================================================================

# %% 2-1. 종목 기본 정보 표 + 체결 기록 표
stock_info = pd.DataFrame({
    '종목코드': ['005930', '000660', '035420', '035720'],
    '종목명': ['삼성전자', 'SK하이닉스', 'NAVER', '카카오']
})
fills = pd.DataFrame({
    '주문번호': [1001, 1002, 1002, 1003, 1004],
    '종목코드': ['035720', '035420', '005930', '035420', '999999'],  # 999999는 기본 정보에 없음
    '수량': [1, 4, 2, 2, 3]
})

# inner: 양쪽 다 있는 키만 → 999999 행, 체결 없는 000660은 빠짐
print(fills.merge(stock_info, on='종목코드', how='inner'))

# %% 2-2. outer: 한쪽에만 있어도 전부 남김, 없는 칸은 NaN
print(fills.merge(stock_info, on='종목코드', how='outer', sort=True))
# 000660(체결 없음) → 주문번호·수량 NaN / 999999(종목명 모름) → 종목명 NaN

# %% 2-3. left: 왼쪽(체결 기록)은 전부 남기고 오른쪽 정보만 붙임
# 실무에서 제일 많이 씀: "체결 기록은 하나도 잃으면 안 되고, 종목명만 붙이고 싶다"
print(fills.merge(stock_info, left_on='종목코드', right_on='종목코드', how='left'))
# 두 표의 키 열 이름이 다를 땐 left_on='코드', right_on='종목코드'처럼 따로 적음

# %% 2-4. 합친 표 크기 확인 (행 수, 열 수)
merged = fills.merge(stock_info, on='종목코드', how='outer', sort=True)
print(merged.shape)          # (6, 4): 체결 5줄 + 체결 없는 000660 1줄

# ================================================================
# 3. groupby: 그룹별 요약 (실제 주가 데이터)
# ================================================================

# %% 3-1. 연습 데이터 불러오기 + 일간 수익률
df = pd.read_csv(r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터\prices.csv',
                 dtype={'code': str}, parse_dates=['date'])
df = df.sort_values(['code', 'date'])
df['ret'] = df.groupby('code')['close'].pct_change()   # 종목마다 따로 (전날 대비 %)
df['year'] = df['date'].dt.year
print(df.head())

# %% 3-2. 종목별 평균 (책의 iris.groupby('class').mean()와 같은 자리)
print(df.groupby('code')[['ret', 'amount']].mean().head())

# %% 3-3. 종목별 중앙값: 거래대금은 하루 튀는 날이 있어서 평균보다 중앙값이 대표값으로 나을 때가 많음
print(df.groupby('code')['amount'].median().head())

# %% 3-4. 여러 요약 한 번에 (agg)
print(df.groupby('code')['ret'].agg(['mean', 'std', 'count']).head())

# %% 3-5. 개수 세기 (value_counts): 연도별 행 수
print(df['year'].value_counts().sort_index())

# ================================================================
# 4. qcut + crosstab: 숫자를 3등분해서 범주로 → 범주끼리 개수표
# ================================================================

# %% 4-1. 하루 거래대금을 크기 순서로 3등분 (같은 개수씩)
df = df.dropna(subset=['ret'])           # 첫날(수익률 NaN) 빼기
df['거래대금수준'] = pd.qcut(df['amount'], q=3, labels=['적음', '보통', '많음'])
print(df['거래대금수준'].value_counts().to_frame())   # 셋이 거의 같은 개수

# %% 4-2. crosstab: 거래대금 수준 × 오른 날인지 개수표
df['상승'] = df['ret'] > 0
print(pd.crosstab(df['거래대금수준'], df['상승']))
# 이 표가 카이제곱 검정(범주끼리 관련 있는지)의 재료가 됨

# ================================================================
# 5. pivot_table / melt: 긴 표 ↔ 넓은 표
# ================================================================

# %% 5-1. 작은 예시: 연도·시장·종목구분별 수익률 (긴 표 = 한 줄에 값 하나)
# 숫자는 모양 연습용으로 지어낸 값 (실제 수익률 아님)
perf = pd.DataFrame({
    '연도': [2024, 2024, 2024, 2024, 2025, 2025],
    '시장': ['코스피', '코스피', '코스닥', '코스닥', '코스피', '코스피'],
    '구분': ['대형주', '소형주', '대형주', '소형주', '대형주', '소형주'],
    '수익률': [7.6, 8.8, 8.5, 7.2, 6.8, 7.0]
})
print(perf)

# %% 5-2. pivot_table: 행=연도·시장, 열=구분, 칸=수익률 (넓은 표)
wide = perf.pivot_table(index=['연도', '시장'], columns='구분', values='수익률')
print(wide)

# %% 5-3. melt: 넓은 표를 다시 긴 표로 (pivot의 반대)
# reset_index()로 연도·시장을 다시 보통 열로 내린 뒤 melt
long = wide.reset_index().melt(id_vars=['연도', '시장'], var_name='구분', value_name='수익률')
print(long)

# %% 5-4. 실제 데이터: 행=종목, 열=연도, 칸=평균 일간 수익률
pv = df.pivot_table(index='code', columns='year', values='ret', aggfunc='mean')
print(pv.head())


# %%
import pandas as pd
# 단순연결
""" pandas.concat(objs,axis=0, ignore_index =False)"""
# objs: concat을 실행할 객체의 리스트(DataFrame,Series, Pandel object)
# axis: 0이면 열방향 1이면 행방향 합치기
# ignore_index: True이면 기존 index 무시하고 0부터 시작하는 정수로 재설정

HR1 = pd.DataFrame({
    '이름': ['장화', '홍련'],
    '부서': ['영업', '회계'],
    '직급': ['팀장', '사원']
})
HR2 = pd.DataFrame({
    '이름': ['콩쥐', '팥쥐'],
    '직급': ['사원', '팀장'],
    '부서': ['영업', '인사']
})
pd.concat([HR1, HR2], axis=0)
# 기본은 index 유지 index 변경시 ignore_index = True 옵션 사용 가능

# %%
HR3 = pd.DataFrame({
    '이름': ['콩쥐', '팥쥐'],
    '부서': ['영업', '인사'],
    '급여': [3500, 2800]
})
pd.concat([HR1, HR3], axis=0, ignore_index=True)

# 컬럼 구성이 다른 경우 

# %% 열방향 결합
HR4 = pd.Series({1: 2500}, name='급여')
pd.concat([HR1, HR4], axis=1)

# %%
HR5 = pd.DataFrame({'급여': [4500, 3000, 3500]})
pd.concat([HR1, HR5], axis=1)


""" concat과 merge 구분하기
concat() : 구조를 그대로 이어 붙임
merge(): key값을 기준으로 행을 정렬 또는 매칭 
-> 데이터를 늘리고 싶은지 기준 컬럼으로 맞추고 싶은지 고민해보기 """
# %%
"""
조인: 두 데이터프레임이 공통적으로 가지는 KEY 칼럼의 값을 기준으로 데이터를 결합하는 방식
key: 같은 의미의 값과 범위(도메일) 가지는 컬럼
조인은 관계의 형태에 따라 1:1, 1:M, M:M 결합 가능 
"""

#%% 
""" MERGE 함수
DataFrame.merge(
    rigth, how = 'inner', left_on = None, right_on = None, 
    sort = False, suffixes = ('x_', '_y')
)
how: inner, outer, left, right 
on: 두 테이터프레임 KEY 컬럼명 같은 경우
left_on/right_on : key 컬럼명이 서로 다른 경우
sort : key 값을 기준으로 정렬할지 여부
suffixes: 중복 컬럼며엥 붙일 접미사 
"""

#%% inner join
# 양족 데이터 프레임 모두 존재하는 Key 값만을 기준으로 결합 즉 교집합 
product = pd.DataFrame({
    '상품코드': ['G1', 'G2', 'G3', 'G4'],
    '상품명': ['우유', '감자', '빵', '치킨']
})
sale = pd.DataFrame({
    '주문번호': [1001, 1002, 1002, 1003, 1004],
    '상품코드': ['G4', 'G3', 'G1', 'G3', 'G5'],
    '주문수량': [1, 4, 2, 2, 3]
})
sale.merge(product, on='상품코드', how='inner')

# %% outer join 합칩합 한쪽만 존재하면 NAN
sale.merge(product, on='상품코드', how='outer', sort=True)

# %% left join 
# 왼쪽 다들어오고 오른족은 KEy겹치는애만
sale.merge(product, left_on='상품코드', right_on='상품코드', how='left')

#%% right join
# left 랑 반대
sale.merge(product,left_on = '상품코드', right_on = '상품코드',how = 'right' )

# %% 실수 확인
# 실무에서 하는 흔한 실수인 바, 조인 전 key 컬럼 중복갑 ㅅ있는지 확인하기 
# 조인 전후에는 shape 통해 행의 개수 비교해보기
sale_merged = sale.merge(product, on='상품코드', how='outer', sort=True)
sale_merged.shape


#%% AI 질문
# 1.  내가 작성한 조인 코드
# 2. 각 데이터 프레임의 컬럼 정보
# 3. 원한 결과 
# 위 3가지를 포함해서 질문할 것. 
# %% 데이터 요약과 집계 
# 데이터 나누기: grouping 
# 집계 : aggregation 
"""1. 그룹화와 집계 
DataFrame['집계할 컬럼'].집계 함수()
DataFrame[['컬럼1', '컬럼2']].집계 함수() 
DataFrame.groupby('그룹화 기준 컬럼').집계함수()
"""
#%%
"""일반적인 함수
DataRame.groupby(by=None, level = None, as_index = True, sort = False, dropna= True).집계함수()
by: 그룹 결정
level: 축이 계층 구조일 대 특정 수준 기준으로 그룹화
as_index : 그룹 레이블이 인덱스로 출력될지 여부 , 기본값 True
sort : 집계 행으로 정렬 ㅇ부
dropna: Ture이면 결측값이 행/열과 함게 삭제, False이면 결측값도 그룹의 키로 처리
"""

#%% 
""" 집계함수
count() : 값의 개수
sum(): 합계
min(): 최소값
max(): 최대값
median(): 중앙값
mean(): 평균
std() : 표준편차
var() : 분산
quantile(n): 분위수
frist(): 첫번쨰 값
last(): 마지막 값
mode(): 최빈값
"""
#%%
import pandas as pd
from sklearn.datasets import load_iris

IRIS = load_iris()
iris = pd.DataFrame(IRIS.data, columns=IRIS.feature_names)
iris['class'] = IRIS.target
iris['class'] = iris['class'].map({
    0: 'setosa', 1: 'versicolor', 2: 'virginica'
})
iris.groupby(by='class').mean()  # 평균

# %%
iris.groupby(by='class').median() # 중간값

# %%도수분표ㅗ표
"""pd.Series(DataFrame['컬럼명']).value_counts()"""
pd.Series(iris['class']).value_counts()

# %% 수치형 데이터 구간화와 도수분포표 
# 수치형 데이터에 value_counts()를 그대로 적용시 모든 값에 대해 개수를 세게 되어 분포 형태 파악이 어려움
# so,수치형 데이터는 구간을 나눈후 도수분포표를 생성할 것 

iris['petal width level'] = pd.qcut(
    iris['petal width (cm)'], q=3, labels=['short', 'middle', 'long']
)
pd.Series(iris['petal width level']).value_counts().to_frame()

# %% 교차표 crosstab
# 두개 이상의 기준에 따른 데이터 분포 동시 확인 시 교차표 (contingency table) 사용
# pandas 에서는 pd.crosstab() 활용
"""pd.crosstab(index, columns, dropna= True)
index : 행 기준 변수
columns : 열 기준 변수
dropna : 모든 값이 NaN인 행/열 제거 여부 """

pd.crosstab(iris['petal width level'], iris['class'])

# %% 데이터 재구조화 
""" 피벗테이블 및 melt 
데이터의 열 행을 바꾸는 데 사용

(1) Pivot table 
원본 데이터에서 필요한 열만 선택하여 행(index), 열(columns), 값(values)으로 재배치 
집계결과 나타냄
판다스는 pivot_table() 사용

ex) 
index columns values
12345 name 1  00001
12345 name 2  00002
34567 name 1  00003 
34567 name 2  00004

-> 
index name 1 name 2
12345 00001  00002
34567 00003  00004
"""
#%% 형태 
"""DataFrame.pivot_table(index = None, columns = None, values = None, aggfunc = 'mean')
index : 피벗 테이블의 행 인덱스로 사용할 컬럼 , 2개 이상인 경우 list 지정
columns : 열로 분리할 기준 컬럼 (일반적으로 범주형 사용)
values: 집계할 값이 들어 있는 컬럼
aggfunc: 집계 함수 (기본값은 평균)
"""
#%% pivot table 
import pandas as pd

score = {
    '학년': [1, 1, 1, 1, 2, 2],
    '반': ['A', 'A', 'B', 'B', 'C', 'C'],
    '성별': ['여자', '남자', '여자', '남자', '여자', '남자'],
    '성적': [76, 88, 85, 72, 68, 70]
}

score = pd.DataFrame(score)
score
#%% pivot table 
score = score.pivot_table(
    index=['학년', '반'], columns='성별', values='성적'
)
score

# %% melt 
""" melt 는 pivot과 정반대 
여러개 컬럼을 하나의 변수로 압축 

ex) 
ID col_1 col_2
N1 AAAAA 00001
N2 BBBBB 00002
N3 CCCCC 00003

->
ID variable value
N1 col_1    AAAAA
N2 col_1    BBBBB
N3 col_1    CCCCC
N1 col_2    00001
N2 col_2    00002
N3 col_2    00003

"""
#%% melt
""" 
DataFrame.melt(id_vars= None, var_name = None, value_name = None)
id_vars : 고정컬럼(variabler과 value로 변환 x 컬럼)
var_name: 변수 이름 저장될 컬럼명 (선택사항)
value_name : 값이 저장될 컬럼명  (선택사항)
"""

score.reset_index().melt(
    id_vars=['학년', '반'], var_name='성별', value_name='성적'
)

