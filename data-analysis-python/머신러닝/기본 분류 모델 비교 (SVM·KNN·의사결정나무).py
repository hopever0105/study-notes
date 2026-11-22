# -*- coding: utf-8 -*-
# 기본 분류 모델 비교 (SVM·KNN·의사결정나무) (6-3)
#
# 언제 쓰나: 로지스틱(직선 경계) 말고 다른 모양의 경계로 분류해 볼 때.
#   - SVM           : 두 무리 사이 '여백(margin)'이 가장 넓은 경계. 커널로 곡선 경계도 가능. 단위 맞추기 필수
#   - KNN           : 가장 가까운 k개 이웃의 다수결. 학습이 없고 거리만 잼 → 단위 맞추기 필수
#   - 의사결정나무   : "mom_3m 순위 > 0.7 ?" 같은 질문을 이어 붙임. 단위 상관없음, 깊으면 과적합


# %% 월말 패널 만들기 (6-2 파일과 같은 변수·같은 정답)
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix, accuracy_score
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report
from sklearn.tree import DecisionTreeRegressor
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.tree import export_text

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

# %% 시간순 3분할 (3-3 파일과 같은 생각): 학습 ~2023 / 검증 2024 (설정값 고르기) / 시험 2025~ (마지막 한 번)
#   월말 1개월 정답이라 경계에서 한 달씩 겹침 → 학습 마지막 달(2023-12)의 정답은 2024-01 가격 → 1달 버림
train = me[me['ym'] <= pd.Period('2023-11', 'M')]
valid = me[(me['ym'] >= pd.Period('2024-01', 'M')) & (me['ym'] <= pd.Period('2024-11', 'M'))]
test = me[me['ym'] >= pd.Period('2025-01', 'M')]
print('학습', len(train), '/ 검증', len(valid), '/ 시험', len(test))


def score_rank(d, prob, k=10):
    """확률 순위로 매달 상위 k 매수·하위 k 매도 → 평균 월 롱숏, 이긴 달 수"""
    t = d.assign(prob=prob)
    rows = []
    for ym, x in t.groupby('ym'):
        x = x.sort_values('prob')
        rows.append(x['fwd_1m'].tail(k).mean() - x['fwd_1m'].head(k).mean())
    ls = pd.Series(rows)
    return round(roc_auc_score(d['y'], prob), 4), round(ls.mean(), 4), f'{int((ls > 0).sum())}/{len(ls)}'


def prob_of(model, X):
    """SVC는 확률 대신 경계까지 거리(decision_function)를 줌 → 순위만 필요하니 그대로 써도 됨"""
    if hasattr(model, 'predict_proba'):
        return model.predict_proba(X)[:, 1]
    return model.decision_function(X)


# %% 1) 설정값 고르기 — 학습으로 fit, '검증'(2024)으로 점수. 시험은 아직 안 봄
#   SVM C    : 클수록 학습 데이터에 딱 맞춤(여백 좁음) → 과적합 쪽
#   KNN k    : 작을수록 이웃 몇 개에 휘둘림 → 과적합 쪽. 클수록 평균에 가까워짐
#   나무 depth: 깊을수록 질문이 많아짐 → 과적합 쪽
cands = {}
for C in [0.01, 0.1, 1.0]:
    cands[f'SVM rbf C={C}'] = make_pipeline(StandardScaler(), SVC(C=C, kernel='rbf'))
for k in [5, 25, 100, 300]:
    cands[f'KNN k={k}'] = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=k))
for dep in [2, 3, 5, 10]:
    cands[f'나무 depth={dep}'] = DecisionTreeClassifier(max_depth=dep, min_samples_leaf=30, random_state=0)
cands['로지스틱(6-2 기준)'] = make_pipeline(StandardScaler(), LogisticRegression(C=1.0))

rows = []
for name, m in cands.items():
    m.fit(train[FEATS], train['y'])
    tr_auc = roc_auc_score(train['y'], prob_of(m, train[FEATS]))
    va = score_rank(valid, prob_of(m, valid[FEATS]))
    rows.append([name, round(tr_auc, 4), *va])
res = pd.DataFrame(rows, columns=['모델', '학습 AUC', '검증 AUC', '검증 롱숏/월', '이긴 달'])
print(res.to_string(index=False))
print('→ 학습 AUC는 높은데 검증 AUC가 0.5 근처면 과적합 (KNN k=5, 나무 depth=10 확인)')

# %% 2) 모델 종류마다 검증 AUC 1등 설정만 골라 → 시험(2025~)에서 딱 한 번
res['종류'] = res['모델'].str.split(' ').str[0]
best = res.sort_values('검증 AUC', ascending=False).groupby('종류').head(1)
rows = []
for name in best['모델']:
    m = cands[name]
    m.fit(pd.concat([train, valid])[FEATS], pd.concat([train, valid])['y'])   # 고른 뒤엔 학습+검증으로 다시 학습
    rows.append([name, *score_rank(test, prob_of(m, test[FEATS]))])
print(pd.DataFrame(rows, columns=['모델', '시험 AUC', '시험 롱숏/월', '이긴 달']).to_string(index=False))

# %% 3) 나무는 '규칙'을 글로 볼 수 있다 (depth=2)
tree2 = DecisionTreeClassifier(max_depth=2, min_samples_leaf=30, random_state=0).fit(train[FEATS], train['y'])
print(export_text(tree2, feature_names=FEATS))
print(pd.Series(tree2.feature_importances_, index=FEATS).sort_values(ascending=False).round(3))

# %% 4) 단위를 안 맞추면 KNN이 어떻게 되나 — 순위 대신 '원래 값'을 넣어 비교
#   amt_log(로그 거래대금)는 20~30, 수익률은 0.0x → 거리 계산을 amt_log 하나가 다 차지함
raw = px.groupby(['code', 'ym']).tail(1).sort_values(['code', 'ym']).copy()
raw['fwd_1m'] = raw.groupby('code')['close'].shift(-1) / raw['close'] - 1
raw = raw.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATS + ['fwd_1m']).reset_index(drop=True)
raw['y'] = (raw['fwd_1m'] >= raw.groupby('ym')['fwd_1m'].transform('median')).astype(int)
r_tr = raw[raw['ym'] <= pd.Period('2023-11', 'M')]
r_va = raw[(raw['ym'] >= pd.Period('2024-01', 'M')) & (raw['ym'] <= pd.Period('2024-11', 'M'))]
print(r_tr[FEATS].describe().loc[['mean', 'std']].round(3))
for nm, m in [('KNN k=100 단위 그대로', KNeighborsClassifier(n_neighbors=100)),
              ('KNN k=100 StandardScaler', make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=100)))]:
    m.fit(r_tr[FEATS], r_tr['y'])
    print(nm, '→ 검증 AUC', round(roc_auc_score(r_va['y'], m.predict_proba(r_va[FEATS])[:, 1]), 4))

# %% 단위 그대로가 오히려 높게 나온 이유 확인
#   위 표에서 표준편차가 큰 변수: amt_log 1.35, mom_12_1 1.31, amt_chg 0.62 (나머지는 0.5 아래)
#   → 거리 계산을 이 세 개가 거의 다 차지. 세 개만 넣은 KNN과 점수가 비슷하면, '단위 그대로' 모델은
#     사실상 변수 3개짜리 모델. 2024년에 그 셋이 마침 맞았던 것이지 모델이 좋아진 게 아님.
#   어떤 변수를 쓸지는 내가 정해야지, 단위 크기가 정하면 안 됨.
for cols in [['amt_log'], ['amt_log', 'mom_12_1'], ['amt_log', 'mom_12_1', 'amt_chg']]:
    m1 = KNeighborsClassifier(n_neighbors=100).fit(r_tr[cols], r_tr['y'])
    print('KNN k=100', cols, '만 → 검증 AUC', round(roc_auc_score(r_va['y'], m1.predict_proba(r_va[cols])[:, 1]), 4))

# %% 정리 — 11/20 실행 결과(F5, 약 1분)
# - 검증(2024): 학습 AUC가 높을수록 과적합 — KNN k=5 학습 0.79 → 검증 0.52, 나무 depth=10 학습 0.72
# - 시험(2025~, 21달): SVM C=0.1 AUC 0.513·롱숏 +3.4%/월(12/21달), KNN k=25 0.507, 로지스틱 0.505
#   나무 depth=10은 검증 1등(0.541)이었는데 시험 0.464·롱숏 -3.5%/월 → 검증 1등도 우연일 수 있음(11달뿐)
# - 단위 그대로 KNN이 검증 0.561로 더 높게 나왔지만, 큰 변수 3개(amt_log·mom_12_1·amt_chg)만 쓴 KNN이 0.557
#   → 사실상 변수 3개짜리 모델. 단위 크기가 변수를 골라 버린 것 (amt_log 하나만이면 0.449)
# - 책: 무작위 70/30, 정확도·F1. 금융판: 시간순 학습/검증/시험, AUC + 확률 순위 상위10-하위10 롱숏
# - 설정값(C, k, depth)은 검증 기간으로만 고르고, 시험은 마지막에 한 번
# - SVM·KNN은 거리 기반 → 단위 맞추기(3-3) 안 하면 큰 숫자 변수 하나가 결과를 결정
# - 나무는 단위 상관없고 규칙이 보이지만, 깊으면 학습 AUC만 올라감 → 6-4 앙상블(여러 나무 평균)로 이어짐

# %% 서포트 벡터 머신(SVM) 개념
"""
개념
1. 서포트 벡터 머신(SVM, Support Vector Machine)
- 두 집단을 나누는 경계를 가능한 한 넓게 확보하는 분류하는 방법
- 분류뿐 아니라 회귀 문제에도 쓸 수 있고, 다음 세 단계를 거쳐 발전했다.
: 최대 마진 분류기 → 서포트 벡터 분류기(SVC) → 서포트 벡터 머신(SVM) 
(각 단계는 이전 방법의 한계를 극복하고 더 넓은 상황에 적용할 수 있도록 확장된 것)

1) 최대 마진 분류기
- 두 클래스를 나누는 경계선(초평면, Hyperplane)은 이론적으로 무한히 생성 가능.

(1) 최대마진 초평면 
그중 양쪽 클래스와의 거리가 가장 균등하게 최대화된 초평면
이건 2차원 적인 평면

(2) 서포트 벡터 
초평면에 가장 가까이 있는 데이터 포인트들 
서포트 벡터들이 초평면의 위치를 사실상 결정한다.
이건 그 경계선들 점이라고 생각하면 편ㅎ다.  


(3) 한계
- 모든 데이터가 초평면으로 완벽히 나뉘지 않으면 쓰기 어렵다.
- 이상치 하나에도 경계가 크게 흔들리는 민감한 구조



2. 서포트 벡터 분류기(SVC)
(1) 개념
- 일부 데이터가 경계를 침범하는 것을 허용하면서 더 안정적인 분류 경계를 만드는 분류기
- 이 허용 정도를 조절하는 것이 파라미터 C(비용, Cost)

(2) c의 특성 
"C가 작을수록 경계 위반에 엄격 → 마진 좁고 복잡(과적합 위험),
C가 클수록 위반을 관대하게 허용 → 마진 넓고 단순(과소적합 위험)


(3) 주의
- scikit-learn의 SVC에서는 반대다. 
- C = 경계를 넘은 점 하나당 '벌점'의 크기.
     
ex) 
C = 100 → 한 점만 넘어도 벌점이 커서 모든 점을 맞히려 함 → 마진 좁음·복잡(과적합 쪽)
C = 0.01 → 넘어도 벌점이 작아 몇 개는 포기하고 넓은 도로 → 마진 넓음·단순(과소적합 쪽)



3. 서포트 벡터 머신(SVM)
(1) 커널 트릭(Kernel Trick)
클래스 경계가 직선이 아니라 곡선·비선형일 때, 입력특성을 더 높은 차원으로 변환해 고차원 공간에서 선형 분리를 시도


(2) 사용 이유 
데이터가 많지 않고 정확한 경계를 찾고 싶을 때 좋은 선택.
반대로 데이터가 매우 많으면 학습 속도가 느려져 트리 계열 모델을 더 많이 쓴다.



4, 주요 파라미터 (sklearn SVC 클래스)
| 파라미터 | 기본값 | 설명                                                    |
| C        | 1.0    | 경계 위반 허용에 대한 비용 (책: 클수록 유연, 작을수록 엄격) |
| kernel   | 'rbf'  | 커널 유형: 'linear', 'poly', 'rbf', 'sigmoid' 중 선택     |
"""


# %% 1. 서포트벡터머신 (SVM)
import pandas as pd
import numpy as np

DATA = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\데이터분석_파이썬\참고코드\개정판_py\data'
c = pd.read_csv(DATA + r'\classification.csv')
# 케글의 classification 데이터 활용해 SVC 모델 학습

# %% 입력특성 (X)와 레이블 (y)를 설정한 후 7:3의 비율로 학습 데이터와 평가 데이터 분리
from sklearn.model_selection import train_test_split

X = c[["age", "interest"]]
y = c["success"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, stratify=y, train_size=0.7, random_state=1)
print(X_train.shape, X_test.shape)

# %% 
# svc 이상치에 민감한 바, 표준화 통해 스케일링하면 예측력 높은 결정경계 생성 가능
# 표준하 이용해 스케일링 하고 학습 데이터의 클래스 분포를 산점도로 확인
import seaborn as sns
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)

X_train_df = pd.DataFrame(X_train_sc, columns=X_train.columns)
X_train_df['success'] = y_train.reset_index(drop=True).copy()

sns.pairplot(hue="success", data=X_train_df)
# 나이와 흥미에 따라 성공 여부가 나누어짐 

# %% SVC로 모델 생성 후 데이터 학습
from sklearn.svm import SVC

clf = SVC(C=0.5, random_state=45)
clf.fit(X_train_sc, y_train)

# %% 테스트 데이터로 모델 평가 수행
from sklearn.metrics import confusion_matrix, accuracy_score
from sklearn.metrics import precision_score, recall_score, f1_score

X_test_sc = scaler.transform(X_test)
pred = clf.predict(X_test_sc)

acc = accuracy_score(y_test, pred)
prc = precision_score(y_test, pred)
rcll = recall_score(y_test, pred)
f1 = f1_score(y_test, pred)

print("정확도\t{}%".format(round(acc * 100, 2)))
print("정밀도\t{}%".format(round(prc * 100, 2)))
print("재현율\t{}%".format(round(rcll * 100, 2)))
print("F1\t{}%".format(round(f1 * 100, 2)))

# %% 서포트 벡터 회귀(SVR)
"""
1. SVR
- SVM의 원리를 회귀분석에 적용한 방법.
- 분류에서는 두 클래스 사이 마진을 최대화, 회귀에서는 허용 범위(엡실론) 안에 최대한 많은 데이터를 포함시키면서 회귀선을 찾는 것이 목표

2. SVR 하이퍼파라미터 
- C(비용): 허용 범위 밖 데이터에 주는 페널티 크기. C가 클수록 회귀선이 복잡해짐
- ε(엡실론): 회귀선 위아래로 허용하는 오차 범위. ε이 클수록 더 많은 데이터가 허용 범위 안에 들어감


3. 주요 파라미터 (sklearn SVR 클래스)
| 파라미터 | 기본값 | 설명                                                  |
| epsilon  | 0.1    | 회귀선 주변 허용 오차 범위. 범위 안의 예측은 손실 없음   |
| C        | 1.0    | 범위 밖 데이터에 대한 페널티 크기. 클수록 유연해져 회귀선이 복잡해짐 |
| kernel   | 'rbf'  | 커널 유형: 'linear', 'poly', 'rbf', 'sigmoid' 중 선택   |

숫자 예: ε = 0.1이면 실제값 1.00, 예측 1.08 → 오차 0.08 < 0.1 → 손실 0
         예측 1.25 → 오차 0.25 → 범위 밖 0.15만큼 × C 가 손실
"""

# %% SVR: SVM으로 숫자 예측 (회귀)
# 샘플 데이터 생성하기
X = np.sort(5 * np.random.rand(40, 1), axis=0)
y = np.sin(X).ravel()

# 타깃 데이터에 노이즈 추가하기
y[::5] += 3 * (0.5 - np.random.rand(8))

# %% 커널을 기본값으로 선택하여 SVR 모델 생성
from sklearn.svm import SVR

svr = SVR()
svr.fit(X, y)

# %% 회귀 성능 평가 지표 통해 학습 데이터 예측 성능 확인 
from sklearn.metrics import mean_squared_error, mean_absolute_error

pred = svr.predict(X)
mse = mean_squared_error(y, pred)
mae = mean_absolute_error(y, pred)
rmse = np.sqrt(mse)

print("MSE: ", mse)
print("MAE: ", mae)
print("RMSE: ", rmse)


"""

데이터가 많지 않고 정확한 경계 찾고 싶을 때 SVM은 좋은 선택
반대로 데이터가 매우 많으면 학습 속도가 느려져 트리 계열 모델을 더 많이 사용한다. 

"""
# %% KNN 개념
"""
KNN(K-Nearest Neighbors)
1. 개념
- 새로운 데이터가 들어오면 학습 데이터에서 거리가 가장 가까운 k개의 데이터 포인트를 찾아, 
  이들의 레이블로 분류 또는 회귀값을 예측하는 방법
- 학습 단계에서 별도의 모델을 만들지 않고 학습 데이터를 그대로 저장하는 방식 → 지연 학습(Lazy Learning)
- 거리 계산은 주로 유클리디안 거리: 두 점 사이의 직선 거리(우리가 상식으로 아는 가장 짧은 거리) 사용
      d = √((x1 - x2)² + (y1 - y2)²)
예: (1, 2)와 (4, 6) → √(3² + 4²) = √25 = 5


2. KNN 분류
- k=1이면 가장 가까운 데이터 1개만으로 분류 → 데이터 경계 근처에서는 이상치 하나에도 결과가 바뀜
- k를 적절히 크게 하면 이상치 영향을 줄이고 더 안정적인 분류 경계를 얻는다

3. KNN 회귀
- k개 이웃 레이블 값의 평균을 예측값으로 돌려줌
- 선형회귀처럼 회귀식을 하나 만들지 않으므로 입력특성 각각의 영향력을 직접 확인할 수 없다

4. 주요 파라미터 (KNeighborsClassifier / KNeighborsRegressor)
| 파라미터    | 기본값 | 설명                              |
| n_neighbors | 5      | 이웃으로 참고할 데이터 포인트 수(k) |


5.  k 값 선택 시 주의점
 - k가 너무 작으면 이상치에 민감해 과적합될 수 있다
 - k가 너무 크면 너무 많은 데이터를 고려해 경계가 흐릿해진다(과소적합)
 - 보통 홀수 k를 써서 동점을 피하고, 교차검증으로 최적값을 찾는다

6. KNN 활용 
 - 데이터 분포를 가정하기 어렵거나 결정 경계가 복잡할 때 효과적
 - 비모수적 방법이라 데이터 분포에 대한 사전 가정이 필요 없어 유연하다
 - 분류·회귀 모두 가능, 데이터 양이 적고 특징(feature) 수가 많지 않을 때 특히 효율적
"""

# %% 2. KNN
liver = pd.read_csv(DATA + r'\indian_liver_patient.csv')

# 레이블 이진화: 간암환자(1) / 비환자(0)
liver["Dataset"] = np.where(liver["Dataset"] == 2, 0, 1)
# 성별 원핫인코딩
liver["Gender"] = np.where(liver["Gender"] == "Female", 0, 1)
# 결측치 제거
liver.dropna(axis=0, inplace=True)

# %%
from sklearn.neighbors import KNeighborsClassifier

X = liver[liver.columns.difference(["Dataset"])]
y = liver["Dataset"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, stratify=y, train_size=0.7, random_state=1)

clf = KNeighborsClassifier(n_neighbors=15)
clf.fit(X_train, y_train)

# %%
pred = clf.predict(X_test)

acc = accuracy_score(y_test, pred)
prc = precision_score(y_test, pred)
rcll = recall_score(y_test, pred)
f1 = f1_score(y_test, pred)

print("정확도\t{}%".format(round(acc * 100, 2)))
print("정밀도\t{}%".format(round(prc * 100, 2)))
print("재현율\t{}%".format(round(rcll * 100, 2)))
print("F1\t{}%".format(round(f1 * 100, 2)))

# %% 의사결정나무 개념
"""
의사결정나무(Decision Tree)

1. 개념
-  데이터를 분류하거나 예측하는 결정에 이르기 위해, 각 단계에서 최적의 분리 기준을 찾아 트리 구조로 데이터를 나눠 가는 모델
- 입력특성과 레이블 모두 연속형·범주형을 가리지 않고 사용 가능
- 선형성이나 정규성 같은 통계적 가정이 필요 없다


2.분리 기준
- 각 노드에서 데이터를 나눌 때, 레이블이 범주형이면 지니 지수 또는 엔트로피를 사용.
- 각 노드에서 데이터를 나눌 때 레이블이 연속형이면 분산 감소량을 기준으로 사용
- 모든 기준은 "불순도(Impurity)"를 최소화하는 방향으로 분리를 고른다.

3. 불순도
- 한 노드 안에 서로 다른 레이블이 섞여 있으면 "불순도가 높다".
- 의사결정나무는 분기 후 노드의 불순도가 가장 많이 낮아지는 입력특성과 기준값을 고른다.
- 즉, 나눈 뒤 각 그룹이 가능한 한 순수하게 같은 레이블로 이뤄지도록 학습한다.
  
 
불순도 예시 
지니 = 1 - Σp²
위험 5·안전 5 → 1 - (0.5² + 0.5²) = 0.5 (가장 불순함)
위험 9·안전 1 → 1 - (0.9² + 0.1²) = 0.18 (거의 순수)
위험 10·안전 0 → 0 (완전 순수)


4. 과적합 방지: 가지치기(pruning)
- 질문 목록을 제한 없이 만들다 보면 학습 데이터에만 지나치게 맞는 과적합(Overfitting) 발생이 쉽다. 
- 이를 막기 위해 트리 성장을 제한하는 사전 가지치기(Pre-pruning)를 쓴다.
- scikit-learn에서는 max_depth, min_samples_split, min_samples_leaf 등으로 조절한다.


5. 특성 중요도(Feature Importance)
- 학습 후 각 입력특성이 분류·예측에 얼마나 기여했는지를 특성 중요도(0~1 사이)로 제공
- 값이 클수록 그 입력특성이 레이블 예측에 중요하게 쓰였다는 뜻
- 단, 이 값은 항상 양수이며, 레이블의 어느 방향(증가·감소)에 영향을 주는지는 알 수 없다

6. 의사결정나무 실습 — 주요 파라미터 (DecisionTreeClassifier / DecisionTreeRegressor)
| 파라미터          | 기본값 | 설명                                                               |
| criterion         | 'gini' | (분류) 'gini' 또는 'entropy' / (회귀) 'squared_error' 또는 'absolute_error' |
| max_depth         | None   | 트리의 최대 깊이. 제한이 없으면 과적합 가능성 높음                     |
| min_samples_split | 2      | 노드를 나누기 위한 최소 샘플 수                                       |
| ccp_alpha         | 0      | 비용-복잡도 가지치기 파라미터. 0보다 크면 가지치기 수행                 |



7.  의사결정나무의 활용 
 - 데이터 특징 간 관계를 직관적으로 파악하고 싶을 때
 - 범주형과 연속형 데이터가 섞인 경우
 - 비선형 관계가 있는 문제
 → 트리 구조로 결과를 시각화해 해석이 쉽고, 전처리가 거의 필요 없으며,
   의사결정 근거가 중요한 분야(의료, 금융 등)에서 유용하다
"""

#%%
# SVM · KNN · 의사결정나무 비교
#| 구분       | SVM                                        | KNN                                        | 의사결정나무                         |
#| 장점       | 고차원 데이터 성능↑, 비선형 경계(커널)        | 구현 단순, 직관적, 가정 불필요(비모수)        | 해석·시각화 쉬움, 전처리 영향 거의 없음 |
#| 단점       | 대용량에서 학습 느림, 커널·파라미터 선택 중요 | 예측 때 전체 학습 데이터와 비교, 고차원 성능↓ | 과적합 가능성 높음, 단일 트리 일반화 성능 제한 |
#| 단위 민감도 | 민감(표준화 필수)                           | 민감(표준화 권장)                             | 거의 없음                            |
#| 해석 용이성 | 낮음                                       | 중간                                         | 높음                                 |

# %% 3. 의사결정나무
credit = pd.read_csv(DATA + r'\credit_final.csv')

# %%
feature_columns = list(credit.columns.difference(["credit.rating"]))
X = credit[feature_columns]
y = credit["credit.rating"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, stratify=y, test_size=0.3, random_state=1)

print(X_train.shape, X_test.shape)

# %%
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report

clf = DecisionTreeClassifier(max_depth=5)
clf.fit(X_train, y_train)

pred = clf.predict(X_test)
print(classification_report(y_test, pred))

# %%
importances = clf.feature_importances_
column_nm = pd.DataFrame(X.columns)
feature_importances = pd.concat(
    [column_nm, pd.DataFrame(importances)], axis=1)
feature_importances.columns = ["feature_nm", "importances"]

# 중요도 기준으로 내림차순 정렬
print(feature_importances.sort_values("importances", ascending=False))

# %% 의사결정나무 회귀
from sklearn.tree import DecisionTreeRegressor

# 임의 데이터 생성 및 노이즈 추가
np.random.seed(0)
X = np.sort(5 * np.random.rand(400, 1), axis=0)
y = np.sin(X).ravel()
y[::1] += 1 * (0.5 - np.random.rand(400))

# 학습·평가 분할
train_x, test_x, train_y, test_y = train_test_split(
    X, y, train_size=0.7, random_state=1)

# %% max_depth 2와 5 비교
regr_1 = DecisionTreeRegressor(max_depth=2)
regr_2 = DecisionTreeRegressor(max_depth=5)

y_1 = regr_1.fit(train_x, train_y).predict(test_x)
y_2 = regr_2.fit(train_x, train_y).predict(test_x)

# %% 성능 비교
for pred, label in [(y_1, "depth=2"), (y_2, "depth=5")]:
    mse = mean_squared_error(test_y, pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(test_y, pred)
    print(f"{label} | MSE: {mse:.3f}, RMSE: {rmse:.3f}, MAE: {mae:.3f}")





