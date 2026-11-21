# 모델 성적 매기기 ( 머신러닝 성능평가)
# =====================================================================
# 제3절 성능 평가 기법
# =====================================================================
# 모델 학습이 완료되면, 해당 모델이 새로운 데이터에서도 잘 작동하는지를
# 확인해야 합니다. 성능 평가는 모델의 예측 결과가 실젯값과 얼마나
# 일치하는지를 객관적으로 측정하는 단계입니다.
# 이때 반드시 학습에 사용하지 않은 평가 데이터(Test Set)를 사용해야 합니다.
# 학습 데이터를 다시 사용할 경우, 실제보다 성능이 높게 나타나는
# 과적합 문제를 적절히 확인할 수 없습니다.
# 본 절에서는 실무에서 자주 사용하는 핵심 성능 평가 지표와 기법을 정리합니다.
#
# ---------------------------------------------------------------------
# 1. 성능 평가 지표 요약
# ---------------------------------------------------------------------
# (1) 분류모델 지표
# | 지표              | 의미                     | 사용 상황                 | 해석 방법                         | 점수 범위 |
# |-------------------|--------------------------|---------------------------|-----------------------------------|-----------|
# | 정확도(Accuracy)  | 전체 예측 중 정답 비율   | 클래스 비율이 유사한 경우 | 값이 높을수록 전반적 성능 우수    | 0~1       |
# | 정밀도(Precision) | 양성 예측 중 실제 양성 비율 | 오탐(FP) 최소화가 중요한 경우 | 값이 높을수록 신뢰도가 높음   | 0~1       |
# | 재현율(Recall)    | 실제 양성 중 예측 성공 비율 | 미탐(FN) 최소화가 중요한 경우 | 값이 높을수록 탐지 성능 우수  | 0~1       |
# | F1-Score          | 정밀도와 재현율의 조화 평균 | 데이터 불균형 상황      | 값이 높을수록 균형 잡힌 성능      | 0~1       |
# | AUC-ROC           | 양성·음성 구분 능력      | 모델 비교 및 임곗값 조정  | 1에 가까울수록 우수               | 0.5~1     |
#
# (2) 회귀모델 지표
# | 지표 | 의미                   | 사용 상황                 | 해석 방법            | 점수 범위 |
# |------|------------------------|---------------------------|----------------------|-----------|
# | MAE  | 절대 오차 평균         | 평균 오차 수준 파악       | 값이 작을수록 정확   | 0 이상    |
# | RMSE | 제곱 오차 평균의 제곱근 | 큰 오차를 줄이고자 할 때 | 값이 작을수록 우수   | 0 이상    |
# | R²   | 데이터 변동 설명 비율  | 모델 설명력 비교          | 1에 가까울수록 우수  | 0~1       |
#
# ---------------------------------------------------------------------
# 2. 성능 평가 기법별 이해
# ---------------------------------------------------------------------
# (1) 혼동행렬 및 분류 지표
# 분류모델의 성능을 이해하기 위해서는 혼동행렬(Confusion Matrix)을 먼저
# 이해해야 합니다. 혼동행렬은 모델의 예측 결과와 실젯값을 비교하여
# 오류 유형을 나타낸 표입니다.
#
#                    예측
#   실제        |  음성(N)  |  양성(P)
#   ------------+-----------+----------
#   음성(F)     |    TN     |    FP
#   양성(T)     |    FN     |    TP
#
# 혼동행렬의 각 요소는 다음과 같습니다.
#  - TP(True Positive) : 실제 양성을 양성으로 올바르게 예측한 경우
#  - TN(True Negative) : 실제 음성을 음성으로 올바르게 예측한 경우
#  - FP(False Positive): 실제 음성을 양성으로 잘못 예측한 경우
#  - FN(False Negative): 실제 양성을 음성으로 잘못 예측한 경우
# 혼동행렬을 통해 모델의 오류 유형을 파악할 수 있으며,
# 이에 따라 적절한 평가 지표를 선택합니다.
#
#  ① 정확도(Accuracy): 전체 예측 중 정답 비율을 나타냅니다.
#     데이터가 균형 잡힌 경우 전반적인 성능을 평가하는 데 적합합니다.
#     다만, 데이터 불균형 상황에서는 성능이 왜곡될 수 있습니다.
#     → (TP + TN) / (TP + TN + FP + FN)
#  ② 정밀도(Precision): 양성으로 예측한 결과 중 실제 양성의 비율을 나타냅니다.
#     FP를 줄이는 것이 중요한 상황에서 활용합니다.
#     → TP / (TP + FP)
#  ③ 재현율(Recall): 실제 양성 중 올바르게 예측한 비율을 나타냅니다.
#     FN을 줄이는 것이 중요한 상황에서 활용합니다.
#     → TP / (TP + FN)
#  ④ F1-Score: 정밀도와 재현율의 조화 평균으로, 두 지표 간 균형을 평가합니다.
#     데이터 불균형 상황에서 유용합니다.
#     → 2 * (Precision * Recall) / (Precision + Recall)
#
# (2) AUC-ROC
# AUC-ROC는 모델이 양성과 음성을 얼마나 잘 구분하는지를 평가하는 지표입니다.
# 임곗값 변화에 따른 모델 성능을 종합적으로 평가할 수 있으며,
# 모델 간 비교에도 유용합니다.
# 값이 1에 가까울수록 구분 능력이 우수하며,
# 값이 0.5인 경우 무작위 예측과 동일한 수준을 의미합니다.
#
# (3) 회귀 지표 이해
#  ① MAE(Mean Absolute Error): 절대 오차의 평균을 나타내는 지표입니다.
#     전체적인 오차 수준을 직관적으로 파악할 때 적합합니다.
#  ② RMSE(Root Mean Squared Error): 오차를 제곱한 후 평균을 구하고
#     제곱근을 취한 값입니다. 큰 오차에 더 큰 페널티를 부여하므로,
#     큰 오류를 줄이는 데 적합합니다.
#     RMSE가 MAE보다 크게 나타나는 경우, 일부 큰 오차가 존재함을 의미합니다.
#  ③ R²(결정계수): 모델이 종속변수의 변동을 얼마나 설명하는지를 나타내는
#     지표입니다. 값이 1에 가까울수록 설명력이 높으며,
#     회귀모델의 전반적인 적합도를 평가할 때 활용합니다.
#
# ---------------------------------------------------------------------
# 3. 파이썬 활용 방법
# ---------------------------------------------------------------------
# (1) 분류모델 지표 계산
# 분류모델은 실젯값(y_test)과 예측값(y_pred) 또는
# 예측 확률(y_prob)을 기반으로 계산합니다.
# | 지표명   | 함수(sklearn.metrics) | 인자           | 비고             |
# |----------|-----------------------|----------------|------------------|
# | 정확도   | accuracy_score        | y_test, y_pred | 전체 정확도      |
# | 정밀도   | precision_score       | y_test, y_pred | 양성 예측 신뢰도 |
# | 재현율   | recall_score          | y_test, y_pred | 양성 탐지율      |
# | F1-Score | f1_score              | y_test, y_pred | 균형 성능        |
# | AUC-ROC  | roc_auc_score         | y_test, y_prob | 확률값 필요      |
#
# (2) 회귀모델 지표 계산
# 회귀모델은 실젯값(y_test)과 예측값(y_pred)의 차이를 기반으로 계산합니다.
# | 지표명   | 함수(sklearn.metrics)       | 인자           | 비고          |
# |----------|-----------------------------|----------------|---------------|
# | MAE      | mean_absolute_error         | y_test, y_pred | 절대 오차 평균 |
# | MSE      | mean_squared_error          | y_test, y_pred | 제곱 오차 평균 |
# | RMSE     | np.sqrt(mean_squared_error) | y_test, y_pred | MSE의 제곱근  |
# | 결정계수 | r2_score                    | y_test, y_pred | 설명력        |
# =====================================================================
#%%
import numpy as np
from sklearn.datasets import load_breast_cancer, load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_absolute_error, mean_squared_error, r2_score
)

# ---------------------------------------------------------------------
# (1) 분류모델 지표 계산
# ---------------------------------------------------------------------
X, y = load_breast_cancer(return_X_y=True)

# 반드시 학습에 사용하지 않은 평가 데이터(Test Set)를 분리
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)   # 학습 데이터로만 fit
X_test = scaler.transform(X_test)         # 평가 데이터는 transform만

clf = LogisticRegression(max_iter=1000)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)               # 예측값 (0 또는 1)
y_prob = clf.predict_proba(X_test)[:, 1]   # 양성(1)일 예측 확률 → AUC-ROC에 필요

# 혼동행렬: sklearn은 [[TN, FP], [FN, TP]] 순서로 반환
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()
print("혼동행렬:\n", cm)
print(f"TN={tn}, FP={fp}, FN={fn}, TP={tp}")

print("정확도(Accuracy)  :", accuracy_score(y_test, y_pred))
print("정밀도(Precision) :", precision_score(y_test, y_pred))
print("재현율(Recall)    :", recall_score(y_test, y_pred))
print("F1-Score          :", f1_score(y_test, y_pred))
print("AUC-ROC           :", roc_auc_score(y_test, y_prob))  # y_pred가 아니라 y_prob

# 공식으로 직접 계산해서 함수 결과와 비교
acc_manual = (tp + tn) / (tp + tn + fp + fn)
prec_manual = tp / (tp + fp)
rec_manual = tp / (tp + fn)
f1_manual = 2 * prec_manual * rec_manual / (prec_manual + rec_manual)
print("직접 계산 →", acc_manual, prec_manual, rec_manual, f1_manual)

# ---------------------------------------------------------------------
# (2) 회귀모델 지표 계산
# ---------------------------------------------------------------------
X, y = load_diabetes(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

reg = LinearRegression()
reg.fit(X_train, y_train)
y_pred = reg.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)                # = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("MAE  :", mae)
print("MSE  :", mse)
print("RMSE :", rmse)
print("R²   :", r2)

# RMSE가 MAE보다 크게 나타나면 일부 큰 오차가 존재함을 의미
print("RMSE / MAE 비율:", rmse / mae)


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
''')
