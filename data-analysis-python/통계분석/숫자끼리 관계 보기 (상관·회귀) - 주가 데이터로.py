# -*- coding: utf-8 -*-
# 숫자끼리 관계 보기 (상관·회귀) - 주가 데이터로
# 같은 주제의 책 코드: 참고코드/개정판_py/통계분석/숫자끼리 관계 보기 (상관·회귀).py (그대로 둠)
# 책 코드는 집값·자동차 가격 데이터로 했다. 이 파일은 똑같은 도구(상관, ols, VIF, 잔차 진단,
# 이상치, 변수 선택)를 주가에 쓰면 어디가 달라지는지 보여 준다.
#
# 데이터: 06_퀀트공부/연습데이터/prices.csv (50종목, 2021-01 ~ 2026-10, KRX 요청 없음)
# Spyder: F5 전체 실행 / Ctrl+Enter 현재 셀 실행 / F9 선택 줄 실행
#
# 기준 3사 어디에 쓰이나
#   어센드(Quantitative Research Engineer): 5번 날짜별 회귀(Fama-MacBeth), 6번 IC·IR, 7번 시간순 검증
#   라온지아이(퀀트 트레이더): 2번 베타(헤지 비율 = 회귀계수), 1번 상관(페어·분산)
#   SNJ LAB(기준점): 0번에서 열 단위 계산을 groupby로 묶는 파이썬다운 코드

# %% 0. 데이터 불러오기 · 수익률과 특징값 만들기
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

# %% 1. 상관 - 가격끼리 상관은 믿으면 안 된다, 수익률끼리 본다
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

# %% 1-2. 상관은 고정값이 아니다 - 60일 이동 상관
roll = ret_wide['005930'].rolling(60).corr(ret_wide['000660'])
roll.plot(figsize=(10, 4), title='삼성전자-SK하이닉스 60일 이동 수익률 상관')
plt.axhline(roll.mean(), color='red', linestyle='--', label=f'전체 평균 {roll.mean():.2f}')
plt.legend()
plt.show()
# 책 데이터는 "상관 = 숫자 하나"로 끝나지만, 주가는 시기마다 다르다.
# 폭락장엔 모든 종목 상관이 올라간다 → 분산투자가 제일 필요할 때 효과가 줄어든다.

# %% 2. 단순회귀 = 베타 구하기 (책의 price ~ sqft_living 자리)
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

# %% 2-2. 베타도 해마다 달라진다
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

# %% 3. 다중회귀 - 다음 달 수익률을 특징값 여러 개로 설명
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

# %% 3-2. 상관행렬 · VIF (책과 같은 방법)
from patsy import dmatrices
from statsmodels.stats.outliers_influence import variance_inflation_factor

print(panel[feats].corr().round(2))
y_, X_ = dmatrices('fwd1m ~ mom12_1 + rev1 + vol60 + liq', data=panel, return_type='dataframe')
vif = pd.DataFrame({'variable': X_.columns[1:],
                    'vif': [variance_inflation_factor(X_.values, i) for i in range(1, X_.shape[1])]})
print(vif.round(2))
# VIF 10 넘으면 빼라는 기준은 책과 같다. 주가 특징값은 "모멘텀 3개월·6개월·12개월"처럼
# 비슷한 걸 여러 개 넣을 때 VIF가 튄다.

# %% 4. 잔차 진단 - 주가에선 "정규성 실패"가 정상, 대신 표준오차를 고친다
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
# 책: 정규성 실패 → 로그 변환·이상치 삭제로 맞췄다.
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

# %% 5. 이상치 - 지우지 말고 끝을 자른다 (winsorize)
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

# %% 6. 날짜별 회귀 (Fama-MacBeth) - 퀀트 리서치에서 제일 많이 쓰는 회귀
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

# %% 7. IC · IR - 어센드 면접에서 나오는 말
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

# %% 8. 변수 선택은 시간순으로 검증 - 책의 전진·후진·단계적 선택이 위험한 이유
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
