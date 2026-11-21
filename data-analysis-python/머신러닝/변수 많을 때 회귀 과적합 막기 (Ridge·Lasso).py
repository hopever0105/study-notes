# -*- coding: utf-8 -*-
""" 규제가 있는 선형회귀: 릿지, 라쏘, 엘라스틱넷 """
#%% 
# 한 줄 요약
#   보통 회귀(OLS): 오차 제곱합만 최소화 → 변수가 많으면 잡음까지 외움(과적합)
#   Ridge : 오차 제곱합 + alpha × (계수 제곱의 합)   → 계수를 0 쪽으로 '줄임' (0은 안 됨)
#   Lasso : 오차 제곱합 + alpha × (계수 절댓값의 합) → 쓸모없는 계수를 '정확히 0'으로 (변수 고르기)
#   ElasticNet: 둘을 섞음 (l1_ratio = Lasso 비중)
#   alpha가 클수록 벌점이 커져 계수가 더 작아짐

#  릿지·라쏘·엘라스틱넷 회귀 한눈에 보기
# | 구분           | 릿지(Ridge)        | 라쏘(Lasso)          | 엘라스틱넷(ElasticNet) |
# |----------------|--------------------|----------------------|------------------------|
# | 페널티 방식    | 제곱 합산(L2)      | 절댓값 합산(L1)      | L1+L2 혼합             |
# | 계수 수축      | 0에 가깝게 수축    | 정확히 0으로 수축    | 0 근접 or 정확히 0     |
# | 자동 변수 선택 | 없음               | 가능(0으로 만듦)     | 가능                   |
# | 다중공선성     | 강건함             | 하나만 선택          | 그룹 선택 가능         |
# | 주요 파라미터  | alpha              | alpha                | alpha+l1_ratio         |
# | 적용 상황      | 변수 모두 유효할 때 | 불필요한 변수 多    | 상관 높은 변수 多      |
#
#
# 세 기법 모두 alpha 값을 적절히 설정하는 것이 핵심.
# alpha가 너무 작으면 규제 효과가 거의 없고, 너무 크면 모든 가중치가 0에 수렴하여 예측력이 저하

# 기법 선택 가이드
#  - 입력특성이 모두 의미 있고 다중공선성이 우려될 때 → 릿지(Ridge)
#  - 입력특성이 많고 불필요한 변수도 많아 희소 모델이 필요할 때 → 라쏘(Lasso)
#  - 상관관계 높은 입력특성 그룹이 존재하고 안정적인 변수 선택이 필요할 때
#    → 엘라스틱넷(ElasticNet)
# =====================================================================
#%% 머신러닝 지도학습 -> 규제가 있는 선형회귀 
# 1. 개념
# 다중 회귀분석과, 회귀모형의 복잡도를 제어하기 위한 규제(Regularization)가 적용된 선형 회귀 기법
# 대표적인 규제 기법인 릿지(Ridge), 라쏘(Lasso),엘라스틱넷(ElasticNet)에 대해 살펴봅니다.
#
# 다중 회귀분석 
# 두 개 이상의 입력특성(X변수)이 하나의 레이블(y변수)에 동시에 영향을 미치는 관계를 수식으로 표현하는 회귀모형.
# 단순 선형 회귀가 하나의 입력특성과 레이블 간의 관계를 설명하는 
# 빈먄. 다중 회귀분석은 여러 입력특성이 동시에 작용하는 현실을 보다 잘 반영
#
# 다중 회귀모형에서는 각 입력특성에 해당 특성이 레이블에 미치는 영향을 나타내는 가중치(회귀계수, β)가 곱해짐. 가중치의 절댓값이 클수록
# 해당 입력특성이 레이블에 미치는 영향이 크다고 해석할 수 있음 
#
#   나이(X1)       × β1 ─┐
#   혈압(X2)       × β2 ─┤
#   BMI(X3)        × β3 ─┼─> Σ ─> 다중 회귀모델 ─> 레이블 예측(y: 혈당 수치)
#   혈당(X4)       × β4 ─┤
#   콜레스테롤(X5) × β5 ─┘
#
#   → y = β0 + β1*X1 + β2*X2 + β3*X3 + β4*X4 + β5*X5
#
# 입력특성의 수가 증가할수록 모델의 표현력은 증가하지만 아래와 같은 문제가 발생할 수 있음. 

#  ① 다중공선성(Multicollinearity)
# 입력특성 간 상관관계가 높은 경우 발생하며, 회귀계수의 추정이 불안정해지는 문제

#  ② 과적합(Overfitting)
# 모델이 학습 데이터에 과도하게 적합되어  새로운 데이터에 대한 예측 성능이 저하되는 현상
# 이러한 문제를 해결하기 위해 변수선택법과 규제 기법이 활용

#  - 다중 회귀: 여러 입력특성이 동시에 하나의 레이블을 예측하는 회귀모형
#  - 가중치(β): 각 입력특성이 레이블에 미치는 영향의 크기
#  - 다중공선성: 입력특성들 간의 상관관계가 높아 회귀계수의 추정이 불안정해지는 문제


#%%2. 변수선택법
# ---------------------------------------------------------------------
# 변수선택법은 다수의 입력특성 중에서 레이블 예측에 유의미한 변수만을 선택하여 모델을 단순화
# 불필요한 변수를 제거함으로써 모델의 해석력을 높이고, 과적합을 방지
#
# 변수선택법은 일반적으 세 가지 방식으로 구분

#
# | 구분 | 전진선택법(Forward Selection) | 후진소거법(Backward Elimination) | 단계적 선택법(Stepwise Selection) |
# |------|-------------------------------|----------------------------------|-----------------------------------|
# | 출발 | 빈 모델(입력특성 없음)        | 전체 모델(모든 특성 포함)        | 빈 모델에서 시작                  |
# | 반복 | 가장 유용한 특성 하나씩 추가  | 가장 불필요한 특성 하나씩 제거   | 추가(+)/제거(-) 동시 검토         |
# | 종료 | 성능 개선 없으면 탐색 중단    | 성능 저하 없으면 탐색 중단       | 성능 개선 없으면 탐색 중단        |
#   → 세 방법 모두 최종적으로 "최적 입력특성 조합 확정"
#



#%% 3. 규제가 있는 회귀모델
# 변수선택법이 '어떤 입력특성을 포함할 것인가'를 결정하는 방법
# 규제(Regularization)는 모든 입력특성을 유지한 상태에서 회귀계수(가중치)의 크기에 제약을 가하여 모델의 복잡도를 조절
#  즉, 규제는 모델이 특정 입력특성에 과도하게 의존하지않도록 하여 보다 안정적인 예측을 가능케 함. 


# 규제가 적용된 회귀모형의 목적
#  ① 과적합 방지
#  일반적인 선형 회귀모형은 학습 데이터에 지나치게 적합될 수 있으며, 이로 인해 새로운 데이터에 대한 예측 성능이 저하되는 문제가 발생
#  규제는 회귀계수의 크기에 페널티를 부여하여 모델을 단순화함으로써, 학습 데이터에 대한 과도한 적합을 방지하고 일반화 성능을 향상시킴
#  입력특성의 수가 많거나,  표본 수에 비해 입력특성의 수가 많은 경우에 효과적으로 활용

#  ② 다중공선성 완화
#  입력특성 간 상관관계가 높은 경우, 회귀계수의 추정값이 크게 변동하여 모델의 해석과 예측이 불안정해질 수 있음.
#  규제를 적용하면 회귀계수의 크기가 제한되면서 이러한 변동성이 감소하고, 보다 안정적인 추정이 가능해짐. 




#%% 4. 릿지(Ridge) (L2방식)

# (1) 개념
# 릿지 회귀는 모델이 학습하는 동안 가중치(β)가 너무 커지지 않도록 제곱 합산 페널티(L2)를 추가하는 개념
#  모델이 어떤 특성 하나에 지나치게 의존하는 것을 막고 모든 가중치를 고르게 낮추는 방향으로 학습이 이루어짐
#   → 손실함수 = Σ(y - ŷ)² + α * Σβ²

# 릿지 회귀에서 규제의 강도는 하이퍼파라미터 α(alpha)에 의해 결정
# α 값이 0인 경우, 규제가 적용되지 않으며 일반 선형 회귀와 동일한 결과
# α 값이 증가하는 경우, 모든 회귀계수가 0에 가까워지며 모델은 점점 단순
# 적절한 α 값을 선택하는 것은 모델 성능에 중요함.
# 릿지 회귀는 편향-분산 트레이드오프(Bias-Variance Trade-off) 관점에서도 이해 가능
# α 값이 클수록 분산이 감소하므로, 모델이 단순해져 학습 데이터의 작은 변동에 덜 민감해지나, 편향이 증가하므로 모델이 학습 데이터를 충분히 설명하지 못하는 오차가 증가할 수 있습니다.



#   규제 강도(α) 따른 구분
#   [과소규제]     
#    학습 데이터에는 적합하나 새로운 데이터에 대한 성능 저하 발생 → 과적합(Overfitting) 위험 증가

#   [최적 균형 지점] 
#    편향과 분산의 균형이 이루어지는 구간→ 일반화 성능 최대화 → 교차검증(CV)을 통한 최적 지점 탐색 필요

#   [과도한 규제] 
#     모든 회귀계수가 0에 수렴 → 모델의 단순화 심화  → 과소적합(Underfitting) 위험 증가
#


# 릿지 회귀의 한계
# 릿지 회귀는 회귀계수를 0에 가깝게 만들 수는 있지만, 정확히 0으로 만들지는 않는다. 
# 따라서 예측에 거의 기여하지 않는 입력특성도 모델에 계속 포함된다. 
#  이와 같은 한계를 보완하기 위해 일부 계수를 0으로 만드는 라쏘(Lasso) 회귀가 활용


# (2) 주요 파라미터
# 릿지 회귀는 scikit-learn의 Ridge 클래스를 통해 구현할 수 있으며, 주요 파라미터는 아래 

# | 파라미터      | 기본값 | 설명                                                  |
# |---------------|--------|-------------------------------------------------------|
# | alpha         | 1.0    | - 규제 강도를 조절하는 하이퍼파라미터                 |
# |               |        | - 반드시 0 이상의 값을 가짐                           |
# |               |        | - 값이 클수록 규제 강도가 증가하며, 회귀계수의 축소 정도가 커짐 |
# | fit_intercept | True   | - 절편(β0)의 포함 여부를 결정                         |
# |               |        | - False로 설정하면 원점을 통과하는 회귀모형이 생성됨  |
#
# (그래프 해석)
# 그래프를 해석하면 α 값이 증가할수록 가중치가 점점 0에 수렴하는 것을 확인할 수 있음
# 그러나 가중치가 0이 되지는 않으므로, 릿지 모델은 모든 입력특성을 유지
#%%
# %%  릿지 (Ridge)
from sklearn.datasets import load_diabetes
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

diabetes = load_diabetes()
X = pd.DataFrame(diabetes.data, columns=diabetes.feature_names)
y = diabetes.target
print(X.head())
# 참고: 이 데이터는 이미 열마다 단위를 맞춰(스케일링) 놓은 것. 실제 데이터는 직접 맞춰야 함 (2부 참고)

# %% alpha를 로그 간격으로 5단계: [0.01, 0.1, 1, 10, 100]
from sklearn.linear_model import Ridge

alpha = np.logspace(-2, 2, 5)
np.set_printoptions(suppress=True)   # 숫자를 지수 표기 없이
print(alpha)

# %% alpha마다 Ridge를 학습하고 계수 모으기
data = []
for a in alpha:
    ridge = Ridge(alpha=a, random_state=45)
    ridge.fit(X, y)
    data.append(pd.Series(ridge.coef_))

df_ridge = pd.DataFrame(data, index=alpha)
df_ridge.columns = X.columns
print(df_ridge)

# %% alpha에 따른 계수 변화 그림
plt.semilogx(df_ridge)
plt.xticks(alpha, labels=[str(round(a, 3)) for a in alpha])
plt.legend(labels=df_ridge.columns, bbox_to_anchor=(1, 1))
plt.axhline(y=0, linestyle='--', color='black', linewidth=2)
plt.title('Ridge: alpha에 따른 가중치(β) 변화')
plt.xlabel('alpha(α)')
plt.ylabel('Coefficient (size)')
plt.tight_layout()
plt.show()


#%% 5. 라쏘(Lasso)

# (1) 개념
# 라쏘 회귀는 릿지 회귀와 마찬가지로 가중치가 과도하게 커지는 것을 방지하는 규제 기법,  규제 방식에 차이가 있음
# 절댓값 합(L1)에 대한 페널티를 사용하며, 이로 인해 일부 가중치를 정확히 0으로 만들어 해당 입력특성을 모델에서 제거
# 즉, 가중치를 단순히 작게 만드는 것이 아니라, 중요하지 않은 변수는 완전히 제외하는 효과
#   → 손실함수 = Σ(y - ŷ)² + α * Σ|β|
#
# 이 특성 때문에 라쏘 회귀는 규제와 변수 선택을 동시에 수행
# 입력특성이 많은 고차원 데이터에서 일부 변수만 실제로 의미가 있을 때 특히 효과적
# 다만, 입력특성 간 상관관계가 높은 경우에는 일부만 선택되고 나머지는 0으로 처리되므로, 선택된 변수가 데이터에 따라 달라질 수 있어 결과가 불안정할 수 있음
#

# (2) 주요 파라미터
# 라쏘 회귀는 scikit-learn의 Lasso 클래스를 통해 구현할 수 있으며, 주요 파라미터는 아래와 같음.
# | 파라미터      | 기본값 | 설명                                                  |
# |---------------|--------|-------------------------------------------------------|
# | alpha         | 1.0    | - 규제 강도를 조절하는 하이퍼파라미터                 |
# |               |        | - 값이 클수록 규제 강도가 증가하며 일부 가중치는 0으로 수렴 |
# | fit_intercept | True   | - 절편(β0)의 포함 여부를 결정                         |
# |               |        | - False로 설정하면 원점을 통과하는 회귀모형 생성      |
#

#%%  라쏘 (Lasso)
from sklearn.linear_model import Lasso

data_lasso = []
for a in alpha:
    lasso = Lasso(alpha=a, random_state=45)
    lasso.fit(X, y)
    data_lasso.append(pd.Series(lasso.coef_))

df_lasso = pd.DataFrame(data_lasso, index=alpha)
df_lasso.columns = X.columns
print(df_lasso)   # alpha가 커지면 0이 되는 계수가 늘어남

# %%
plt.semilogx(df_lasso)
plt.xticks(alpha, labels=[str(round(a, 3)) for a in alpha])
plt.legend(labels=df_lasso.columns, bbox_to_anchor=(1, 1))
plt.axhline(y=0, linestyle='--', color='black', linewidth=2)
plt.title('Lasso: alpha에 따른 가중치(β) 변화')
plt.xlabel('alpha(α)')
plt.ylabel('Coefficient (size)')
plt.tight_layout()
plt.show()


#%%
# ---------------------------------------------------------------------
# 6. 엘라스틱넷(ElasticNet)
# ---------------------------------------------------------------------
# (1) 개념
# 엘라스틱넷 회귀는 릿지(L2)와 라쏘(L1)의 규제 방식을 혼합한 절충형 ㅍ회귀 기법. 
# 두 기법의 장점을 동시에 활용할 수 있으며, 혼합 비율은 l1_ratio 하이퍼파라미터로 조절
# 예를 들어, l1_ratio=1이면 순수라쏘 회귀와 동일하게 동작하고, l1_ratio=0이면 순수 릿지 회귀와 동일하게 동작
#
# 서로 상관관계가 높은 입력특성이 여러 개일 경우, 라쏘 회귀는 그중 일부만 선택하지만 엘라스틱넷 회귀는 그룹 전체를 고려하는 경향이 있음. 
# .단, alpha와 l1_ratio를 동시에 최적화해야 하므로 탐색 공간이 넓음. 
# . scikit-learn의 ElasticNetCV를 사용하면 교차검증으로 최적조합을 자동 탐색 가능
#

# (2) 주요 파라미터
# ElasticNet은 scikit-learn의 ElasticNet 클래스를 통해 구현할 수 있으며, 주요 파라미터는 아래와 같다. 
# | 파라미터      | 기본값 | 설명                                                  |
# |---------------|--------|-------------------------------------------------------|
# | alpha         | 1.0    | - 규제 강도를 결정하는 하이퍼파라미터                 |
# |               |        | - 값이 클수록 규제 강도가 세짐                        |
# | l1_ratio      | 0.5    | - L1과 L2 혼합 정도를 결정                            |
# |               |        | - 0이면 릿지(L2), 1이면 라쏘(L1)와 동일               |
# | fit_intercept | True   | - 회귀모델 절편(β0) 계산 여부 결정                    |
# |               |        | - False로 설정하면 원점을 통과하는 회귀모형 생성      |
#


# %%  엘라스틱넷 (ElasticNet)
from sklearn.linear_model import ElasticNet, ElasticNetCV

enet = ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=10000, random_state=45)
enet.fit(X, y)
df_enet = pd.DataFrame(pd.Series(enet.coef_)).T
df_enet.columns = X.columns
print(df_enet)

# %% 교차검증으로 alpha·l1_ratio 고르기 (책: cv=5 무작위 → 이 데이터는 시간 순서가 없어서 괜찮음)
enet_cv = ElasticNetCV(l1_ratio=[0.3, 0.5, 0.7, 0.9, 1.0], alphas=alpha, cv=5, random_state=45)
enet_cv.fit(X, y)
print('최적 alpha  :', round(enet_cv.alpha_, 4))
print('최적 l1_ratio:', enet_cv.l1_ratio_)
df_enet_cv = pd.DataFrame(pd.Series(enet_cv.coef_)).T
df_enet_cv.columns = X.columns
print(df_enet_cv)


# %% 데이터 → 월말 패널 (행 = 종목×월)
from sklearn.linear_model import LinearRegression
from scipy.stats import spearmanr

PATH = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터\prices.csv'
px = pd.read_csv(PATH, dtype={'code': str}, parse_dates=['date'], encoding='utf-8-sig')
px = px.sort_values(['code', 'date']).reset_index(drop=True)
g = px.groupby('code')['close']
px['ret'] = g.pct_change()

# 일별로 계산해 두고 월말 값만 뽑는다 (전부 그날까지의 정보)
px['mom_1m'] = g.pct_change(21)                                   # 1개월 수익률 (단기 반전)
px['mom_3m'] = g.pct_change(63)
px['mom_6m'] = g.pct_change(126)
px['mom_12_1'] = g.shift(21) / g.shift(252) - 1                   # 12개월 모멘텀 (최근 1개월 제외)
px['vol_1m'] = px.groupby('code')['ret'].transform(lambda s: s.rolling(21).std())
px['vol_3m'] = px.groupby('code')['ret'].transform(lambda s: s.rolling(63).std())
px['amt_log'] = np.log(px.groupby('code')['amount'].transform(lambda s: s.rolling(21).mean()))  # 규모(유동성)
px['amt_chg'] = px.groupby('code')['amount'].transform(lambda s: s.rolling(21).mean() / s.rolling(126).mean())
px['dist_hi'] = px['close'] / g.transform(lambda s: s.rolling(252).max()) - 1                  # 52주 고가 대비
px['dist_lo'] = px['close'] / g.transform(lambda s: s.rolling(252).min()) - 1
px['max_ret'] = px.groupby('code')['ret'].transform(lambda s: s.rolling(21).max())              # 지난달 최대 일간 상승
px['skew_3m'] = px.groupby('code')['ret'].transform(lambda s: s.rolling(63).skew())
REAL = ['mom_1m', 'mom_3m', 'mom_6m', 'mom_12_1', 'vol_1m', 'vol_3m',
        'amt_log', 'amt_chg', 'dist_hi', 'dist_lo', 'max_ret', 'skew_3m']

px['ym'] = px['date'].dt.to_period('M')
month_end = px.groupby(['code', 'ym']).tail(1).copy()            # 종목별 그달 마지막 거래일
month_end = month_end.sort_values(['code', 'ym'])
month_end['fwd_1m'] = month_end.groupby('code')['close'].shift(-1) / month_end['close'] - 1   # 정답: 다음 달 수익률

# 가짜 변수 10개: 아무 의미 없는 난수 → 좋은 방법이라면 이걸 버려야 함
rng = np.random.default_rng(0)
NOISE = [f'noise_{i}' for i in range(10)]
for c in NOISE:
    month_end[c] = rng.standard_normal(len(month_end))
FEATS = REAL + NOISE

panel = month_end.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATS + ['fwd_1m']).reset_index(drop=True)
print(panel.shape, panel['ym'].min(), '~', panel['ym'].max())

# %% 스케일링: 달마다 z점수 (그달 50종목 안에서 평균 0, 표준편차 1)
# 이유 ① Ridge·Lasso 벌점은 계수 크기에 붙음 → 단위가 다르면(거래대금 log 25 vs 수익률 0.05) 벌점이 불공평
# 이유 ② 달마다 하면 그달 정보만 씀(미래 섞임 없음) + 시장 전체가 오른 달/내린 달 영향 제거
def zscore_by_month(df, cols):
    out = df.copy()
    grp = out.groupby('ym')[cols]
    out[cols] = (out[cols] - grp.transform('mean')) / grp.transform('std')
    return out

panel = zscore_by_month(panel, FEATS)
panel[FEATS] = panel[FEATS].clip(-3, 3)                         # 튀는 값 자르기 (3-1)
# 정답도 그달 평균을 빼서 '다른 종목보다 얼마나 더 올랐나'로 (종목 고르기 문제로 바꿈)
panel['y'] = panel['fwd_1m'] - panel.groupby('ym')['fwd_1m'].transform('mean')

# %% 시간순으로 나누기: 학습 ~2024-12 / 시험 2025-01~
train = panel[panel['ym'] <= pd.Period('2024-12', 'M')]
test = panel[panel['ym'] >= pd.Period('2025-01', 'M')]
Xtr, ytr, Xte, yte = train[FEATS].values, train['y'].values, test[FEATS].values, test['y'].values
print('학습', train.shape, '/ 시험', test.shape)

# %% 책과 같은 그림: alpha에 따른 계수 변화 (금융판)
alphas_r = np.logspace(0, 5, 11)       # Ridge: 1 ~ 100000 (행이 1천 개 넘으면 alpha도 커야 효과가 보임)
alphas_l = np.logspace(-4, -1, 9)      # Lasso: 0.0001 ~ 0.1 (Lasso는 alpha 단위가 다름)
coef_r = pd.DataFrame([Ridge(alpha=a).fit(Xtr, ytr).coef_ for a in alphas_r], index=alphas_r, columns=FEATS)
coef_l = pd.DataFrame([Lasso(alpha=a, max_iter=10000).fit(Xtr, ytr).coef_ for a in alphas_l], index=alphas_l, columns=FEATS)

fig, ax = plt.subplots(1, 2, figsize=(13, 5))
for c in FEATS:
    style = ':' if c.startswith('noise') else '-'
    ax[0].semilogx(coef_r.index, coef_r[c], style)
    ax[1].semilogx(coef_l.index, coef_l[c], style, label=c)
ax[0].set_title('Ridge 계수 (점선 = 가짜 변수)')
ax[1].set_title('Lasso 계수 (점선 = 가짜 변수)')
for a_ in ax:
    a_.axhline(0, color='black', linewidth=1)
ax[1].legend(bbox_to_anchor=(1, 1), fontsize=7)
plt.tight_layout()
plt.show()

print('Lasso alpha별 0이 아닌 계수 개수 (진짜 / 가짜):')
for a in alphas_l:
    nz = coef_l.loc[a] != 0
    print(f'  alpha={a:.4f}: {nz[REAL].sum():2d} / {nz[NOISE].sum():2d}')

# %% alpha 고르기: 학습 기간 안에서 다시 시간순으로 (확장 창 검증)
# 책의 ElasticNetCV(cv=5)는 무작위로 섞음 → 금융엔 안 씀. 달 단위로 직접 나눈다
def month_cv_ic(model_fn, df, feats, n_folds=4, min_train=12):
    months = np.sort(df['ym'].unique())
    test_blocks = np.array_split(months[min_train:], n_folds)
    ics = []
    for blk in test_blocks:
        tr = df[df['ym'] < blk[0]]
        va = df[df['ym'].isin(blk)]
        m = model_fn().fit(tr[feats].values, tr['y'].values)
        pred = m.predict(va[feats].values)
        va = va.assign(pred=pred)
        # 달마다 IC(스피어만) → 평균
        ics.append(va.groupby('ym').apply(lambda d: spearmanr(d['pred'], d['y'])[0], include_groups=False).mean())
    return np.mean(ics)

res = []
for a in alphas_r:
    res.append(['Ridge', a, month_cv_ic(lambda: Ridge(alpha=a), train, FEATS)])
for a in alphas_l:
    res.append(['Lasso', a, month_cv_ic(lambda: Lasso(alpha=a, max_iter=10000), train, FEATS)])
cv_res = pd.DataFrame(res, columns=['model', 'alpha', 'cv_IC'])
print(cv_res.round(4))
# 계수가 전부 0이 되면 예측이 모두 같아 IC를 못 구함(NaN) → NaN은 빼고 가장 높은 것
ok = cv_res.dropna()
best_r = ok.loc[ok[ok['model'] == 'Ridge']['cv_IC'].idxmax(), 'alpha']
best_l = ok.loc[ok[ok['model'] == 'Lasso']['cv_IC'].idxmax(), 'alpha']
print('고른 alpha - Ridge:', best_r, '/ Lasso:', best_l)

# %% 시험 기간(2025~) 성적: OLS vs Ridge vs Lasso vs ElasticNet
def test_report(name, model, feats=FEATS):
    model.fit(train[feats].values, ytr)
    t = test.assign(pred=model.predict(test[feats].values))
    ic_m = t.groupby('ym').apply(lambda d: spearmanr(d['pred'], d['y'])[0], include_groups=False)
    # 매달 예측 상위 10종목 - 하위 10종목 수익률 차이 (롱숏)
    def spread(d):
        d = d.sort_values('pred')
        return d['fwd_1m'].tail(10).mean() - d['fwd_1m'].head(10).mean()
    ls = t.groupby('ym').apply(spread, include_groups=False)
    n_used = int((np.abs(model.coef_) > 1e-10).sum())
    return [name, n_used, ic_m.mean(), ic_m.mean() / ic_m.std(), (ic_m > 0).mean(), ls.mean()]

rows = [
    test_report('OLS (규제 없음)', LinearRegression()),
    test_report('OLS (진짜 12개만)', LinearRegression(), REAL),
    test_report(f'Ridge a={best_r:g}', Ridge(alpha=best_r)),
    test_report(f'Lasso a={best_l:g}', Lasso(alpha=best_l, max_iter=10000)),
    test_report('ElasticNet', ElasticNet(alpha=best_l, l1_ratio=0.5, max_iter=10000)),
]
report = pd.DataFrame(rows, columns=['모델', '쓴 변수 수', '평균 IC', 'ICIR', 'IC>0 달 비율', '월 롱숏 수익'])
print(report.round(4).to_string(index=False))
# ICIR = 평균 IC / IC 표준편차 → IC가 매달 얼마나 꾸준한가 (0.5 넘으면 꽤 좋음)

# %% 최종 Lasso가 남긴 변수
lasso_final = Lasso(alpha=best_l, max_iter=10000).fit(Xtr, ytr)
coef_final = pd.Series(lasso_final.coef_, index=FEATS)
print(coef_final[coef_final != 0].sort_values())
print('살아남은 가짜 변수:', [c for c in NOISE if coef_final[c] != 0])

# %% 정리 — 11/18 실행 결과(F5, 약 5초)를 보고 쓴 것
# 학습 2022-01~2024-12 (1,768행) / 시험 2025-01~2026-09 (1,032행)
#   Lasso 계수 개수(진짜/가짜): alpha 0.0013 → 10/10, 0.0032 → 7/4, 0.0075 → 6/0  ← alpha를 키우면 가짜부터 빠짐
#   시간순 검증으로 고른 alpha: Ridge 31,623 / Lasso 0.0032
#   시험 평균 IC: OLS -0.036, Ridge -0.011, Lasso -0.055, ElasticNet -0.040  (전부 0 아래)
print('''
- 계수 그림: alpha가 커질수록 Ridge는 모든 계수가 같이 작아지고, Lasso는 하나씩 0이 된다.
- Lasso는 alpha 0.0075에서 가짜 변수 10개를 전부 0으로 만들었다. 하지만 검증 IC로 고른 0.0032에서는 가짜 4개가 남았다
  → '검증 점수가 가장 높은 alpha'도 잡음을 일부 고른다. 변수 수가 적고 기간이 짧으면 특히 그렇다.
- 규제가 강할수록(Ridge) 시험 IC가 OLS보다 덜 나빴다: -0.036 → -0.011. 규제 = 학습 기간 잡음을 덜 외우게 하는 것.
- 그래도 시험 기간 IC가 전부 음수 → 2022~2024에 통하던 관계가 2025~2026에 뒤집힘(시장 국면 변화).
  규제는 과적합을 줄여 줄 뿐, 없는 신호를 만들어 주지는 않는다.
- 금융에서 alpha는 반드시 시간순 검증으로 고른다 (책의 무작위 cv=5는 X).
- 스케일링은 달마다(단면) 한다 → 벌점이 공평해지고 미래 정보도 안 섞인다.
''')
