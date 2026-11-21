
#%% 로지스틱 회귀분석 
import pandas as pd
import numpy as np
import warnings
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import RocCurveDisplay
import matplotlib.pyplot as plt

# 금융  — 다음 달 상위 절반에 들까?


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



#%% 
""" 
로지스틱 회귀
1. 개념
종속변수가 범주형인 경우에 사용하는 분류 알고리즘
선형회귀는 연속적인 값을 예측하나, 로지스틱은  
입력특성 (X)가 주어질 대 특정 결과 클래스에 속할 확률을 추정하는 것. 
일반적으로 로지스틱 회귀는 S자곡선을 띈다. 

선형회귀를 분류문제에 적용하면 예측값이 0보다 작거나 1보다 크게 나타날 수 있어 확률로 해석하기 어려움
-> 로지스틱 회귀는 시그모이드 함수를 사용한다. 


2. 시그모이드 함수
- 입력값의 범위와 관계없이 항상 0과 1사의 값을 출력하는 S자 형태 함수
- 출력값은 확률로 해석 가능 
- 예측 확률이 0.5이상이면 레이블을 1(양성), 0.5미만이면 0(음성)으로 분류
- 기준값을 결정경계 Decision Boundary 라고 한다. 
- 0.3 등으로 민감하게 결정경계를 만들수도 잇따. 


3. 승산비(Odds)dhk fhwlt qusghk
(1) odds
- 실패 대비 성공할 가능성의 비율을 의미 
- 성공 확률이 p일 때 승산비는 성공확률 p를 실패확률 1-p로 나눈것으로 정의된다. 
- 확률이 1에 가까워질수록 odds 무한대로 증가하는 경향이 있는 바, 이를 해결하기 위해 log를 취하며 이를 logit이라고 부른다.
- 로짓 변화시 값의 범위가 음의 무한대에서 양의 무한대까지 확장되며 확률 0.5는 0에eodmdgksek. 

(2) rhkwjd
1) 확률 : 어떤 범주형 자료에 대한 p 값을 0~1사이로 표현
2) odds: 성공과 실패의 비율 범위 0부터 양의 무한대까지 가능 
3) 로짓 : oods에 로그 적용범위로 음의 무한대부터 양의 무한대까지 가능
4) 선형 예측값: 입력 특성의 가중치 합으로 로짓을 예측 (회귀식과 유사)
5) 최종 확률: 시그모이드 함수로 다시 0~1 변환 

    
4. 훈련 및 비용 함수
- 학습목적은 모델의 파라미터를 최적화하는 것 즉 레이블에 부합하는 확률을 예측하는 파라미터 최적화 
- 이 학습을 위해 MLE(최대 우조 추정법 Maximum Likelihood Estimation) 사용
- 최대우도 추정은 주어진 데이터가 모델에 의해 생성되었을 가능성을 최대화하는 파라미터를 찾는다. 
- 해를 갖지 않는 바, 경사하강법(Gradient Descent)과 같은 반복 최적화 기법 사용하여 파라미터 추정
- 여기서 Log-Loss ,  Binary Cross-Entropy 함수 등을 비용함수로 사용
- 실제 레이블과 차이가 크게 날수록 비용함수는 급격히 증가함 -> 즉 큰 패널티 부여 
- 확신의 정도 예측 정확도 등을 모두 고려함 


5. 주요 파라미터 
-scikil-learn의 LogisticRegression 클래스를 활용한다. 

파라미터 
(1) penalty 
-> 규제유형을 설정
-> 11, 12, elasticnet, none 중 선택하며 기본적으로 12로 규제 

(2) C 
-> 정규화 강도의 역수
-> 값이 작을수록 규제가 강해짐
-> 릿지의 Alpha와 반대 방향으로 작용 
-> 기본값은 1.0임

(3) multi_class
-> 클래스 타입 설정
-> 기본값은 'auto'로 자동설정 
-> 'ovr' : 이중 클래스 
-> 'multinomial' : 다중 클래스 
"""


# %% 데이터
warnings.filterwarnings('ignore')

BOOK_DATA = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\데이터분석_파이썬\참고코드\개정판_py\data\bodyPerformance.csv'
body = pd.read_csv(BOOK_DATA)
# 책 원래 줄: pd.read_csv("https://raw.githubusercontent.com/ADPclass/ADP_book_ver01/main/data/bodyPerformance.csv")

# %% 글자 → 숫자
body['gender'] = np.where(body['gender'] == 'M', 0, 1)      # 남자=0, 여자=1
body['class_1'] = np.where(body['class'] == 'A', 1, 0)      # A등급=1, 나머지=0 (이진 분류)
print(body.head())

# %% 학습 70% / 시험 30% (stratify=y: 두 쪽의 1 비율을 같게)
feature_columns = list(body.columns.difference(['class', 'class_1']))
X = body[feature_columns]
y = body['class_1']
X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, train_size=0.7, random_state=1)
print(X_train.shape, X_test.shape)

# %% 학습
logR = LogisticRegression(random_state=45)
logR.fit(X_train, y_train)

# %% 평가: 혼동행렬·정확도·정밀도·재현율·F1 (5-3에서 손계산한 것)

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
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

RocCurveDisplay.from_estimator(logR, X_test, y_test)
plt.title('ROC Curve')
plt.show()


#%% 
""" 
다중 클래스 분류 - 소프트맥스 회귀
(1) 개념
- 3개 이상의 클래스 동시 예측하기 위함
- 소프트맥스 회귀 (Softmax Regression, 다항 로지스틱 회귀) tkdyd
- scikit - learn에서는 LogisticRegression모델에서 multi_class = 'multinomial' 파라미터 설정하면 바로 소프트맥스 회귀 적용 가능
- 다만 현재 sscikit-learn(1.9)에서는 multi_class 옵션이 없어짐 → 기본값이 이미 소프트맥스(multinomial) 임으로 버전따라 굳이 언급하지 않아도됨. 
(2) 소프트맥스 함수
- 각 클래스에 대한 점수를 계산한 후 확률로 변환
- 모든 클래스 예측 확률 합이 정확히 1이 되는 것이 가장 중요함
- 예측확률이 가장 높은 클래스가 최종 예측 레이블로 선택된다. 

"""
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




