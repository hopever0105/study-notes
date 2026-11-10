# -*- coding: utf-8 -*-
# 2-1 데이터 불러오기와 기본 구조 이해

#%% 데이터 프레임생성

import numpy as np 
import pandas as pd

dataset = np.array ([['삼성전자', 250000], ['삼성전기', 1000000]])
df = pd.DataFrame(dataset, colums = ['name','price'])
df

# 방법은 여러개다
df = pd.DataFrame([['삼성전자', 250000], ['삼성전기', 1000000]],columns = ['name','price'])
#
df = pd.DataFrame({'name': ['삼성전자','삼성전기'],'Price':['250000','10000000']})

#%% 시리즈
# 시리즈란 1차원 데이터 구조로 하나의 열로 구성 인데스와 같을 가진다. 
# 데이터프레임의 각 열이 내부적으로 시리즈 객체임 
#pd.series({'idx1':value1,'idx2':value2},name='class')

#%% 데이터 불러오기와 저장
# 데이터 저장하기 
# DF csv 파일로 저장시 to_csv() 사용
# 컬럼명은 저장 but 인덱스는 저장 x 기본값
# index = True 사용하면 인덱스 함께 저장 가능 
# 한글 데이터 깨지는 바 utf-8 설정
filepath = 'data.csv'
df.to_csv(filepath,encoding = 'utf-8')

# csv 파일 읽기
df = pd.read_csv(filepath,encoding='utf-8')

# 결측값 빈칸이 아닌 특정 문자열 지정시 na_vallues 옵션 사용해서 해당 값 결측 값 인식 가능
df = pd.read_csv(filepath,na_values = 'Blank', encoding = 'utf-8')

#%% 데이터 확인 
# 데이터 구조확인하기에는 scikit -learn 등을 사용 가능 
from sklearn.datasets import load_iris
iris = load_iris()
iris = pd.DataFrame(iris.data, columns =iris.feature_names)

iris # 데이터 보기 
iris.head() # 데이터 앞행 5개보기 
iris.tail() # 데이터 뒤행 5개 보기 
iris.info() # 데이터 정보 구조 확인하기 
iris.describe() # 데이터 기초통계 요약
# 데이터개수(count), 평군(mean)l,표준편자(std),최솟값(min)
# 1분위수, median, 3분위수, min, max 제공

#%% 데이터프레임의 구성요소 
# pandas는 행을 index로 열을 columns로 관리하며 고유한 데이터 타임 가짐
# dtypes 
# int: 정수형: 소수점을 가지지 않는 숫자
# float: 실수형, 소수점 이하의 값을 포함한 숫자
# bool: 논리형, True/False
# datetime : 날짜와 시간 데이터
## category : 범주형 데이터
# object : 문자열 여러타입 섞임 

iris.dtypes


#%% 데이터타입 변경하기  astype사용
# 실수형을 정수형으로 바꿈
iris['sepal length (cm)'] = iris['sepal length (cm)'].astype('int')

# \는 줄이 너무 길어서 줄바굴떄 쓰는거 뒤에 아무것도 오면 안되며 뒤에 뭐가오면 에러남 
iris[['sepal width (cm)', 'petal length (cm)']] = \
iris[['sepal width (cm)', 'petal length (cm)']].astype('int')
iris.head(3)

#인덱스와 칼럼 
# 데이터를 식별하는 기준이며 인덱스는 기본적으로 0부터 시작하는 정수 인덱스가 생성된다
# 컬럼은 문자형 리스트 형태로 관리된다. 

iris.index
iris.columns

#%% 인덱스 확인 및 변경
# 인덱스 컬럼명 직접 변경시 list나 numpy 배열 사용 가능 
# 이때 주의 점은 데이터의 길이가 바꾸지 전후 반드시 일치해야함
# 특정 컬럼을 인덱스로 사용할 때는 set_index() 함수 사용
"""df.set_index(keys, drop = True, append = False, inplace = True)"""
# keys : 인덱스로 사용할 컬럼 이름
# drop: 인덱스로 설정한 컬럼 데이터프레임에서 제거할지 여부
# append: 기존 인덱스 유지한 채 추가할 지 여부
# inplace: 원본 데이터 프레임 직접 변경 여부

iris.set_index('sepal length(cm)', drop = True, append = False, inplace= True)
iris.head()

# 기존인덱스 제거 -> 기본 정수 인덱스 되돌리고자 할 때 reset_index 사용
""" df.reset_index(drop=False, inplace= False)"""
# drop : 기존 인덱스 DataFrame 내에서 삭제할지, 컬럼으로 추가할지 여부
# inplace: 원본 객체를 변경할 지 여부

iris.reset_index(inplace = True)
iris.head()


#%% 컬럼명 확인 및 변경
# 컬럼명 역시 인덱스와 동일 방식으로 columns 속성 사용하여 확인 또는 변경 가능
iris.columns = ['Sepal 길이','Sepal 넓이', 'Petal 길이', 'Petal 넓이']
iris.columns

#%% 컬럼명에 포함된 특정 문자 일괄 변경 시 문자열 메서드 활용 가능 
#ex: 컬럼명 공백 언더바로 변경하면 컬럼명을 변수처럼 사용하기 편리해짐
"""DataFrame.columns.str.replace('기존문자','바꿂 문자')"""
iris.columns = iris.columns.str.replace(' ', '_') # 공백을 언더바로 바꿈
iris.head(3) # 확인