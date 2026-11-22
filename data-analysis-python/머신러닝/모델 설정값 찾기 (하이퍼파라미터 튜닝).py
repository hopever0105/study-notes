# -*- coding: utf-8 -*-
# 모델 설정값 찾기 (6-5 하이퍼파라미터 튜닝: GridSearchCV·RandomizedSearchCV)
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split

from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint


# %% 월말 패널 만들기 (6-2·6-3·6-4 파일과 같은 변수·같은 정답)
from lightgbm import LGBMClassifier
from sklearn.model_selection import KFold
from sklearn.metrics import roc_auc_score

PATH = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터\prices.csv'
px = pd.read_csv(PATH, dtype={'code': str}, parse_dates=['date'], encoding='utf-8-sig')
px = px.sort_values(['code', 'date']).reset_index(drop=True)
g = px.groupby('code')['close']
px['ret'] = g.pct_change()
px['mom_1m'] = g.pct_change(21)
px['mom_3m'] = g.pct_change(63)
px['mom_12_1'] = g.shift(21) / g.shift(252) - 1
px['vol_1m'] = px.groupby('code')['ret'].transform(lambda s: s.rolling(21).std())
px['amt_log'] = np.log(px.groupby('code')['amount'].transform(lambda s: s.rolling(21).mean()))
px['amt_chg'] = px.groupby('code')['amount'].transform(lambda s: s.rolling(21).mean() / s.rolling(126).mean())
px['dist_hi'] = px['close'] / g.transform(lambda s: s.rolling(252).max()) - 1
px['max_ret'] = px.groupby('code')['ret'].transform(lambda s: s.rolling(21).max())
FEATS = ['mom_1m', 'mom_3m', 'mom_12_1', 'vol_1m', 'amt_log', 'amt_chg', 'dist_hi', 'max_ret']

px['ym'] = px['date'].dt.to_period('M')
me = px.groupby(['code', 'ym']).tail(1).sort_values(['code', 'ym']).copy()
me['fwd_1m'] = me.groupby('code')['close'].shift(-1) / me['close'] - 1
me = me.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATS + ['fwd_1m']).reset_index(drop=True)
me['y'] = (me['fwd_1m'] >= me.groupby('ym')['fwd_1m'].transform('median')).astype(int)
for c_ in FEATS:
    me[c_] = me.groupby('ym')[c_].rank(pct=True)       # 달마다 순위 0~1

# 날짜순으로 정렬해 두어야 '앞 = 과거'가 됨
me = me.sort_values(['ym', 'code']).reset_index(drop=True)

# 설정값 고르는 기간(학습+검증) ~2024-11 / 시험 2025~ (마지막 한 번만)
dev = me[me['ym'] <= pd.Period('2024-11', 'M')].reset_index(drop=True)
test = me[me['ym'] >= pd.Period('2025-01', 'M')].reset_index(drop=True)
print('고르는 기간', dev['ym'].min(), '~', dev['ym'].max(), len(dev), '행 / 시험', len(test), '행')


# %% 시간순 교차검증 덩어리 만들기 (월 단위, 앞에서부터 늘려 가는 방식 + 1달 비우기)
#   책의 cv=5는 행을 섞지 않고 5등분할 뿐이지만, 덩어리마다 '뒤 기간으로 학습, 앞 기간 채점'도 생김
#   여기서는 항상 '과거로 학습 → 바로 다음 기간 채점'만 하도록 직접 만든다
#   정답이 '다음 1개월 수익률'이라 학습 마지막 달의 정답은 채점 첫 달 가격으로 만들어짐 → 경계에서 1달 버림(gap)
def month_folds(d, n_splits=5, min_train=12, gap=1):
    months = sorted(d['ym'].unique())
    rest = months[min_train:]                                 # 처음 12달은 항상 학습
    size = len(rest) // n_splits                              # 채점 덩어리 하나의 달 수
    folds = []
    for k in range(n_splits):
        val_m = rest[k * size:(k + 1) * size] if k < n_splits - 1 else rest[k * size:]
        train_m = [m for m in months if m < val_m[0]][:-gap] if gap > 0 else [m for m in months if m < val_m[0]]
        tr_idx = d.index[d['ym'].isin(train_m)].to_numpy()
        va_idx = d.index[d['ym'].isin(val_m)].to_numpy()
        folds.append((tr_idx, va_idx))
        print(f'  {k + 1}번: 학습 {train_m[0]}~{train_m[-1]} ({len(train_m)}달) → 1달 비움 → 채점 {val_m[0]}~{val_m[-1]} ({len(val_m)}달)')
    return folds


time_cv = month_folds(dev)

# %% 1) 같은 후보를 '무작위 5겹'과 '시간순 5겹'으로 각각 채점해 보기
#   LightGBM 후보: 잎 수(num_leaves)·나무 수(n_estimators)·학습률·잎당 최소 행 수
lgb_grid = {
    'num_leaves': [3, 7, 31],
    'n_estimators': [50, 200, 500],
    'learning_rate': [0.02, 0.1],
    'min_child_samples': [20, 100],
}
base = LGBMClassifier(subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                      random_state=0, verbose=-1)
# 3 × 3 × 2 × 2 = 36조합 × 5겹 = 180번 학습

gs_random = GridSearchCV(base, lgb_grid, scoring='roc_auc',
                         cv=KFold(5, shuffle=True, random_state=0), n_jobs=-1)
gs_random.fit(dev[FEATS], dev['y'])

gs_time = GridSearchCV(base, lgb_grid, scoring='roc_auc', cv=time_cv, n_jobs=-1)
gs_time.fit(dev[FEATS], dev['y'])

print('무작위 5겹 1등:', gs_random.best_params_, 'CV AUC', round(gs_random.best_score_, 4))
print('시간순 5겹 1등:', gs_time.best_params_, 'CV AUC', round(gs_time.best_score_, 4))

# %% 2) 시간순 결과 표: 상위 10개 조합과 덩어리별 점수 흔들림
cvr = pd.DataFrame(gs_time.cv_results_)
cvr['조합'] = cvr['params'].apply(lambda p: f"잎{p['num_leaves']} 나무{p['n_estimators']} lr{p['learning_rate']} 최소{p['min_child_samples']}")
fold_cols = [f'split{k}_test_score' for k in range(5)]
show = cvr.sort_values('mean_test_score', ascending=False)[['조합', 'mean_test_score', 'std_test_score'] + fold_cols].head(10)
show.columns = ['조합', '평균 AUC', '표준편차'] + [f'{k + 1}번' for k in range(5)]
print(show.round(4).to_string(index=False))
print('→ 1등과 10등의 평균 차이 vs 표준편차를 비교. 차이가 더 작으면 1등은 우연일 수 있음')

# %% 3) 무작위 5겹 점수 vs 시간순 5겹 점수 — 조합 36개를 점 하나씩
rnd = pd.DataFrame(gs_random.cv_results_)['mean_test_score']
tim = cvr['mean_test_score']
print('36조합 평균 AUC — 무작위 5겹:', round(rnd.mean(), 4), '/ 시간순 5겹:', round(tim.mean(), 4))
print('두 방식 순위 상관(스피어만):', round(pd.Series(rnd.values).rank().corr(pd.Series(tim.values).rank()), 3))

plt.figure(figsize=(5.5, 5))
plt.scatter(rnd, tim)
lo, hi = min(rnd.min(), tim.min()) - 0.005, max(rnd.max(), tim.max()) + 0.005
plt.plot([lo, hi], [lo, hi], color='gray', lw=0.8, ls='--')
plt.xlabel('무작위 5겹 평균 AUC')
plt.ylabel('시간순 5겹 평균 AUC')
plt.title('같은 조합 36개, 채점 방식만 다름')
plt.show()

# %% 4) RandomizedSearchCV: 범위를 넓히고 40개만 무작위로 (시간순 5겹)
from scipy.stats import loguniform

lgb_dist = {
    'num_leaves': randint(3, 64),
    'n_estimators': randint(30, 600),
    'learning_rate': loguniform(0.01, 0.3),     # 0.01~0.3을 '자릿수' 기준으로 고르게 (0.01~0.1과 0.1~0.3이 비슷한 확률)
    'min_child_samples': randint(10, 200),
}
rs_time = RandomizedSearchCV(base, lgb_dist, n_iter=40, scoring='roc_auc',
                             cv=time_cv, random_state=0, n_jobs=-1)
rs_time.fit(dev[FEATS], dev['y'])
print('무작위 탐색 1등:', {k: (round(float(v), 4) if isinstance(v, float) else v) for k, v in rs_time.best_params_.items()},
      'CV AUC', round(rs_time.best_score_, 4))


# %% 5) 시험(2025~)에서 딱 한 번: 기본값 vs 무작위 5겹이 고른 것 vs 시간순 5겹이 고른 것 vs 무작위 탐색
#   GridSearchCV는 고른 뒤 고르는 기간 전체(dev)로 다시 학습해 둠(refit) → best_estimator_를 바로 씀
def score_rank(d, prob, k=10):
    """확률 순위로 매달 상위 k 매수·하위 k 매도 → AUC, 평균 월 롱숏, 이긴 달 수"""
    t = d.assign(prob=prob)
    rows = []
    for ym, x in t.groupby('ym'):
        x = x.sort_values('prob')
        rows.append(x['fwd_1m'].tail(k).mean() - x['fwd_1m'].head(k).mean())
    ls = pd.Series(rows)
    return round(roc_auc_score(d['y'], prob), 4), round(ls.mean(), 4), f'{int((ls > 0).sum())}/{len(ls)}'


default = LGBMClassifier(random_state=0, verbose=-1).fit(dev[FEATS], dev['y'])   # 아무것도 안 고른 기본값(잎31·나무100·lr0.1)
rows = [['기본값(안 고름)', *score_rank(test, default.predict_proba(test[FEATS])[:, 1])],
        ['무작위 5겹이 고른 것', *score_rank(test, gs_random.best_estimator_.predict_proba(test[FEATS])[:, 1])],
        ['시간순 5겹이 고른 것', *score_rank(test, gs_time.best_estimator_.predict_proba(test[FEATS])[:, 1])],
        ['시간순 무작위 탐색 40개', *score_rank(test, rs_time.best_estimator_.predict_proba(test[FEATS])[:, 1])]]
print(pd.DataFrame(rows, columns=['설정', '시험 AUC', '시험 롱숏/월', '이긴 달']).to_string(index=False))

# %% 6) CV 점수가 시험 점수를 얼마나 맞히나 — 36조합 전부 시험까지 돌려 보기 (공부용. 실전에선 시험을 여러 번 보면 반칙)
rows = []
for p, cv_auc in zip(cvr['params'], cvr['mean_test_score']):
    m = LGBMClassifier(subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                       random_state=0, verbose=-1, **p).fit(dev[FEATS], dev['y'])
    rows.append([cv_auc, roc_auc_score(test['y'], m.predict_proba(test[FEATS])[:, 1])])
chk = pd.DataFrame(rows, columns=['시간순 CV AUC', '시험 AUC'])
print('36조합 CV AUC와 시험 AUC 순위 상관:', round(chk['시간순 CV AUC'].rank().corr(chk['시험 AUC'].rank()), 3))
print('시험 AUC 범위:', round(chk['시험 AUC'].min(), 4), '~', round(chk['시험 AUC'].max(), 4))

# %% 정리 — 11/22 실행 결과(F5, 약 1분 40초)
# - 책(심장병, 무작위 80/20): Grid 1등 depth=3·나무200 CV 0.843 → 테스트 0.803
#   Randomized 1등 depth=7·sqrt·나무393 CV 0.856 → 테스트 0.820. 1~5등 차이 0.004 < 표준편차 0.03~0.05
#   → 1등 조합에 큰 의미 없음. 비슷하면 단순한 쪽(얕은 나무)을 고른다
# - 금융판: 같은 36조합을 두 방식으로 채점
#   무작위 5겹: 평균 AUC 0.536, 1등 잎31·나무50·lr0.1 (0.553) → 미래 달로 과거 달을 맞히는 덩어리가 섞여 점수가 부풀려짐
#   시간순 5겹: 평균 AUC 0.509, 1등 잎3·나무50·lr0.02 (0.524) → 가장 단순한 조합이 1등
#   두 방식의 순위 상관 -0.07 → 채점 방식이 다르면 '좋은 설정'이 아예 다르게 뽑힘
# - 시간순 1등도 덩어리별로 0.49~0.55, 표준편차 0.02~0.05 → 1등과 10등 차이(0.011)보다 흔들림이 큼
# - 시험(2025~, 21달, 딱 한 번):
#   기본값(잎31·나무100) AUC 0.501·롱숏 -2.2%/월 / 무작위 5겹이 고른 것 0.492·-4.3%/월
#   시간순 5겹이 고른 것 0.511·+3.5%/월(12/21달) / 시간순 무작위 탐색 40개 0.516·-2.5%/월
#   → 무작위 5겹으로 고르면 시험에서 제일 나쁨. 시간순으로 고른 단순한 모델만 롱숏 플러스
# - 공부용으로 36조합 전부 시험까지 돌려 보면: CV 순위와 시험 순위 상관 -0.14, 시험 AUC 0.485~0.522
#   → 신호가 약한 주가 데이터에선 튜닝으로 얻는 이득이 잡음 수준. 튜닝보다 '시간순으로 채점'과 '단순하게'가 더 중요
# - 실무 순서: 시간순 교차검증(경계 비우기) → 비슷하면 단순한 설정 → 시험 기간은 맨 마지막에 한 번

# %% 하이퍼파라미터 튜닝의 개념
"""
- 머신러닝 모델에는 파라미터와 하이퍼파라미터가 있다.

1. 파라미터(Parameter)   
  - 모델이 학습 데이터로 스스로 찾아내는 값 (예: 회귀분석의 입력특성 가중치인 회귀계수)
  
  
2. 하이퍼파라미터(Hyperparameter) 
(1) 개념
- 학습 시작 전에 사람이 직접 정하는 값 
- 예: LightGBM의 max_depth, learning_rate

(2) 하이퍼파라미터 튜닝 
- 조절 노브의 최적 위치를 찾는 과정
- 하이퍼파라미터는 데이터로부터 학습되지 않으므로 미리 반드시 정해야 한다
- 잘못된 설정은 과적합(Overfitting) 또는 과소적합(Underfitting)을 일으킨다
- 튜닝 과정에서는 교차검증(Cross-Validation)을 함께 써서 일반화 성능을 평가한다
  
(3) 대표적인 자동 튜닝 도구
- GridSearchCV(전수 탐색),
- RandomizedSearchCV(무작위 탐색)

예시: 
  GridSearchCV      : max_depth 3·5·7·9·11 × learning_rate 0.01·0.05·0.1·0.5·1.0 격자점을 전부 시험
                      → 탐색 횟수 5 × 5 = 25회, 최적점은 격자 위에서만 찾음(예: depth 7, lr 0.5)
  RandomizedSearchCV: 같은 범위 안에서 무작위로 점을 골라 시험 → 탐색 횟수 10회(n_iter=10, 조절 가능),
                      격자 사이 값도 시험할 수 있어 격자 밖의 최적점을 찾기도 함



3. GridSearchCV
(1) 개념
사용자가 지정한 파라미터 조합을 모두 탐색해 최적 조합을 찾는 방법
  
(2) 격자(Grid) 탐색
- 지정한 파라미터 값들의 모든 조합을 빠짐없이 실험하는 것
- 교차검증(CV) 내장: 각 조합을 교차검증해 과적합 없이 성능을 평가
- 탐색 비용: 파라미터 값이 많아질수록 조합 수가 곱셈으로 늘어나 주의 필요 (예: 5 × 5 × 3 = 75회 학습)
- scoring 지정: 정확도(accuracy), F1, AUC 등 평가 기준을 사용자가 고를 수 있다
- 파라미터 후보(조합)가 많아지면 탐색 시간이 기하급수적으로 늘어난다.
-  GridSearchCV는 후보 조합이 수십 개 이하일 때 적합하고, 후보가 많으면 RandomizedSearchCV를 쓴다.

(3) GridSearchCV 주요 파라미터
| 파라미터   | 기본값 | 설명                                         |
| estimator  | -      | 탐색할 모델 객체 지정                          |
| param_grid | -      | 탐색할 파라미터 딕셔너리 지정                   |
| scoring    | None   | 성능 평가 기준 지정                            |
| cv         | 5      | 교차검증 폴드 수 지정 (보통 3~10)               |
| verbose    | 0      | 진행 메시지 출력 수준 (1~3, 높을수록 자세히)     |
| refit      | True   | True면 최적 파라미터로 전체 데이터 재학습         |
| n_jobs     | 1      | 병렬 처리 수 (음수면 모든 CPU 코어 사용)          |




4. RandomizedSearchCV
(1) 개념
- 파라미터 조합을 무작위로 샘플링해 빠르게 최적 구간을 찾는 방법

(2) 무작위 탐색
지정한 n_iter 횟수만큼 조합을 무작위로 골라 실험.
   
(3) 연속형 분포 지원
scipy.stats의 분포(uniform, randint 등)를 파라미터 범위로 지정할 수 있어 탐색 공간이 넓어진다

(4) n_iter로 탐색 횟수 조절
시간이 부족하면 줄이고, 정밀도가 필요하면 늘려 탐색 비용을 직접 제어
  
(5) 대용량·고차원 파라미터에 적합
파라미터가 5개 이상이거나 범위가 매우 넓을 때 GridSearchCV보다 효율적

(6) RandomizedSearchCV  주요 파라미터
| 파라미터            | 기본값 | 설명                                              |
| estimator           | -      | 탐색할 모델 객체 지정                               |
| param_distributions | -      | 탐색할 파라미터 딕셔너리 지정 (리스트 또는 scipy 분포) |
| n_iter              | 10     | 무작위 탐색 횟수 (클수록 정밀하지만 느림)             |
| scoring             | None   | 평가 기준                                          |
| cv                  | 5      | 교차검증 폴드 수 지정 (보통 3~10)                    |
| random_state        | None   | 재현성 확보를 위한 난수 시드                         |
| verbose             | 0      | 진행 메시지 출력 수준 (1~3, 높을수록 자세히)          |
| refit               | True   | True면 최적 파라미터로 전체 데이터 재학습              |
| n_jobs              | 1      | 병렬 처리 수 (음수면 모든 CPU 코어 사용)               |
"""

# %% 데이터 (UCI Heart Disease)
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

url = 'https://raw.githubusercontent.com/sharmaroshan/Heart-UCI-Dataset/master/heart.csv'
LOCAL = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\데이터분석_파이썬\참고코드\개정판_py\data\heart.csv'
try:
    df = pd.read_csv(url)
except Exception:
    df = pd.read_csv(LOCAL)

# %% 학습·평가 분할
from sklearn.model_selection import train_test_split

X = df.drop(columns=['target'])    # 입력특성
y = df['target']                   # 레이블: 심장병 여부 (1=있음, 0=없음)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)
print(f'학습 데이터: {X_train.shape}, 평가 데이터: {X_test.shape}')

# %% 1. GridSearchCV 설정
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

param_grid = {
    'n_estimators': [50, 100, 200],         # 트리 수
    'max_depth': [3, 5, 7, None],           # 트리 최대 깊이
    'min_samples_split': [2, 5, 10],        # 분할 최소 샘플 수
}

# 3 × 4 × 3 = 36가지 조합 × 5-fold = 180회 학습
grid_search = GridSearchCV(
    estimator=RandomForestClassifier(random_state=42),
    param_grid=param_grid,
    scoring='accuracy',
    cv=5,
    n_jobs=-1,          # 책은 1(코어 1개). -1이면 CPU 코어 전부 → 빨라짐
    verbose=1,
)

# %% 학습
grid_search.fit(X_train, y_train)

# %% 결과
print('최적 파라미터:', grid_search.best_params_)
print('CV 최고 정확도:', round(grid_search.best_score_, 4))

best_model = grid_search.best_estimator_      # 최적 조합으로 '학습 데이터 전체'에 다시 학습된 모델
test_acc = best_model.score(X_test, y_test)
print('테스트 정확도:', round(test_acc, 4))

# %% 상위 5개 조합
results = pd.DataFrame(grid_search.cv_results_)
top5 = results[['params', 'mean_test_score', 'std_test_score']] \
    .sort_values('mean_test_score', ascending=False).head(5)
top5['mean_test_score'] = top5['mean_test_score'].round(4)
top5['std_test_score'] = top5['std_test_score'].round(4)
print(top5.to_string(index=False))
#   → 1등과 5등의 평균 차이가 표준편차(std)보다 작으면, 1등은 '운 좋게 1등'일 수 있다

# %% 2. RandomizedSearchCV
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint

param_dist = {
    'n_estimators': randint(50, 500),          # 50~499 정수 균등 분포
    'max_depth': [3, 5, 7, 10, None],
    'min_samples_split': randint(2, 20),       # 2~19 정수 균등 분포
    'min_samples_leaf': randint(1, 10),
    'max_features': [None, 'sqrt', 'log2'],    # 책의 "auto"는 없어짐 → None
}

rand_search = RandomizedSearchCV(
    estimator=RandomForestClassifier(random_state=42),
    param_distributions=param_dist,
    n_iter=50,            # 50가지 조합만 무작위 탐색 → 50 × 5겹 = 250회 학습
    scoring='accuracy',
    cv=5,
    random_state=42,
    n_jobs=-1,
    verbose=1,
)

# %% 학습
rand_search.fit(X_train, y_train)

# %% 결과
print('최적 파라미터:', rand_search.best_params_)
print('CV 최고 정확도:', round(rand_search.best_score_, 4))

best_rand = rand_search.best_estimator_
print('테스트 정확도:', round(best_rand.score(X_test, y_test), 4))

# %% 두 방법 비교
comparison = {
    '방법': ['GridSearchCV', 'RandomizedSearchCV'],
    '탐색 횟수': [180, 250],
    'CV 정확도': [grid_search.best_score_, rand_search.best_score_],
    '테스트 정확도': [best_model.score(X_test, y_test), best_rand.score(X_test, y_test)],
}
print(pd.DataFrame(comparison))





