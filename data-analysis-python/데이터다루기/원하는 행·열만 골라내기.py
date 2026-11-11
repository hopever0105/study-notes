# -*- coding: utf-8 -*-
# 원하는 행·열만 골라내기

#%% 행과 열 선택하기
from sklearn.datasets import load_iris
import pandas as pd 
iris = load_iris()
iris = pd.DataFrame(iris.data, columns = iris.feature_names)

# 행선택
# DataFrame[시작인덱스: 끝인덱스] : 행을 슬라이킹함 다만, 슬라이싱은 끝 인덱스 전가지 된다. 
s= [1,2,3,4,5,6,7]
s[1:5] # 2,3,4,5
s[:-2] # 끝에서 두번째 
s[:] # 전부다 
iris[1:4]

#%%
# 열선택
# DataFrame['컬럼명'] : 하나의 컬럼 선택 결과 Series
# DataFrame[['컬럼명1', '컬럼명2']] : 여러개 컬럼 선택 결과 DataFrame 대괄호 한번 더 씌어주기

iris['sepal length (cm)'].head(4)
iris[['sepal length (cm)','sepal width (cm)']].head(4)

#%% 행과 열 동시 선택하기 
#1. iloc: 위치기반선택
""" DataFrame.iloc[row.column]"""
iris.iloc[1:4] # d인수 하나 지정시 행, 인수 두개 지정지 순서대로 행과 열 선택
iris.iloc[[1,3,5],2:4] # 1,3,5행의 2,4column 끌고옴
iris.iloc[:, [True,True,False,True]] # 이경우는 1열 2열 4열은 true니까 가져오고 행은 다가지고옴

#%%
#2. loc: 레이블 기반 선택 
"""DataFrame.loc[row,column]"""
# 인덱스 이름이나 컬럼명과 같은 레이블을 기준으로 데이터를 선택한다. 
iris.loc[1:3]
""" 내해석: 
주의점은 먼저 얘는 end 점 포함해서 끌고옴
걍 어떤 index 나 column지정하면 행을 끌고 오려고 씀"""

iris.loc[[1,2], 'sepal length (cm)' : 'petal length (cm)'] # 얘는 열까지 지정한 행 끌고옴

#%% 선택값 변경
import pandas as pd 
stock = pd.DataFrame(
    {'삼성전자': [250000,300000], '하이닉스' : [2000000,30000000], 'LG':[100000,200000]},
    index= ['최저가', '최고가']
)
stock.loc['최고가','LG'] = 300000 # lg의 최고가 데이터를 바꿈
stock['삼성전자'] = stock['삼성전자'] + 10000 # (2개다 바꾸는 결과)
stock

#%%행 추가하기 
# 데이터 프레임 행 추가는 concat() 사용, 
# concat()인수는 DataFrame, Series, Dictionary 사용
new_stocks = pd.DataFrame(
    {'삼성전자': [25000,30000], '하이닉스' : [30000,40000], 'LG':[3000,60000]},
    index= ['총매수', '총매도']
)
stock = pd.concat([stock, new_stocks])
new_stock = pd.Series(
    {'삼성전자':8000,'하이닉스':4000,'LG':2000},
    name= '개인순매수'
)

stock = pd.concat([stock,new_stock.to_frame().T]) 
stock     

#%% 열추가 
# 새로운 열은 단일 값이나 데이터프레임의 행 개수와 동일한 길이의 리스트를 대입 추가 가능
Hanhwa = [80000, 70000, 9000, 8500, 7500]
stock['한화'] = Hanhwa
stock['국가'] = 'korea'
stock

#%% 기존 컬럼 계산 결과 새로운 컬럼으로 추가 가능
stock['한화'] = stock['한화'] +5
stock['총계'] = stock['삼성전자']+stock['하이닉스']+stock['LG']+stock['한화']
stock

#%% 행과 열 삭제 
""" 
drop() 매서드 사용
DataFrame.drop(index = None, columns = None, inplace = False)
index:  삭제한 인덱스 또는 리스트
columns: 삭제할 컬럼명 또는 리스트
inplace: True일 경우 원본 데이터프레임 직접 수정 
"""

stock.drop(['총매수','개인순매수'],inplace = True)
stock.drop(columns = ['국가','총계'],inplace = True)
stock

#%% 조건에 맞는 데이터 탐색 
"""
기본형태: DataFrame[조건식]
조건 하나인 경우 : DataFrame[DataFrame['컬럼명'] >= 값]
"""

import pandas as pd
stock = pd.DataFrame({
    '이름': ['삼성전자', 'SK', 'LG', '한화', '두산', '현대'],
    '가격': [250000, 200000, 100000,50000, None, 30000],
    '거래량': [500, 400, 300, 200, None, 100]
})
stock[stock['이름'] == '한화']

#%% 조건 2개 이상인 경우 
""" AND 연산자: &
    or 연산자 |
    DataFrame[(조건1) & (조건2)]
    DataFrame[(조건1) | (조건2)]
    """
stock[(stock['가격'] >= 200000)& (stock['거래량'] >= 200)]

#%%  새로운 데이터 및 조건 따라 데이터 선정
# df.loc['조건문','컬럼명']
# 지정한컬럼이 이미 존재하는 경우 : 조건을 만족하는 행의 값만 변경
# 지정한 컬럼 존재 x 경우 : 새로운 컬럼 생성, 조건 만족 x 행 NAN 삽입

stock.loc[6, '이름':'거래량'] = ['lS', 100000, 60]
stock.loc[
    (stock['가격'] >= 100000) & (stock['거래량'] >= 200),
    '구매여부'
] = '매수'
stock.loc[stock['구매여부'] != '매수', '구매여부'] = '매수대기'
stock

# %% 하나 컬럼 여러개 조건 다라 서로 다른 조건 할당시 numpy select() 활용
# if-else 다중 구조 
# np.select(조건목록, 선택목록, default = 기본값)
import numpy as np
condition_list = [
    stock['가격'] >= 200000,
    (stock['가격'] >= 100000) & (stock['가격'] < 200000),
    (stock['가격'] >= 50000) & (stock['가격'] < 100000)
]
choice_list = ['대형', '중형', '소형']
stock['기업분류'] = np.select(condition_list, choice_list, default='확인필요')
stock


# %%
stock.isnull().sum() # 열 기준 결측값 탑색 -> na이면 True
#%%
stock.isna().sum(axis=1)   # 행 기준 결측값 탐색
#%%
stock.notna() # 결측값이 아니면 true
#%%
stock.notnull() # 위와 동일
#%%
stock.notnull().sum()


# %% 결측값 제거
""" DataFrame.dropna(axis-0, how='any' , thresh = None, subset = None, inplace = False)
axis: 0 인 경우 행, 1인경우 열
how: any이면 결측값이 존재하는 모든 행/열 삭제 'all' 이면 모든 값이 결측값일 떄 삭제
thresh: 정숫값을 지정하면 결측값이 아닌 값이 그보다 많을 때 행 또는 열을 유지
subset: 어떤 레이블에 결측값이 존재하면 삭제할 지 정의
inplace: True이면 제자리에서 작업을 수행하고 None을 반환 """

stock.dropna()          # 결측값이 포함된 모든 행 삭제

# %%
stock.dropna(thresh=4) # 결측값이 아닌 값이 4개 이상인 행만 유지

# %% 결측값 대체 
""" DataFrame.fillna(valeu=None, method = None, axis = None, inplace = False, limit = None)
"""
# value:단일 값 혹은 dict/Series/DataFrame 형식으로 대체 값 직접 입력
# method : 'pad' , 'fill' 이전 값으로 채우고, 'bfill'은 다음에 오는 값으로 채움
# axis : 0 또는 'index'이면 행방향, 1또는 'columns'이면 열방향으로 채움
# limit : method 인자 지정 시 limit으로 지정한 개수만큼 대체 가능

kospi = pd.DataFrame({
    'year': [2021, 2022, 2023, 2024, 2025, 2026],
    'point': [2500, 3000, 2000, None, None, 7500],
    'volume': [300, 700, None, 400, 800, 1500],
    'call_price': [1.8, None, 1.8, 2.5, 2.5, 3.4],
    'put_price': [None, None, 2, 4.3, None, 2]
})

# %% 그냥 하는거 
kospi.fillna(0) # 결측값 0으로 대체

# %% 통계량 활용
kospi.fillna(kospi.mean()) # 결측값 평균 대체

# %% 시계열 특성 고려
# 직전 값으로 대체
kospi.ffill() # 결측값 직접 값 대체

# %% 시계열 특성고려
# 이후 값으로 대체
kospi.bfill()

# %% 중복행 삭제 
kospi['call_price'].drop_duplicates()

# %%
kospi[['call_price', 'put_price']].drop_duplicates()




# %% 데이터 정렬하기 
import pandas as pd
from sklearn.datasets import load_iris
iris = load_iris()
iris = pd.DataFrame(iris.data, columns=iris.feature_names)

# %% 인덱스 기준 정렬
"""DataFrame.sort_index(axis=0,ascending = True, inplace = False)"""
iris.sort_index(ascending=False, inplace=True) # 행기준 정렬
iris.head()
iris.sort_index(axis=1, ascending=True, inplace=True) # 열기준 정렬 
iris.head()

# %% 값기준 정렬
""" DataFrame.sort_values(by, axis = 0, ascending = True, inplace = False)
by: 정렬 기준으로 사용할 컬럼의 이름 또는 리스트 """

iris.sort_values('petal length (cm)')
iris

# %%
iris.sort_values(['petal width (cm)', 'sepal length (cm)'])








