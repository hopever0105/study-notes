# 언제 쓰나: 모델에 넣기 전에 (1) 학습용·검증용·시험용으로 나누고 (2) 변수 단위를 맞출 때.
#   - train_test_split(stratify=y) : 무작위로 나누되 정답 비율을 똑같이 (책 방식, 주가엔 그대로 쓰면 안 됨)
#   - MinMaxScaler                 : (x - 최솟값) / (최댓값 - 최솟값) → 0~1
#   - StandardScaler               : (x - 평균) / 표준편차 → 평균 0, 표준편차 1
#   - RobustScaler                 : (x - 중앙값) / (3사분위 - 1사분위) → 튀는 값에 덜 흔들림
#   - 규칙: 스케일러는 '학습용'에만 fit, 검증·시험에는 transform만

#%%
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

PATH = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터\prices.csv'
px = pd.read_csv(PATH, dtype={'code': str}, parse_dates=['date'], encoding='utf-8-sig')
px = px.sort_values(['code', 'date']).reset_index(drop=True)
g = px.groupby('code')['close']
px['ret'] = g.pct_change()
px['mom_20'] = g.pct_change(20)                                   # 20일 수익률
px['vol_20'] = px.groupby('code')['ret'].transform(lambda s: s.rolling(20).std())
px['amt_log'] = np.log(px['amount'].where(px['amount'] > 0))      # 거래대금(원) → 로그
px['fwd_5'] = g.shift(-5) / px['close'] - 1                       # 정답: 앞으로 5일 수익률
FEATS = ['close', 'mom_20', 'vol_20', 'amt_log']
d = px.dropna(subset=FEATS + ['fwd_5']).reset_index(drop=True)
print(d['date'].min().date(), '~', d['date'].max().date(), '/', len(d), '행 /', d['code'].nunique(), '종목')

# %% 1) 책 방식(무작위)으로 나누면 생기는 일
#   같은 날 같은 종목들이 학습·시험에 섞이고, 내일 행이 학습에, 오늘 행이 시험에 들어간다.
#   fwd_5(앞으로 5일)는 이웃한 날끼리 4일이 겹치므로 → 시험 정답을 학습에서 거의 본 셈.
tr_r, te_r = train_test_split(d, test_size=0.2, random_state=42)
print('무작위 시험 기간:', te_r['date'].min().date(), '~', te_r['date'].max().date(), '(학습 기간과 똑같이 전부)')

# 시험 행 하나를 골라, 같은 종목의 '바로 다음 날' 행이 학습에 있는지 세기
key_tr = set(zip(tr_r['code'], tr_r['date']))
nxt = d.groupby('code')['date'].shift(-1)
te_next = nxt.loc[te_r.index]
share = np.mean([(c, t) in key_tr for c, t in zip(te_r['code'], te_next)])
print('시험 행 중 "같은 종목 다음 날"이 학습에 들어간 비율:', round(share, 3))

# %% 2) 시간순으로 나누기: 학습 ~2023 / 검증 2024 / 시험 2025~
#   검증 = 설정값 고르는 곳, 시험 = 마지막에 딱 한 번 보는 곳
#   경계에서 5일이 겹치므로 학습 마지막 5거래일은 버림(정답이 검증 기간 가격으로 계산되기 때문)
dates = np.sort(d['date'].unique())
tr_end = pd.Timestamp('2023-12-31')
va_end = pd.Timestamp('2024-12-31')
gap = 5
tr_last = dates[dates <= tr_end][-gap - 1]        # 경계 앞 5일 버린 학습 마지막 날
va_last = dates[dates <= va_end][-gap - 1]

train = d[d['date'] <= tr_last]
valid = d[(d['date'] > tr_end) & (d['date'] <= va_last)]
test = d[d['date'] > va_end]
for name, part in [('학습', train), ('검증', valid), ('시험', test)]:
    print(f'{name}: {part["date"].min().date()} ~ {part["date"].max().date()}  {len(part):>6}행  비율 {len(part) / len(d):.2f}')

# %% 3) 스케일러를 '전체'에 fit하면 안 되는 이유 (미래 정보 누수)
#   종가(close)는 시간이 갈수록 수준이 바뀐다. 전체 최댓값에는 2025년 가격이 들어 있음.
mm_all = MinMaxScaler().fit(d[['close']])          # 잘못: 시험 기간 값까지 보고 최소·최대를 정함
mm_tr = MinMaxScaler().fit(train[['close']])        # 맞음: 학습 기간 값으로만
print('전체 fit  → 시험 close 범위:', mm_all.transform(test[['close']]).min().round(3), '~', mm_all.transform(test[['close']]).max().round(3))
print('학습 fit  → 시험 close 범위:', mm_tr.transform(test[['close']]).min().round(3), '~', mm_tr.transform(test[['close']]).max().round(3))
print('→ 학습만으로 fit하면 1을 넘는 값이 나온다. 그게 "처음 보는 가격대"라는 정직한 신호.')

# %% 4) 세 스케일러 비교: 튀는 값(급등락일)이 있는 20일 수익률
#   숫자 예시: 값이 [-0.02, 0.00, 0.01, 0.03, 0.60] 이면
#     MinMax   : 최소 -0.02, 최대 0.60 → 0.01은 (0.01+0.02)/0.62 = 0.048 (대부분이 0 근처로 눌림)
#     Standard : 평균 0.124, 표준편차 0.237 → 0.01은 (0.01-0.124)/0.237 = -0.48
#     Robust   : 중앙값 0.01, 사분위범위 0.03-0.00 = 0.03 → 0.01은 0, 0.03은 0.67, 0.60은 19.7 (보통 값은 넓게 펴짐)
toy = np.array([[-0.02], [0.00], [0.01], [0.03], [0.60]])
print(pd.DataFrame({
    '원래값': toy.ravel(),
    'MinMax': MinMaxScaler().fit_transform(toy).ravel(),
    'Standard': StandardScaler().fit_transform(toy).ravel(),
    'Robust': RobustScaler().fit_transform(toy).ravel(),
}).round(3))

# %% 같은 걸 실제 mom_20으로: 학습 fit → 시험 transform, 가운데 50% 폭 비교
cols = ['mom_20']
out = {}
for nm, sc in [('MinMax', MinMaxScaler()), ('Standard', StandardScaler()), ('Robust', RobustScaler())]:
    sc.fit(train[cols])
    z = sc.transform(test[cols]).ravel()
    q1, q3 = np.percentile(z, [25, 75])
    out[nm] = {'최소': z.min(), '1사분위': q1, '3사분위': q3, '최대': z.max(), '가운데 50% 폭': q3 - q1}
print(pd.DataFrame(out).T.round(3))
print('→ MinMax는 가운데 50%가 아주 좁은 폭에 몰림. 수익률처럼 꼬리가 두꺼운 값은 Standard·Robust가 낫다.')

# %% 5) 금융에서 자주 쓰는 방법: 날짜마다 종목끼리 순위(0~1) 또는 z점수
#   그날 50종목 안에서만 계산 → 미래 정보가 들어갈 틈이 없고, 시장 전체가 오르내린 효과도 빠진다.
d['mom_20_rank'] = d.groupby('date')['mom_20'].rank(pct=True)
d['mom_20_z'] = d.groupby('date')['mom_20'].transform(lambda s: (s - s.mean()) / s.std())
print(d[['date', 'code', 'mom_20', 'mom_20_rank', 'mom_20_z']].tail(5).round(3))
print('날짜별 z점수 평균(0이어야 함):', round(d.groupby('date')['mom_20_z'].mean().abs().max(), 6))

# %% 6) 정답 비율 맞추기(stratify)의 금융판: 정답을 '그날 중앙값 이상이면 1'로 만들면
#   매일 1과 0이 반반 → 시간순으로 나눠도 학습·검증·시험 1 비율이 저절로 0.5 근처
d['y'] = (d['fwd_5'] >= d.groupby('date')['fwd_5'].transform('median')).astype(int)
for name, idx in [('학습', train.index), ('검증', valid.index), ('시험', test.index)]:
    print(name, '1 비율:', round(d.loc[idx, 'y'].mean(), 3))

# %% 정리
#   train_test_split(stratify) 무작위 → 주가에선 이웃한 날 정답이 겹쳐 시험 성적이 부풀려짐
# - 금융: 날짜 경계로 학습 / 검증 / 시험, 경계에서 정답 기간(5일)만큼 버림
# - 스케일러는 학습 기간에만 fit. 또는 날짜마다 종목끼리 순위·z점수로 바꾸면 fit 자체가 필요 없음
# - 꼬리가 두꺼운 수익률은 MinMax보다 Standard·Robust·순위
#%%
"""
데이터 분할과 스케일링
- 머신러닝 모델 학습하고 성능 평가 위해 필요 
- 검증 등에해 데이터 분할 필요하고 스케일링도 필요함

(1) 데이터 분할
- 모델 성과 평가위해 학습과 평가 사용 데이터 분리 필요
- 모든 데이터 학습 사용시 과적합이 발생할 수 있고, 새 데이터 예측 성능 객관적이지 못함

train: 모델 학습 사용
test : 최종 성능 평가 사용
Validation : 하이퍼파라미터 튜닝 및 모델 선택 사용(분석목적따라 생략하기도 함)

통상적인 분할 비율
Train: test -> 7:3, 8:2 
Train: Validation : Test -> 6:2:2, 8:1:1
데이터 압도적으로 많을 때 -> train의 비율을 늘릴수있음. 그럼에도 과적합 항상 주의

코드
x_train, x_test, y_train, y_test = train_test_split(x,y,test_size=None, random_state = None, shuffle = True, stratify = None)

x: 독립변수 테이블
y: 종속변수 테이블
test_size: 테스트 사이즈 비율
random_state: 임의의 번호 지정, 같은 숫자 사용시 같은 출력 나옴.
shuffle: True이면 추출 전에 데이터 섞음, False이면 섞지 않음
stratify: None이 아닌 경우 지정 변수 기준으로 층화임의추출 실행 ( 분류의 경우 = y를 붙임)

- scikit - learn의 train_test_split()함수는 기본적으로 무작위 추출(Random Samling)을 통해 데이터 분할
- 종속변수 범주형인 경우, 무작위 분할로 인해 각 범주의 비율이 원본 데이터와 다르게 분포될 수 잇음. 
- 층화임의추출은 모집단을 특정기준으로 나누고 각 꼐층 비율 유지하며 데이터 무작위 추출 
- 클래스 불균형, 범주형, 데이터 대표성 유지시에 층화임의추출은 큰 힘을 발휘한다. 

"""
# %%
from sklearn.datasets import load_iris

# 데이터 가져오기
iris = load_iris()
iris = pd.DataFrame(iris.data, columns=iris.feature_names)
iris['class'] = load_iris().target
iris['class'] = iris['class'].map({0: 'Setosa', 1: 'Versicolour', 2: 'Virginica'})

# 층화임의추출

X = iris.drop(columns='class')
y = iris['class']

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("원본 분포: ", y.value_counts().to_dict())
print("Train 분포:", y_train.value_counts().to_dict())
print("Test 분포:", y_test.value_counts().to_dict())

# %% 시험용 20%를 다시 반으로 → 검증 10% + 시험 10%
X_val, X_test, y_val, y_test = train_test_split(
    X_test, y_test,
    test_size=0.5,   # 0.2의 절반 → 0.1
    random_state=42,
    stratify=y_test
)

print("Train 분포:", y_train.value_counts().to_dict())
print("Validation 분포:", y_val.value_counts().to_dict())
print("Test 분포:", y_test.value_counts().to_dict())


#%% 
""" 
데이터 스케일링

데이터세트의 각 변수는 서로 다른 범위를 가진다. 
이것이 해석을 폄하할 수 있는 바 비율을 맞춰준다 
특히 선형회귀, 로지스틱회귀, SVM, KNN, 신경망 ,PCA에서 스케일링은 중요하다. 


(1) 절차
스케일러 선택 및 객체 생성 -> Train 데이터로 fit() 수행 -> Train 데이터 transform() -> Test 데이터 transfor()

(2) scaler 종류  
1) StandardScaler
- 평균 0 , 분산 1 
- 가장 자주 사용
- 이상치 영향 큼
- 선형모델, SVM, PCA 등에서 주료 사용

2) MinMaxScaler
- 0~1범위
- 값 범위 제한
- 이상치 영향 큼
- 신경망, 거리기반 모델 주로 사용

3) MaxAbsScaler
- -1~1범위
- 최소행렬에ㅓㅅ 사용
- 이상치  영향 큼
- 텍스트 데이터에서 주로 사용


4) RobustScaler
- 중앙값 기준
- 이상치에 강함
- 이상치 영향 작음
- 이상치 많은 데이터에서 주로 사용

- > 변수간 영향력 균형 유지, 모델 학습속도 향상, 거리기반 알고리즘의 성능 개선, 최적화 가정의아정성 향상등의 효과를 기대

"""
# %%
print(iris.describe().loc[['min', 'max']])

# %%
scaler = MinMaxScaler()

# Train 데이터로 학습
scaler.fit(X_train)

# Train 데이터로 설정한 스케일러를 각 데이터셋에 적용
X_train_scaled = scaler.transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# %% 스케일링 결과 확인 (검증·시험은 0~1을 살짝 벗어날 수 있음 → 정상)
X_train_sc = pd.DataFrame(X_train_scaled, columns=X_train.columns)
X_val_sc = pd.DataFrame(X_val_scaled, columns=X_val.columns)
X_test_sc = pd.DataFrame(X_test_scaled, columns=X_test.columns)

print("X_train_scaled:\n", X_train_sc.describe().loc[['min', 'max']])
print("\nX_val_scaled:\n", X_val_sc.describe().loc[['min', 'max']])
print("\nX_test_scaled:\n", X_test_sc.describe().loc[['min', 'max']])





