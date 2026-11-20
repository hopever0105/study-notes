# -*- coding: utf-8 -*-
# 숫자끼리 관계 보기 (상관·회귀)


"""회귀분석의 개념
회귀분석: 하나 이상의 독립변수가 종속변수에 미치는 영향을 분석하고 수치로 표현하는 통계기법
전통적 회귀분석: 잔차 제곱합을 최소화하는 최소제곱법 사용 
결정계수(R^2)과 RMSE로 주로 판단함. 

SST: total sum of square: 총변동
SSE: Explained Sum of Squares설명된 변동 
SSR: Residual Sum of Squares 설명되지 않는 변동 

R^2: 결정계수 / 총 변동대비 설명된 변동의 비율 
즉, 회귀모형이 데이터를 얼마나 잘 설명하는지 나타내는 지표 

R^2 = 1- SSR/SST

RMSE: 평균 제곱근 오차 : Root Mean Square Error 
예측값과 실제 관측값 간의 차이를 기반으로 계산되는 지표 
예측값과 실제값의 차이를 제곱한 후 평균을 구한 후 그 값에 제곱근을 취하여 산출된다. 


다중선형회귀분석 평가 
독립변수 수가 증가되면 결정계수가 증가하는 바 조정된 수정결정계수(Adjusted R^2) 사용한다. 


회귀분석 검토사항 
(1) 모형이 데이터를 적절히 적합하는가? 
=> 잔차가 무작위로 분포해야 한다가 기본임 

1) 잔차가 랜덤하게 분포: 등분산성 만족-> 그냥 사용
2 등분산성 벗어나는 경우 -> 분산 증가하는 바 가중회귀직선이 적합
3) 선형성이 벗어나는 경우 -> 이차항을 추가한 다항회귀가 적합 
4) 잔차가 선형을 이루는 경우 -> 새로운 독립변수를 추가하는 것이 적합


(2) 회귀모형이 통계적으로 유의한가? 
전체의 유의성 : F통계량 검정 : H0 회귀모형 유의하지 않다, H1 회귀모형 유의하다

(3) 모형은 데이터를 얼마나 설명할 수 있는가? 
결정계수 확인 -> 얼머나 잘 설명하는가

(4) 모형 내의 회귀계수는 유의한가? 
각 독립변수의 회귀게수에 대해 개별적으로 검정을 수행
t- 통계량을 사용하며, p-value가 유의수준보다 작으면 회귀계수는 통계적으로 유의함. 

(5) 파이썬 패키지 
statsmodels.formula.api.ols(formula,data,subset=None,drop_cols= None, *args, **kwargs)
formula : 모델을 지정하는 공식 작성(데이터 타입 str)
ex) "price~ bedrooms+bathrooms+sqft_living + sqft_lot"
data: 모델이 적용되는 데이터(데이터타입: array_like)
drop_cols: 데이터에서 삭제할 컬럼 범주형 데이터 삭제시 등에서 사용(데이터 타입: array_like)

ols 함수의 반환값은 formula에 따라 학습된 회귀모형
model.summary() : 모형 적합 결과를 요약하여 제공한다.
model.params: 각 변수의 회귀게수를 반환
model.predict() : 새로운 데이터에 대한 예측값 반환
"""

#%%
# ======================================
# %% 2-0. 데이터 불러오기 · 수익률과 특징값 만들기
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf
import scipy.stats as stats
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'Malgun Gothic'   # 그래프 한글
plt.rcParams['axes.unicode_minus'] = False

# 이 파일 위치 기준으로 연습데이터 찾기 (Spyder F5면 __file__ 있음)
try:
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, '..', '..', '..', '연습데이터', 'prices.csv')
except NameError:
    path = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터\prices.csv'

px = pd.read_csv(path, dtype={'code': str}, parse_dates=['date'])
px = px.sort_values(['code', 'date']).reset_index(drop=True)

# 일별 수익률: 오늘 종가 / 어제 종가 - 1  (종목마다 따로 계산해야 하므로 groupby)
px['ret'] = px.groupby('code')['close'].pct_change()

# 시장 수익률 대용: 그날 50종목 수익률의 단순평균 (코스피 지수 대신)
mkt = px.groupby('date')['ret'].mean().rename('mkt')
px = px.merge(mkt, on='date', how='left')

# 넓은 표(행 = 날짜, 열 = 종목)로도 하나 만들어 둔다. 상관 계산은 이 모양이 편하다.
ret_wide = px.pivot(index='date', columns='code', values='ret')
close_wide = px.pivot(index='date', columns='code', values='close')
print(ret_wide.shape)   # (거래일 수, 50)

# %% 2-1. 상관 - 가격끼리 상관은 믿으면 안 된다, 수익률끼리 본다
# 책: house.corr() 로 price 와 sqft_living 의 상관을 봤다. 집 한 채 한 채는 서로 독립이라 괜찮다.
# 주가는 시간에 따라 쌓이는 값이라, 아무 관계 없는 두 종목도 "둘 다 올랐다"는 이유만으로
# 가격 상관이 0.9가 나올 수 있다(가짜 상관, spurious correlation).
#
# 숫자 예시 (5일)
#   A 가격: 100 102 103 105 106   → 수익률: +2.0% +1.0% +1.9% +1.0%
#   B 가격: 100 101 103 104 106   → 수익률: +1.0% +2.0% +1.0% +1.9%
#   가격 상관   = +0.97 (둘 다 오르니까)
#   수익률 상관 = -1.00 (A가 많이 오른 날 B는 적게 올랐다 → 날마다는 반대로 움직임)
a = pd.Series([100, 102, 103, 105, 106])
b = pd.Series([100, 101, 103, 104, 106])
print('가격 상관 :', round(a.corr(b), 3))
print('수익률 상관:', round(a.pct_change().corr(b.pct_change()), 3))

# 실제 데이터: 삼성전자(005930) vs SK하이닉스(000660), 삼성전자 vs 셀트리온(068270)
pairs = [('005930', '000660'), ('005930', '068270')]
for x, y in pairs:
    p_corr = close_wide[x].corr(close_wide[y])
    r_corr = ret_wide[x].corr(ret_wide[y])                       # 피어슨: 크기 그대로
    s_corr = ret_wide[x].corr(ret_wide[y], method='spearman')    # 스피어만: 순위로 바꿔서
    print(f'{x}-{y}  가격상관 {p_corr:.2f} | 수익률 피어슨 {r_corr:.2f} | 수익률 스피어만 {s_corr:.2f}')
# 피어슨 vs 스피어만: 하루 -15% 같은 튀는 날 하나가 피어슨을 크게 흔든다.
# 스피어만은 순위만 보니까 튀는 날에 덜 흔들린다. → 6번 IC에서 스피어만을 쓰는 이유

# %% 2-1-2. 상관은 고정값이 아니다 - 60일 이동 상관
roll = ret_wide['005930'].rolling(60).corr(ret_wide['000660'])
roll.plot(figsize=(10, 4), title='삼성전자-SK하이닉스 60일 이동 수익률 상관')
plt.axhline(roll.mean(), color='red', linestyle='--', label=f'전체 평균 {roll.mean():.2f}')
plt.legend()
plt.show()
# 책 데이터는 "상관 = 숫자 하나"로 끝나지만, 주가는 시기마다 다르다.
# 폭락장엔 모든 종목 상관이 올라간다 → 분산투자가 제일 필요할 때 효과가 줄어든다.

# %% 2-2. 단순회귀 = 베타 구하기 (책의 price ~ sqft_living 자리)
# 종목 수익률 = 알파 + 베타 × 시장 수익률 + 잔차
# 베타 1.3 이면: 시장이 하루 +1% 일 때 이 종목은 평균 +1.3%
sam = px[px['code'] == '005930'].dropna(subset=['ret', 'mkt'])
lr = smf.ols('ret ~ mkt', data=sam).fit()
print(lr.summary())

# 같은 값을 공식으로: 베타 = Cov(종목, 시장) / Var(시장)
beta_formula = np.cov(sam['ret'], sam['mkt'])[0, 1] / np.var(sam['mkt'], ddof=1)
print('ols 베타:', round(lr.params['mkt'], 4), '/ 공식 베타:', round(beta_formula, 4))
# 알파는 하루 값이라 작아 보인다 → 1년(252일)으로 바꿔서 읽는다
print('연 알파(대략):', f"{lr.params['Intercept'] * 252:.2%}")

plt.figure(figsize=(6, 6))
plt.scatter(sam['mkt'], sam['ret'], s=4, alpha=0.4)
xs = np.linspace(sam['mkt'].min(), sam['mkt'].max(), 50)
plt.plot(xs, lr.params['Intercept'] + lr.params['mkt'] * xs, color='red')
plt.xlabel('시장(50종목 평균) 일수익률')
plt.ylabel('삼성전자 일수익률')
plt.title(f"베타 = {lr.params['mkt']:.2f}")
plt.show()

# %% 2-2-2. 베타도 해마다 달라진다
beta_by_year = {}
for yr, g in sam.groupby(sam['date'].dt.year):
    beta_by_year[yr] = smf.ols('ret ~ mkt', data=g).fit().params['mkt']
print(pd.Series(beta_by_year, name='연도별 베타').round(2))
# 헤지할 때 쓰는 베타는 "과거 전체 평균"이 아니라 최근 값으로 계속 다시 잡는다.

# 50종목 전부 베타 한 번에 (groupby + 함수)
def get_beta(g):
    g = g.dropna(subset=['ret', 'mkt'])
    return np.cov(g['ret'], g['mkt'])[0, 1] / np.var(g['mkt'], ddof=1)

betas = px.groupby('code').apply(get_beta).sort_values()
print('베타 낮은 5:\n', betas.head().round(2))
print('베타 높은 5:\n', betas.tail().round(2))

# %% 2-3. 다중회귀 - 다음 달 수익률을 특징값 여러 개로 설명
# 책: Price ~ EngineSize + RPM + Weight + ... (자동차 93대, 행끼리 독립)
# 여기: 다음 달 수익률 ~ 모멘텀 + 단기반전 + 변동성 + 거래대금 (종목 × 월)
#
# 특징값 4개 (모두 그 날까지 알 수 있는 값만 → 미래 정보 섞이지 않게)
#   mom12_1 : 12개월 전 ~ 1개월 전 수익률 (최근 1개월은 뺌, 단기반전과 겹치지 않게)
#   rev1    : 최근 1개월 수익률 (지난달 많이 오른 종목이 다음 달 쉬는 현상)
#   vol60   : 최근 60일 일수익률 표준편차 × √252 (연 변동성)
#   liq     : 최근 60일 평균 거래대금의 로그 (규모·유동성 대용)
g = px.groupby('code')
px['mom12_1'] = g['close'].shift(21) / g['close'].shift(252) - 1
px['rev1'] = g['close'].shift(0) / g['close'].shift(21) - 1
px['vol60'] = g['ret'].transform(lambda s: s.rolling(60).std()) * np.sqrt(252)
# 거래정지일은 거래대금이 0으로 들어 있다(500행). 0을 그대로 두면 log(0) = -무한대 → 회귀가 깨진다.
# 0은 "그날 거래 없음"이라 빈칸으로 바꾸고, 60일 중 거래된 날이 40일 이상일 때만 평균을 낸다.
px['amount_ok'] = px['amount'].where(px['amount'] > 0)
px['liq'] = np.log(px.groupby('code')['amount_ok'].transform(lambda s: s.rolling(60, min_periods=40).mean()))

# 월말 하루만 뽑는다. 매일 뽑아서 "다음 21일 수익률"을 쓰면 오늘과 내일의 목표값이
# 20일이 겹쳐서 행끼리 독립이 아니다(겹침 문제). 월말만 뽑으면 다음 달 수익률이 안 겹친다.
px['ym'] = px['date'].dt.to_period('M')
month_end = px.groupby(['code', 'ym']).tail(1).copy()
month_end = month_end.sort_values(['code', 'date'])
month_end['fwd1m'] = month_end.groupby('code')['close'].shift(-1) / month_end['close'] - 1

feats = ['mom12_1', 'rev1', 'vol60', 'liq']
panel = month_end.dropna(subset=feats + ['fwd1m']).reset_index(drop=True)
print(panel[['date', 'code'] + feats + ['fwd1m']].head())
print('행 수:', len(panel), '/ 월 수:', panel['ym'].nunique())

pooled = smf.ols('fwd1m ~ mom12_1 + rev1 + vol60 + liq', data=panel).fit()
print(pooled.summary())
# R² 가 0.01 ~ 0.03 수준이어도 놀라지 말 것. 책의 자동차 가격은 R² 0.7도 나오지만,
# 주식 다음 달 수익률은 대부분 잡음이라 1%만 설명해도 쓸 만한 신호일 수 있다.

# %% 2-3-2. 상관행렬 · VIF (책과 같은 방법)
from patsy import dmatrices
from statsmodels.stats.outliers_influence import variance_inflation_factor

print(panel[feats].corr().round(2))
y_, X_ = dmatrices('fwd1m ~ mom12_1 + rev1 + vol60 + liq', data=panel, return_type='dataframe')
vif = pd.DataFrame({'variable': X_.columns[1:],
                    'vif': [variance_inflation_factor(X_.values, i) for i in range(1, X_.shape[1])]})
print(vif.round(2))
# VIF 10 넘으면 빼라는 기준은 책과 같다. 주가 특징값은 "모멘텀 3개월·6개월·12개월"처럼
# 비슷한 걸 여러 개 넣을 때 VIF가 튄다.

# %% 2-4. 잔차 진단 - 주가에선 "정규성 실패"가 정상, 대신 표준오차를 고친다
resid = pooled.resid
from statsmodels.stats.stattools import durbin_watson, jarque_bera
print('Shapiro p  :', stats.shapiro(resid.sample(min(len(resid), 4999), random_state=0))[1])
jb, jb_p, skew, kurt = jarque_bera(resid)
print(f'Jarque-Bera p: {jb_p:.4g} / 왜도 {skew:.2f} / 첨도 {kurt:.2f} (정규분포는 첨도 3)')
print('Durbin-Watson:', round(durbin_watson(resid), 3))

fig, ax = plt.subplots(1, 2, figsize=(12, 5))
sm.qqplot(resid, line='s', ax=ax[0])
ax[0].set_title('Q-Q: 양 끝이 휜다 = 꼬리가 두껍다')
ax[1].scatter(pooled.fittedvalues, resid, s=4, alpha=0.4)
ax[1].axhline(0, color='red', linestyle='--')
ax[1].set_title('잔차 vs 예측값')
plt.tight_layout()
plt.show()
#  정규성 실패 → 로그 변환·이상치 삭제로 맞췄다.
# 주가: 수익률 꼬리가 두꺼운 건 시장의 성질이라 변환으로 없어지지 않는다.
#       더 큰 문제는 "같은 달의 50종목은 같이 움직인다"(시장 전체가 빠진 달은 다 같이 빠짐).
#       행 2,000개가 사실상 독립 표본 몇십 개(월 수)짜리라서 t값이 부풀려진다.
#       → 같은 달끼리 묶어서 표준오차 계산 (클러스터 표준오차)
clustered = smf.ols('fwd1m ~ mom12_1 + rev1 + vol60 + liq', data=panel).fit(
    cov_type='cluster', cov_kwds={'groups': panel['ym'].astype(str).factorize()[0]})
compare = pd.DataFrame({'계수': pooled.params,
                        't (보통)': pooled.tvalues,
                        't (월로 묶음)': clustered.tvalues}).round(3)
print(compare)
# 보통 t가 2를 넘어 "유의"해 보여도, 월로 묶으면 1 근처로 떨어지는 경우가 많다.

# %% 2-5. 이상치 - 지우지 말고 끝을 자른다 (winsorize)
# 책: IQR 상한 넘는 자동차를 지웠다.
# 주가: 다음 달 +80% 오른 종목, -50% 빠진 종목을 지우면 "실제로 일어난 일"을 지우는 것이다.
#       특히 폭락 종목을 지우면 결과가 좋아 보이게 치우친다(생존 편향과 같은 방향).
#       → 달마다 하위 5%·상위 95% 값으로 눌러 둔다 (행은 남기고 크기만 줄임)
# 숫자 예시: 한 달 수익률 [-50%, -3%, 0%, +2%, +5%, +80%], 하위 5%=-40%, 상위 95%=+60% 라면
#            → [-40%, -3%, 0%, +2%, +5%, +60%]  (6개 그대로, 극단값만 안쪽으로)
def winsorize_by_month(df, col, lo=0.05, hi=0.95):
    q = df.groupby('ym')[col].transform
    return df[col].clip(lower=q(lambda s: s.quantile(lo)), upper=q(lambda s: s.quantile(hi)))

panel_w = panel.copy()
for c in feats + ['fwd1m']:
    panel_w[c] = winsorize_by_month(panel_w, c)
w_res = smf.ols('fwd1m ~ mom12_1 + rev1 + vol60 + liq', data=panel_w).fit(
    cov_type='cluster', cov_kwds={'groups': panel_w['ym'].astype(str).factorize()[0]})
print(pd.DataFrame({'원래 계수': clustered.params, '자른 뒤 계수': w_res.params,
                    '자른 뒤 t': w_res.tvalues}).round(3))

# %% 2-6. 날짜별 회귀 (Fama-MacBeth) - 퀀트 리서치에서 제일 많이 쓰는 회귀
# 3번처럼 전부 한 번에 넣지 않고, "달마다 50종목으로 회귀 1번"을 반복 → 계수 시계열을 얻는다.
# 계수 평균 / (계수 표준편차 / √달 수) = t값
# 숫자 예시: 4달 동안 rev1 계수가 -0.10, -0.05, +0.02, -0.07 이면
#            평균 -0.05, 표준편차 0.051, t = -0.05 / (0.051/√4) = -1.96
# 장점: 같은 달 종목끼리 같이 움직이는 문제가 자동으로 빠진다(달마다 따로 회귀하니까).
coefs = []
for ym, gm in panel_w.groupby('ym'):
    if len(gm) < 20:
        continue
    # 달마다 특징값을 평균 0, 표준편차 1로 맞춘다 → 계수 = "1표준편차 높을 때 다음 달 수익률 차이"
    z = gm[feats].apply(lambda s: (s - s.mean()) / s.std())
    res = sm.OLS(gm['fwd1m'], sm.add_constant(z)).fit()
    coefs.append(res.params.rename(ym))
fm = pd.DataFrame(coefs)
fm_table = pd.DataFrame({'평균 계수': fm.mean(),
                         't값': fm.mean() / (fm.std() / np.sqrt(len(fm)))}).round(4)
print(fm_table)
fm[feats].cumsum().plot(figsize=(10, 4), title='특징값별 계수 누적 (오른쪽 위로 가면 꾸준히 +)')
plt.show()

# %% 2-7. IC · 
# IC(Information Coefficient) = 달마다 "특징값 순위"와 "다음 달 수익률 순위"의 스피어만 상관
# 숫자 예시 (5종목)
#   종목       A   B   C   D   E
#   모멘텀순위  1   2   3   4   5
#   수익률순위  2   1   3   5   4
#   d = 순위 차: -1, 1, 0, -1, 1 → d² 합 = 4
#   스피어만 = 1 - 6×4 / (5×(25-1)) = 1 - 24/120 = 0.80
# 실제로는 IC 0.03~0.05만 꾸준해도 쓸 만하다. 종목 수가 많으면 작은 우위가 쌓이기 때문.
# IR(여기서는 ICIR) = IC 평균 / IC 표준편차 → "얼마나 꾸준한가". 0.5 넘으면 좋은 편.
ic = panel.groupby('ym').apply(
    lambda gm: pd.Series({f: stats.spearmanr(gm[f], gm['fwd1m'])[0] for f in feats}))
ic_table = pd.DataFrame({'IC 평균': ic.mean(),
                         'IC 표준편차': ic.std(),
                         'ICIR': ic.mean() / ic.std(),
                         'IC>0 비율': (ic > 0).mean(),
                         't값': ic.mean() / ic.std() * np.sqrt(len(ic))}).round(3)
print(ic_table)
# 스피어만이라 5번처럼 이상치를 자를 필요가 없다(순위는 극단값에 안 흔들림).

# %% 2-8. 변수 선택은 시간순으로 검증 - 책의 전진·후진·단계적 선택이 위험한 이유
# 책: AIC가 제일 낮은 변수 조합을 "전체 데이터"로 골랐다.
# 주가: 전체 기간으로 고르면 미래를 보고 고른 셈이다. 2025년 데이터를 보고 고른 변수로
#       2025년을 "예측"하면 당연히 잘 맞는다.
# → 2024년까지로 고르고 학습, 2025년부터는 처음 보는 데이터로 평가
import itertools
train = panel_w[panel_w['date'] < '2025-01-01']
test = panel_w[panel_w['date'] >= '2025-01-01']
print('학습 월 수:', train['ym'].nunique(), '/ 평가 월 수:', test['ym'].nunique())

rows = []
for k in range(1, len(feats) + 1):
    for combo in itertools.combinations(feats, k):
        formula = 'fwd1m ~ ' + ' + '.join(combo)
        m = smf.ols(formula, data=train).fit()
        pred = m.predict(test)
        # 평가는 달마다 예측 순위 vs 실제 순위 스피어만 → 평균 (= 예측값의 IC)
        tmp = test.assign(pred=pred)
        oos_ic = tmp.groupby('ym').apply(lambda gm: stats.spearmanr(gm['pred'], gm['fwd1m'])[0]).mean()
        rows.append({'변수': formula[8:], '학습 AIC': m.aic, '평가 IC': oos_ic})
sel = pd.DataFrame(rows).sort_values('학습 AIC').reset_index(drop=True)
print(sel.round(4))
# 볼 것: 학습 AIC 1등 조합이 평가 IC도 1등인가? 보통은 아니다.
# 그래서 퀀트는 "학습 기간 성적"이 아니라 "안 본 기간 성적"으로 고른다 (López de Prado 7장 교차검증).

# %%
import pandas as pd 
import numpy as np 
import warnings
warnings.filterwarnings('ignore') # 모든 경고를 무시합니다.

house = pd.read_csv("https://raw.githubusercontent.com/ADPclass/ADP_book_ver01/main/data/kc_house_data.csv")
house = house[["price","sqft_living"]]
## 독립변수와 종속변수의 선형 가정 
house.corr()
# 선형 회귀분석 이전에 pandas.corr()함수 사용하여 상관관계 확인 
# 0.720035로 양의 상관관계 존재함. 


# %%
from statsmodels.formula.api import ols
import matplotlib.pyplot as plt

# 변수 할당 
y = house['price']
X = house[['sqft_living']]

# 단순 선형 회귀 모형 적합
lr = ols('price ~ sqft_living', data=house).fit()
y_pred = lr.predict(X)

# 시각화 
plt.scatter(X, y) ## 원 데이터 산포도
plt.plot(X, y_pred, color='red') ## 회귀직선 추가 
plt.xlabel('sqft_living', fontsize=10)
plt.ylabel('price', fontsize=10)
plt.title('Linear Regression Result')
plt.show()


# 독립변수 x는 데이터프레임 형태, 종속변수 y는 시리즈 -> 단순회귀분석 수행
# 예측값은 y_pred , 회귀선의 적합도 확인 
# 전체데이터 충분히 설명에는 무리가 있음. 
# 
# %%
lr.summary()
# 다만 f통꼐량 및 p-value 0에 매우가까운 바 통계적으로 유의함
# 결정계수는 0.493으로 49.3 %만을 설명함 통계적유의성과 설명력이 높은거는 아님
# 높은 확률로 0.493정도는 설명한다 이정도가 맞는듯 
# 모형내의 회귀변수 유의성확인 역시 p-value 0.05보다 작은 바 유의한 변수 
#%% 
"""다중회귀분석 유의사항
다중공선성
-> 독립변수의 개수로인해 문제가 생김. 독립변수 두개이상이 경우에 다중공선성 문제 반드시 고려할 것. 
-> 독립변수 사이에서 강한 솽관관계로 인해 발생, 해석력이 저해됨 
-> 패널티를 부여하거나 너무 상관성이 높으면 그 변수 제거할 것. 
-> LASSO , RIDGE 회귀분석 사용

다중공선성 진단
(1) 독립변수 간 상관계수 확인 
일반적으로 0.9이상이면 다중공선성 존재한다고 판단

(2) 허용오차 확인
다중공선성이 의심되는 독립변수를 다른 독립변수로 회귀분석하여 허용오차 계산
허용오차 0.1이하이면 다중공선성 심각하다고 통산적으로 판단 
허용오차는 1-R^2

(3) 분산팽창지수(VIF) 확인
VIF = 1/(1-R^2)
-> 10이상이면 다중공선성 존재 가능성 높다 판단

(4) 허용오차와 VIF 관계 
결정계수에 의해 결정되는 지표 
결정게수는 하나의 독립변수가 다른 독립변수들에 의해 얼머나 설명되는지를 판단
변수가 증가할 수록 조합의 수에 비례하여 (nC2) 증가
"""

"""변수선택법
적절한 설명변수를 선택해야 하는 바, 개수 최적화가 필요해 대표적 기준으로 AIC,BIC,F-value가 있다. 
AIC = -2log(L) + 2K
L = likelihood function
k: number of parameter

전진선택법: 하나씩 변수 추가
후진소거법: 하나씩 변수 제거
단계적 선택법 : 변수 추가 제거 동시에 하는 것.  성능은 가장 좋음 

"""

# %%
import pandas as pd
# 데이터 불러오기
Cars = pd.read_csv('https://raw.githubusercontent.com/ADPclass/ADP_book_ver01/main/data/Cars93.csv')
Cars.info()

# %%
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
# ols 모델의 formula을 정의할 때, 일부 특수문자는 쓸 수 없기에, 컬럼 특수문자 제거 
Cars.columns = Cars.columns.str.replace(".","")
model = smf.ols(formula ="Price ~ EngineSize + RPM + Weight+ Length + MPGcity + MPGhighway", data = Cars)
result = model.fit()
result.summary()

# 수정결정계수 0.542
# 변수선택법 도입 가능 

# %% 상관관계 분석
# 먼저 변수선택법 도입 전에 다중공선성 확인해야 하는 바 상관관계 파악
Cars[['EngineSize','RPM' , 'Weight','Length','MPGcity','MPGhighway']].corr()
# MpGcity와 MPGhighway 상관 0.9이상 다중공선성 존재 but 둘중 뭘 ㅈ거할지는 파악 어려움 이때 VIF 사용
# %% VIF
from patsy import dmatrices
from statsmodels.stats.outliers_influence import variance_inflation_factor

# 독립변수와 종속변수를 데이터프레임으로 나누어 저장하는 함수 
y,X = dmatrices("Price ~ EngineSize + RPM + Weight+ Length + MPGcity + MPGhighway",
                data = Cars,return_type ="dataframe")

# 독립변수끼리의 VIF값을 계산하여 데이터프레임으로 만드는 과정 
vif_list = []
for i in range(1,len(X.columns)): 
    vif_list.append([variance_inflation_factor(X.values,i), X.columns[i]])
pd.DataFrame(vif_list,columns=['vif','variable'])

# 양자 MpGcity와 MPGhighway 모두 VIF 10이상인 바 제거함 

# %%
model = smf.ols(formula ="Price ~ EngineSize + RPM + Weight  + MPGhighway", data = Cars)
result = model.fit()
result.summary()

# 재분석 해도 수정결정계수나 AIC 값은 큰 변화 없음. 
# 반드시 성능향상으로 이어지지 않음
# 그러나 계산량 줄어들어서 데이터관리 해석어려움 부담 감소 효과 

# %%
import time
import itertools
def processSubset(X,y, feature_set):
            model = sm.OLS(y,X[list(feature_set)]) # Modeling
            regr = model.fit() # 모델 학습
            AIC = regr.aic # 모델의 AIC
            return {"model":regr, "AIC":AIC}
        
#%% 전진선택법
def forward(X, y, predictors):
    # 데이터 변수들이 미리정의된 predictors에 있는지 없는지 확인 및 분류
    remaining_predictors = [p for p in X.columns.difference(['Intercept']) if p not in predictors]
    results = []
    for p in remaining_predictors:
        results.append(processSubset(X=X, y= y,            feature_set=predictors+[p]+['Intercept']))
        
    # 데이터프레임으로 변환
    models = pd.DataFrame(results)
    # AIC가 가장 낮은 것을 선택
    best_model = models.loc[models['AIC'].argmin()] # index
    print("Processed ", models.shape[0], "models on", len(predictors)+1, "predictors in")
    print('Selected predictors:',best_model['model'].model.exog_names,' AIC:',best_model[0] )
    return best_model

# %%
# 후진소거법
def backward(X,y,predictors):
    tic = time.time()
    results = []
    
    # 데이터 변수들이 미리정의된 predictors 조합 확인
    for combo in itertools.combinations(predictors, len(predictors) -1):
        results.append(processSubset(X=X, y= y,        feature_set = list(combo)+['Intercept']))
    models = pd.DataFrame(results)
    
    # 가장 낮은 AIC를 가진 모델을 선택
    best_model = models.loc[models['AIC'].argmin()]
    toc = time.time()
    print("Processed ", models.shape[0], "models on",          len(predictors) -1, "predictors in", (toc - tic))
    print('Selected predictors:',best_model['model'].model.exog_names,         'AIC:',best_model[0] )

    return best_model

# %%
# 단계적 선택법
def Stepwise_model(X,y):
    Stepmodels = pd.DataFrame(columns=["AIC", "model"])
    tic = time.time()
    predictors = []
    Smodel_before = processSubset(X,y,predictors+['Intercept'])['AIC']

    for i in range(1, len(X.columns.difference(['Intercept'])) +1):
        Forward_result = forward(X=X, y=y, predictors=predictors) 
        print('forward')
        Stepmodels.loc[i] = Forward_result
        predictors = Stepmodels.loc[i]["model"].model.exog_names
        predictors = [ k for k in predictors if k !='Intercept']
        Backward_result = backward(X=X, y=y, predictors=predictors)

        if Backward_result['AIC']< Forward_result['AIC']:
            Stepmodels.loc[i] = Backward_result
            predictors = Stepmodels.loc[i]["model"].model.exog_names
            Smodel_before = Stepmodels.loc[i]["AIC"]
            predictors = [ k for k in predictors if k !='Intercept']
            print('backward')

        if Stepmodels.loc[i]['AIC']> Smodel_before:
            break
        else:
            Smodel_before = Stepmodels.loc[i]["AIC"]
    toc = time.time()
    print("Total elapsed time:", (toc - tic), "seconds.")

    return (Stepmodels['model'][len(Stepmodels['model'])])

# %%
Stepwise_best_model = Stepwise_model(X=X, y=y)
# AIC가 가장 낮은 값을 찾을 것
# 다만 실무에서는 단순히 AIC 만 의존하지는 않는다. 
# 중요한 판단기준이나 절대적이지는 않다. 
# %%
Stepwise_best_model.summary()
# 선정된 독립변수 기반 선형 회귀모델 구축 완성 
# 이제 통계적 검증과정이 필요
# %% 모형에 따른 회귀진단 
import scipy.stats as stats
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson

# 1. 최종 모델에서 잔차(Residual)와 예측값(Fitted)을 추출합니다.
# result는 앞선 실습에서 fit()을 완료한 다중회귀 모델 객체입니다.
residual = result.resid
fitted = result.fittedvalues

# 2. 잔차의 정규성 검정 (Shapiro-Wilk Test)
# p-value가 0.05보다 크면 정규성을 만족한다고 해석합니다.
s_stat, p_val = stats.shapiro(residual)
print(f"Shapiro-Wilk 정규성 검정 p-value: {p_val:.4f}")

# 3. 잔차의 독립성 검정 (Durbin-Watson)
# 2에 가까울수록 독립적이며, 보통 1.5 ~ 2.5 사이면 통과입니다.
dw_score = durbin_watson(residual)
print(f"Durbin-Watson 지수: {dw_score:.4f}")

# 4. 시각화 진단 (Q-Q Plot & 잔차 산점도)
fig, ax = plt.subplots(1, 2, figsize=(12, 5))

# (1) 잔차의 정규성 시각화 (Q-Q Plot)
# 점들이 대각선 실선에 붙어 있을수록 정규성을 만족합니다.
sm.qqplot(residual, line='s', ax=ax[0])
ax[0].set_title("Normal Q-Q Plot")

# (2) 잔차의 등분산성 시각화 (Residual vs Fitted)
# 점들이 특정 패턴 없이 고르게 흩어져 있어야 합니다.
ax[1].scatter(fitted, residual)
ax[1].axhline(y=0, color='red', linestyle='--')
ax[1].set_xlabel('Fitted values')
ax[1].set_ylabel('Residuals')
ax[1].set_title('Residual vs Fitted Plot')

plt.tight_layout()
plt.show()


"""
1. 정규성 
shapiro-Wilk 검정결과, p-value가 0.05보다 작은 0.000 으로 나타난다. 
따라서 잔차가 정규분포 따르지 않음
또한 qqplot에서 점들이 직선에서 크게 버어나는 경우 다량 정규성 확보되지 않음
이상치 제거나 로그 제곱근 변환 등 데이터 전처리 필요

2. 독립성
DUurbin-Watson 통계량 이용 잔차의 독립성 검정 
1.5~2.5 범위 정도가 독립성 확보 
1.39수준인바, 잔차 간 자기상관 존재 가능성 잇음

3. 등분산성
Residual vs Fitted Plot 통해 잔차 분산 확인
잔차가 일정한 범위 내에서 무작위로 분포해야 등분산성 가정이 만족된다. 
무작위라고 보기 어렵게 일정부분 몰려잇는 바, 등분산성 가정 위반된 것으로 보인다. 
"""



# %% 데이터 가공
""" 
회귀모형 문제 해결 위해 데이터 전처리 수행 

문제 인식 -> 원인 분석(탐색적 데이터 분석 ,EDA) -> 해결방안 도출(전처리) -> 결과 검증


"""
import seaborn as sns
import matplotlib.pyplot as plt

# Price의 분포 확인
plt.figure(figsize=(10, 5))

# 1. 원본 데이터 (sns.distplot은 구버전/신버전 공용입니다)
plt.subplot(1, 2, 1)
sns.distplot(Cars['Price'], kde=True) 
plt.title('Original Price Distribution')
# 분석결과 한쪽으로 치우진 분포를 가지는 바, 
# 오른쪽으로 긴 꼬리를 가지는 형태임 이상치 제거하고 로그변환을 적용하는 것이 적절

# %% 이상치 확인 및 제거 
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Price 변수의 이상치 시각화 (Boxplot)
plt.figure(figsize=(7, 5))
sns.boxplot(x=Cars['Price'])
plt.title('Price Boxplot')
plt.show()

# 2. IQR 방식을 이용한 이상치 경계 계산
Q1 = Cars['Price'].quantile(0.25)
Q3 = Cars['Price'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

print(f"이상치 상한선: {upper_bound}")

# 3. 이상치 제거
# 상한선을 넘는 데이터가 몇 개인지 확인하고 제거합니다.
outliers = Cars[Cars['Price'] > upper_bound]
print(f"제거될 이상치 개수: {len(outliers)}개")

Cars_clean = Cars[Cars['Price'] <= upper_bound].copy()

# %% 최종 전처리 후 잔차 검증
import numpy as np

# 1. 이상치가 제거된 데이터(Cars_clean)에 로그 변환 적용
Cars_clean['log_Price'] = np.log1p(Cars_clean['Price'])

# 2. 최종 모델 적합
final_model = smf.ols(formula ="log_Price ~ EngineSize + RPM + Weight", data = Cars_clean)
final_result = final_model.fit()

# 3. 잔차 검증 재실행
final_residual = final_result.resid
_, final_p_val = stats.shapiro(final_residual)
final_dw = durbin_watson(final_residual)

print(f"[최종 전처리 후 잔차 검증]")
print(f"Shapiro-Wilk p-value: {final_p_val:.4f}")
print(f"Durbin-Watson: {final_dw:.4f}")

# 4. 시각화로 확인
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
sm.qqplot(final_residual, line='s', ax=plt.gca())
plt.title("Final Model Q-Q Plot")

plt.subplot(1, 2, 2)
plt.scatter(final_result.fittedvalues, final_residual)
plt.axhline(y=0, color='r', linestyle='--')
plt.title("Final Model Residual Plot")
plt.show()

#Shapiro-Wilk p-value: 0.0760
# Durbin-Watson: 1.4834


# %% 로그변환 
import seaborn as sns
import matplotlib.pyplot as plt

# Price의 분포 확인
plt.figure(figsize=(10, 5))

# 1. 원본 데이터 (sns.distplot은 구버전/신버전 공용입니다)
plt.subplot(1, 2, 1)
sns.distplot(Cars_clean['Price'], kde=True) 
plt.title('Original Price Distribution')

# 2. 로그 변환 데이터
plt.subplot(1, 2, 2)
sns.distplot(np.log1p(Cars['Price']), kde=True, color='orange')
plt.title('Log-transformed Price Distribution')

plt.tight_layout()
plt.show()


"""
전처리 결과 해석

전처리 이전에는 정규성 검정의 p-value가 0.000임. 
그러나 이상치 제거와 로그 변환을 적용한 이후 p-value가 0.0760으로 증가하여 
유의수준 0.05하에서 잔차의 정규성 가정 만족 
해당 모형은 통계적 가정 충족, 회귀계수에 대한 해석이 가능한 상태로 개선되었다고 판단. 

"""

# %% 최종 분석 모델 서렴ㅇ 
import statsmodels.formula.api as smf

# 1. 이상치가 제거된 Cars_clean 데이터를 사용하여 모델 생성
# 모델명은 구분을 위해 clean_model로 지정합니다.
clean_model = smf.ols(formula ="Price ~ EngineSize + RPM + Weight", data = Cars_clean)
clean_result = clean_model.fit()

# 2. 모델 결과 요약
clean_result.summary()


""" 결론
데이터 이상치 제거, 정규성 확보 위해 로그 변환 적용하여 분포의 왜도를 완화
그 이후 단계적 선택법 통해 Weight, RPM, EngineSize 변수 포함된 다중선형 회귀모델 최종 선정
수정결정계수 : 0.554 
설명력 개선은 맞음 다만 충분히 설명은 못함 
추가적 변수 포함이 필요해보임. 


"""







