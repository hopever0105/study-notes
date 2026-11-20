# -*- coding: utf-8 -*-
# 단위 맞추기·학습용 시험용 나누기 (3-3 데이터 분할 및 스케일링)
# 1부: 책 원본 따라 치기 / 2부: 금융 데이터(prices.csv)로 같은 작업을 시간순으로
# Spyder: F5 전체 실행 / Ctrl+Enter 현재 셀 실행 / F9 선택 줄 실행
#
# 언제 쓰나: 모델에 넣기 전에 (1) 학습용·검증용·시험용으로 나누고 (2) 변수 단위를 맞출 때.
#   - train_test_split(stratify=y) : 무작위로 나누되 정답 비율을 똑같이 (책 방식, 주가엔 그대로 쓰면 안 됨)
#   - MinMaxScaler                 : (x - 최솟값) / (최댓값 - 최솟값) → 0~1
#   - StandardScaler               : (x - 평균) / 표준편차 → 평균 0, 표준편차 1
#   - RobustScaler                 : (x - 중앙값) / (3사분위 - 1사분위) → 튀는 값에 덜 흔들림
#   - 규칙: 스케일러는 '학습용'에만 fit, 검증·시험에는 transform만

# =====================================================================
# 1부. 책 원본
# =====================================================================

# %%
import pandas as pd
from sklearn.datasets import load_iris

# 데이터 가져오기
iris = load_iris()
iris = pd.DataFrame(iris.data, columns=iris.feature_names)
iris['class'] = load_iris().target
iris['class'] = iris['class'].map({0: 'Setosa', 1: 'Versicolour', 2: 'Virginica'})

# 층화임의추출
from sklearn.model_selection import train_test_split

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

# %%
print(iris.describe().loc[['min', 'max']])

# %%
from sklearn.preprocessing import MinMaxScaler

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


# =====================================================================
# 2부. 금융판 — 시간순으로 나누고, 학습 기간 숫자로만 단위 맞추기
# =====================================================================

# %% 데이터 + 변수 (일별)
import numpy as np
from sklearn.preprocessing import StandardScaler, RobustScaler

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
# - 책: train_test_split(stratify) 무작위 → 주가에선 이웃한 날 정답이 겹쳐 시험 성적이 부풀려짐
# - 금융: 날짜 경계로 학습 / 검증 / 시험, 경계에서 정답 기간(5일)만큼 버림
# - 스케일러는 학습 기간에만 fit. 또는 날짜마다 종목끼리 순위·z점수로 바꾸면 fit 자체가 필요 없음
# - 꼬리가 두꺼운 수익률은 MinMax보다 Standard·Robust·순위
