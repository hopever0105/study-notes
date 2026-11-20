# -*- coding: utf-8 -*-
# 예·아니오 분류 예측하기 (6-2 로지스틱 회귀 — 머신러닝 쪽)
# 1부: 책 원본 따라 치기 / 2부: 금융판 — 다음 달 '중앙값보다 많이 오를까'를 맞히고, 상위 10종목을 고르기
# Spyder: F5 전체 실행 / Ctrl+Enter 현재 셀 실행 / F9 선택 줄 실행
#
# 4-8(통계분석/예·아니오 결과의 원인 보기)과 다른 점
#   4-8: statsmodels logit → 계수·p값·오즈비로 '원인 해석'
#   6-2: sklearn LogisticRegression → 시험 데이터 '예측 성능'(혼동행렬·AUC)과 규제(C)
# 로지스틱 회귀 식: P(1) = 1 / (1 + e^-(b0 + b1x1 + ... ))  → 선형 점수를 0~1 확률로 눌러 줌

# =====================================================================
# 1부. 책 원본
# =====================================================================

# %% 데이터 (책은 GitHub 주소에서 받음 → 같은 파일이 참고코드 data 폴더에 있어서 그걸 씀)
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

BOOK_DATA = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\데이터분석_파이썬\참고코드\개정판_py\data\bodyPerformance.csv'
body = pd.read_csv(BOOK_DATA)
# 책 원래 줄: pd.read_csv("https://raw.githubusercontent.com/ADPclass/ADP_book_ver01/main/data/bodyPerformance.csv")

# %% 글자 → 숫자
body['gender'] = np.where(body['gender'] == 'M', 0, 1)      # 남자=0, 여자=1
body['class_1'] = np.where(body['class'] == 'A', 1, 0)      # A등급=1, 나머지=0 (이진 분류)
print(body.head())

# %% 학습 70% / 시험 30% (stratify=y: 두 쪽의 1 비율을 같게)
from sklearn.model_selection import train_test_split

feature_columns = list(body.columns.difference(['class', 'class_1']))
X = body[feature_columns]
y = body['class_1']
X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, train_size=0.7, random_state=1)
print(X_train.shape, X_test.shape)

# %% 학습
from sklearn.linear_model import LogisticRegression

logR = LogisticRegression(random_state=45)
logR.fit(X_train, y_train)

# %% 평가: 혼동행렬·정확도·정밀도·재현율·F1 (5-3에서 손계산한 것)
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score

pred = logR.predict(X_test)
acc = accuracy_score(y_test, pred)
prc = precision_score(y_test, pred)
rcll = recall_score(y_test, pred)
f1 = f1_score(y_test, pred)

print(confusion_matrix(y_test, pred))
print('정확도\t{}%'.format(round(acc * 100, 2)))
print('정밀도\t{}%'.format(round(prc * 100, 2)))
print('재현율\t{}%'.format(round(rcll * 100, 2)))
print('F1\t{}%'.format(round(f1 * 100, 2)))

# %% ROC 곡선
from sklearn.metrics import RocCurveDisplay
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

RocCurveDisplay.from_estimator(logR, X_test, y_test)
plt.title('ROC Curve')
plt.show()

# %% 다중 분류: A=0, B=1, C=2, D=3
mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
body['class_2'] = body['class'].map(mapping)

feature_columns = list(body.columns.difference(['class', 'class_1', 'class_2']))
X = body[feature_columns]
y = body['class_2']
X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, train_size=0.7, random_state=1)
print(X_train.shape, X_test.shape)

# %% 소프트맥스 회귀
# 책 원래 줄: LogisticRegression(multi_class='multinomial', random_state=45)
# 지금 설치된 scikit-learn(1.9)에서는 multi_class 옵션이 없어짐 → 기본값이 이미 소프트맥스(multinomial)
softm = LogisticRegression(random_state=45)
softm.fit(X_train, y_train)

# %%
pred = softm.predict(X_test)
print(confusion_matrix(y_test, pred))
print('정확도\t{}%'.format(round(accuracy_score(y_test, pred) * 100, 2)))

# %% 마지막 행 하나: 예측 클래스와 클래스별 확률
pred_sample = softm.predict(X_test.iloc[[-1]])
prb_sample = softm.predict_proba(X_test.iloc[[-1]])
print('예측 클래스: ', pred_sample[0])
print('실제 클래스: ', y_test.iloc[-1])
print('각 클래스에 속할 확률', prb_sample[0])   # 네 개 더하면 1

# %% 계수와 오즈비
print(logR.coef_)
print(np.exp(logR.coef_))   # e^계수 = x가 1 늘 때 '1일 오즈'가 몇 배가 되나


# =====================================================================
# 2부. 금융판 — 다음 달 상위 절반에 들까?
# =====================================================================

# %% 월말 패널 만들기 (6-1 Ridge·Lasso 파일과 같은 변수, 가짜 변수는 뺌)
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

# 정답: 그달 50종목 중 다음 달 수익률이 중앙값 이상이면 1 → 매달 1과 0이 반반 (기준선 정확도 50%)
me['y'] = (me['fwd_1m'] >= me.groupby('ym')['fwd_1m'].transform('median')).astype(int)

# 3분류 정답(소프트맥스용): 하위 1/3 = 0, 가운데 = 1, 상위 1/3 = 2 (달마다)
me['y3'] = me.groupby('ym')['fwd_1m'].transform(lambda s: pd.qcut(s.rank(method='first'), 3, labels=False))

# 입력 변수: 달마다 순위를 0~1로 (튀는 값에 강하고 단위 문제 없음)
for c in FEATS:
    me[c] = me.groupby('ym')[c].rank(pct=True)
print(me.shape, me['ym'].min(), '~', me['ym'].max(), '/ 1 비율:', round(me['y'].mean(), 3))

# %% 시간순으로 나누기 (책의 train_test_split 무작위 X)
train = me[me['ym'] <= pd.Period('2024-12', 'M')]
test = me[me['ym'] >= pd.Period('2025-01', 'M')]
Xtr, ytr, Xte, yte = train[FEATS], train['y'], test[FEATS], test['y']

# %% 학습: 스케일링 + 로지스틱을 한 줄로 (파이프라인: 학습 데이터로만 평균·표준편차를 구함)
clf = make_pipeline(StandardScaler(), LogisticRegression(C=1.0))
clf.fit(Xtr, ytr)

pred = clf.predict(Xte)
prob = clf.predict_proba(Xte)[:, 1]
print(confusion_matrix(yte, pred))
print('정확도 ', round(accuracy_score(yte, pred), 4), '(기준선 0.5)')
print('정밀도 ', round(precision_score(yte, pred), 4))
print('재현율 ', round(recall_score(yte, pred), 4))
print('AUC    ', round(roc_auc_score(yte, prob), 4))
print('학습 AUC', round(roc_auc_score(ytr, clf.predict_proba(Xtr)[:, 1]), 4), '← 시험보다 많이 높으면 과적합')

# %% 계수 → 오즈비: 변수가 '1 표준편차' 늘 때 오즈가 몇 배
coef = pd.Series(clf[-1].coef_[0], index=FEATS)
print(pd.DataFrame({'계수': coef, '오즈비': np.exp(coef)}).sort_values('계수').round(3))

# %% 금융에서 진짜 쓰는 방식: 0.5 기준으로 자르지 않고, 확률 순위로 상위 10종목만 산다
t = test.assign(prob=prob)
def top_bottom(d, k=10):
    d = d.sort_values('prob')
    return pd.Series({
        'top_hit': d['y'].tail(k).mean(),                 # 상위 10종목 중 실제로 상위 절반에 든 비율 = 상위 k 정밀도
        'top_ret': d['fwd_1m'].tail(k).mean(),
        'bot_ret': d['fwd_1m'].head(k).mean(),
        'all_ret': d['fwd_1m'].mean(),
    })
monthly = t.groupby('ym').apply(top_bottom, include_groups=False)
monthly['long_short'] = monthly['top_ret'] - monthly['bot_ret']
print(monthly.round(3))
print('평균 - 상위10 적중률:', round(monthly['top_hit'].mean(), 3),
      '/ 상위10-전체:', round((monthly['top_ret'] - monthly['all_ret']).mean(), 4),
      '/ 롱숏:', round(monthly['long_short'].mean(), 4),
      '/ 롱숏 이긴 달:', int((monthly['long_short'] > 0).sum()), '/', len(monthly))

# %% 기준(threshold)을 바꾸면 정밀도·재현율이 서로 맞바뀐다
for th in [0.4, 0.5, 0.55, 0.6]:
    p_ = (prob >= th).astype(int)
    print(f'기준 {th}: 매수 신호 {p_.sum():4d}개, 정밀도 {precision_score(yte, p_, zero_division=0):.3f}, 재현율 {recall_score(yte, p_):.3f}')
# 기준을 높이면 확실한 것만 사서 정밀도↑ 재현율↓ (신호 개수도 줄어듦)

# %% 규제 C: 6-1의 alpha와 반대 (C = 1/alpha → C가 작을수록 규제가 셈)
# 학습 기간 안에서 시간순으로 C 고르기: 2022~2023 학습 → 2024 검증
inner_tr = train[train['ym'] <= pd.Period('2023-12', 'M')]
inner_va = train[train['ym'] >= pd.Period('2024-01', 'M')]
for C in [0.001, 0.01, 0.1, 1, 10]:
    for pen in ['l2', 'l1']:
        m = make_pipeline(StandardScaler(), LogisticRegression(C=C, l1_ratio=1.0 if pen == 'l1' else 0.0, solver='saga', max_iter=5000))
        m.fit(inner_tr[FEATS], inner_tr['y'])
        auc = roc_auc_score(inner_va['y'], m.predict_proba(inner_va[FEATS])[:, 1])
        nz = int((np.abs(m[-1].coef_) > 1e-8).sum())
        print(f'C={C:<6} {pen}: 검증 AUC {auc:.4f}, 0 아닌 계수 {nz}개')
# l1(라쏘식)은 C가 작으면 계수를 0으로 만들어 변수를 고름. l2(릿지식)는 줄이기만 함

# %% 3분류(소프트맥스): 하위·중간·상위 1/3
soft = make_pipeline(StandardScaler(), LogisticRegression())
soft.fit(Xtr, train['y3'])
p3 = soft.predict(Xte)
print(confusion_matrix(test['y3'], p3))
print('3분류 정확도:', round(accuracy_score(test['y3'], p3), 4), '(기준선 0.333)')
print('한 종목의 세 확률:', soft.predict_proba(Xte.iloc[[0]]).round(3)[0])

# %% 정리 — 11/18 실행 결과(F5, 약 10초)
#   2분류: 시험 정확도 0.500, AUC 0.508 (학습 AUC 0.571) → 학습 기간 관계를 외웠을 뿐 시험에선 거의 동전 던지기
#   상위 10종목: 적중률 0.529, 롱숏 월 +0.9%, 이긴 달 9/21 → 평균은 플러스지만 꾸준하지 않음
#   기준 0.6: 정밀도 0.680이지만 신호가 25개뿐 → 표본이 적어 우연일 수 있음 (개수도 같이 봐야 함)
#   C 고르기: l2 C=0.01 검증 AUC 0.529가 가장 높음. l1은 C 0.01 이하에서 계수 전부 0 (AUC 0.5)
#   3분류: 정확도 0.384 (기준선 0.333)
print('''
- 금융판 정답은 '그달 중앙값 이상' → 매달 반반이라 기준선 정확도가 정확히 50%. 시장 전체 등락을 빼고 '종목 고르기'만 평가.
- 0.5로 잘라 맞혔냐보다, 확률 순위로 상위 10종목을 샀을 때 수익(상위10 - 하위10)이 실제 쓰임새.
- 학습 AUC와 시험 AUC 차이 = 과적합 정도. 규제 C는 시간순 검증으로 고른다.
- 스케일러는 파이프라인 안에 넣어 학습 구간 값으로만 맞춘다(시험 구간 평균이 새지 않게).
''')
