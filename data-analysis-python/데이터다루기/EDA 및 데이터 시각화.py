# -*- coding: utf-8 -*-

# 언제 쓰나: 데이터를 받자마자 모델 돌리기 전에 "어떻게 생겼나"부터 본다.
#   - 막대: 범주별 개수·크기 비교 / 히스토그램: 한 변수의 분포
#   - 상자그림: 튀는 값·집단별 분포 비교 / 산점도: 두 변수 관계 / 히트맵: 여러 변수 상관 한눈에


#%% 
"""
EDA: Exploratory Data Analysis
-데이터 분석의 첫 단계로 데이터에 내제된 특성 ㅁ치 관계를 파악
- 주요 주제 4개 
1) 저항성의 강조
2) 잔차 계산
3) 자료변수의 재표현
4) 그래프를 통한 현시성 
"""

# %% 데이터 불러오기 + 일간 수익률 만들기
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.datasets import load_wine
from sklearn.datasets import load_iris
import seaborn as sns
from pandas.plotting import scatter_matrix


plt.rcParams['font.family'] = 'Malgun Gothic'   # 한글 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False       # 마이너스 기호 깨짐 방지
PATH = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터\prices.csv'
prices = pd.read_csv(PATH, dtype={'code': str}, parse_dates=['date'], encoding='utf-8-sig')
prices = prices.sort_values(['code', 'date']).reset_index(drop=True)

# 수익률은 반드시 종목 안에서만 계산 (groupby 없이 pct_change 하면
# 앞 종목 마지막 날 → 다음 종목 첫날이 이어져 가짜 수익률이 생김)
prices['ret'] = prices.groupby('code')['close'].pct_change()
prices['year'] = prices['date'].dt.year
print(prices.head())
print(prices['ret'].describe())

# %% [막대] 종목별 평균 거래대금 상위 10개
# 금융에서 막대그래프는 "어디에 돈이 몰리나"(유동성) 비교에 자주 씀
amt_top10 = (prices.groupby('code')['amount'].mean() / 1e8).sort_values().tail(10)
plt.barh(amt_top10.index, amt_top10.values)
plt.title('평균 거래대금 상위 10종목 (억 원)')
plt.xlabel('억 원')
plt.show()

# %% [히스토그램] 일간 수익률 분포 + 같은 평균·표준편차의 정규분포 겹쳐 보기
from scipy import stats

r = prices['ret'].dropna()
plt.hist(r, bins=200, range=(-0.15, 0.15), density=True, alpha=0.6, label='실제 수익률')
x = np.linspace(-0.15, 0.15, 300)
plt.plot(x, stats.norm.pdf(x, r.mean(), r.std()), 'r', label='정규분포 (같은 평균·표준편차)')
plt.title('일간 수익률 분포')
plt.legend()
plt.show()

# 첨도(kurtosis): 정규분포면 0 (scipy 기본은 정규를 0으로 맞춘 '초과 첨도')
# 주식 수익률은 보통 크게 양수 → 가운데가 뾰족하고 꼬리가 두꺼움(급등락이 정규분포 예상보다 자주)
print('왜도:', round(stats.skew(r), 3), '/ 초과 첨도:', round(stats.kurtosis(r), 3))
print('±3 표준편차 밖 비율 - 실제:', round((np.abs(r - r.mean()) > 3 * r.std()).mean() * 100, 2), '%',
      '/ 정규분포라면: 0.27 %')

# %% [히스토그램] 종목 하나: 로그 수익률 vs 단순 수익률
# 로그 수익률 = ln(오늘 종가 / 어제 종가). 여러 날을 더하면 기간 수익률이 돼서 분석에 자주 씀
one = prices[prices['code'] == amt_top10.index[-1]].copy()
one['log_ret'] = np.log(one['close'] / one['close'].shift(1))
plt.hist(one['ret'].dropna(), bins=80, alpha=0.5, label='단순 수익률')
plt.hist(one['log_ret'].dropna(), bins=80, alpha=0.5, label='로그 수익률')
plt.title(f'{amt_top10.index[-1]} 일간 수익률')
plt.legend()
plt.show()

# %% [상자그림] 연도별 일간 수익률 → 어느 해가 출렁였나
by_year = [prices.loc[prices['year'] == y, 'ret'].dropna() for y in sorted(prices['year'].unique())]
plt.boxplot(by_year, tick_labels=sorted(prices['year'].unique()), whis=1.5, showfliers=False)
plt.title('연도별 일간 수익률 (이상치 점은 숨김)')
plt.show()
print(prices.groupby('year')['ret'].std().round(4))   # 상자 길이 ≈ 변동성

# %% [상자그림] whis=1.5 기준이면 주식 수익률은 '이상치'가 너무 많이 잡힌다
# → 3-1(빈칸·튀는 값 처리하기)에서 이걸 어떻게 다룰지 이어서 봄
q1, q3 = r.quantile([0.25, 0.75])
iqr = q3 - q1
n_out = ((r < q1 - 1.5 * iqr) | (r > q3 + 1.5 * iqr)).sum()
print(f'1.5×IQR 밖 비율: {n_out / len(r) * 100:.1f}%  (정규분포라면 약 0.7%)')

# %% [산점도] 위험-수익: 종목별 연환산 변동성 vs 연환산 수익률
stat = prices.groupby('code')['ret'].agg(['mean', 'std'])
stat['ann_ret'] = stat['mean'] * 252                 # 거래일 252일 기준
stat['ann_vol'] = stat['std'] * np.sqrt(252)         # 변동성은 √기간으로 늘어남
stat['amount'] = prices.groupby('code')['amount'].mean() / 1e8

plt.scatter(stat['ann_vol'], stat['ann_ret'], s=stat['amount'] / stat['amount'].max() * 300, alpha=0.5)
plt.xlabel('연환산 변동성')
plt.ylabel('연환산 평균 수익률')
plt.title('종목별 위험-수익 (점 크기 = 평균 거래대금)')
plt.axhline(0, color='black', linewidth=0.8)
plt.show()

# %% [산점도] 거래량이 평소보다 많은 날, 가격도 크게 움직이나?
# 거래량 비율 = 오늘 거래량 / 직전 20일 평균 거래량 (오늘 값은 평균에 넣지 않음: shift(1))
prices['vol_ma20'] = prices.groupby('code')['volume'].transform(lambda s: s.shift(1).rolling(20).mean())
prices['vol_ratio'] = prices['volume'] / prices['vol_ma20']
sample = prices.dropna(subset=['vol_ratio', 'ret']).sample(5000, random_state=0)

sns.scatterplot(x=np.log(sample['vol_ratio']), y=sample['ret'].abs(), alpha=0.3, s=10)
plt.xlabel('log(거래량 / 20일 평균)')
plt.ylabel('|일간 수익률|')
plt.title('거래량 급증일과 가격 변동 크기')
plt.show()
print('스피어만 상관:', round(stats.spearmanr(np.log(sample['vol_ratio']), sample['ret'].abs())[0], 3))

# %% [선그래프] 시계열 데이터는 꼭 시간 축으로도 본다: 누적수익률
wide_close = prices.pivot(index='date', columns='code', values='close')   # 행=날짜, 열=종목
cum = wide_close[amt_top10.index[-5:]] / wide_close[amt_top10.index[-5:]].bfill().iloc[0]
cum.plot(figsize=(10, 5), title='거래대금 상위 5종목 누적 수익 (시작 = 1)')
plt.show()

# %% [산점도 행렬] 거래대금 상위 4종목의 일간 수익률끼리
wide_ret = prices.pivot(index='date', columns='code', values='ret')
scatter_matrix(wide_ret[amt_top10.index[-4:]].dropna(), alpha=0.2, diagonal='hist', figsize=(8, 8))
plt.show()

# %% [히트맵] 상위 10종목 수익률 상관 → 같이 움직이는 묶음 찾기
ret_corr = wide_ret[amt_top10.index].corr(method='pearson')
sns.heatmap(ret_corr, annot=True, fmt='.2f', cmap='RdBu_r', vmin=-1, vmax=1)
plt.title('상위 10종목 일간 수익률 상관')
plt.show()
# 대각선 밖 평균 상관 = 분산투자 효과가 얼마나 있나 (높을수록 같이 움직임)
mask = ~np.eye(len(ret_corr), dtype=bool)
print('평균 상관:', round(ret_corr.values[mask].mean(), 3))

# %% [주의] 가격끼리 상관은 거의 항상 높게 나온다 (둘 다 시간 따라 오르내리면)
# 그래서 관계를 볼 땐 가격이 아니라 수익률로 본다 (4-7 상관·회귀에서 본 것과 같은 이야기)
a, b = amt_top10.index[-1], amt_top10.index[-2]
print('가격 상관  :', round(wide_close[a].corr(wide_close[b]), 3))
print('수익률 상관:', round(wide_ret[a].corr(wide_ret[b]), 3))

# %% 1. 막대그래프와 히스토그램
"""
막대그래프: 범주형 데이터를 요약하고 시각적 비교에 효과적

코드 형식
data_cnt = data['traget'].value_counts()
plt.bar (x,heigth, width = 0.8, bottom = None, align = 'center', data= None)

x: 막대의 x좌표
height : 막대의 높이
width: 막대의 넓이
bottom: 막대 바닥면의 y좌표 (누적 막대그래프에서 사용)
align: x좌표에 대한 막대 정렬 ('center', 'edge')


히스토그램 : 연속형 자료의 분포를 확인하기 위한 기본적인 탐색 도구 
- 연속형 변수의 전반적 분포 형태 알고싶을 때
- 데이터가 정규분포 따르는지
- 특정 구간 값에 과도하게 데이터 ㅁㄹ려잇는지
- 극단값 존재하는지
 

코드형식
plt.hist('변수명', bins = None, range = None, density = False, data= df)

bins: 히스토그램 구간 수 
range: 각 bin의 상한 하한값 (x.min(),x.max()로 자동설정 가능)
density: True일 경우 확률밀도함수를 그린 후 반환

해석순서
1) 전반적 분포 모양
- 정규분호? 한쪽으로 치우친 분포(왜도)? , 여러 개 봉우리 (다봉분포)?, 코시분포? 등

2) 데이터 밀집 구간
값이 가장 많이 모인 구간이 어딘지
분석에서 중요한 의미를 가지는 구간이 있는지

3) 이상치 가능성
대부분의 값이 동떨어진 구간이 존재하는지 

"""
#%% 
wine_load = load_wine()
wine = pd.DataFrame(wine_load.data, columns=wine_load.feature_names)
wine['Class'] = wine_load.target
wine['Class'] = wine['Class'].map({0: 'class_0', 1: 'class_1', 2: 'class_2'})

# 도수분포표: 범주마다 몇 개인지
wine_type = wine['Class'].value_counts()
print(wine_type)

# %% 막대그래프
plt.bar(wine_type.index, wine_type.values)
plt.show()

# %% 수평 막대그래프 (범주 이름이 길 때 보기 좋음)
plt.barh(wine_type.index, wine_type.values)
plt.show()

# %% 히스토그램: 숫자 하나가 어떻게 퍼져 있나
plt.title('Wine alcohol histogram')
plt.hist('alcohol', data=wine)
plt.show()


# %% 2. 상자그림 (Box Plot)
"""
상자그림 
-데이터 분포 시간적 표현
- 사분위 수 기반

(1) 상자 
-상자 안에는 데이터 중앙 50% 해당 , Q1과 Q3가 경계값 , 중앙선은 median

(2) IQR(Interquartile Range)
- IQR은 중앙 50% 데이터가 퍼져 있는 정도 나타냄

(3) 수염 
-수염은 기본적으로 1.5 * IQR 범위를 기준으로 설정 
- 이를 벗어나면 이상치 취급 

 """
#%%
iris = load_iris()
iris = pd.DataFrame(iris.data, columns=iris.feature_names)
iris['class'] = load_iris().target
iris['class'] = iris['class'].map({0: 'Setosa', 1: 'Versicolour', 2: 'Virginica'})

plt.boxplot(iris.drop(columns='class'))
plt.show()

# %% whis=1.5: 상자(Q1~Q3) 길이의 1.5배 밖이면 점(이상치)으로 찍음
plt.boxplot(iris['sepal width (cm)'], whis=1.5)
plt.title('sepal width (cm)')
plt.show()

# %% 집단별 상자그림
iris[['sepal width (cm)', 'class']].boxplot(by='class')
plt.show()

# %% 3. 산점도
"""
산점도 
- 두개의 수치형 변수 간의 관계를 시각적으로 탐구 
-직관적이며 2차원 평면에 흩게 나타냄


코드 
import matplotlib.pyplot as plt
plt.scatter(x= 가로축 변수, y= 세로축 변수)


해석
- 관계 유형
: 양의 상관관계, 음의 상관관계, 관계 x 

- 관계 강도 
: 상관계수 -1~1까지 표현 가능
 """

#%%
plt.title('iris scatter')
plt.xlabel('sepal length (cm)')
plt.ylabel('sepal width (cm)')
plt.scatter(x=iris['sepal length (cm)'], y=iris['sepal width (cm)'], alpha=0.5)
plt.show()

# %% seaborn 산점도: hue로 집단마다 색을 다르게
import seaborn as sns

sns.scatterplot(x='sepal length (cm)', y='sepal width (cm)',
                data=iris, hue='class', style='class')
plt.show()

# %% 여러 변수간의 관게 탐색
sns.scatterplot(x='petal length (cm)', y='petal width (cm)',
                data=iris, hue='class')
plt.show()

# %% 4. 상관관계 시각화: 산점도 행렬
""" 
산점도 행렬 
- 두 개 이상의 변수가 있는 데이터에서 변수들 간의 산점도를 그린 것 

해석 방법
- 대각선의 히스토그렘 통해서 각 변수의분포와 이상치 판단
- 종속변수 설명변수 관계 시각적 판단
-설명변수 간의 직선 함수관계를 파악해 다중공선성 문제 진단 가능


코드 
from pandas.plotting import scatter_matrix
scatter_matrix(iris, alpha= 0.5, diagonal = 'hist')

data: 데이터프레임
alpha: 점들의 투명도(0~1)
diagonal: 대각선에 표시될 밀도 그래프 종류 (hist= histogram, kde: 커널 밀도 추정)


what is KDE?
KDE 그래프는 히스토그램과 함계  Non-parametric 밀도 추정법중 하나이다. 
히스토그램은 bin의 크기와 위치에 따라 그래프가 달라지는 단점이 있다.
다만, 커널 함수 사용해 데이터 분포 부드럽게 나타낸다. 
밀도를 시각적 표현 가능 
 """
#%%

scatter_matrix(iris, alpha=0.5, diagonal='hist', figsize=(8, 8))
plt.show()

# %% pairplot: 산점도 행렬의 seaborn 판
""" 범주별로 구분되는 산점도는 seabron의 pairplot()메서드 이용
sns. pairplot(data,diag_kind = 'auto', hue = 'target 컬럼명')

data: 데이터프렝ㅁ
diag_kind : 대각선 밀도 그래프 종류 (Auto, hist, kde)
hue: 색을 구분할 타깃 변수
"""
#%%
sns.pairplot(iris, diag_kind='auto', hue='class')
plt.show()


# %% 상관계수 히트맵
""" 
상관계수 행렬
- 다수 변수간 상관관계 파악 or 독립변수 간 다중공선성 확인 사용

1. 상관관계 해석하기 : -1~ 1 
2. 상관계수 행렬 시각화학

(1) DataFrame.corr() 함수로 생성
code
data= data.corr(method = 'pearson')

method 상관분석 방법에는 3개정 도 잇음
pearson: 두 변수 간의 선형 상관관계 측정, 연속형 변수에서 사용 
kendall: 비선형 상관관계 측정, 순서 데이터에 적합, 순위 일치를 기반함
spearman: 비선형 상관관계 변수 간 순위에 대한 상관성
다만 spearman의 경우는 연속형도 사용가능 (너무 극단값 영향 크면 순위처럼 바꿔서 사용하는것이 대표적)

(2) seabourn의 heatmap() 상관행렬 시각화하기 
sns.heatmap(data,xticklabels = data.columns, yticklabels = data.colums, cmap = 'RdBu_r', annot = True)

data: 상관행렬을 그릴 데이터의 상관계수 데이터프레임 
xticklabels: x축의 라벨명
yticklabels: y축의 라벨명
annot: True일 경우 상관계수를 텍스트로 표시
"""


#%%
iris_corr = iris.drop(columns='class').corr(method='pearson')
sns.heatmap(iris_corr,
            xticklabels=iris_corr.columns,
            yticklabels=iris_corr.columns,
            annot=True)
plt.show()


# =====================================================================
# 2부. 금융판 — 50종목 일별 시세(2021-01 ~ 2026-10)로 같은 그래프
# =====================================================================


