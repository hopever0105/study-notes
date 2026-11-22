# -*- coding: utf-8 -*-
# 여러 모델 묶어 예측력 높이기 (6-4 앙상블: 랜덤포레스트·XGBoost·LightGBM)
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             classification_report, mean_squared_error, mean_absolute_error)

# %% 월말 패널 만들기 (6-2·6-3 파일과 같은 변수·같은 정답)
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
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
print(me.shape, me['ym'].min(), '~', me['ym'].max())

# %% 시간순 3분할: 학습 ~2023-11 / 검증 2024-01~11 / 시험 2025~ (경계마다 1달 버림, 6-3과 같음)
train = me[me['ym'] <= pd.Period('2023-11', 'M')]
valid = me[(me['ym'] >= pd.Period('2024-01', 'M')) & (me['ym'] <= pd.Period('2024-11', 'M'))]
test = me[me['ym'] >= pd.Period('2025-01', 'M')]
print('학습', len(train), '/ 검증', len(valid), '/ 시험', len(test))


def score_rank(d, prob, k=10):
    """확률 순위로 매달 상위 k 매수·하위 k 매도 → AUC, 평균 월 롱숏, 이긴 달 수"""
    t = d.assign(prob=prob)
    rows = []
    for ym, x in t.groupby('ym'):
        x = x.sort_values('prob')
        rows.append(x['fwd_1m'].tail(k).mean() - x['fwd_1m'].head(k).mean())
    ls = pd.Series(rows)
    return round(roc_auc_score(d['y'], prob), 4), round(ls.mean(), 4), f'{int((ls > 0).sum())}/{len(ls)}'


# %% 1) 나무 1그루 → 여러 그루: 깊은 나무(depth=10)도 100그루 평균이면 어떻게 되나
#   6-3에서 depth=10 나무 1그루: 학습 AUC 높고 시험 0.46 → 과적합
#   랜덤포레스트: 같은 깊이 나무 100그루, 나무마다 행은 복원추출·변수는 √8 ≈ 3개만 보고 갈라짐
cands = {
    '나무 1그루 depth=10': DecisionTreeClassifier(max_depth=10, min_samples_leaf=30, random_state=0),
    '랜덤포레스트 depth=10': RandomForestClassifier(n_estimators=300, max_depth=10, min_samples_leaf=30,
                                                   max_features='sqrt', n_jobs=-1, random_state=0),
    '랜덤포레스트 depth=4': RandomForestClassifier(n_estimators=300, max_depth=4, min_samples_leaf=30,
                                                  max_features='sqrt', n_jobs=-1, random_state=0),
    # 부스팅: 얕은 나무(depth 2~3)를 조금씩(learning_rate) 이어 붙임. 나무 수가 많을수록 과적합 쪽
    'XGBoost 나무100 lr0.05': XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05,
                                            subsample=0.8, colsample_bytree=0.8, random_state=0),
    'XGBoost 나무500 lr0.05': XGBClassifier(n_estimators=500, max_depth=3, learning_rate=0.05,
                                            subsample=0.8, colsample_bytree=0.8, random_state=0),
    'LightGBM 잎7 나무200': LGBMClassifier(n_estimators=200, num_leaves=7, learning_rate=0.05,
                                          subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                          min_child_samples=50, random_state=0, verbose=-1),
    'LightGBM 잎31 나무200': LGBMClassifier(n_estimators=200, num_leaves=31, learning_rate=0.05,
                                           subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                           min_child_samples=50, random_state=0, verbose=-1),
    '로지스틱(6-2 기준)': make_pipeline(StandardScaler(), LogisticRegression(C=1.0)),
}

rows = []
for name, m in cands.items():
    m.fit(train[FEATS], train['y'])
    tr_auc = roc_auc_score(train['y'], m.predict_proba(train[FEATS])[:, 1])
    va = score_rank(valid, m.predict_proba(valid[FEATS])[:, 1])
    rows.append([name, round(tr_auc, 4), *va])
res = pd.DataFrame(rows, columns=['모델', '학습 AUC', '검증 AUC', '검증 롱숏/월', '이긴 달'])
print(res.to_string(index=False))
print('→ 학습 AUC와 검증 AUC의 차이 = 과적합 크기. 1그루 → 포레스트에서 차이가 줄어드는지 본다')

# %% 2) 부스팅은 나무 수가 곧 설정값: 나무를 하나씩 더할 때 검증 AUC가 어떻게 변하나
#   LightGBM은 학습 후 '나무 n개까지만 써서' 예측 가능 (num_iteration)
lgbm_curve = LGBMClassifier(n_estimators=600, num_leaves=7, learning_rate=0.05,
                            subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                            min_child_samples=50, random_state=0, verbose=-1)
lgbm_curve.fit(train[FEATS], train['y'])
curve = []
for n in [10, 25, 50, 100, 200, 300, 400, 600]:
    p_tr = lgbm_curve.predict_proba(train[FEATS], num_iteration=n)[:, 1]
    p_va = lgbm_curve.predict_proba(valid[FEATS], num_iteration=n)[:, 1]
    curve.append([n, round(roc_auc_score(train['y'], p_tr), 4), round(roc_auc_score(valid['y'], p_va), 4)])
curve = pd.DataFrame(curve, columns=['나무 수', '학습 AUC', '검증 AUC'])
print(curve.to_string(index=False))
print('→ 학습 AUC는 나무를 더할수록 계속 오름. 검증 AUC가 꺾이는 지점이 멈출 곳(early stopping의 원리)')

plt.figure(figsize=(7, 4))
plt.plot(curve['나무 수'], curve['학습 AUC'], marker='o', label='학습')
plt.plot(curve['나무 수'], curve['검증 AUC'], marker='o', label='검증(2024)')
plt.axhline(0.5, color='gray', lw=0.8, ls='--')
plt.xlabel('나무 수')
plt.ylabel('AUC')
plt.title('LightGBM: 나무를 더할수록 학습만 좋아진다')
plt.legend()
plt.show()

# %% 3) 검증 1등 설정을 종류마다 골라 → 학습+검증으로 다시 학습 → 시험(2025~) 딱 한 번
res['종류'] = res['모델'].str.split(' ').str[0]
best = res.sort_values('검증 AUC', ascending=False).groupby('종류').head(1)
trva = pd.concat([train, valid])
test_prob = {}
rows = []
for name in best['모델']:
    m = cands[name]
    m.fit(trva[FEATS], trva['y'])
    p = m.predict_proba(test[FEATS])[:, 1]
    test_prob[name] = p
    rows.append([name, *score_rank(test, p)])

# 모델끼리 묶기(소프트 보팅): 종류별 확률을 '달마다 순위'로 바꿔 평균 → 서로 다른 실수가 상쇄되길 기대
rank_avg = np.zeros(len(test))
for name, p in test_prob.items():
    rank_avg = rank_avg + test.assign(p=p).groupby('ym')['p'].rank(pct=True).values
rank_avg = rank_avg / len(test_prob)
rows.append(['종류별 1등 순위 평균(보팅)', *score_rank(test, rank_avg)])
print(pd.DataFrame(rows, columns=['모델', '시험 AUC', '시험 롱숏/월', '이긴 달']).to_string(index=False))

# %% 4) 무엇을 보고 골랐나 — 랜덤포레스트 중요도 vs 순열 중요도
#   feature_importances_: 학습 때 그 변수로 갈라서 줄어든 불순도 합 → 값 종류가 많은 변수에 유리, 학습 데이터 기준
#   순열 중요도: '시험' 데이터에서 그 열만 뒤섞었을 때 AUC가 얼마나 떨어지나 → 실제로 예측에 도움 되는지
from sklearn.inspection import permutation_importance

rf = RandomForestClassifier(n_estimators=300, max_depth=4, min_samples_leaf=30,
                            max_features='sqrt', n_jobs=-1, random_state=0).fit(trva[FEATS], trva['y'])
perm = permutation_importance(rf, test[FEATS], test['y'], scoring='roc_auc', n_repeats=10, random_state=0)
imp = pd.DataFrame({'불순도 중요도(학습)': rf.feature_importances_,
                    '순열 중요도(시험 AUC 감소)': perm.importances_mean}, index=FEATS)
print(imp.sort_values('불순도 중요도(학습)', ascending=False).round(4))
print('→ 순열 중요도가 0 근처나 음수면, 학습에선 많이 썼어도 2025년엔 도움 안 된 변수')

# %% 정리 — 11/21 실행 결과(F5, 약 15초)
# - 책(유방암, 무작위 70/30): 랜덤포레스트·XGBoost 정확도 89.5%, LightGBM 87.1%. 자동차 가격 R² 포레스트 92.9%
#   XGBoost는 '시험 데이터'로 멈출 곳(17그루)을 정함 → 시험 점수가 부풀려짐. 원래는 검증 데이터로
# - 금융판 검증(2024, 11달): 깊은 나무를 포레스트로 바꿔도 학습 AUC는 오히려 올라감(0.72 → 0.79)
#   → 깊은 나무 300그루 평균도 '학습 데이터'엔 여전히 딱 맞음. 과적합을 줄이는 건 평균보다 '얕게'(depth=4)
#   검증 AUC는 전부 0.53~0.54 → 11달로는 모델끼리 차이를 가려낼 수 없음
# - 부스팅 곡선: 나무 10 → 600그루, 학습 AUC 0.69 → 0.97로 계속 오름, 검증 AUC는 0.53~0.54에서 제자리
#   → 나무를 더해 얻은 건 전부 학습 데이터 외우기
# - 시험(2025~, 21달): 나무 1그루 depth=10 AUC 0.464·롱숏 -3.5%/월 (6-3과 같음)
#   랜덤포레스트 depth=4 0.510·+1.2%/월(12/21달), XGBoost 나무100 0.509·+1.3%/월(13/21달)
#   LightGBM 0.516인데 롱숏 -0.1%/월, 로지스틱 0.505·+1.2%/월, 순위 평균 보팅 0.503
#   → 앙상블이 확실히 이긴 건 '깊은 나무 1그루'뿐. 로지스틱보다 뚜렷하게 낫지는 않음
#   → AUC가 높아도 롱숏이 마이너스일 수 있음(LightGBM): 전체 순서보다 양 끝 10종목이 중요
# - 순열 중요도: 학습에서 가장 많이 쓴 amt_log(거래대금)는 2025년엔 오히려 마이너스.
#   2025년에 조금이라도 도움 된 건 amt_chg·dist_hi(고점 대비)·mom_3m (각 +0.004~0.006)
# - 표 데이터 앙상블이 강해도, 주가 다음 달 상·하위 맞히기는 AUC 0.5 근처가 정상. 0.52~0.53이면 쓸 만한 편
# - 설정값 고르기는 6-5(하이퍼파라미터 튜닝)에서 시간순 교차검증(TimeSeriesSplit)으로 이어짐

# %% 앙상블 · 부트스트랩 · 배깅과 부스팅
"""
1. 앙상블(Ensemble)
(1) 개념
- 단일 모델이 가진 편향과 분산으로 인한 오류를 줄이기 위해 여러 개의 예측 모델을 만들어 결합하는 방법
- 대표 기법: 배깅(Bagging), 부스팅(Boosting), 랜덤포레스트(Random Forest) 및 
            이를 발전시킨 XGBoost와 LightGBM이 실무에서 널리 쓰인다.


(2) 부트스트랩
1) 개념
- 단순 임의 복원 추출(Random Sampling with Replacement)로 원본 데이터에서 여러 개의 같은 크기 표본을 만드는 방법
- 각 표본에서 독립적으로 모델을 학습가능 
- 중복을 허용하므로 원본 데이터 일부가 한 번 이상 뽑힐 수 있다

2) 앙상블에서 부트스트랩을 쓰는 두가지 학습전략
- 부트스트랩  병렬로 학습 = 배깅(Bagging)
- 부트스트랩 순차적으로 학습 = 부스팅(Boosting)
 
→ 부트스트랩은 단일 모델의 편향과 분산을 줄이는 앙상블 기법의 핵심 기반
  
예: 원본 [A, B, C, D, E]에서 5번 복원 추출 → [A, A, C, D, D] (B·E는 빠지고 A·D는 두 번)



2. 배깅과 부스팅
(1) 배깅
- 원본 학습 데이터에서 중복 허용 무작위 샘플링(부트스트랩)으로 여러 서브셋을 만들고,
  각 모델을 병렬로 학습시킨 뒤 다수결(분류) 또는 평균(회귀)으로 결합
- 부트스트랩을 하면 확률적으로 학습 데이터의 약 63%만 사용되고, 뽑히지 않은 37%는
  OOB(Out-of-Bag) 샘플로 따로 검증에 쓸 수 있으며 이를 oob_score라고 한다.
  
한 행이 n번 뽑기에서 한 번도 안 뽑힐 확률 = (1 - 1/n)^n → n=100이면 0.366 ≈ 37%


(2) 부스팅
- 이전 모델이 틀린 데이터에 가중치를 더 주면서 순차적으로 약한 학습기를 이어 붙여 강한 모델을 만든다
- 배깅보다 높은 예측력을 얻을 수 있지만, 순차 학습이라 학습 속도가 느리고 과적합 위험이 있다


(3) 배깅 vs 부스팅 핵심 차이
· 배깅: 병렬 학습, 분산 감소, OOB 검증 가능
· 부스팅: 순차 학습, 편향 감소, 과적합 주의 필요



3. 랜덤포레스트
(1) 개념
- 랜덤포레스트는 부트스트랩 샘플링으로 수백~수천 개의 결정트리를 만들고, 
  각 트리를 만들 때 전체 입력특성 중 일부만 무작위로 골라 분기 기준을 정한다
- 트리 간 상관관계를 낮춰 과적합 문제를 줄이면서도 높은 예측력을 유지한다
- OOB 샘플을 쓰면 별도 검증세트 없이 모델의 일반화 성능을 추정할 수 있고,
  feature_importances_로 입력특성이 예측에 얼마나 기여했는지 알 수 있다
  
  

- 예시 
  Stage 1 Bootstrap 샘플링: 데이터세트 → Random subset 1, 2, 3 ...
  Stage 2 모델 학습:        subset마다 Tree 1, Tree 2, ... Tree n
  Stage 3 예측 모델:        Predict 1, Predict 2, ... Predict n
  Stage 4 결과 취합:        개별 트리모델의 예측 결과를 취합(다수결·평균)




4. 랜덤포레스트 주요 파라미터 (RandomForestClassifier / RandomForestRegressor)
| 파라미터     | 기본값 | 설명                                                    |
| n_estimators | 100    | 생성할 결정트리 수. 클수록 안정적이나 학습 시간 증가        |
| criterion    | 'gini' | 분할 기준, 'gini' 또는 'entropy'                         |
| max_depth    | None   | 각 트리의 최대 깊이. None이면 불순도 0이 될 때까지 성장     |
| max_features | 'auto' | 분기 때 고려할 입력특성 수, 'sqrt', 'log2' 또는 정수       |
| oob_score    | False  | True면 OOB 샘플로 검증 자동 수행                          |

(※ 'auto'는 sklearn 1.3부터 없어짐. 지금 분류 기본값은 'sqrt' = 특성 8개면 √8 ≈ 2~3개씩)

"""

# %% 1. 랜덤포레스트 — (1) 분류 문제
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             classification_report, mean_squared_error, mean_absolute_error)

warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

DATA = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\데이터분석_파이썬\참고코드\개정판_py\data'
breast = pd.read_csv(DATA + r'\breast-cancer.csv')
# 책 원래 줄: pd.read_csv("https://raw.githubusercontent.com/ADPclass/ADP_book_ver01/main/data/breast-cancer.csv")

breast['diagnosis'] = np.where(breast['diagnosis'] == 'M', 1, 0)   # 악성(M)=1, 양성(B)=0
features = ['area_mean', 'texture_mean']
X = breast[features]
y = breast['diagnosis']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=1)

# %% 모델 학습
from sklearn.ensemble import RandomForestClassifier

clf = RandomForestClassifier(n_estimators=100, min_samples_split=5, random_state=42)
clf.fit(X_train, y_train)

# %% 성능 평가
pred = clf.predict(X_test)
acc = accuracy_score(y_test, pred)
prs = precision_score(y_test, pred)
rcll = recall_score(y_test, pred)
f1 = f1_score(y_test, pred)

print(classification_report(y_test, pred))
print('정확도\t{}%'.format(round(acc * 100, 2)))
print('정밀도\t{}%'.format(round(prs * 100, 2)))
print('재현율\t{}%'.format(round(rcll * 100, 2)))
print('F1\t{}%'.format(round(f1 * 100, 2)))

# %% OOB 평가 (별도 검증세트 없이 성능 추정)
#   복원추출하면 나무마다 약 37%의 행이 안 뽑힘(Out-Of-Bag) → 그 행으로 채점
#   (1 - 1/n)^n → n이 크면 e^-1 = 0.368
clf_oob = RandomForestClassifier(n_estimators=100, oob_score=True, random_state=42)
clf_oob.fit(X, y)
print('OOB Score:', round(clf_oob.oob_score_, 4))

# %% 특성 중요도
fi = pd.DataFrame({'feature': features, 'importance': clf_oob.feature_importances_})
print(fi.sort_values('importance', ascending=False))

# %% 1. 랜덤포레스트 — (2) 회귀 문제
from sklearn.ensemble import RandomForestRegressor

car = pd.read_csv(DATA + r'\CarPrice_Assignment.csv')
car_num = car.select_dtypes(['number'])

features_reg = list(car_num.columns.difference(['car_ID', 'symboling', 'price']))
X = car_num[features_reg]
y = car_num['price']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)

reg = RandomForestRegressor(n_estimators=100, random_state=42)
reg.fit(X_train, y_train)

# %% 성능 평가
pred = reg.predict(X_test)
mse = mean_squared_error(y_test, pred)
rmse = np.sqrt(mse)
mae = mean_absolute_error(y_test, pred)
r2 = reg.score(X_test, y_test)
print(f'MSE: {mse:.1f}, RMSE: {rmse:.1f}, MAE: {mae:.1f}')
print(f'R2(Acc): {r2 * 100:.3f}%')

# %% 특성 중요도
fi = pd.DataFrame({'feature': features_reg, 'importance': reg.feature_importances_})
print(fi.sort_values('importance', ascending=False))

# %% XGBoost
"""
XGBoost(eXtreme Gradient Boosting)
1. 개념
- 속도와 성능을 모두 잡은 대표적인 부스팅 알고리즘
- 이전 트리가 예측한 오류(잔차)를 다음 트리가 보정하는 그래디언트 부스팅 방식을 기반으로 만들어짐. 
- L1·L2 규제, 병렬 처리, 결측값 자동 처리 등으로 성능과 속도를 크게 높인 것이 특징
- 트리를 레벨(깊이) 단위로 분할하고, learning_rate와 early_stopping 기능으로 과적합을 막는다


XGBoost 주요 파라미터 (XGBClassifier / XGBRegressor)
| 파라미터              | 기본값 | 설명                                              |
| max_depth             | 6      | 각 트리의 최대 깊이. 클수록 복잡하며 과적합 주의       |
| learning_rate         | 0.3    | 각 트리의 축소율. 작을수록 과적합 방지                 |
| subsample             | 1.0    | 각 트리 학습 때 쓸 샘플 비율(0~1), 1이면 전체 사용     |
| colsample_bytree      | 1.0    | 각 트리에서 쓸 입력특성 비율, 작을수록 다양성 증가     |
| early_stopping_rounds | None   | 지정 라운드 동안 성능 개선이 없으면 조기 종료          |

"""

# %% 2. XGBoost — (1) 분류 문제
from xgboost import XGBClassifier, XGBRegressor, plot_importance

X = breast[features]
y = breast['diagnosis']
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=1)

xgb = XGBClassifier(learning_rate=0.2, early_stopping_rounds=20, random_state=42)
xgb.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
#   주의: 책은 시험 데이터로 '언제 멈출지'를 정함 → 시험 점수가 좋게 나옴. 원래는 검증 데이터를 따로 둬야 함
print('최적 트리 수:', xgb.best_iteration)

# %% 성능 평가
pred_xgb = xgb.predict(X_test)
acc = accuracy_score(y_test, pred_xgb)
prs = precision_score(y_test, pred_xgb)
rcll = recall_score(y_test, pred_xgb)
f1 = f1_score(y_test, pred_xgb)

print(classification_report(y_test, pred_xgb))
print('정확도\t{}%'.format(round(acc * 100, 2)))
print('정밀도\t{}%'.format(round(prs * 100, 2)))
print('재현율\t{}%'.format(round(rcll * 100, 2)))
print('F1\t{}%'.format(round(f1 * 100, 2)))

# %% 특성 중요도
plot_importance(xgb, title='XGBoost 특성 중요도')
plt.show()

# %% 2. XGBoost — (2) 회귀 문제
X = car_num[features_reg]
y = car_num['price']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)

xgb_reg = XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.2, random_state=42)
xgb_reg.fit(X_train, y_train)
pred_xgb_r = xgb_reg.predict(X_test)

mse = mean_squared_error(y_test, pred_xgb_r)
rmse = np.sqrt(mse)
mae = mean_absolute_error(y_test, pred_xgb_r)
print(f'RMSE: {rmse:.1f}, MAE: {mae:.1f}')
print(f'R2(ACC): {xgb_reg.score(X_test, y_test) * 100:.3f}%')

# %% 특성 중요도
plot_importance(xgb_reg, title='XGBoost 특성 중요도')
plt.show()

# %% LightGBM
"""
LightGBM(Light Gradient Boosting Machine)

1. 개념 
- 빠르고 메모리 효율이 높은 최강의 부스팅 기법
- LightGBM은 Leaf-wise 전략으로 손실 감소가 가장 큰 리프를 골라 분할한다.
- 트리 깊이가 비대칭으로 커질 수 있고, 같은 조건에서 Level-wise 방식보다 더 빠르게 손실을 줄이는 경향
- GOSS(Gradient-based One-Side Sampling)와 EFB(Exclusive Feature Bundling)로 속도와 메모리 효율을 크게 높임
- 손실이 가장 큰 리프(Leaf)부터 분할하므로 더 적은 트리로도 높은 정확도 가능

2. LightGBM의 장점
  (1) 속도: GOSS로 불필요한 샘플 제거 → XGBoost 대비 수배 빠름
  (2)메모리: EFB로 희소 입력특성 압축 → 대용량 데이터 처리 가능
  (3) 범주형: 범주형 입력특성을 인코딩 없이 직접 처리(categorical_feature 지정)
  
  
3. LightGBM 사용 시 주의상황
- Leaf-wise 분할은 데이터가 적을 때 과적합 위험이 있어 leaf 수와 depth를 적절히 조절해야 한다.
- 소규모 데이터에서는 XGBoost나 랜덤포레스트가 더 안전할 수 있다.
-  XGBoost와 LightGBM은 수천 개 이상의 대규모 데이터에서 강력한 효과를 낸다.
    

4. LightGBM 주요 파라미터 (LGBMClassifier / LGBMRegressor)
| 파라미터            | 기본값 | 설명                                                      |
| n_estimators        | 100    | 생성할 결정트리 수. 클수록 안정적이나 학습 시간 증가          |
| num_leaves          | 31     | 하나의 트리에서 허용할 최대 리프 수                           |
| max_depth           | -1     | 최대 트리 깊이, -1이면 제한 없음                              |
| learning_rate       | 0.1    | 학습률. 작을수록 천천히 학습하고 일반화 성능 향상              |
| categorical_feature | 'auto' | 범주형 입력특성 컬럼 지정, 인코딩 없이 직접 처리 가능          |

"""
#%%
"""
[Tip] 랜덤포레스트 · XGBoost · LightGBM 종합 비교
| 비교 항목       | 랜덤포레스트 | XGBoost         | LightGBM               |
| 학습 방식       | 배깅(병렬)   | 순차 부스팅      | 순차 부스팅(Leaf-wise)  |
| 예측 정확도     | ★★★★☆      | ★★★★★          | ★★★★★                 |
| 학습 속도       | ★★★☆☆      | ★★★☆☆          | ★★★★★                 |
| 메모리 효율     | ★★★☆☆      | ★★★☆☆          | ★★★★★                 |
| 범주형 처리     | 인코딩 필요  | 인코딩 필요      | 직접 처리 가능          |
| 과적합 방지     | 강함(앙상블) | 중간(규제 내장)  | num_leaves 주의         |
| 추천 데이터 규모 | 중~대규모   | 중~대규모        | 대규모                  |
| 코드 라이브러리 | sklearn      | xgboost          | lightgbm               |
"""

# %% 3. LightGBM — (1) 분류 문제
import lightgbm as lgb
from lightgbm import LGBMClassifier, LGBMRegressor

X = breast[features]
y = breast['diagnosis']
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=1)

lgbm_clf = LGBMClassifier(n_estimators=200, num_leaves=31, learning_rate=0.05,
                          random_state=42, verbose=-1)     # verbose=-1: 학습 로그 끄기
lgbm_clf.fit(X_train, y_train)
pred_lgbm = lgbm_clf.predict(X_test)

print(classification_report(y_test, pred_lgbm))
print('정확도:', round(accuracy_score(y_test, pred_lgbm) * 100, 2), '%')

# %% 특성 중요도
lgb.plot_importance(lgbm_clf, figsize=(6, 4), title='LightGBM 특성 중요도')
plt.show()

# %% 3. LightGBM — (2) 회귀 문제
X = car_num[features_reg]
y = car_num['price']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)

lgbm_reg = LGBMRegressor(n_estimators=200, num_leaves=31, learning_rate=0.05,
                         subsample=0.8, random_state=42, verbose=-1)
lgbm_reg.fit(X_train, y_train)
pred_lgbm_r = lgbm_reg.predict(X_test)

mse = mean_squared_error(y_test, pred_lgbm_r)
rmse = np.sqrt(mse)
mae = mean_absolute_error(y_test, pred_lgbm_r)
print(f'RMSE: {rmse:.1f}, MAE: {mae:.1f}')
print(f'R2(ACC): {lgbm_reg.score(X_test, y_test) * 100:.3f}%')

# %% 특성 중요도
lgb.plot_importance(lgbm_reg, figsize=(6, 4), title='LightGBM 특성 중요도')
plt.show()



