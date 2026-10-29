#%% [Sector 1] NumPy 배열 만들기 및 모양 변경 
# NumPy 라이브러리 호출 (보통 np로 줄여서 사용합니다)
import numpy as np

# 1. 1차원, 2차원, 3차원 배열 만들기
# 리스트 괄호 []의 중첩 횟수에 따라 차원이 결정됩니다.
a1 = np.array([1, 2, 3]) # 1차원 배열
print("1차원 배열:\n", a1)

a2 = np.array([[1, 2, 3], [4, 5, 6]]) # 2차원 배열 (행렬)
print("2차원 배열:\n", a2)

a3 = np.array([[[1, 2, 3], [4, 5, 6]], [[1, 2, 3], [4, 5, 6]]]) # 3차원 배열
print("3차원 배열:\n", a3)

# 2. 배열 모양 변경하기 (arange, reshape)
# np.arange(시작, 끝, 간격): 파이썬의 range()와 유사하게 배열 생성 (끝 번호 직전까지)
c = np.arange(15) # 0부터 14까지 1씩 증가하는 배열 생성
print("arange(15):\n", c)

# reshape(행, 열)을 사용하여 1차원 배열을 2차원(3x5)으로 형태 변경
c = c.reshape(3, 5)
print("reshape(3, 5) 후:\n", c)

# 시작, 끝, 간격 지정 및 3차원으로 reshape
d = np.arange(0, 100, 5) # 0부터 95까지 5씩 증가
print("arange(0, 100, 5):\n", d)

d = d.reshape(2, 2, 5) # 2개의 (2x5) 배열, 즉 3차원으로 변경
print("reshape(2, 2, 5) 후:\n", d)


#%% [Sector 2] NumPy 배열의 스칼라 연산
# 행렬의 형태를 유지한 채 '같은 위치의 원소끼리' 사칙연산을 수행합니다.
n1 = np.array([[1, 0], 
               [0, 1]]) # 2x2 배열 생성
n2 = np.array([[1, 2], 
               [3, 4]]) # 2x2 배열 생성

print("n1 + n2 (덧셈):\n", n1 + n2) # 같은 위치 원소끼리 더함
print("n1 - n2 (뺄셈):\n", n1 - n2) # 같은 위치 원소끼리 뺌
print("n1 * n2 (곱셈):\n", n1 * n2) # 같은 위치 원소끼리 곱함 (행렬 곱셈 아님!)
print("n1 / n2 (나눗셈):\n", n1 / n2) # 같은 위치 원소끼리 나눔

# 주의: 0으로 나누면 에러로 멈추지 않고, 경고 메시지와 함께 inf(무한대)가 반환됩니다.
print(n2 / n1) 

# 단일 숫자(스칼라)와의 연산: 배열 내 전체 원소 각각에 일괄 적용됩니다.
print("n1 + 1 (각각 1 더하기):\n", n1 + 1)
print("n1 - 1 (각각 1 빼기):\n", n1 - 1)
print("n1 * 2 (각각 2 곱하기):\n", n1 * 2)
print("n1 / 2 (각각 2 나누기):\n", n1 / 2)


#%% [Sector 3] NumPy 배열의 벡터 연산 및 집계 연산 
# 1. 행렬 곱셈 (내적, Dot product)
# 같은 위치의 원소끼리 곱하는 스칼라 연산(*)이 아닌, 선형대수학의 진짜 '행렬 곱셈'입니다.
print("np.dot(n1, n2):\n", np.dot(n1, n2))
print("n1.dot(n2):\n", n1.dot(n2)) # 위 np.dot()과 완전히 동일한 표현

# 2. 축(axis) 기준 연산
n3 = np.arange(12).reshape(3, 4)
print("n3 배열:\n", n3)

# axis=0 은 열 단위(세로) 연산, axis=1 은 행 단위(가로) 연산입니다.
print("n3.sum(axis=0) (각 열의 합계):\n", n3.sum(axis=0))
print("n3.sum(axis=1) (각 행의 합계):\n", n3.sum(axis=1))
print("n3.max(axis=1) (각 행에서 최댓값):\n", n3.max(axis=1))
print("n3.mean(axis=0) (각 열의 평균값):\n", n3.mean(axis=0))

# 축(axis)을 지정하지 않으면 1차원으로 취급하여 '전체 배열 원소'에 대해 연산.
print("전체 최댓값:", n3.max())
print("전체 최솟값:", n3.min())
print("전체 합계:", n3.sum())
print("전체 평균값:", n3.mean())
print("전체 표준편차:", n3.std())
print("전체 분산:", n3.var())
print("전체 누적 합:\n", n3.cumsum())
print("전체 누적 곱:\n", n3.cumprod())


#%% [Sector 4] NumPy 배열에서 특정 데이터 뽑아오기 (슬라이싱)
# 파이썬 기본 리스트 슬라이싱과 동일하지만 차원(행, 열)별로 콤마(,)로 구분
# ※ 인덱스는 항상 1이 아니라 0부터 시작한다는 점에 주의
v = np.array([[11, 12, 13, 14, 15], 
              [21, 22, 23, 24, 25], 
              [31, 32, 33, 34, 35], 
              [41, 42, 43, 44, 45]])

print("v[1, 2] (2행 3열 데이터):", v[1, 2]) # 인덱스가 0부터 시작하므로 두 번째 행, 세 번째 열 의미
print("v[1][2] (위와 완전히 같은 표현):", v[1][2])

# 콜론(:)은 해당 차원의 '전체' 또는 '지정된 범위'를 의미합니다.
print("v[:, 1] (전체 행, 2열 데이터 추출):\n", v[:, 1]) 
print("v[1:3, 1] (2~3행, 2열 데이터 추출):\n", v[1:3, 1])  
#슬라이싱은 v[a:b]인 경우 a 이상 b 미만으로 읽어야 한다. 
print("v[1, :] (2행, 전체 열 데이터 추출):\n", v[1, :])



#%% [Sector 5] 날짜 생성(date_range)과 시리즈(Series) 기초
# pd.date_range: 시작 날짜와 끝 날짜, 또는 기간(periods)을 지정해 날짜 배열을 생성합니다
# numpy는 하나의 배열에 동일한 형태만 가능
# pandas는 하나의 데이터프레임에 다양한 데이터 가능
# 1차원 데이터는 series, 2차원 데이터는 dataframe을 이용한다. 
# freq='D'(매일), 'W'(매주), 'M'(매달) 등으로 주기 설정 가능 (기본값은 'D')[cite: 21].
import pandas as pd
import numpy as np

# 주가 리스트 준비
prices = [1000, 1010, 1020]

""" 
형식: 
pd. date_range('시작 날짜', '끝 날짜', periods = 날짜 수, freq= '주기')

시작 날짜와 끝 날짜 또는 시작 날짜와 날짜수를 쌍으로 지정
주기는 D: 매일, W= 매주 , M= 매달, 생략 시 기본값은 'D' 이다,
"""


dates = pd.date_range('20181201', periods=3) 
print("생성된 날짜(dates):\n", dates)

# 1주일 단위 날짜 생성 예시 (출력만 확인)
print(pd.date_range('20180101', '20180131', freq='W'))

# 주가 리스트 준비 (이전 장에서 이어진 데이터)
prices = [1000, 1010, 1020]

# 시리즈(Series) 생성: 주가를 데이터로, 날짜를 인덱스로 지정
s = pd.Series(prices, index=dates)
print("\n날짜를 인덱스로 가진 시리즈(s):\n", s)

# 인덱스를 지정하지 않으면 0부터 자동으로 숫자 일련번호가 매겨집니다
s2 = pd.Series(prices) # S 대문자 주의 
print("\n인덱스 미지정 시리즈(s2):\n", s2)

# 시리즈에 데이터 추가: 시리즈명[인덱스] = 값[cite: 22]
s2[3] = 1030 
print("\n데이터가 추가된 s2:\n", s2)

# [참고] 문자형과 숫자형의 차이[cite: 22]
# print('123' + '123')  # 결과: 123123 (문자열 연결)
# print(123 + 123)      # 결과: 246 (수학 연산)


#%% [Sector 6] 시리즈 인덱스 활용 및 데이터 추출
# pd.to_datetime(): 문자 형식의 날짜를 연산 가능한 datetime 형식으로 변환합니다[cite: 23].
s[pd.to_datetime('2018-12-04')] = 1030
print("\n새로운 날짜 데이터가 추가된 시리즈(s):\n", s) #\n 은 줄바꿈을 의미한다. 

# 데이터 추출 방법 1: 리스트나 배열처럼 위치 번호(순서)를 이용해 추출[cite: 23]
print("\ns[2] (3번째 데이터 추출):", s[2])

# 데이터 추출 방법 2: 레이블(인덱스 이름)을 이용해 추출 (Pandas의 장점)[cite: 23]
print("s['2018-12-03'] (해당 날짜 데이터 추출):", s['2018-12-03'])


#%% [Sector 7] 데이터프레임(DataFrame) 생성
# 여러 종목, 여러 날짜의 시세를 2차원 배열 형태로 한 번에 저장합니다
# 종목명을 키(Key)로, 시세 리스트를 값(Value)으로 하는 딕셔너리 생성
prices_dict = {'A전자': [1000, 1010, 1020], 
               'B화학': [2000, 2010, 2020], 
               'C금융': [3000, 3010, 3020]}

# 딕셔너리를 데이터프레임으로 변환 (인덱스 자동 지정: 0, 1, 2)[cite: 24]
df1 = pd.DataFrame(prices_dict)
print("\n데이터프레임 생성(df1):\n", df1)

# 인덱스에 사용할 날짜를 지정하여 데이터프레임 생성[cite: 24]
df2 = pd.DataFrame(prices_dict, index=dates)
print("\n날짜 인덱스가 지정된 데이터프레임(df2):\n", df2)


#%% [Sector 8] 데이터프레임 조회 (iloc vs loc)
# 데이터프레임.iloc[줄번호,열번호] : 열번호는 생략가능하면 생략하면 열 전체를 선택한다. 
# 1. iloc: 위치 번호(숫자)를 이용한 조회
print("\ndf2.iloc[0] (1행 전체 선택):\n", df2.iloc[0])
print("\ndf2.iloc[:, 0] (행 전체 선택, 1열 - A전자 열):\n", df2.iloc[:, 0])
print("\ndf2.iloc[0, 0] (1행 1열의 특정 데이터 선택):", df2.iloc[0, 0])

# 2. loc: 레이블(이름)을 이용한 조회
# 데이터프레임. loc[행 레이블', '열 레이블']: 열 레이블 생략 가능, 생략하면 열 전체 선택
print("\ndf2.loc['2018-12-01'] (해당 날짜의 행 전체 선택):\n", df2.loc['2018-12-01'])
print("\ndf2.loc[:, 'A전자'] (A전자열의 행 전체 선택):\n", df2.loc[:, 'A전자'])
print("\ndf2.loc['2018-12-01', 'A전자'] (특정 날짜, 특정 종목 데이터):", df2.loc['2018-12-01', 'A전자'])

# 3. 데이터프레임 열 직접 선택 (사전 키값처럼 조회)
print("\ndf2['A전자'] (해당 열에 있는 값 전체 선택):\n", df2['A전자'])
print("\ndf2['A전자']['2018-12-01'] (열 선택 후 행 선택):", df2['A전자']['2018-12-01'])


#%% [Sector 9] 데이터프레임 확장 (열 추가 및 병합)
# 데이터프레임['레이블']= 시리즈 형태로 지정한다. 
# 새로운 종목(열) 추가 1: 리스트를 이용해 직접 추가
df2['D엔터'] = [4000, 4010, 4020]
print("\nD엔터 열이 추가된 df2:\n", df2)

# 새로운 종목(열) 추가 2: 기존에 만든 시리즈(s)를 이용해 추가[cite: 27]
# (인덱스가 일치하는 데이터만 알아서 매칭되어 들어갑니다)[cite: 27]
df2['E텔레콤'] = s
print("\nE텔레콤 열(시리즈)이 추가된 df2:\n", df2)

# pd.concat을 이용한 데이터프레임 확장 (axis=1은 가로(열) 방향 병합)[cite: 28]
"""
pd.concat(A,B,axis=1)

A,B는 합쳐질 프레임 
axis는 합치는 방향으로 0은 행, 1은 열을 의미한다. 
 """
s.name = 'F소프트'  # 병합 전 시리즈에 이름을 지정해주면 열 이름이 됩니다[cite: 28].
df2 = pd.concat([df2, s], axis=1) # df2와 s를 가로로 합침[cite: 29]
print("\nF소프트가 병합된 df2:\n", df2)


#%% [Sector 6] 데이터프레임 연산 및 행 추가 
# 12월 1일 시세에 60원씩 더해서 12월 7일 시세 만들기[cite: 29]
df3 = df2.iloc[0] + 60                      # 12월 1일 자 시세 추출 후 60 추가[cite: 29]
df3.name = pd.to_datetime('20181207')       # 해당 데이터의 이름을 12월 7일로 레이블 지정[cite: 29]


df2 = pd.concat([df2, df3.to_frame().T])    
print("\n12월 7일 데이터가 추가된 df2:\n", df2)

# 12월 1일 시세에 50원씩 더해서 12월 6일 시세 만들기[cite: 30]
df3_2 = df2.iloc[0] + 50                    # 12월 1일 자 시세 추출 후 50 추가[cite: 30]
df3_2.name = pd.to_datetime('20181206')     # 해당 데이터의 이름을 12월 6일로 레이블 지정[cite: 30]

#  pd.concat 사용[cite: 30]
df2 = pd.concat([df2, df3_2.to_frame().T])  
print("\n12월 6일 데이터가 추가된 df2 (날짜가 역전됨):\n", df2)

# [참고] 날짜(인덱스)가 7일 뒤에 6일이 와서 섞여 있으므로, 
# 데이터프레임.sort_index()를 사용해 정렬해야 한다고 책에서 언급하며 끝납니다[cite: 30].
# df2 = df2.sort_index()




#%% [Sector 1] 데이터프레임 정렬 및 특정 데이터 빼기
# 인덱스(날짜)를 기준으로 오름차순(과거->최신) 정렬합니다[cite: 31].
# axis=0은 행 방향을 의미하며, True(오름차순)가 기본값이므로 생략 가능합니다[cite: 31]

""" 
데이터프레임.sort_index(axis=0 or 1 , ascending = True)
axis= 0은 행방향, axis = 1은 열방향 TRue(기본값)이면 오름차순, 생략가능

데이터프레임이 인덱스를 재정렬
"""

df2 = df2.sort_index(axis=0)

# 행 삭제: 파이썬 내부에 저장된 값은 날짜 형식이므로, 문자열로 지정하면 에러가 납니다. 
# 반드시 pd.to_datetime()으로 날짜 형식을 지정해 빼주어야 합니다
# (참고: 별도로 결과를 저장하지 않으면 df2 원본에는 삭제 결과가 반영되지 않습니다)
"""
데이터프레임.drop(label, axis= 0 or 1
            
            
        해당 데이터 프레임에서 행 또는 열 삭제 """

df2.drop(pd.to_datetime('2018-12-06'))

# 여러 행을 동시에 삭제할 때는 대괄호 []를 이용해 묶어줍니다[cite: 32].
df2.drop([pd.to_datetime('2018-12-02'), pd.to_datetime('2018-12-06')])

# 열 삭제: axis=1로 지정하여 가로축 종목명을 기준으로 삭제합니다[cite: 32].
df2.drop('D엔터', axis=1)
df2.drop(['C금융', 'E텔레콤'], axis=1) # 여러 열 동시 삭제[cite: 33]


#%% [Sector 2] 데이터프레임 보간법(결측기 처리) (Images 33~35)
# 시세 정보가 없는 NaN(결측치) 데이터를 없애거나 다른 값으로 메웁니다[cite: 33].

# 1. NaN이 포함된 행을 통째로 싹 지워버립니다
df2.dropna()

# 2. NaN 값을 일괄적으로 0으로 대체합니다[cite: 34].
# 데이터프레임.fillna(대체값 또는 방법)
# 값이 아닌 method = ffill or bfill이면 앞 or 뒤 값으로 변경한다. 
df2.fillna(0)



# 3. 빈칸을 앞의 값으로 채우기 (Forward Fill)[cite: 34]
# 주가는 추가 거래가 없으면 전일 가격이 유지되므로 보통 이 방식을 사용합니다[cite: 34].
# (※ 책의 df2.fillna(method='ffill') 대신 최신 표준 코드 적용)
df2.ffill()

# 4. 빈칸을 뒤의 값으로 채우기 (Backward Fill)[cite: 35]
# 뒤에 오는 데이터가 더 중요한 경우 역방향으로 채워 넣습니다[cite: 35].
# (※ 책의 df2.fillna(method='bfill') 대신 최신 표준 코드 적용)
df2.bfill()


#%% [Sector 3] 엑셀 데이터 읽어오기 (Chapter 11 시작) (Images 36~38)
# 팬더스를 이용해 엑셀 파일에서 데이터를 읽어와 데이터프레임(df)에 저장합니다[cite: 36, 37].
# (실제 실행하려면 같은 폴더 안에 엑셀 파일이 있어야 합니다)

file_path = '09.2 KOSPI200 F 201712.xlsx' 
try:
    # sheet_name='Sheet1'을 지정하고, '일자' 칼럼을 인덱스로 불러옵니다[cite: 37].
    df = pd.read_excel(file_path, sheet_name='Sheet1', index_col='일자')

    # 엑셀에서 불러온 일자가 단순 문자 형식일 수 있으므로 날짜 형태(datetime)로 변환해 덮어씌웁니다[cite: 38].
    df.index = pd.to_datetime(df.index)
    
    print("\n엑셀 데이터 인덱스 타입 확인:", type(df.index)) # DatetimeIndex로 잘 변환되었는지 확인[cite: 38]
except FileNotFoundError:
    print(f"'{file_path}' 파일이 없어 엑셀 불러오기를 건너뜁니다.")


#%% [Sector 4] 금융공학: KOSPI200 선물 이론가 산출 (연속복리 모델) (Images 39~40)
# 선물 이론가 공식: F = S * e^((r-d)*t)[cite: 39]
# (S: 현물가격, r: 이자율, d: 배당률, t: 잔존만기)[cite: 39]

# 잔존만기를 계산할 때 휴일을 제외한 '영업일'만 구하기 위해 넘파이의 np.busday_count를 이용합니다[cite: 39].
def futures_price(S, r, d, T, t0):
    # 금융공학에서는 1년을 보통 252일로 계산하므로 남은 날짜 수를 252로 나눕니다[cite: 39].
    # (최신 버전에 맞춰 .date()를 붙여 오류를 방지했습니다)
    t = np.busday_count(t0.date(), T.date()) / 252  # busday는 휴일을 제외한 날짜를 불러오는 것을 의미함. 
    F = S * np.exp((r - d) * t)   # 자연지수는 np.exp()를 사용합니다[cite: 39].
    return F

T = pd.to_datetime('2017-12-14')  # 2017년 12월 만기 상품의 최종거래일[cite: 39]
r = 0.0225                        # 이자율 2.25%[cite: 39]
d = 0.015                         # 배당률 1.5%[cite: 39]

# 위 Sector 3에서 엑셀 데이터(df)를 성공적으로 불러왔다면 아래 연산을 수행합니다.
if 'df' in locals() and not df.empty:
    for n in df.index:
        t0 = n                    # 기준일자[cite: 39]
        S = df.loc[n, '지수']       # 해당 일자의 현물 지수[cite: 39]
        F = futures_price(S, r, d, T, t0)
        
        # 가독성을 위해 천의 자리마다 쉼표(,)를 찍고 소수점 아래 두 자리까지 표시하도록 포매팅합니다[cite: 40].
        f_formatted = '{:,.2f}'.format(F)
        
        # '이론가1'이라는 새로운 칼럼을 만들어 값을 추가합니다[cite: 40].
        df.loc[n, '이론가1'] = f_formatted  


#%% 보급형 공식을 이용한 선물 이론가 산출 (단리 모델) (Image 40)
# 단순 보급형 공식: F = S * [1 + (r-d) * (t / 365)][cite: 40]

def S_futures_price(S, r, d, T, t0):
    # 연속복리와 달리 단순형은 1년을 365일로 잡으므로, 주말을 포함한 일수를 구하는 .days를 사용합니다[cite: 40].
    t = (T - t0).days / 365
    F = S * (1 + (r - d) * t)
    return F

import pandas as pd
import numpy as np

#%% [Sector 1] 보급형 공식을 이용한 선물 이론가 계산 마무리 (Image 41)
# (이전 채팅의 df와 S_futures_price 함수가 메모리에 있다고 가정합니다)
'''
d = 0.015 # 배당률[cite: 41]
for n in df.index:
    t0 = n
    S = df.loc[n, '지수']
    F = S_futures_price(S, r, d, T, t0)  # 단리 보급형 함수 호출[cite: 41]
    f = '{:,.2f}'.format(F)              # 이론가 숫자 포매팅[cite: 41]
    df.loc[n, '이론가2'] = f               # '이론가2' 칼럼에 값 추가[cite: 41]

print(df) # 결과 출력[cite: 41]
'''


#%% [Sector 2] 엑셀에서 WTI 현물, 최근월물, 차근월물 데이터 읽어오기 (Images 42~43)
# WTI(서부 텍사스 중질유) 데이터를 바탕으로 롤오버 비용이 손익에 미치는 영향을 모델링합니다[cite: 42].
# 최근월물(Front): 만기를 앞두고 있는 선물[cite: 42].
# 차근월물(Second): 다음 주기에 만기가 도래할 선물[cite: 42].

# 엑셀 파일의 각 시트('Spot', 'Front', 'Second')에서 데이터를 불러오고 Date를 인덱스로 지정합니다[cite: 43].
# (실제 실행 시 '11.2 WTI.xlsx' 파일이 폴더에 있어야 합니다)
try:
    df1 = pd.read_excel('11.2 WTI.xlsx', sheet_name='Spot', index_col='Date')
    df2 = pd.read_excel('11.2 WTI.xlsx', sheet_name='Front', index_col='Date')
    df3 = pd.read_excel('11.2 WTI.xlsx', sheet_name='Second', index_col='Date')
    
    # 3개의 데이터프레임을 하나로 합칩니다 (axis=1은 가로로 병합)[cite: 43].
    df_wti = pd.concat([df1, df2, df3], axis=1)
    
    # 데이터에 구멍(NaN)이 난 곳을 메우는 보간법 수행 (최신 표준 메서드 적용)[cite: 43]
    df_wti = df_wti.ffill()  # 앞의 데이터를 가져와 덮어씀 (method='ffill' 대체)[cite: 43]
    df_wti = df_wti.bfill()  # 뒤의 데이터를 가져와 덮어씀 (method='bfill' 대체)[cite: 43]
    
    print("\nWTI 병합 데이터(df_wti) 꼬리부분 확인:\n", df_wti.tail())
except FileNotFoundError:
    print("'11.2 WTI.xlsx' 파일이 없어 WTI 데이터 불러오기를 건너뜁니다.")


#%% [Sector 3] 엑셀에서 WTI 만기일 정보 읽어오기 및 처리 (Images 44~45)
# 롤오버는 대체로 만기일에 가까워지면 시행하므로 만기일 정보가 필요합니다[cite: 44].
try:
    # 'Expiry' 시트에서 만기일 정보를 불러옵니다[cite: 44].
    df_e = pd.read_excel('11.2 WTI.xlsx', sheet_name='Expiry')
    
    # 필요한 'Last Trade'(최종거래일) 열만 추출[cite: 44]
    # 문자열로 되어 있을 수 있으므로 날짜 형식(datetime)으로 변환 후 시리즈로 저장합니다[cite: 44, 45].
    expiry = pd.Series(pd.to_datetime(df_e['Last Trade']))
    print("\n만기일 정보(expiry) 확인:\n", expiry.head())
except FileNotFoundError:
    pass


#%% [Sector 4] 시세 데이터프레임에 최종거래일 표시하기 (Image 46)
# 롤오버 거래(최근월물 매도, 차근월물 매수)가 일어나는 최종거래일을 시세 데이터에 표시합니다[cite: 46].

if 'df_wti' in locals() and 'expiry' in locals():
    # 1. 만기를 뜻하는 Expiry 칼럼을 만들고 초기값으로 NaN을 입력합니다[cite: 46].
    df_wti['Expiry'] = np.nan
    
    # 2. Trading day 중 만기일을 찾아서 1로 표시합니다[cite: 46].
    for d in df_wti.index:
        # Date 값을 하나씩 읽어와서 expiry 시리즈에 같은 값이 있는지 확인[cite: 46]
        if d in pd.to_datetime(expiry.values): 
            df_wti.loc[d, 'Expiry'] = 1  # 만기일이면 1 표시[cite: 46]
            
    print("\n만기일이 표시된 데이터(df_wti) 일부:\n", df_wti[5:10])


#%% [Sector 5] 손익 계산: 현물에 투자했을 경우 (Image 46)
# 현물은 만기라는 개념 없이 팔지 않으면 계속 들고 가는 상품이므로 단순히 (현재가 - 매입가)로 계산합니다[cite: 46].

if 'df_wti' in locals() and not df_wti.empty:
    try:
        # 2017년 12월 28일 현물 현재가격[cite: 46]
        price_now = float(df_wti.loc['2017-12-28', 'Spot']) 
        # 2010년 1월 4일 현물 초기가격[cite: 46]
        price_before = float(df_wti.loc['2010-01-04', 'Spot']) 
        
        profit = (price_now - price_before) * 1000
        print("\n손익 (현재가격 - 초기가격): '{:,.2f}'".format(profit))
    except KeyError:
        print("현물 손익 계산: 지정된 날짜의 데이터가 없습니다.")


#%% [Sector 6] 손익 계산: 선물에 투자했을 경우 (롤오버 비용 반영) (Image 47)
# 선물은 매달 만기가 있어 롤오버를 해야 하며, 이때 차근월물 가격 - 최근월물 가격 만큼의 비용이 발생합니다[cite: 47].

if 'df_wti' in locals() and not df_wti.empty:
    try:
        roll_over_cost_acc = 0  # 롤오버 비용 누적값 초기화[cite: 47]
        
        # 일자별로 순환하며 최종거래일(Expiry==1)이면 롤오버 비용을 계산하여 누적합니다[cite: 47].
        for d in df_wti.index:
            if df_wti.loc[d, 'Expiry'] == 1:
                # 롤오버 비용 = 차근월물 가격(Second) - 최근월물 가격(Front)[cite: 47]
                roll_over_cost = df_wti.loc[d, 'Second'] - df_wti.loc[d, 'Front']
                roll_over_cost_acc = roll_over_cost_acc + roll_over_cost # 누적[cite: 47]
                
        print("\n누적 롤오버 비용: '{:,.2f}'".format(roll_over_cost_acc))
        
        # 롤오버 비용을 반영한 선물 손익 계산[cite: 47]
        price_now_f = float(df_wti.loc['2017-12-28', 'Front'])   # 선물 현재가[cite: 47]
        price_before_f = float(df_wti.loc['2017-12-28', 'Front'])# 책 오타로 추정됨 (보통 '2010-01-04'이어야 하지만 책 코드대로 작성)[cite: 47]
        
        # 책 원본 코드 기준: profit = (price_now - price_before - roll_over_cost_acc) * 1000[cite: 47]
        # (주의: 책의 2행 코드가 price_before = float(df['2017-12-28']['Front'])로 2017년으로 잘못 적혀 있는 것으로 보입니다. 
        # 논리상 2010-01-04가 맞지만 책의 코드 흐름을 그대로 남깁니다.)
        
        # 수정된 논리를 적용하려면 아래 주석을 해제하고 사용하세요.
        # price_before_f = float(df_wti.loc['2010-01-04', 'Front']) 
        
        profit_f = (price_now_f - price_before_f - roll_over_cost_acc) * 1000
        print("누적 손익: '{:,.2f}'".format(profit_f))
        
    except KeyError:
        print("선물 손익 계산: 지정된 날짜의 데이터가 없습니다.")