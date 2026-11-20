# -*- coding: utf-8 -*-
# 기본 분류 모델 비교 (SVM·KNN·의사결정나무) (6-3)
# 1부: 책 원본 따라 치기 / 2부: 금융판 — 다음 달 상위 절반 맞히기를 세 모델로 (로지스틱 6-2와 같은 패널)
# Spyder: F5 전체 실행 / Ctrl+Enter 현재 셀 실행 / F9 선택 줄 실행
#
# 언제 쓰나: 로지스틱(직선 경계) 말고 다른 모양의 경계로 분류해 볼 때.
#   - SVM           : 두 무리 사이 '여백(margin)'이 가장 넓은 경계. 커널로 곡선 경계도 가능. 단위 맞추기 필수
#   - KNN           : 가장 가까운 k개 이웃의 다수결. 학습이 없고 거리만 잼 → 단위 맞추기 필수
#   - 의사결정나무   : "mom_3m 순위 > 0.7 ?" 같은 질문을 이어 붙임. 단위 상관없음, 깊으면 과적합
# 책 데이터는 GitHub 주소에서 받는데, 같은 파일이 참고코드 data 폴더에 있어서 그걸 씀

# =====================================================================
# 1부. 책 원본
# =====================================================================

# %% 1. 서포트벡터머신 (SVM)
import pandas as pd
import numpy as np

DATA = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\데이터분석_파이썬\참고코드\개정판_py\data'
c = pd.read_csv(DATA + r'\classification.csv')

# %%
from sklearn.model_selection import train_test_split

X = c[["age", "interest"]]
y = c["success"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, stratify=y, train_size=0.7, random_state=1)
print(X_train.shape, X_test.shape)

# %%
import seaborn as sns
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)

X_train_df = pd.DataFrame(X_train_sc, columns=X_train.columns)
X_train_df['success'] = y_train.reset_index(drop=True).copy()

sns.pairplot(hue="success", data=X_train_df)

# %%
from sklearn.svm import SVC

clf = SVC(C=0.5, random_state=45)
clf.fit(X_train_sc, y_train)

# %%
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

# %% SVR: SVM으로 숫자 예측 (회귀)
# 샘플 데이터 생성하기
X = np.sort(5 * np.random.rand(40, 1), axis=0)
y = np.sin(X).ravel()

# 타깃 데이터에 노이즈 추가하기
y[::5] += 3 * (0.5 - np.random.rand(8))

# %%
from sklearn.svm import SVR

svr = SVR()
svr.fit(X, y)

# %%
from sklearn.metrics import mean_squared_error, mean_absolute_error

pred = svr.predict(X)
mse = mean_squared_error(y, pred)
mae = mean_absolute_error(y, pred)
rmse = np.sqrt(mse)

print("MSE: ", mse)
print("MAE: ", mae)
print("RMSE: ", rmse)

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


# =====================================================================
# 2부. 금융판 — 다음 달 상위 절반에 들까? (6-2 로지스틱과 같은 문제, 모델만 바꿈)
# =====================================================================

# %% 월말 패널 만들기 (6-2 파일과 같은 변수·같은 정답)
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
