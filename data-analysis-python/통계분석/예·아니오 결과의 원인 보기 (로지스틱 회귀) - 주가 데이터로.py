# -*- coding: utf-8 -*-
# 예·아니오 결과의 원인 보기 (로지스틱 회귀) - 주가 데이터로
# 같은 주제의 책 코드: 참고코드/개정판_py/통계분석/예·아니오 결과의 원인 보기 (로지스틱 회귀).py (그대로 둠)
# 책 코드는 타이타닉 생존(1/0) ~ 객실등급 + 성별 + 나이 + 운임 으로 했다.
# 이 파일은 "다음 달에 이 종목이 다른 종목들보다 잘할까(1/0)"를 같은 smf.logit 으로 본다.
#
# 데이터: 06_퀀트공부/연습데이터/prices.csv (50종목, 2021-01 ~ 2026-10, KRX 요청 없음)
# Spyder: F5 전체 실행 / Ctrl+Enter 현재 셀 실행 / F9 선택 줄 실행
#
# 기준 3사 어디에 쓰이나
#   어센드(Quantitative Research Engineer): ML 알파의 가장 단순한 형태(분류 모델), 4번 시간순 검증,
#                                          5번 무작위 섞기 검증이 왜 틀렸는지 설명
#   라온지아이(퀀트 트레이더): 확률 출력 → "이길 확률 55%면 얼마나 걸까" 판단의 출발점
#   SNJ LAB(기준점): 0번 특징값 함수를 한 곳에 모아 학습·평가에 똑같이 쓰기(정합성)

# %% 0. 데이터 불러오기 · 특징값 만들기 (상관·회귀 파일과 같은 특징값)
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

try:
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, '..', '..', '..', '연습데이터', 'prices.csv')
except NameError:
    path = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터\prices.csv'

px = pd.read_csv(path, dtype={'code': str}, parse_dates=['date'])
px = px.sort_values(['code', 'date']).reset_index(drop=True)
g = px.groupby('code')
px['ret'] = g['close'].pct_change()

# 특징값 (그 날까지 알 수 있는 값만)
#   mom12_1 : 12개월 전 ~ 1개월 전 수익률
#   rev1    : 최근 1개월 수익률
#   vol60   : 최근 60일 연 변동성
#   liq     : 최근 60일 평균 거래대금의 로그 (거래정지일 0원은 빈칸 처리)
px['mom12_1'] = g['close'].shift(21) / g['close'].shift(252) - 1
px['rev1'] = px['close'] / g['close'].shift(21) - 1
px['vol60'] = g['ret'].transform(lambda s: s.rolling(60).std()) * np.sqrt(252)
px['amount_ok'] = px['amount'].where(px['amount'] > 0)
px['liq'] = np.log(px.groupby('code')['amount_ok'].transform(lambda s: s.rolling(60, min_periods=40).mean()))

# 월말 하루만 (다음 달 수익률이 서로 안 겹치게)
px['ym'] = px['date'].dt.to_period('M')
me = px.groupby(['code', 'ym']).tail(1).sort_values(['code', 'date']).copy()
me['fwd1m'] = me.groupby('code')['close'].shift(-1) / me['close'] - 1

feats = ['mom12_1', 'rev1', 'vol60', 'liq']
panel = me.dropna(subset=feats + ['fwd1m']).reset_index(drop=True)

# %% 1. 목표값(1/0) 정하기 - "오를까"가 아니라 "남들보다 잘할까"
# 책: survived 는 이미 1/0 으로 주어졌다.
# 주가: 1/0 을 직접 만들어야 하고, 어떻게 만드느냐가 결과를 좌우한다.
#   (나쁜 예) 다음 달 수익률 > 0 이면 1
#       → 시장 전체가 오른 달은 50종목 거의 다 1, 빠진 달은 거의 다 0.
#         모델이 배우는 건 "종목 고르기"가 아니라 "시장 방향 맞히기"가 돼 버린다.
#   (좋은 예) 그 달 50종목 수익률의 중앙값보다 높으면 1
#       → 달마다 1과 0이 반반. 시장 방향은 빠지고 "어떤 종목이 상대적으로 잘하나"만 남는다.
# 숫자 예시: 어떤 달 5종목 다음 달 수익률 [-8%, -5%, -4%, -1%, +2%] (시장 전체 하락)
#   나쁜 예 → [0, 0, 0, 0, 1]  /  좋은 예(중앙값 -4%) → [0, 0, 0, 1, 1] ... -4%는 중앙값과 같아 0
panel['up_abs'] = (panel['fwd1m'] > 0).astype(int)
panel['up'] = (panel['fwd1m'] > panel.groupby('ym')['fwd1m'].transform('median')).astype(int)

by_month = panel.groupby('ym')[['up_abs', 'up']].mean()
print('달마다 1의 비율 (나쁜 예는 0.1 ~ 0.9로 출렁, 좋은 예는 0.5 근처)')
print(by_month.describe().round(2))

# %% 2. 특징값을 달마다 표준화 (z-점수)
# 책: age(나이), fare(운임)를 원래 단위 그대로 넣었다 → 계수 = "나이 1살 많을 때".
# 주가: 변동성 0.3 이 높은 건지 낮은 건지는 그 달 시장 분위기에 따라 다르다.
#       → 달마다 "평균에서 표준편차 몇 개 떨어졌나"로 바꾼다.
# 숫자 예시: 어떤 달 vol60 = [0.20, 0.25, 0.30, 0.35, 0.40]  평균 0.30, 표준편차 0.079
#   → z = [-1.26, -0.63, 0, +0.63, +1.26]
# 이러면 계수 = "그 달 다른 종목보다 1표준편차 높을 때" 로 읽힌다 → 특징값끼리 크기 비교도 가능
for f in feats:
    panel[f + '_z'] = panel.groupby('ym')[f].transform(lambda s: (s - s.mean()) / s.std())
zfeats = [f + '_z' for f in feats]

# %% 3. 시간순으로 나눠 학습 → smf.logit (책과 같은 함수)
# 2024년 말까지 학습, 2025년부터는 처음 보는 데이터
train = panel[panel['date'] < '2025-01-01'].copy()
test = panel[panel['date'] >= '2025-01-01'].copy()
print('학습:', train['ym'].min(), '~', train['ym'].max(), len(train), '행')
print('평가:', test['ym'].min(), '~', test['ym'].max(), len(test), '행')

formula = 'up ~ ' + ' + '.join(zfeats)
logit_result = smf.logit(formula, data=train).fit(disp=0)
print(logit_result.summary())

# 같은 달 종목끼리 같이 움직이는 문제 → 상관·회귀 파일 4번과 같은 이유로 월로 묶은 표준오차도 본다
logit_cl = smf.logit(formula, data=train).fit(
    disp=0, cov_type='cluster', cov_kwds={'groups': train['ym'].astype(str).factorize()[0]})
print(pd.DataFrame({'계수': logit_result.params,
                    'z (보통)': logit_result.tvalues,
                    'z (월로 묶음)': logit_cl.tvalues}).round(3))
# 목표값을 중앙값 기준으로 만들었으므로 달마다 1:0 = 반반 → 특징값 계수는 묶어도 크게 안 변한다.
# 절편(Intercept)의 z가 -0.3 → -4로 뛰는 건 무시해도 된다: 달마다 1의 비율이 늘 0.49라
# 달 사이 흔들림이 0에 가까워서 생긴 숫자일 뿐, 의미 있는 발견이 아니다.

# %% 3-2. 오즈비 읽기 (책과 같은 np.exp)
# 오즈 = p / (1 - p).  p = 0.5 → 오즈 1,  p = 0.55 → 오즈 1.22
# 오즈비 1.10 이면 "특징값 1표준편차 ↑ → 오즈 10% ↑"
#   p 0.50 (오즈 1.00) → 오즈 1.10 → p = 1.10 / 2.10 = 0.524  (확률로는 +2.4%p)
# 책의 성별 오즈비(0.08 정도)처럼 크게 나오지 않는다. 주식에서 1.05~1.15면 충분히 쓸 만한 크기.
odds = pd.DataFrame({'오즈비': np.exp(logit_result.params),
                     '확률 변화(0.5에서 1표준편차 ↑)':
                         np.exp(logit_result.params) / (1 + np.exp(logit_result.params)) - 0.5})
print(odds.drop('Intercept').round(3))

# 확률로 바로 읽고 싶으면 한계효과 (평균 종목에서 1표준편차 ↑ 할 때 확률 변화)
print(logit_result.get_margeff().summary())

# %% 4. 처음 보는 기간(2025~)에서 평가
from sklearn.metrics import roc_auc_score, accuracy_score, confusion_matrix
test['prob'] = logit_result.predict(test)
test['pred'] = (test['prob'] > 0.5).astype(int)

print('정확도:', round(accuracy_score(test['up'], test['pred']), 3), '(동전 던지기 = 0.5)')
print('AUC   :', round(roc_auc_score(test['up'], test['prob']), 3), '(아무 의미 없는 모델 = 0.5)')
print('혼동행렬 [[실제0 예측0, 실제0 예측1], [실제1 예측0, 실제1 예측1]]')
print(confusion_matrix(test['up'], test['pred']))
# AUC 숫자 예시: 1인 종목 하나, 0인 종목 하나를 아무렇게나 뽑았을 때
#   1인 종목의 예측 확률이 더 높을 확률. 0.53이면 100쌍 중 53쌍을 맞게 줄 세운다.
# 주식에선 0.52 ~ 0.55가 현실적인 범위. 0.7이 나오면 성공이 아니라 미래 정보가 섞였는지부터 의심.

# 달마다 따로 AUC → 평균과 꾸준함 (상관·회귀 파일 7번 IC와 같은 생각)
auc_m = test.groupby('ym').apply(lambda gm: roc_auc_score(gm['up'], gm['prob']))
print('달마다 AUC 평균:', round(auc_m.mean(), 3), '/ 0.5 넘은 달 비율:', round((auc_m > 0.5).mean(), 2))

# 확률 상위 10종목 vs 하위 10종목의 다음 달 수익률 차이 (평가용, 매매 아님)
def top_bottom(gm, n=10):
    gm = gm.sort_values('prob')
    return gm['fwd1m'].tail(n).mean() - gm['fwd1m'].head(n).mean()
spread = test.groupby('ym').apply(top_bottom)
print('상위10 - 하위10 월평균 차이:', f'{spread.mean():.2%}', '/ 양(+)인 달:', f'{(spread > 0).mean():.0%}')
spread.cumsum().plot(figsize=(10, 4), title='확률 상위10 - 하위10 다음 달 수익률 차이 누적 (2025~)')
plt.axhline(0, color='gray', linestyle='--')
plt.show()
# 2026-11-14에 돌린 결과: AUC 0.52로 0.5는 넘었는데 상위10 - 하위10 차이는 월 -0.8%.
# AUC는 "순서를 맞혔나"만 보고 "얼마나 올랐나"는 안 본다. 작은 종목 여러 개를 맞히고
# 크게 오른 종목 하나를 틀리면 AUC는 좋아도 수익률 차이는 음수가 될 수 있다.
# → 분류 점수(AUC)와 수익률 차이를 항상 같이 본다. 면접에서 "AUC 0.52면 돈 버나요?"에 대한 답.

# %% 5. 무작위로 섞어 나누면 안 되는 이유 - 직접 비교
# 책(머신러닝 단원): train_test_split, KFold(shuffle=True) 로 무작위로 나눈다.
# 주가에 그대로 쓰면: 2025년 3월 행으로 학습하고 2025년 2월 행을 맞히는 일이 생긴다(미래로 과거 맞히기).
# 아래에서 일부러 "미래 정보가 섞인 특징값"을 하나 만들어 두 방식 점수를 비교한다.
#   leak = 다음 달 수익률을 3개월 이동평균 한 값 (이번 달 다음 달 값이 섞여 있음 → 원래 쓰면 안 되는 값)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold

panel = panel.sort_values(['code', 'date'])
panel['leak'] = panel.groupby('code')['fwd1m'].transform(lambda s: s.rolling(3, center=True, min_periods=1).mean())
panel['leak_z'] = panel.groupby('ym')['leak'].transform(lambda s: (s - s.mean()) / s.std())
panel = panel.sort_values(['date', 'code']).reset_index(drop=True)
cols = zfeats + ['leak_z']
X = panel[cols].values
y = panel['up'].values

# (가) 무작위 5등분
kf_auc = []
for tr, te in KFold(n_splits=5, shuffle=True, random_state=0).split(X):
    m = LogisticRegression().fit(X[tr], y[tr])
    kf_auc.append(roc_auc_score(y[te], m.predict_proba(X[te])[:, 1]))

# (나) 시간순 앞으로 걸어가기: 2023년까지 학습 → 2024 평가, 2024년까지 학습 → 2025 평가, ...
#      그리고 학습 끝 ~ 평가 시작 사이에 1달을 비운다(엠바고). leak 처럼 앞뒤 달이 섞인 값이
#      학습 마지막 달과 평가 첫 달에 걸치지 않게. (López de Prado 7장 purging·embargo)
wf_auc = []
years = sorted(panel['date'].dt.year.unique())
for yr in years[2:]:
    tr = (panel['date'] < f'{yr - 1}-12-01').values           # 12월은 비움
    te = (panel['date'].dt.year == yr).values
    if te.sum() == 0:
        continue
    m = LogisticRegression().fit(X[tr], y[tr])
    a = roc_auc_score(y[te], m.predict_proba(X[te])[:, 1])
    wf_auc.append(a)
    print(f'{yr}년 평가 AUC: {a:.3f}')

print('무작위 5등분 AUC 평균:', round(np.mean(kf_auc), 3))
print('시간순 평가 AUC 평균  :', round(np.mean(wf_auc), 3))
# 볼 것
#   leak 은 "다음 달 수익률" 자체가 섞인 값이라 두 방식 모두 점수가 높게 나온다 → 미래 정보 하나가
#   들어가면 AUC가 비현실적으로(0.7 이상) 뛴다는 걸 눈으로 확인. 실제 특징값만 쓴 4번(0.5 근처)과 비교.
#   그래서 점수가 너무 좋으면 먼저 "이 열을 그 날 정말 알 수 있었나"를 확인한다.
#   진짜 특징값만 넣어도 무작위 섞기는 같은 달 종목들이 학습·평가에 나뉘어 들어가
#   시간순 평가보다 점수가 조금 높게 나오는 경향이 있다 → 아래에서 leak 빼고 다시 비교.
X2 = panel[zfeats].values
kf2 = np.mean([roc_auc_score(y[te], LogisticRegression().fit(X2[tr], y[tr]).predict_proba(X2[te])[:, 1])
               for tr, te in KFold(n_splits=5, shuffle=True, random_state=0).split(X2)])
wf2 = []
for yr in years[2:]:
    tr = (panel['date'] < f'{yr - 1}-12-01').values
    te = (panel['date'].dt.year == yr).values
    if te.sum() == 0:
        continue
    wf2.append(roc_auc_score(y[te], LogisticRegression().fit(X2[tr], y[tr]).predict_proba(X2[te])[:, 1]))
print('[leak 뺀 진짜 특징값만] 무작위 5등분:', round(kf2, 3), '/ 시간순:', round(np.mean(wf2), 3))
