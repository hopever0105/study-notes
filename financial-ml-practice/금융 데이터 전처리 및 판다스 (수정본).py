#%%
# ==========================================
# 금융 데이터 전처리 및 판다스 (수정본)
# ==========================================


#%%
# ==========================================
# 0. 준비: 데이터 폴더와 AAPL 데이터 받기
# ==========================================
# [여기만 수정하면 됨] 데이터를 저장할 폴더 (없으면 자동으로 만듦)
import os
from pathlib import Path

DATA_DIR = Path(r'C:\Users\arlo0\OneDrive\바탕 화면\금융데이터_연습')
AAPL_PATH = DATA_DIR / 'AAPL.csv'
os.makedirs(DATA_DIR, exist_ok=True)

# AAPL.csv 가 없으면 FinanceDataReader로 받아서 저장 (미국 종목이라 KRX에 요청하지 않음)
if not AAPL_PATH.exists():
    import FinanceDataReader as fdr
    fdr.DataReader('AAPL', '2024-01-01').to_csv(AAPL_PATH)
    print('AAPL 데이터 저장 완료:', AAPL_PATH)

#%%
# ==========================================
# 판다스(Pandas) 데이터 입출력 - CSV 파일 읽기
# ==========================================
# [판다스 주요 입출력 API]
"""CSV(read_csv / to_csv), JSON(read_json / to_json), HTML(read_html / to_html)
MS Excel(read_excel / to_excel), Pickle(read_pickle / to_pickle), SQL(read_sql / to_sql)"""

# read_csv() 함수로 CSV 파일을 데이터프레임(DataFrame) 형태로 불러오기
# DataFrame은 2차원 테이블 형식(행=Index, 열=Series 객체)으로 구성됨
import pandas as pd
df = pd.read_csv(AAPL_PATH)
df.head()  # 상위 5개 행만 출력


#%%
# ==========================================
# 판다스(Pandas) 데이터 구조 및 read_csv 옵션 활용
# ==========================================
# [Series vs DataFrame 비교]
# - Series (1차원): 1D 배열이고 같은 데이터 타입의 데이터만 허용됨
# - DataFrame (2차원): 2D 테이블 형태의 데이터 구조이고 컬럼끼리는 다른 데이터 타입을 허용함
# -> DataFrame의 장점은 서로 다른 형태의 변수를 하나의 틀 안에서 분석할 수 있어 다양한 종류의 데이터를 동시에 전처리할 수 있음

# read_csv() 호출 시 주요 옵션 활용:
# 1) index_col: 인덱스로 설정할 컬럼명 지정 (미지정 시 0, 1, 2, 3, 4 같은 정수형 인덱스가 잡힘)
# 2) parse_dates: str 타입의 날짜 컬럼값을 Timestamp 타입으로 변환 (인덱스 전체는 DatetimeIndex, 각 항목은 Timestamp가 됨)
# -> 인덱스를 Timestamp 타입으로 만들어주면 데이터 결합, 시계열 분석 등이 용이해짐

import pandas as pd
aapl_df = pd.read_csv(AAPL_PATH, index_col=0, parse_dates=True)
aapl_df.index.name = 'Date'  # 인덱스 이름을 'Date'로 지정 (선택)
print(aapl_df.head())
print(type(aapl_df.index))
print(type(aapl_df.index[0]))
#%%

#%%
# ==========================================
# 결측치(NaN)와 이상치 다루기 - 실습 데이터 생성
# ==========================================
# 데이터 수집 과정에서 실수나 전산 오류로 결측치(missing value)가 발생하며, 분석 전 처리는 필수임
# 판다스에서 결측치는 NaN으로 표시되며, 무한값(infinity) 역시 연산 에러를 유발하므로 일단 결측치로 간주함

import numpy as np
import pandas as pd

# 3개의 Series 객체를 만들어 하나의 DataFrame으로 구성 (컬럼마다 1개의 NaN 포함)
s1 = pd.Series([1, np.nan, 3, 4, 5])
s2 = pd.Series([1, 2, np.nan, 4, 5])
s3 = pd.Series([1, 2, 3, np.nan, 5])
df = pd.DataFrame({'S1': s1, 'S2': s2, 'S3': s3})
df.head()

#%%
# ==========================================
# 결측치 확인 함수 - isna(), isin(), isnull()
# ==========================================
# NaN 데이터를 확인하는 함수: isna(), isnull(), isin()
# isna(): 결측치이면 True, 아니면 False를 Boolean 타입으로 반환
# -> Series에서 호출하면 Series 반환, DataFrame에서 호출하면 DataFrame 반환
# -> 반환된 객체에 멤버함수를 연속으로 호출하는 '체인(chain) 기법'으로 이어갈 수 있음

df['S1'].isnull()
df.isna()

#%%
# sum()을 체인하여 각 변수(컬럼)별 결측치 개수 확인 (파이썬에서 True=1, False=0으로 계산됨)
# 참고: count() 함수를 호출하면 NaN 값을 제외한 유효 데이터 개수를 출력함 (변수별 개수가 다르면 문제 의심)
df.isna().sum()

# isin(): 각 컬럼 값이 매개변수로 전달받은 인자(iterable, Series, DataFrame, dict 등 주로 리스트)에 포함되는지 True/False 판단
# 판다스에 저장되는 NaN 값은 np.nan을 뜻하므로 리스트로 [np.nan] 전달 시 isna()와 동일하게 동작
df.isin([np.nan])
df.isin([np.nan]).sum()

#%%
# isnull() 역시 isna()와 완전히 동일한 동작을 수행함
# (판다스가 R의 영향을 받아 na와 null이 존재하지만, 내부적으로 둘 다 넘파이의 NaN으로 대체하여 구분이 없어졌기 때문)
df.isnull()
df.isnull().sum()

# [참고: 판다스 라이브러리 코어 내부 구현]
# def isna(obj):
#     return _isna(obj)
# isnull = isna

#%%
# ==========================================
# 결측치 처리하기 - 채우기(fillna)
# ==========================================
# 결측치 처리 방법은 크게 '합리적인 다른 값으로 채우기'와 '결측치가 있는 행/열 제거하기'가 있음
# 시계열 길이가 짧거나 데이터 포인트가 적다면 바로 제거하기보다 합리적인 대체값을 고안하는 것이 좋음

# fillna(0): 데이터프레임의 모든 NaN 값을 0으로 치환
df.fillna(0)

#%%
# 단순 0 대체 대신 방향을 정해서 채울 수 있음 (또는 평균(mean) 등 특정 값 지정 가능)
# - ffill(): 앞선 행의 값을 가져옴 (forward fill, 예전 method='pad' 와 같은 뜻)
# - bfill(): 다음 행의 값을 가져옴 (backward fill, 예전 method='bfill' 과 같은 뜻)
df.ffill()
df.bfill()

# [실무 주의사항]
# 금융 시계열 분석에서 backward fill(bfill)은 미래 데이터를 끌어다 쓰는 '사전 관찰 편향(look-ahead bias)' 문제를 일으킬 수 있음
# 따라서 보통 한 단계 앞의 시계열 값을 가져오는 forward fill(ffill)이나 전후 평균값을 많이 사용함

#%%
# ==========================================
# 결측치 처리하기 - 제거하기(dropna)
# ==========================================
# dropna(): 결측치가 발생한 행이나 열을 완전히 제거 (시계열 분석에서는 가급적 지양)
# - axis=0 (디폴트, 'rows'): 아래로 향하는 행 방향으로 동작 -> 결측치가 있는 행 제거
# - axis=1 ('columns'): 열 방향으로 동작 -> 결측치가 있는 열 제거

df.dropna()
df.dropna(axis='rows')
df.dropna(axis=0)

# 현재 예제 df는 인덱스를 제외한 모든 열(S1, S2, S3)에 결측치가 존재하므로 모든 열이 삭제됨
df.dropna(axis='columns')
df.dropna(axis=1)

#%%
# ==========================================
# 실제 주가 데이터에서 결측치 및 무한값 동시 확인
# ==========================================
# 결측치(np.nan) 외에 계산 결과로 생성된 무한값(np.inf, -np.inf)도 이후 연산 오류를 유발하므로 함께 확인해야 함
# isin()으로 해당 값 포함 여부를 True/False로 찾고, .any(axis=1)을 연속 호출해 행(Row)에 하나라도 True가 있으면 해당 행 출력
# (예전 문법 .any(1) 은 최신 판다스에서 에러가 나므로 axis=1 로 씀)
aapl_df[aapl_df.isin([np.nan, np.inf, -np.inf]).any(axis=1)]

#%%
# ==========================================
# 데이터 선택 방법 - 슬라이싱, 인덱싱, 서브셋 데이터 추출
# ==========================================
# 인덱싱(Indexing): 위치 정보의 개념
# 슬라이싱(Slicing): 인덱싱(위치 정보)을 기반으로 대괄호 연산자([])를 이용해 해당 부분을 잘라내어 서브셋 데이터를 만드는 것

# 파이썬 리스트 슬라이싱 예시 (0번째부터 5-1번째 위치까지 잘라냄, 마지막 인덱스는 참조하지 않음)
a = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
a[0:5]


#%%
# DataFrame에서 대괄호 연산자([])로 컬럼 단위 데이터 추출
# 한 개의 컬럼만 선택하면 판다스 1차원 객체인 Series가 출력됨
import pandas as pd
df = pd.read_csv(AAPL_PATH, index_col=0, parse_dates=True)
df.index.name = 'Date'
df['Open'].head()

# 주의: 다수의 컬럼을 선택할 때 대괄호 하나에 쉼표로 나열하면 KeyError가 발생함 (아래 줄은 일부러 에러가 나는 예시라 주석 처리)
# df['Open', 'High']  # KeyError: ('Open', 'High')




#%%
# ==========================================
# 다수 컬럼 선택 및 행 단위 슬라이싱 (대괄호 연산자)
# ==========================================
# 대괄호 연산자에 df['Open', 'High']처럼 쉼표로 나열하면 판다스 내부적으로 ('Open', 'High') 튜플 형식의
# 단일 컬럼명으로 인식하여 KeyError가 발생함 -> 여러 컬럼 선택 시 반드시 리스트([]) 형식으로 전달해야 함
df[['Open', 'High', 'Low', 'Close']].head()

# 행 단위로 데이터 추출 (파이썬 인덱싱 규칙: [시작:끝] 지정 시 시작 인덱스는 포함, 끝 지정 인덱스는 미포함)
df[0:3]  # 0, 1, 2번째 행 데이터 추출 (컬럼 범위 미지정 시 전체 컬럼 출력)

# 인덱스(Date) 값을 사용해 행 데이터 슬라이싱
df['2025-10-10':'2025-10-20']



#%%
# ==========================================
# loc과 iloc을 이용한 단일 행 및 행/열 동시 추출
# ==========================================
# 단일 행 추출 시 loc과 iloc 모두 1차원 객체인 Series 타입을 반환함
df.loc['2025-12-12']
df.iloc[0]
type(df.loc['2025-12-12'])  # pandas.core.series.Series

# 행과 열 동시 추출: df.loc[행 인덱싱 값, 열 인덱싱 값] / df.iloc[행 인덱싱, 열 인덱싱]
# 콤마(,) 왼쪽은 항상 행, 오른쪽은 항상 열을 선택함
df.loc['2025-10-10':'2025-10-20', ['Open', 'High', 'Low', 'Close']]

# iloc은 정수형 인자를 받으며 마지막 원소를 포함하지 않으므로 슬라이싱할 때 끝 인덱스에 1을 더해야 함
# (데이터가 많을 때는 위치 번호로 찾기 어려우므로 주가 분석에서는 loc 사용을 권장)
df.iloc[0:10, [0, 1, 2, 3]]

#%%
# ==========================================
# loc에서 다양한 str 날짜 포맷 자동 인식
# ==========================================
# 판다스는 내부적으로 넘파이(ISO 8601 표준)를 기반으로 동작하므로, str 타입으로 날짜를 넘겨도
# ISO 8601 규칙에 어긋나지 않으면 내부적으로 자동 변환되어 Timestamp 인덱스와 비교 연산이 가능함

# '연-월' 형식만 전달해 해당 월 전체 데이터 추출
df.loc['2025-11'].head()

# 영문 약자 및 풀네임 월 표기 형식도 판다스 내부적으로 자동 변환되어 정상 추출됨
df.loc['2025-Nov-1':'2025-Nov-10'].head()
df.loc['November 1, 2025':'November 10, 2025'].head()
df.loc['2025-10-10':'2025-10-20']

#%%
# 금융 시계열 데이터 분석에 유용한 함수 - shift()
# 시계열 데이터 분석시 서로 다른 시갠대 데이터 손쉽게 가져옴 
# shift(): 인덱스 변화 없이 연결된 데이터만 일정 간격(periods)으로 전/후 이동(lagging)시키는 함수
# -> 전일 주가 대비 당일 변화량, 변화율, 모멘텀, 수익률 계산 시 유용
# -> periods 기본값은 1이며, 양의 정수 전달 시 아래로 이동, 음의 정수 전달 시 위로 이동함
# -> axis='1'(columns) 전달 시 데이터가 오른쪽으로 이동(디폴트는 row 방향인 0)

aapl_df['Close_lag1'] = aapl_df['Close'].shift()
aapl_df.head()

#%%
# ==========================================
# 백분율 변화량(수익률) 계산 - pct_change()
# ==========================================
# pct_change(): 현재 값과 이전 요소 값의 백분율 변화량(주가 데이터에서는 곧 수익률)을 연산하는 함수
# -> 아무 숫자도 전달하지 않으면 기본적으로 periods 값에 1이 전달됨
# -> shift()와 마찬가지로 periods에 정수 전달 시 해당 간격만큼 백분율을 계산함
#    (음의 정수 전달 시 위 방향으로 변화율 계산, 양의 정수 전달 시 아래 방향으로 변화율 계산)

aapl_df['pct_change'] = aapl_df['Close'].pct_change()
aapl_df.head(10)


#%%
# ==========================================
# 데이터 변화량(차분) 계산 - diff()
# ==========================================
# diff(): 현재 값에서 이전 값을 차감하는 뺄셈 연산을 통해 변화량을 구하는 함수
# -> pct_change()가 백분율 변화율(%)을 계산한다면, diff()는 절대적인 변화량(차이)을 계산함
# -> shift(), pct_change(), diff() 모두 기본 periods=1이며, 양수는 아래로 미루고 음수는 위로 올림
# -> axis 기본값은 0('rows')이며, 1('columns')을 전달하면 오른쪽 컬럼 방향으로 계산을 수행함

aapl_df['Close_diff'] = aapl_df['Close'].diff()
aapl_df.head()

#%%
# ==========================================
# 이동 평균선 및 윈도우 연산 - rolling()
# ==========================================
# rolling(): 윈도우(window)라는 일정 구간 데이터들의 평균값, 최솟값, 최댓값 등을 계산하는 윈도우 함수
# -> 가장 기본적인 스무딩(smoothing) 기법으로 주식 차트의 이동 평균선, 지수 이동 평균, 볼린저 밴드 계산에 응용됨
# -> window 크기를 5로 설정하면 초기 5개 데이터가 확보되기 전(앞선 4개 행)에는 정상 계산이 불가하므로 NaN이 출력됨
#    (이동 평균선 계산 시에는 결측치가 생기는 것이 자연스러우므로 보통 NaN 값을 그대로 둠)

df['MA'] = df['Close'].rolling(window=5).mean()
print(df.head(10))

# rolling() 함수의 출력 타입은 Rolling 클래스(pandas.core.window.Rolling)이므로
# 평균을 구하는 mean() 외에 다양한 내장 집계 함수를 연속으로 체인하여 사용할 수 있음
type(df['Close'].rolling(window=5))

#%%
# ==========================================
# 시계열 시간 간격 재조정 - resample()
# ==========================================
# resample(): 일별 데이터를 월별·연별 데이터로 가공하거나 시간별 데이터로 재조정(리샘플링)하는 함수
# - 업 샘플링(up-sampling): 분 단위, 초 단위로 샘플 빈도수를 증가시킴 (보간법 interpolation으로 누락 데이터 채움)
# - 다운 샘플링(down-sampling): 몇 일, 몇 달 단위로 샘플 빈도수를 감소시킴 (기존 데이터를 집계 aggregation, 금융에서 주로 사용)

import pandas as pd

# 영업일(freq='B', 주말 제외 평일) 기준의 임의 시계열 데이터 생성
index = pd.date_range(start='2025-01-01', end='2025-10-01', freq='B')
series = pd.Series(range(len(index)), index=index)
series

#%%
# resample()의 rule 매개변수에 날짜 주기(Frequency) 단위를 전달하여 간격 재조정
# -> rule='ME'(월말) 전달 시 월말 일자를 기준으로 데이터를 정렬하며, sum()을 체인하면 월별 합계를 구함
#    (최신 판다스는 월말을 'M'이 아니라 'ME'로 씀. 'M'은 경고가 뜨거나 빠질 수 있음)
#    (예: 2025-01-31의 값은 2025-01-01부터 2025-01-31까지의 데이터를 전부 합계한 값)
series.resample(rule='ME').sum()

#%% 월말 일자 하루 데이터만 확인하는 경우 last() 함수 호출
series.resample(rule='ME').last()

#%% 월초 일자 하루 데이터를 확인하는 경우 rule에 'MS'를 전달하고 first() 함수 호출
series.resample(rule='MS').first()

# [rolling() vs resample() 핵심 차이]
# - rolling(): 윈도우 기반 시간 델타(delta) 간격으로 이동하며 새로운 시점마다 결괏값을 계산 (시간 기반 윈도우 작업)
# - resample(): 고정된 주기(일, 주, 월 등) 범위 내에서 집계된 일정 값을 보여줌 (주기 기반 윈도우 작업)


