# -*- coding: utf-8 -*-
# 모델 성적 매기기 (5-3 머신러닝 성능평가)
# 1부: 책 5-3절 지표를 작은 숫자 예시로 손계산 → sklearn 값과 맞춰 보기
#      (5장은 책 원본 코드 파일이 따로 없어서, 책에 나오는 지표를 직접 확인하는 형태로 만듦)
# 2부: 금융판 — 다음날 오를까(분류) / 다음 20일 수익률(회귀)을 예측하고,
#      무작위 KFold vs 시간순 검증 성적이 얼마나 다른지 비교
# Spyder: F5 전체 실행 / Ctrl+Enter 현재 셀 실행 / F9 선택 줄 실행

# =====================================================================
# 1부. 지표를 손으로 계산하기
# =====================================================================

# %% [분류] 실제 10개 vs 예측 10개 → 혼동행렬
import numpy as np
import pandas as pd
from sklearn.metrics import (confusion_matrix, accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, mean_squared_error, mean_absolute_error, r2_score)

y_true = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])   # 1 = 다음날 상승, 0 = 하락
y_pred = np.array([1, 1, 0, 0, 1, 0, 0, 0, 0, 0])

TP = ((y_true == 1) & (y_pred == 1)).sum()   # 오른다 했고 실제로 오름: 2
FN = ((y_true == 1) & (y_pred == 0)).sum()   # 안 오른다 했는데 오름(놓침): 2
FP = ((y_true == 0) & (y_pred == 1)).sum()   # 오른다 했는데 안 오름(헛발): 1
TN = ((y_true == 0) & (y_pred == 0)).sum()   # 안 오른다 했고 안 오름: 5
print('TP, FN, FP, TN =', TP, FN, FP, TN)
print(confusion_matrix(y_true, y_pred))   # sklearn 순서: [[TN, FP], [FN, TP]]

# %% 정확도·정밀도·재현율·F1
acc = (TP + TN) / 10                 # 7/10 = 0.70  전체 중 맞힌 비율
prec = TP / (TP + FP)                # 2/3 = 0.667  '오른다'고 한 것 중 진짜 오른 비율 → 매수 신호의 적중률
rec = TP / (TP + FN)                 # 2/4 = 0.50   실제 오른 것 중 잡아낸 비율
f1 = 2 * prec * rec / (prec + rec)   # 0.571        정밀도·재현율의 조화평균
print('손계산 :', round(acc, 3), round(prec, 3), round(rec, 3), round(f1, 3))
print('sklearn:', accuracy_score(y_true, y_pred), round(precision_score(y_true, y_pred), 3),
      recall_score(y_true, y_pred), round(f1_score(y_true, y_pred), 3))

# %% 정확도의 함정: 언제나 '0(하락)'이라고만 해도 정확도 0.60
always0 = np.zeros(10, dtype=int)
print('항상 0 예측 정확도:', accuracy_score(y_true, always0))
# → 정확도만 보면 안 되고, '아무것도 안 하는 기준선'과 비교해야 함

# %% ROC AUC: 확률 순서가 얼마나 맞나
# AUC = (실제 1 하나, 실제 0 하나)를 뽑았을 때 1 쪽 확률이 더 높을 확률
prob = np.array([0.9, 0.7, 0.4, 0.35, 0.6, 0.3, 0.2, 0.2, 0.1, 0.05])
pairs, win = 0, 0.0
for i in np.where(y_true == 1)[0]:
    for j in np.where(y_true == 0)[0]:
        pairs = pairs + 1
        if prob[i] > prob[j]:
            win = win + 1
        elif prob[i] == prob[j]:
            win = win + 0.5
print('손계산 AUC:', win, '/', pairs, '=', round(win / pairs, 3))
print('sklearn AUC:', round(roc_auc_score(y_true, prob), 3))
# 0.5 = 동전 던지기, 1.0 = 완벽. 주가 예측에선 0.52~0.55만 꾸준해도 쓸 만함

# %% [회귀] 실제 5개 vs 예측 5개
y = np.array([3.0, -1.0, 2.0, 0.0, 1.0])     # 실제 수익률(%)
yhat = np.array([2.0, 0.0, 1.0, 1.0, 1.0])   # 예측
err = y - yhat                               # [1, -1, 1, -1, 0]
mse = (err ** 2).mean()                      # (1+1+1+1+0)/5 = 0.8
rmse = np.sqrt(mse)                          # 0.894 (원래 단위 %로 돌아옴)
mae = np.abs(err).mean()                     # 4/5 = 0.8
sst = ((y - y.mean()) ** 2).sum()            # 평균(1.0)만 예측했을 때 오차 제곱합 = 4+4+1+1+0 = 10
r2 = 1 - (err ** 2).sum() / sst              # 1 - 4/10 = 0.6
print('손계산 :', mse, round(rmse, 3), mae, r2)
print('sklearn:', mean_squared_error(y, yhat), round(np.sqrt(mean_squared_error(y, yhat)), 3),
      mean_absolute_error(y, yhat), r2_score(y, yhat))
# R² < 0 이면 '평균만 찍는 것'보다도 못하다는 뜻

# %% [금융 지표] IC = 예측 순위와 실제 순위의 상관 (스피어만)
from scipy.stats import spearmanr
print('IC:', round(spearmanr(yhat, y)[0], 3))
# 퀀트는 '값을 정확히 맞혔나'보다 '순서를 맞혔나'(많이 오를 걸 위에 두었나)를 더 봄


# =====================================================================
# 2부. 금융판 — 무작위 KFold vs 시간순 검증
# =====================================================================

# %% 데이터와 입력 변수(feature) 만들기 — 전부 '오늘까지' 정보만
from sklearn.model_selection import KFold, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

PATH = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터\prices.csv'
df = pd.read_csv(PATH, dtype={'code': str}, parse_dates=['date'], encoding='utf-8-sig')
df = df.sort_values(['code', 'date']).reset_index(drop=True)
g = df.groupby('code')['close']

df['ret1'] = g.pct_change()
df['mom5'] = g.pct_change(5)                  # 지난 5일 수익률
df['mom20'] = g.pct_change(20)                # 지난 20일 수익률
df['mom60'] = g.pct_change(60)
df['vol20'] = df.groupby('code')['ret1'].transform(lambda s: s.rolling(20).std())
df['amt_chg'] = np.log(df['amount'] / df.groupby('code')['amount'].transform(lambda s: s.rolling(20).mean()))
df['dist_hi'] = df['close'] / g.transform(lambda s: s.rolling(250).max()) - 1   # 1년 최고가 대비

# 정답(target) — 미래 값이므로 shift(-n)
df['up_next'] = (g.shift(-1) > df['close']).astype(int)      # 분류: 다음날 오르면 1
df['fwd20'] = g.shift(-20) / df['close'] - 1                 # 회귀: 다음 20일 수익률
df.loc[g.shift(-1).isna(), 'up_next'] = np.nan

FEATS = ['mom5', 'mom20', 'mom60', 'vol20', 'amt_chg', 'dist_hi']
# 거래대금 0인 날(거래정지)은 log(0) = -무한대 → 모델이 못 받으므로 NaN으로 바꾼 뒤 그 행을 뺌
df[FEATS] = df[FEATS].replace([np.inf, -np.inf], np.nan)
data = df.dropna(subset=FEATS + ['up_next', 'fwd20']).sort_values('date').reset_index(drop=True)
X, y_cls, y_reg = data[FEATS].values, data['up_next'].values, data['fwd20'].values
print(data.shape, '/ 기간:', data['date'].min().date(), '~', data['date'].max().date())

# %% 기준선: 아무 모델 없이
print('다음날 상승 비율(항상 1 예측 정확도):', round(y_cls.mean(), 4))
# 보합(0%)은 '상승 아님'으로 셌기 때문에 50%보다 낮을 수 있음

# %% 검증 방법 3가지를 같은 모델로 비교하는 함수
def run_cv(splitter, model, X, y, kind):
    scores = []
    for tr, te in splitter:
        model.fit(X[tr], y[tr])
        if kind == 'cls':
            p = model.predict_proba(X[te])[:, 1]
            scores.append(roc_auc_score(y[te], p))
        else:
            p = model.predict(X[te])
            scores.append(spearmanr(p, y[te])[0])   # IC
    return np.mean(scores), np.round(scores, 3)

def time_splits(dates, n_splits=5, gap_days=0):
    """날짜 기준으로 앞부분 학습 → 바로 다음 구간 시험 (확장 창).
    gap_days: 학습 끝과 시험 시작 사이를 비워 둠 (정답이 20일 앞을 보면 20일 이상 비워야 겹치지 않음)"""
    udates = np.sort(np.unique(dates))
    blocks = np.array_split(udates, n_splits + 1)
    out = []
    for k in range(1, n_splits + 1):
        test_start, test_end = blocks[k][0], blocks[k][-1]
        train_end = udates[max(0, np.searchsorted(udates, test_start) - gap_days - 1)]
        tr = np.where(dates <= train_end)[0]
        te = np.where((dates >= test_start) & (dates <= test_end))[0]
        out.append((tr, te))
    return out

dates = data['date'].values

# %% [분류] 다음날 상승 — AUC 비교
rf_c = RandomForestClassifier(n_estimators=100, min_samples_leaf=50, max_depth=8, n_jobs=-1, random_state=0)
kf = list(KFold(5, shuffle=True, random_state=0).split(X))
print('무작위 KFold AUC :', run_cv(kf, rf_c, X, y_cls, 'cls'))
print('시간순(확장 창) AUC:', run_cv(time_splits(dates, 5, 1), rf_c, X, y_cls, 'cls'))

# %% [회귀] 다음 20일 수익률 — IC 비교 (여기서 차이가 크게 남)
# 정답이 20일 앞까지 보므로, 오늘 행과 내일 행의 정답이 19일이나 겹침
# 무작위로 섞으면 '내일 행'이 학습에, '오늘 행'이 시험에 들어가 → 사실상 답을 보고 시험
rf_r = RandomForestRegressor(n_estimators=100, min_samples_leaf=50, max_depth=8, n_jobs=-1, random_state=0)
ic_kf = run_cv(kf, rf_r, X, y_reg, 'reg')
ic_ts0 = run_cv(time_splits(dates, 5, 0), rf_r, X, y_reg, 'reg')
ic_ts20 = run_cv(time_splits(dates, 5, 20), rf_r, X, y_reg, 'reg')
print('무작위 KFold IC        :', ic_kf)
print('시간순, 틈 없음 IC     :', ic_ts0)
print('시간순, 20일 틈(purge) IC:', ic_ts20)

# %% sklearn TimeSeriesSplit도 같은 생각 (행 순서로 자르니 반드시 날짜순 정렬 뒤에)
# gap=: 학습과 시험 사이 행 수를 비움 (여기선 하루 약 50종목 × 20일 = 1000행)
tss = list(TimeSeriesSplit(n_splits=5, gap=50 * 20).split(X))
print('TimeSeriesSplit(gap) IC :', run_cv(tss, rf_r, X, y_reg, 'reg'))
# 11/18 실행 결과(F5, 약 30초):
#   다음날 상승 AUC  - 무작위 0.515 / 시간순 0.509   (정답이 하루짜리라 겹침이 적어 차이 작음)
#   다음 20일 IC    - 무작위 0.140 / 시간순 0.030 / 20일 틈 0.025 / TimeSeriesSplit(gap) 0.021
#   → 무작위 KFold가 5배 넘게 부풀림. 시간순 IC 0.02~0.03이 이 변수들의 '진짜' 실력에 가까움
#   → 시간순 IC는 구간마다 0.13 ~ -0.05로 흔들림: 평균만 보지 말고 구간별 값도 본다

# %% 정리
print('''
- 무작위 KFold는 '미래로 과거를 맞히는' 학습이 섞여 점수가 부풀려진다. 특히 정답 기간이 겹치는 경우(20일 수익률).
- 시간순 검증 + 정답 기간만큼 틈(purge)을 둬야 실제로 돈을 굴릴 때와 같은 조건.
- 분류는 정확도만 보지 말고 기준선·AUC를, 수익률 예측은 R²보다 IC(순서 맞히기)를 본다.
- 이 이야기는 López de Prado 『실전 금융 머신러닝 완벽 분석』 7장(purged K-fold)에서 다시 나옴 (12/16 계획).
''')
