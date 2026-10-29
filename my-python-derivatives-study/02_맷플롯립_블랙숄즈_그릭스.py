#%% 맷플롯립 라이브러리 호출 및 기본 그래프 출력 
# 맷플롯립(matplotlib)은 파이썬의 대표적인 그래프 전문 라이브러리입니다.
import matplotlib.pyplot as plt

# 주피터 노트북 환경에서는 그래프를 결과 화면(라인 사이)에 바로 출력하기 위해 아래 명령어를 추가해야 합니다.
# (노트북이 아닌 일반 .py 파일로 실행할 때는 새로운 창이 뜨면서 그래프가 보입니다)
# %matplotlib inline

# 내용이 없는 빈 그래프 틀 출력 plt.plot()

# 그래프 사이즈 조절: plt.figure(figsize=(가로, 세로))
# 사이즈 조절을 별도로 하지 않은 기본 사이즈는 6x4 입니다.
plt.figure(figsize=(10, 5)) # 10x5 사이즈의 그래프 껍데기 설정
plt.plot()


#%% [Sector 2] 넘파이를 활용한 데이터 생성 및 그래프 그리기 (Images 50~52)
import numpy as np

# 1. X축 데이터 생성
# np.arange(시작, 끝, 간격): 시작과 끝 사이를 일정한 간격으로 채운 배열을 반환합니다.
x = np.arange(100, 300, 10) # 100부터 300 직전까지 10 간격으로 총 20개의 값 생성

# 2. Y축 데이터 생성
# np.random.randn(n): 표준정규분포(평균 0, 표준편차 1)를 따르는 임의의 난수를 n개 반환합니다.
# 주의: 그래프를 그릴 때 x의 개수와 y의 개수가 같지 않으면 에러가 발생하므로 동일하게 20개로 맞춥니다.
y = np.random.randn(20) 

# 3. 그래프 그리기
# X축 값을 생략하고 plt.plot(y)만 입력하면 X축은 0부터 시작해서 데이터 개수만큼 자동으로 출력됩니다.
# 틀 사이즈를 (10, 5)로 조절한 후 x, y를 지정해서 그래프 그리기
plt.figure(figsize=(10, 5)) 
plt.plot(x, y)

#%%
plt.plot(y)

#%% [Sector 3] rcParams를 이용한 전역 파라미터 설정 (Image 53)
"""
그래프를 그릴 때마다 plt.figure()로 사이즈를 지정하기 귀찮다면, 
rc라는 파라미터를 미리 세팅해 놓으면 프로그램 전역에 해당 값이 적용되어 편리합니다.
세팅 가능한 파라미터는 약 300가지 정도이며, plt.rcParams를 입력해 전체 리스트를 확인할 수 있습니다.
"""
# 그래프 기본 사이즈를 10x5로 전역 설정
plt.rcParams['figure.figsize'] = (10, 5)

# 이제 별도의 사이즈 지정 없이(plt.figure 생략) 바로 plot을 해도 크게 출력됩니다.
# plt.plot(x, y)

#%%
plt.rcParams

#%% [Sector 4] 그래프 모양 설정하기 (색상, 선, 마커) (Images 54~55)
"""
plt.plot() 안에 속성값으로 그래프의 색상(color), 선 모양(linestyle), 데이터 점 표시(marker)를 지정할 수 있습니다.
- 색상(color): 'r'(red), 'b'(blue), 'g'(green), 'k'(black), 'w'(white), 'c'(cyan), 'm'(magenta), 'y'(yellow)
- 선 모양(linestyle): '-'(실선), '--'(점선), '-.'(일점쇄선), ':'(점선)
- 마커(marker): 'o'(원), '*'(별), '^'(삼각형), 's'(사각형) 등 다양함
"""

# 색상은 빨강, 모양은 점선, 마커는 동그라미로 지정
plt.plot(x, y, color='r', linestyle='--', marker='o')

# (참고) 자주 사용하는 옵션은 'ro--' 처럼 짧게 축약형으로 나타낼 수도 있습니다 (r=빨강, o=원, --=점선).
# plt.plot(x, y, 'ro--') 

# 기타 꾸미기 속성들:
# markersize (마커 크기), markerfacecolor (마커 내부 색), markeredgecolor (마커 테두리 색), alpha (투명도, 0~1)


#%% [Sector 5] 제목 추가 및 한글 폰트 깨짐 해결 (Images 56~57)
# 제목 삽입은 plt.title('제목')을 사용합니다.
# 하지만 맷플롯립의 기본 폰트가 영어 전용이라 그대로 쓰면 한글이 네모 폰트로 깨져 보입니다.

# [해결책] rcParams를 이용해 한글 폰트와 마이너스 기호 설정을 미리 세팅합니다.
plt.rcParams['font.family'] = 'Malgun Gothic'  # 윈도우 맑은 고딕 기준 (맥은 AppleGothic 등)
plt.rcParams['font.size'] = 12                 # 기본 폰트 크기 설정
plt.rcParams['axes.unicode_minus'] = False     # 폰트 변경 시 마이너스(-) 기호가 깨지는 것을 방지

"""
(참고) 내 컴퓨터에서 사용 가능한 맷플롯립 폰트 리스트 조회 방법:
from matplotlib import font_manager
font_list = set([f.name for f in font_manager.fontManager.ttflist])
print(font_list)
-> 여기서 나온 폰트명 중 하나를 골라 'font.family'에 넣어주면 됩니다.
"""

# 한글 세팅 완료 후 그래프 다시 그리기
# 색상=자주색, 선=점선, 마커=별모양, 마커사이즈=20
plt.plot(x, y, color='m', linestyle=':', marker='*', markersize=20)
plt.title('앙앙') # 이제 한글이 정상적으로 출력됩니다.

#%% [Sector 1] 그래프 꾸미기 심화 (그리드, 폰트 딕셔너리, 범례) (Images 58~61)
# 1. 그리드(격자) 추가하기: 더 읽기 쉬운 그래프를 만들기 위해 plt.grid(True)를 사용합니다.
# plt.grid(True)

# 2. 제목, 축 레이블마다 각각 다른 폰트 적용하기
# 폰트 속성(family, color, weight, size)을 딕셔너리 형태로 묶어 변수에 저장합니다.
# 주의: 내 PC에 설치된 폰트명을 정확히 기재해야 하며, 없으면 에러가 납니다.
font_title = {'family': 'Malgun Gothic', 'color': 'black', 'weight': 'bold', 'size': 20} # 책의 Nanum Brush Script 대체
font_label = {'family': 'Malgun Gothic', 'color': 'black', 'weight': 'regular', 'size': 15}# 책의 Nanum Pen Script 대체

# 3. 그래프 그리고 꼬리표(Label) 달기
# 여러 그래프를 겹쳐 그릴 때 구분을 위해 plt.plot() 안에 label='이름'을 지정합니다.
plt.figure(figsize=(10, 5))
# 첫 번째 선 그래프 (자주색 점선, 별마커)
plt.plot(x, y, color='m', linestyle=':', marker='*', markersize=20, label='그래프1') 
# 두 번째 선 그래프 (오렌지색 실선)
plt.plot(x, y+1, color='orange', linestyle='-', label='그래프2') 

# 4. 꾸미기 적용 요소들
plt.title('제목', fontdict=font_title)              # 제목 지정 및 폰트 적용
plt.xlabel('X값(독립변수)', fontdict=font_label)    # X축 레이블 지정
plt.ylabel('Y값(종속변수)', fontdict=font_label)    # Y축 레이블 지정
plt.grid(True)                                      # 격자 추가

# 5. 범례(Legend) 표시
# 앞서 설정한 label 정보를 바탕으로 범례 박스를 생성합니다.
# loc='best'로 지정하면 컴퓨터가 알아서 데이터와 겹치지 않는 가장 좋은 위치에 표시합니다.
plt.legend(loc='best') 
plt.show()


#%% [Sector 2] 여러 개의 그래프를 한 번에 모아서 보여주기 (Images 61~63)
# 큰 껍데기(figure)를 분할하여 여러 그래프(subplot)를 배치하는 방법입니다.

"""
# 방법 1: add_subplot(행, 열, 순서) 사용하기
fig = plt.figure(figsize=(16, 10))
ax1 = fig.add_subplot(2, 3, 1) # 2행 3열 껍데기 중 1번째 자리
ax1.plot(x, y)                 # 1번 자리에 선 그래프

ax2 = fig.add_subplot(2, 3, 2) # 2번째 자리
ax2.hist(y)                    # 히스토그램

ax3 = fig.add_subplot(2, 3, 3) # 3번째 자리
ax3.scatter(x, y)              # 산점도

ax4 = fig.add_subplot(2, 3, 4) # 4번째 자리
ax4.plot(x, y, color='r', linestyle='--')
# 5번, 6번 자리는 할당하지 않았으므로 빈 공간으로 남습니다.
"""

# 방법 2: plt.subplots(행, 열)을 사용하여 배열로 접근하기 (더 권장되는 방식)
# fig는 전체 껍데기, axes는 2x3 배열 형태의 각 subplot 주소를 가리키게 됩니다.
fig, axes = plt.subplots(2, 3, figsize=(16, 10))

axes[0, 0].plot(y)           # 1행 1열 위치에 그래프 그림
axes[0, 1].hist(y)           # 1행 2열 위치
axes[0, 2].scatter(x, y)     # 1행 3열 위치
axes[1, 0].plot(y, 'g--')    # 2행 1열 위치에 초록색 점선 그래프
plt.show()


#%% [Sector 3] Pandas와 맷플롯립의 연동 (가상 주가 데이터 생성 및 기본 선 그래프) (Images 63~64)
import pandas as pd
import numpy as np

# 1. 30일간 3개 종목의 주가 가상 데이터 생성
# 평균이 1000, 표준편차가 100인 난수 매트릭스를 (30, 3) 형태로 생성합니다.
random_data = np.random.randn(30, 3) * 100 + 1000 
# 인덱스는 2018년 9월 1일부터 30일간의 날짜('D': 일단위)
date_idx = pd.date_range(start='2018-09-01', periods=30, freq='D')
# 컬럼명은 3개 기업 이름으로 설정
col_names = ['천리마마트', '히드라마트', '터렛마트']

df_stock = pd.DataFrame(random_data, index=date_idx, columns=col_names)

# 2. Pandas 내장 plot 기능으로 선 그래프 그리기
# 팬더스는 맷플롯립과 결합하여 복잡한 차트를 .plot() 메서드로 아주 쉽게 그려냅니다.
df_stock.plot.line() 
plt.show()


#%% [Sector 4] Pandas 막대 그래프 (기본, 누적, 수평) (Images 64~66)
# 1. 기본 수직 막대 그래프 그리기
# 9월 1일부터 5일까지 데이터만 추출하여 그립니다.
df_stock[:5].plot.bar() 

# X축이 시간까지 표시되어 너무 길고 거슬리므로, 인덱스에서 날짜(.date) 부분만 잘라내어 X축 값으로 지정합니다.
df_stock[:5].plot.bar(x=df_stock[:5].index.date)
plt.show()

# 2. 수직 누적 막대 그래프 (Stacked Bar)
# 인수 stacked=True를 넣어주면 막대들이 합쳐져서 쌓인 형태로 그려집니다.
df_stock[:5].plot.bar(x=df_stock[:5].index.date, stacked=True)
plt.title("수직 누적 막대")
plt.show()

# 3. 수평 누적 막대 그래프 (Horizontal Stacked Bar)
# bar 대신 barh()를 사용하면 수평 방향으로 표시됩니다.
df_stock[:5].plot.barh(x=df_stock[:5].index.date, stacked=True)
plt.title("수평 누적 막대")
plt.show()


#%% [Sector 5] 데이터 분포를 보는 히스토그램 (Image 67)
# 어느 영역에 데이터가 많이 분포하는지 파악할 때 사용합니다.
# 구간 사이즈(bins)를 지정해주면 그 사이즈에 맞게 데이터를 나누어 개수를 헤아립니다.
# alpha는 투명도(0=투명, 1=불투명)로, 데이터가 겹쳐 보일 수 있도록 1보다 작게 0.5로 설정했습니다.
df_stock.plot.hist(bins=20, grid=True, alpha=0.5) 
plt.title("주가 분포 히스토그램")
plt.show()

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#%% [Sector 1] 여러 가지 그래프 그리기 (원, 밀도, 박스, 산포도) (Images 68~70)

"""
1. 원그래프 (Pie Chart)
특정 시점의 데이터 값 크기를 비교할 때 유용합니다. (예: 특정 일자의 시가총액 비교)
autopct='% .2f' 인수를 전달하면 자동으로 비율을 계산해 소수점 둘째 자리까지 표시합니다.
"""
# df의 첫 번째 행(0번 인덱스) 데이터를 파이 차트로 그리기
# df.iloc[0].plot.pie(figsize=(6, 6), autopct='%.2f')
# plt.show()

"""
2. 밀도 그래프 (KDE: Kernel Density Estimation)
데이터 값이 어떤 모양으로 분포되어 있는지(밀집도)를 알아보기 위해 사용합니다.
"""
# df.plot.kde()
# plt.show()

"""
3. 박스 그래프 (Box Plot)
통계치를 그래프와 함께 보여줍니다.
박스의 맨 위에서부터 각각 가로줄이 '최댓값, 상위 25%값, 중간값, 하위 25%값, 최솟값'을 의미합니다.
"""
# df.plot.box()
# plt.show()

"""
4. 산포도 (Scatter Plot)
X값과 Y값의 관계를 알아볼 때 사용하며, 회귀분석 시 두 변수 간의 추세선을 그리기 전 관계를 파악하는 데 도움이 됩니다.
"""
# df.plot.scatter(x='히드라마트', y='천리마마트', figsize=(5, 5))
# plt.show()


#%% [Sector 2] 3D 막대 그래프 그리기 (Images 71~72)
"""
3D 그래프를 그리기 위해서는 맷플롯립의 추가 기능인 mplot3d 라이브러리를 호출해야 합니다.
"""
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure(figsize=(8, 6)) # 그래프 틀 설정

# projection='3d'라고 명시하여 3D 그래프를 그릴 것임을 선언하고 서브플롯을 ax에 할당합니다.
ax = fig.add_subplot(111, projection='3d') 

# X축은 기간, Y축은 종목, Z축은 가격을 나타냅니다.
# 파이썬은 문자를 기준으로 3D 그래프를 그리지 못하므로, zip을 이용해 각 종목(문자)에 임의의 숫자 1, 2, 3을 부여해 묶어줍니다.
# (※ 테스트를 위해 임의의 df가 있다고 가정)
# for z, n in zip([1, 2, 3], df.columns):
#     left = df[n].index       # X축 (값)
#     height = df[n].values    # Z축 (높이값)
#     zs = z                   # Y축 (데이터 구분, 1/2/3)
#     
#     # zdir='y'는 어느 방향으로 데이터를 움직여 그릴지 지정합니다.
#     # alpha=0.8은 1(불투명)과 0(투명) 사이의 반투명도를 지정합니다.
#     ax.bar(left, height, zs, zdir='y', alpha=0.8) 

# 축 이름 및 범례 삽입
# ax.set_xlabel('날짜') 
# ax.set_ylabel('종목')
# ax.set_zlabel('가격')
# ax.legend(df.columns)
# plt.show()


#%% [Sector 3] 3D 입체 평면 (Surface) 그리기 (Images 73~74)
"""
입체 평면을 그릴 때는 선이 아니라 면을 그리는 것이므로, X, Y 값을 1x1 형태의 점이 아니라 매트릭스 형태로 넣어줘야 합니다.
이를 위해 np.meshgrid()를 사용하여 X, Y 범위를 섞어 매트릭스 형태로 반환합니다.
"""
from matplotlib import cm # 컬러맵: 맷플롯립이 미리 만들어둔 색 조합 편의 기능

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

# X축, Y축 범위 지정
X = np.arange(0, 20, 1) 
Y = np.arange(-10, 10, 1) 

# X, Y를 매트릭스로 변환
X, Y = np.meshgrid(X, Y) 

# 매트릭스 각 점마다 Z값 계산 (예제용 임의 수식)
Z = (X**2) + (Y**2) 

# 입체 평면 그리기 (ax.plot_surface)
# cmap=cm.summer (색상 톤 지정), linewidth=1 (선 두께), alpha=0.8 (투명도)
surf = ax.plot_surface(X, Y, Z, cmap=cm.summer, linewidth=1, alpha=0.8) 

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

# 평면과 컬러바를 연결하여 화면에 표시
fig.colorbar(surf, shrink=0.5, aspect=5) 
# plt.show()


#%% [Sector 4] Chapter 15. 파이썬으로 구현하는 블랙-숄즈 모형 (Images 75~77)
"""
블랙-숄즈 방정식에는 표준정규분포, 제곱근, 로그, 지수함수 등이 포함됩니다.
이를 계산하기 위해 scipy(과학, 통계 관련 기능)와 numpy(수학 연산) 라이브러리를 호출합니다.
"""
import scipy.stats as stats # 표준정규분포 누적밀도함수(N) 구현에 사용

# 1. 잔존만기 계산 함수
# 정규 거래소 금융상품은 공휴일을 제외한 252일을 1년으로 봅니다 (잔존만기는 1년을 꽉 채우면 1).
# (※ 이전과 마찬가지로 np.busday_count 에러를 방지하기 위해 .date() 처리를 추가하는 것이 좋습니다)
def time_to_maturity(t0, T, y=252):
    t0 = pd.to_datetime(t0) # 문자열을 날짜 형식으로 변환
    T = pd.to_datetime(T)
    # np.busday_count를 이용해 평일(weekday)만 카운트한 뒤 1년 기준 날짜 수인 y로 나눔
    return (np.busday_count(t0.date(), T.date()) / y) 

print("잔존만기 예시:", time_to_maturity('2018-8-1', '2018-12-14')) # 결과: 약 0.385


# 2. 블랙-숄즈 방정식을 이용한 콜옵션 가격 구하기 함수
def call_price(S, K, ttm, r, sigma):
    """
    S: 기초자산 가격, K: 행사가격, ttm: 잔존만기, r: 이자율, sigma: 변동성
    """
    # d1, d2 계산 (로그, 제곱근 활용)
    d1 = (np.log(S / K) + (r + sigma**2 * 0.5) * ttm) / (sigma * np.sqrt(ttm))
    d2 = (np.log(S / K) + (r - sigma**2 * 0.5) * ttm) / (sigma * np.sqrt(ttm))
    # 참고: d2 = d1 - sigma * np.sqrt(ttm) 도 같은 수식입니다.
    
    # 옵션 가격 계산 (stats.norm.cdf를 이용해 표준정규분포 누적밀도함수 계산)
    val = (S * stats.norm.cdf(d1, 0.0, 1.0)) - K * np.exp(-r * ttm) * stats.norm.cdf(d2, 0.0, 1.0)
    
    return val # 계산한 옵션가격 반환

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import scipy.stats as stats


# 테스트를 위해 변수 세팅
ttm = 0.3849 # time_to_maturity('2018-9-1', '2018-12-14')의 결과값 가정
r = 0.025    # 이자율
sigma = 0.15 # 변동성

# 기초자산과 행사가격이 모두 350일 때의 콜옵션 가격 계산 확인
# print(call_price(350, 350, ttm, r, sigma))


#%% [Sector 1] 기초자산 및 행사가격 변화에 따른 콜옵션 가격 계산 (Images 78~80)
"""
기초자산(S)과 행사가격(K)이 변할 때 옵션 가격이 어떻게 변하는지 확인하기 위해 
for 반복문을 사용하여 값들을 계산하고 데이터프레임으로 만듭니다.
"""
call_space = dict()
K = np.arange(250, 350, 10) # 행사가격 구간: 250~340 (350 미포함)
S = np.arange(200, 400, 10) # 기초자산 가격 구간: 200~390 (400 미포함)

for k in K:
    single_space = dict()
    for s in S:
        # 행사가격이 k, 기초자산 가격이 s일 때의 콜옵션 가격을 계산하여 저장
        single_space[s] = call_price(s, k, ttm, r, sigma)
    # k값에 대한 시리즈로 변환하여 딕셔너리에 저장
    call_space[k] = pd.Series(single_space)

# 가독성을 높이기 위해 딕셔너리를 데이터프레임으로 변환합니다.
df_call_space = pd.DataFrame(call_space)
print("콜옵션 가격 데이터프레임 일부:\n", df_call_space.head())


#%% [Sector 2] 행사가별 콜옵션 가격 2D 그래프 그리기 (Images 80~81)
"""
앞서 구한 데이터프레임을 이용해 행사가격(K)이 290, 300, 310일 때의 
기초자산 가격 변화에 따른 콜옵션 가격을 선 그래프로 그립니다.
행사가격이 낮아질수록 콜옵션이 행사될 확률이 높아지므로 가격이 더 높게 형성됩니다.
"""
# 한글 사용 세팅
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.unicode_minus'] = False

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

# 특정 행사가격(K) 열만 추출하여 선 그래프 그리기
ax.plot(df_call_space[290], label='k=290')
ax.plot(df_call_space[300], label='k=300')
ax.plot(df_call_space[310], label='k=310')

ax.set_xlabel('기초자산(Underlying)')
ax.set_ylabel('콜옵션가격(Call Price)')
ax.set_title('행사가별 옵션가격')
ax.legend(loc='best')
plt.show()


#%% [Sector 3] 배열 연산을 이용한 원샷 계산 및 3D 그래프의 실패 사례 (Images 82~84)
"""
for 반복문 대신 넘파이 배열을 직접 함수에 넣어 한 번에 계산(원샷)해보려는 시도입니다.
하지만 S(20개)와 K(10개)의 원소 개수가 다르면 'ValueError: operands could not be broadcast together' 에러가 발생합니다.

개수를 둘 다 20개로 맞추면(K 간격을 5로 변경) 계산은 되지만, 
이 데이터로 3D 그래프(plot)를 그리면 곡면(면)이 아니라 단순한 1차원 선(선분)이 그려지게 됩니다.
K와 S 값을 매트릭스(행렬) 형태로 입력하지 않았기 때문입니다.
"""
K = np.arange(250, 350, 5)  # 개수를 20개로 맞춤
S = np.arange(200, 400, 10) # 개수 20개

# Z = call_price(S, K, ttm, r, sigma) 
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')
# ax.plot(S, K, Z) # <-- 면이 아니라 선이 그려짐 (책의 시행착오 부분)


#%% [Sector 4] 콜옵션 가격 3D 곡면(Surface) 올바르게 그리기 (Images 85~86)
"""
선이 아닌 입체적인 '면(Surface)'으로 그래프를 그리려면, np.meshgrid()를 사용하여 
모든 K값과 모든 S값이 교차하는 매트릭스(그물망)를 만들어주어야 합니다.
"""
K = np.arange(250, 350, 5)
S = np.arange(200, 400, 10)

# K, S를 2차원 매트릭스 형태로 변환 (핵심!)
K, S = np.meshgrid(K, S) 
Z = call_price(S, K, ttm, r, sigma) # 매트릭스 데이터를 바탕으로 Z값 계산

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# ax.plot() 대신 ax.plot_surface()를 사용합니다.
surf = ax.plot_surface(S, K, Z, cmap=cm.summer, linewidth=1, antialiased=True, alpha=0.8)

ax.set_xlabel('기초자산(Underlying)')
ax.set_ylabel('행사가격(Strike)')
ax.set_zlabel('콜옵션가격(Call Price)')
ax.set_title('콜옵션 가격 곡면')
fig.colorbar(surf, shrink=0.5, aspect=5)
plt.show()
# 결과 해석: 기초자산 가격이 높을수록, 행사가격이 낮을수록 콜옵션 가격이 높아지는 곡면이 그려집니다.


#%% [Sector 5] 풋옵션 가격 산출 및 3D 곡면 그리기 (Images 86~87)
"""
풋옵션(Put Option) 가격을 구하는 블랙-숄즈 공식을 함수로 정의하고 3D 곡면을 그립니다.
수식: P = K * e^(-rt) * N(-d2) - S * N(-d1)
"""
def put_price(S, K, ttm, r, sigma):
    # d1, d2 계산 (콜옵션과 동일)
    d1 = (np.log(S / K) + (r + sigma**2 * 0.5) * ttm) / (sigma * np.sqrt(ttm))
    d2 = (np.log(S / K) + (r - sigma**2 * 0.5) * ttm) / (sigma * np.sqrt(ttm))
    
    # 풋옵션 공식 적용 (콜옵션과 부호 및 위치가 다름에 주의)
    val = K * np.exp(-r * ttm) * stats.norm.cdf(-d2, 0.0, 1.0) - (S * stats.norm.cdf(-d1, 0.0, 1.0))
    return val

# 풋옵션 3D 곡면 그리기
K = np.arange(250, 350, 5)
S = np.arange(200, 400, 10)
K, S = np.meshgrid(K, S) # 매트릭스 변환

Z_put = put_price(S, K, ttm, r, sigma) # 풋옵션 가격 계산

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

surf_put = ax.plot_surface(S, K, Z_put, cmap=cm.winter, linewidth=1, antialiased=True, alpha=0.8)

ax.set_xlabel('기초자산(Underlying)')
ax.set_ylabel('행사가격(Strike)')
ax.set_zlabel('풋옵션가격(Put Price)')
ax.set_title('풋옵션 가격 곡면')
fig.colorbar(surf_put, shrink=0.5, aspect=5)
plt.show()

import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import re

# 한글 폰트 세팅 (앞선 설정과 동일)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

#%% [Sector 1] 옵션 그릭스 1: 델타(Delta) 3D 곡면 (Images 88~89)
"""
델타(Delta)는 기초자산 가격 변화에 따른 콜옵션 가격의 변화율입니다.
- 콜옵션 델타 공식: N(d1)
- 잔존만기, 이자율, 변동성 등은 고정하고 기초자산(S)과 행사가격(K)의 변화를 봅니다.
"""
def call_delta(S, K, ttm, r, sigma):
    d1 = (np.log(S / K) + (r + sigma**2 * 0.5) * ttm) / (sigma * np.sqrt(ttm))
    val = stats.norm.cdf(d1, 0.0, 1.0)
    return val

K = np.arange(300, 350, 5)
S = np.arange(200, 400, 10)
K, S = np.meshgrid(K, S)
Z_delta = call_delta(S, K, 0.38, 0.02, 0.30)

# 델타 곡면 그래프 그리기
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(S, K, Z_delta, cmap=cm.coolwarm, linewidth=1, antialiased=True, alpha=0.8)
ax.set_xlabel('기초자산(Underlying)'); ax.set_ylabel('행사가격(Strike)'); ax.set_zlabel('델타(Delta)')
ax.set_title('델타 곡면')
fig.colorbar(surf, shrink=0.5, aspect=5)
plt.show()
# 해석: 기초자산 가격이 높아질수록 델타가 1에 가까워지는 것을 확인할 수 있습니다.


#%% [Sector 2] 옵션 그릭스 2: 감마(Gamma) 3D 곡면 (Images 90~91)
"""
감마(Gamma)는 기초자산 가격 변화에 따른 '델타'의 변화율입니다.
- 콜과 풋의 공식이 동일하므로 하나의 함수로 정의합니다.
- 공식 내 N'(d1)을 구하기 위해 확률밀도함수(PDF)를 반환하는 ndx(x) 함수를 먼저 만듭니다.
"""
def ndx(x):
    # N'(x) = (1 / sqrt(2*pi)) * e^(-x^2 / 2)
    return (np.exp(-1 * x**2 * 0.5) / np.sqrt(2 * np.pi))

def gamma(S, K, ttm, r, sigma):
    d1 = (np.log(S / K) + (r + sigma**2 * 0.5) * ttm) / (sigma * np.sqrt(ttm))
    val = (ndx(d1)) / (S * sigma * np.sqrt(ttm))
    return val

K_gamma = np.arange(300, 305) 
S_gamma = np.arange(200, 400, 10)
K_gamma, S_gamma = np.meshgrid(K_gamma, S_gamma)
Z_gamma = gamma(S_gamma, K_gamma, 0.38, 0.02, 0.30)
# 해석: 등가격(기초자산 가격과 행사가격이 비슷한 지점) 주변에서 감마가 가장 높은 값을 나타냅니다.


#%% [Sector 3] 옵션 그릭스 3: 세타(Theta) 3D 곡면 (Images 92~93)
"""
세타(Theta)는 시간 경과에 따른 옵션 가격의 변화(시간가치)를 나타냅니다.
잔존만기(ttm)가 0에 가까워지면서 그래프가 어떻게 변하는지 보기 위해 
X축 값을 양수에서 0으로 거꾸로 흘러가게 출력하는 기법(ax.invert_xaxis)을 사용합니다.
"""
def call_theta(S, K, ttm, r, sigma):
    d1 = (np.log(S / K) + (r + sigma**2 * 0.5) * ttm) / (sigma * np.sqrt(ttm))
    d2 = (np.log(S / K) + (r - sigma**2 * 0.5) * ttm) / (sigma * np.sqrt(ttm))
    val = -1 * ((S * ndx(d1) * sigma) / (2 * np.sqrt(ttm))) - r * K * np.exp(-r * ttm) * stats.norm.cdf(d2, 0.0, 1.0)
    return val

T_theta = np.arange(1.0, 0.0, -0.01) # 잔존만기 1년에서 0년까지 0.01씩 감소
S_theta = np.arange(350, 355)
T_theta, S_theta = np.meshgrid(T_theta, S_theta)
Z_theta = call_theta(S_theta, 350, T_theta, 0.02, 0.30)

# 3D 그래프 세팅 시 축 거꾸로 출력하기
ax.invert_xaxis() # X축을 1부터 0의 순서로 거꾸로 출력하여 시간의 흐름을 표현
# 해석: 날짜가 만기일(0)에 가까워질수록 세타가 급격히 감소합니다.


#%% [Sector 4] 옵션 그릭스 4: 베가(Vega) 3D 곡면 (Images 94~95)
"""
베가(Vega)는 변동성(Volatility) 변화에 따른 옵션 가격의 변화율입니다.
- 감마와 마찬가지로 콜과 풋의 공식이 동일합니다.
"""
def vega(S, K, ttm, r, sigma):
    d1 = (np.log(S / K) + (r + sigma**2 * 0.5) * ttm) / (sigma * np.sqrt(ttm))
    # d2는 공식에 직접 쓰이진 않지만 통상 같이 계산함
    val = (S * np.sqrt(ttm) * ndx(d1))
    return val

# V_vega = np.arange(0.05, 0.95, 0.01) # 변동성(V) 범위 지정
# S_vega = np.arange(350, 352)
# V_vega, S_vega = np.meshgrid(V_vega, S_vega)
# Z_vega = vega(S_vega, 350, 0.38, 0.02, V_vega)
# 해석: 변동성이 아주 낮은 구간(10% 미만)에서 베가가 급격히 올라가고, 변동성이 증가함에 따라 베가가 점점 감소합니다.

