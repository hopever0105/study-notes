#%% DB 연결 및 테이블/컬럼 구조 확인
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, inspect

QUANT_DIR = Path(r'C:\Users\arlo0\OneDrive\바탕 화면\취업\quant')
env = {}
for line in (QUANT_DIR / '.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

db_url = (
    f"mysql+pymysql://{env['DB_USER']}:{env['DB_PASSWORD']}"
    f"@{env['DB_HOST']}:{env.get('DB_PORT', 3306)}/{env['DB_NAME']}?charset=utf8mb4"
)
engine = create_engine(db_url)
inspector = inspect(engine)

for table in inspector.get_table_names():
    df_sample = pd.read_sql(f"SELECT * FROM `{table}` LIMIT 2", engine)
    cnt = pd.read_sql(f"SELECT COUNT(*) AS cnt FROM `{table}`", engine)['cnt'].iloc[0]
    cols = [f"{col}({dtype})" for col, dtype in df_sample.dtypes.items()]
    print(f"[{table}] 행 수: {cnt:,} | 컬럼: {', '.join(cols)}")
    
    
"""
================================================================================
[파일 03] 트리 앙상블(RandomForest · XGBoost · LightGBM) 기반 시장 트렌드 예측 전략
--------------------------------------------------------------------------------
1. 배깅(Random Forest) vs 부스팅(XGBoost · LightGBM) 원리 및 하이퍼파라미터 가이드
2. XGBoost 단일 모델의 과적합 진단 실험 (훈련 정확도 vs 테스트 정확도 괴리 확인)
3. TimeSeriesSplit + GridSearchCV 기반 랜덤 포레스트 하이퍼파라미터 튜닝
4. 타겟 임계값 재정의(>0.05%) 재학습 & 국내 ETF+거시지표 실전 확장 백테스트
================================================================================
"""

#%% [1. 공통 환경 설정 및 SQL DB 연결 헤더]
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    confusion_matrix, accuracy_score, precision_score,
    recall_score, f1_score, roc_auc_score
)

warnings.filterwarnings('ignore')

SEED = 42
np.random.seed(SEED)

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.figsize'] = (12, 5)

QUANT_DIR = Path(r'C:\Users\arlo0\OneDrive\바탕 화면\취업\quant')
env = {}
for line in (QUANT_DIR / '.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

db_url = (
    f"mysql+pymysql://{env['DB_USER']}:{env['DB_PASSWORD']}"
    f"@{env['DB_HOST']}:{env.get('DB_PORT', 3306)}/{env['DB_NAME']}?charset=utf8mb4"
)
engine = create_engine(db_url)

def load_sql(query: str) -> pd.DataFrame:
    return pd.read_sql(query, engine)

print("[03] 환경 설정 및 stock_db 연결 완료!")
#%%
"""
[의사결정나무(Decision Tree)와 앙상블 학습 (배깅 vs 부스팅)]
1. 단일 의사결정나무의 한계:
   - 데이터를 특정 기준(불순도: 지니 계수 또는 엔트로피 감소)으로 반복 분할하여 직관적(화이트박스)이고
     피처 스케일링이 필요 없다는 장점이 있음
   - 그러나 트리가 깊어질수록 훈련 데이터의 노이즈까지 완벽히 분기하여 과적합(높은 분산)이 극심하며,
     데이터가 조금만 바뀌어도 트리 구조 전체가 뒤바뀌는 불안정성이 큼 → 금융에서는 단일 트리를 거의 쓰지 않고 앙상블 사용

2. 배깅 (Bagging: Bootstrap Aggregating) - 대표 모델: 랜덤 포레스트(Random Forest):
   - 원리: 원본 데이터에서 중복을 허용해 무작위 샘플링(부트스트랩)하고, 각 노드 분할 시 전체 피처 중 일부만 무작위로
     선택해 수백 개의 독립적인 트리를 병렬 학습한 뒤 다수결(Voting)로 최종 예측
   - 효과: 개별 트리의 과적합(분산, Variance)을 대폭 낮춰 금융 시계열에서 안정적인 성능을 보임
    - 로페즈 교수는 PCA 사용해 차원 축소 후 랜덤 포레스트에 적합하는 방법을 권장한다. 
    (Advances in financiaㅣ machine learning)
3. 부스팅 (Boosting) - 대표 모델: AdaBoost, GBM, XGBoost, LightGBM, CatBoost:
   - 원리: 여러 개의 약한 학습기(얕은 트리)를 순차적으로 학습시키되, 앞선 트리가 틀린 샘플(오차/잔차)에
     가중치를 부여해 다음 트리가 집중적으로 보완하는 방식
   - 효과: 모델의 편향(Bias)을 줄여 높은 예측력을 달성하지만, 학습률과 트리 깊이를 강하게 규제하지 않으면
     금융 데이터의 노이즈까지 집요하게 학습해 과적합될 위험이 배깅보다 큼
   - XGBoost vs LightGBM 구조 차이:
     * XGBoost: 균형 트리 분할(Level-wise) 방식으로 트리의 균형을 유지하며 과적합에 비교적 강함
     * LightGBM: 리프 중심 트리 분할(Leaf-wise) 방식으로 손실 감소가 큰 리프만 계속 깊게 파고들어 속도가 빠르고
       정확도가 높지만, 데이터가 적은 금융 시계열에서는 과적합 위험이 커서 max_depth와 num_leaves 제한이 필수
     * GBDT : 그래디언트 부스팅: 경사하강법을 사용 -> XGBoost, LightGBM 모두 포함됨. 
     다만, 훈련시간이 길고 파라미터설정이 중요함. 
"""
#%%
"""
[의사결정나무(Decision Tree)와 앙상블 학습: 배깅 vs 부스팅 & 3대 부스팅 모델 비교]
1. 단일 의사결정나무의 한계:
   - 데이터를 특정 기준(불순도: 지니 계수 또는 엔트로피 감소)으로 반복 분할하여 직관적(화이트박스)이고
     피처 스케일링이 필요 없다는 장점이 있음
   - 그러나 트리가 깊어질수록 훈련 데이터의 노이즈까지 완벽히 분기하여 과적합(높은 분산)이 극심하며,
     데이터가 조금만 바뀌어도 트리 구조 전체가 뒤바뀌는 불안정성이 큼 → 금융에서는 단일 트리를 거의 쓰지 않고 앙상블 사용

2. 배깅 (Bagging: Bootstrap Aggregating) - 대표 모델: 랜덤 포레스트(Random Forest):
   - 원리: 원본 데이터에서 중복을 허용해 무작위 샘플링(부트스트랩)하고, 각 노드 분할 시 전체 피처 중 일부만 무작위로
     선택해 수백 개의 독립적인 트리를 병렬 학습한 뒤 다수결(Voting)로 최종 예측
   - 효과: 개별 트리의 과적합(분산, Variance)을 대폭 낮춰 금융 시계열에서 안정적인 성능을 보임

3. 부스팅 (Boosting) 원리:
   - 여러 개의 약한 학습기(얕은 트리)를 순차적으로 학습시키되, 앞선 트리가 틀린 샘플(오차/잔차)에
     가중치를 부여해 다음 트리가 집중적으로 보완하는 방식
   - 모델의 편향(Bias)을 줄여 높은 예측력을 달성하지만, 규제를 걸지 않으면 금융 데이터의 노이즈까지 학습해 과적합 위험이 큼

4. 3대 그래디언트 부스팅 알고리즘 상세 비교 (XGBoost vs LightGBM vs CatBoost):
   (1) XGBoost (eXtreme Gradient Boosting):
       - 개발 배경: 기존 GBM(Gradient Boosting Machine)의 느린 학습 속도와 과적합 규제 부재 한계를 극복하기 위해 개발
       - 트리 분할 방식: 균형 트리 분할(Level-wise / Depth-wise) 방식을 사용하여 트리의 깊이를 최소화하고 좌우 균형을 유지함
       - 핵심 장점:
         * 병렬 처리(Parallel Processing) 지원으로 기존 GBM 대비 학습 속도가 빠름
         * L1(Lasso), L2(Ridge) 과적합 규제(Regularization) 기능이 자체 내장되어 일반화 성능이 우수함
         * 자체 가지치기(Tree Pruning): max_depth까지 분할한 뒤 역방향으로 손실 감소가 기준(gamma)에 못 미치는 가지를 제거
         * 결측치(Missing Value) 자체 처리 기능 및 교차 검증 기능 내장
       - 단점: 균형 트리 분할을 유지하기 위해 연산량이 많아 대용량 데이터에서 LightGBM보다 학습 시간이 오래 걸림

   (2) LightGBM (Light Gradient Boosting Machine):
       - 개발 배경: 마이크로소프트에서 개발했으며, XGBoost의 긴 학습 시간과 높은 메모리 사용량을 획기적으로 개선함
       - 트리 분할 방식: 리프 중심 트리 분할(Leaf-wise) 방식을 사용하여 트리의 균형을 맞추지 않고,
         최대 손실 값(Max Delta Loss)을 가지는 리프 노드만을 지속적으로 비대칭 분할함
       - 핵심 장점:
         * 예측 오류 손실을 최소화할 수 있으며, XGBoost 대비 학습 속도가 매우 빠르고 메모리 사용량이 적음
         * 히스토그램 기반(Histogram-based) 분할, GOSS(기울기 기반 단측 샘플링), EFB(배타적 피처 번들링)로 대용량 데이터에 최적화
       - 단점 및 금융 적용 주의점:
         * 데이터 개수가 적은 경우(보통 10,000건 이하의 일봉 금융 시계열 등) 리프 노드가 한쪽으로 계속 깊어지면서
           심각한 과적합(Overfitting)이 발생하기 쉬움 → max_depth, num_leaves, min_child_samples 규제가 필수적임

   (3) CatBoost (Categorical Boosting):
       - 개발 배경: 얀덱스(Yandex)에서 개발했으며, 범주형 변수(Categorical Feature) 처리와 과적합 방지에 특화됨
       - 트리 분할 방식: 대칭 트리(Oblivious Trees / Symmetric Trees) 구조를 사용하여 같은 깊이의 모든 노드가
         동일한 분할 기준(피처 및 임계값)을 공유함 → 모델 복잡도를 억제하고 추론 속도가 매우 빠름
       - 핵심 장점:
         * 범주형 변수 자동 처리: 별도의 원-핫 인코딩(One-Hot Encoding) 없이도 섹터·요일·국가 같은 범주형 변수를
           Ordered Target Statistics 방식으로 자동 수치화하여 정보 손실과 차원 폭발을 방지함
         * 순서형 부스팅(Ordered Boosting): 기존 부스팅이 전체 훈련 데이터로 잔차를 계산하면서 발생하는
           타겟 누설(Target Leakage)과 예측 편향(Prediction Shift)을 막기 위해, 데이터 순서를 무작위로 섞어
           현재 샘플보다 앞선 데이터만으로 잔차를 계산함 → 하이퍼파라미터 기본값(Default)만으로도 과적합에 매우 강함
       - 단점: 학습 속도가 LightGBM에 비해 느리고, 결측치가 많거나 희소 행렬(Sparse Matrix) 형태의 데이터에는 약점이 있음
"""
#%%
"""
[트리 계열 하이퍼파라미터 완벽 가이드 및 전략 확장 5대 방향]
※ 핵심 전제 — "Garbage In, Garbage Out (쓰레기가 들어가면 쓰레기가 나온다)":
   - 하이퍼파라미터 튜닝만으로 부족한 피처의 한계를 뒤집기는 어려움.
   - 흩어진 데이터 수집 → 기술·거시 지표 생성 → 노이즈 제거 → 모델링 → 결과 피드백 후 전처리 재수정의 순환 과정이 핵심임.
   - 부스팅 계열 튜닝의 기본 정석: 학습률(learning_rate)을 작게 설정하면서 트리 수(n_estimators)를 늘리는 것이나,
     금융 시계열은 과적합 위험이 일반 데이터보다 훨씬 크므로 극단적으로 작은 학습률이나 너무 많은 트리 수는 지양해야 함.

1. 트리 계열 (LightGBM · XGBoost · Random Forest) 9대 핵심 하이퍼파라미터 상세 정리:
   (1) 학습률 — learning_rate (LightGBM) / eta (XGBoost):
       - 0~1 사이 값으로, 부스팅 스텝을 반복할 때 이전 트리의 오차를 얼마나 강하게 보정(업데이트)할지 제어 (보통 0.01 ~ 0.2 사용).
   (2) 트리 수 — num_iterations (파이썬 래퍼 LightGBM) / n_estimators (XGBoost, Random Forest):
       - 반복 생성할 트리의 총 개수. 많이 만들수록 훈련 성능은 올라가지만 과적합 위험도 함께 커짐.
       - 기본값 참고: LightGBM 디폴트는 100(보통 더 큰 값으로 재설정), Random Forest 초기 디폴트는 10(현재 사이킷런 100).
   (3) 트리 깊이 — max_depth (LightGBM, XGBoost, Random Forest):
       - 개별 트리의 최대 깊이 제한. 디폴트는 XGBoost 6, LightGBM -1(깊이 제한 없음 → 반드시 제한 필요!).
       - 얕은 트리: 분산(과적합)은 작지만 편향(과소적합)이 큼 / 깊은 트리: 편향은 작지만 분산(과적합)이 매우 큼.
       - 금융 시계열에서는 보통 3 ~ 10 사이의 값을 사용하며, 피처 수가 많을 경우 조금 더 높게 설정함.
   (4) 조기 종료 — early_stopping_rounds (파이썬 래퍼 LightGBM: early_stopping_round):
       - 검증셋 정확도(Validation Score)가 더 이상 개선되지 않을 때 지정한 학습 횟수 이전이라도 학습을 조기 종료시켜 과적합 방지 (검증셋 필수).
   (5) 서브 샘플링 — bagging_fraction (LightGBM) / subsample (XGBoost):
       - 각 트리를 만들 때 전체 데이터 행(Row) 중 일부만 무작위 추출해 사용하는 비율(0.5 ~ 1.0).
       - 예: 0.5로 지정하면 매 트리마다 절반의 샘플만 사용해 트리를 생성하므로 과적합이 억제됨.
   (6) 변수 샘플링 — feature_fraction (LightGBM) / colsample_bytree (XGBoost):
       - 트리 생성/분할 시 전체 컬럼(Feature) 중 일부만 무작위로 선택하는 비율 (디폴트 1.0은 전체 사용, 보통 0.7 ~ 0.9 사용).
   (7) 리프 최소 가중치 — min_sum_hessian_in_leaf (LightGBM) / min_child_weight (XGBoost):
       - 리프 노드가 되기 위해 필요한 최소 헤시안(가중치) 합계.
       - 값이 클수록 특정 소수 샘플에 의존하는 분기를 막아 모델이 보수적이 됨(과적합 방지). 너무 크면 과소적합되므로 교차 검증으로 탐색.
   (8) 최대 리프 수 — num_leaves (LightGBM 전용):
       - Leaf-wise 분할을 쓰는 LightGBM에서 개별 트리가 가질 수 있는 최대 리프 노드 개수로, 모델 복잡도를 직접 제어하는 핵심 변수.
   (9) 감마 — gamma (XGBoost 전용):
       - 트리 노드를 추가 분할하기 위해 필요한 최소 손실 감소량(Min Split Loss). 값이 클수록 가지치기가 강해져 과적합 감소 효과가 큼.

2. 머신러닝 투자 전략 확장 5가지 핵심 방향:
   - ① 다중 분류(Multi-class) 문제로 전환: 단순 상승/하락(2진 분류)이 아니라 '보합', '3% 이상 급등', '3% 이상 급락' 등 다중 시나리오 레이블 설계
   - ② 알고리즘 다변화: 트리 계열 외에 SVM, 로지스틱 회귀 등 다양한 모델 실험 (※ 트리 모델과 달리 스케일에 민감한 알고리즘은 정규화 필수!)
   - ③ 설명 변수(Feature) 교체 및 발굴: 전략 성패를 가르는 가장 결정적 요소로, 새로운 기술적·거시적·펀더멘털 변수 탐색
   - ④ 예측 대상 자산/종목 변경: 같은 모델·파라미터라도 우상향 추세가 강한 S&P 500과 변동성이 큰 원유(USO) ETF는 결과가 완전히 다름.
     모든 자산에 공통으로 통하는 만능 예측 모델은 존재하지 않음을 명심할 것
   - ⑤ 노이즈 제거 기법 결합: 원 데이터 대신 이동평균·웨이블릿·PCA 등으로 노이즈를 정제한 피처 투입
"""
#%% [2.  재현: SPY + 이종자산 ETF 데이터 준비 및 XGBoost 과적합 진단]
spy_df = load_sql("""
    SELECT 날짜 AS Dates, 종가 AS CLOSE_SPY, 고가 AS HIGH, 저가 AS LOW, 거래량 AS VOLUME
    FROM us_price WHERE 티커 = 'SPY' ORDER BY 날짜 ASC
""")
if spy_df.empty:
    spy_df = load_sql("""
        SELECT Date AS Dates, Close AS CLOSE_SPY, High AS HIGH, Low AS LOW, Volume AS VOLUME
        FROM global_price WHERE ticker = 'SPY' ORDER BY Date ASC
    """)

etf_macro = load_sql("""
    SELECT Date AS Dates, GLD AS CLOSE_GLD, TLT AS CLOSE_TLT, IEF AS CLOSE_IEF, DBC AS CLOSE_DBC
    FROM sample_etf ORDER BY Date ASC
""")
spy_df['Dates'] = pd.to_datetime(spy_df['Dates'])
etf_macro['Dates'] = pd.to_datetime(etf_macro['Dates'])
df = pd.merge(spy_df, etf_macro, on='Dates', how='inner').dropna().reset_index(drop=True)

# 기술 지표 생성 (MA_45, VMA_45, RSI_14)
df['MA_45'] = df['CLOSE_SPY'].rolling(45, min_periods=45).mean()
df['VMA_45'] = df['VOLUME'].rolling(45, min_periods=45).mean()

i, UpI, DoI = 0, [0], [0]
while i + 1 <= df.index[-1]:
    UpMove = df.loc[i + 1, 'HIGH'] - df.loc[i, 'HIGH']
    DoMove = df.loc[i, 'LOW'] - df.loc[i + 1, 'LOW']
    UpI.append(UpMove if (UpMove > DoMove and UpMove > 0) else 0)
    DoI.append(DoMove if (DoMove > UpMove and DoMove > 0) else 0)
    i += 1
PosDI = pd.Series(UpI).ewm(span=14, min_periods=14).mean()
NegDI = pd.Series(DoI).ewm(span=14, min_periods=14).mean()
df['RSI_14'] = PosDI / (PosDI + NegDI)

df = df.set_index('Dates').dropna()

# 타겟 생성 및 shift(-1) 정렬
df['target'] = np.where(df['CLOSE_SPY'].pct_change() > 0, 1, -1)
df['target'] = df['target'].shift(-1)
df = df.dropna()
df['target'] = df['target'].astype(np.int64)

y_var = df['target']
x_var = df.drop(['target', 'HIGH', 'LOW', 'VOLUME', 'CLOSE_SPY'], axis=1)

X_train, X_test, y_train, y_test = train_test_split(x_var, y_var, test_size=0.3, shuffle=False, random_state=3)

def get_confusion_matrix(y_true, pred):
    confusion = confusion_matrix(y_true, pred)
    acc = accuracy_score(y_true, pred)
    prec = precision_score(y_true, pred, zero_division=0)
    rec = recall_score(y_true, pred, zero_division=0)
    f1 = f1_score(y_true, pred, zero_division=0)
    roc = roc_auc_score(y_true, pred)
    print('confusion matrix:\n', confusion)
    print(f'accuracy:{acc:.4f}, precision:{prec:.4f}, recall:{rec:.4f}, F1:{f1:.4f}, ROC AUC score:{roc:.4f}')

# XGBoost 단일 실험 (훈련 정확도는 높지만 테스트 정확도가 떨어지는 과적합 확인)
y_train_xgb = (y_train == 1).astype(int)
xgb_dis = XGBClassifier(n_estimators=400, learning_rate=0.1, max_depth=3, random_state=SEED, eval_metric='logloss')
xgb_dis.fit(X_train, y_train_xgb)
xgb_pred = np.where(xgb_dis.predict(X_test) == 1, 1, -1)

print("\n--- [실험 1] XGBoost 단일 모델 결과 (과적합 사례) ---")
print("Train Accuracy:", round(xgb_dis.score(X_train, y_train_xgb), 4))
get_confusion_matrix(y_test, xgb_pred)


#%% [3. TimeSeriesSplit + GridSearchCV 튜닝 & 타겟 임계값(>0.0005) 재학습]
params = {
    'bootstrap': [True],
    'n_estimators': range(10, 200, 30),
    'max_depth': [4, 6, 8, 10],
    'min_samples_leaf': [2, 3, 4, 5],
    'min_samples_split': [2, 4, 6, 8],
    'max_features': [4]
}

clf = GridSearchCV(RandomForestClassifier(random_state=SEED), params, cv=TimeSeriesSplit(n_splits=5), n_jobs=-1)
clf.fit(X_train, y_train)
print("\n--- [실험 2] GridSearchCV (기준: > 0) 결과 ---")
print("Best Params:", clf.best_params_, "| CV Score:", round(clf.best_score_, 4))
get_confusion_matrix(y_test, clf.predict(X_test))

# 미세 노이즈 상승을 배제하기 위해 임계값(> 0.0005, 0.05%) 적용 후 재학습
df_thresh = df.copy()
df_thresh['target'] = np.where(df_thresh['CLOSE_SPY'].pct_change() > 0.0005, 1, -1)
df_thresh['target'] = df_thresh['target'].shift(-1)
df_thresh = df_thresh.dropna()
df_thresh['target'] = df_thresh['target'].astype(np.int64)

y_var2 = df_thresh['target']
x_var2 = df_thresh.drop(['target', 'HIGH', 'LOW', 'VOLUME', 'CLOSE_SPY'], axis=1)
X_train2, X_test2, y_train2, y_test2 = train_test_split(x_var2, y_var2, test_size=0.3, shuffle=False, random_state=3)

clf2 = GridSearchCV(RandomForestClassifier(random_state=SEED), params, cv=TimeSeriesSplit(n_splits=5), n_jobs=-1)
clf2.fit(X_train2, y_train2)
print("\n--- [실험 3] GridSearchCV (기준: > 0.0005 임계값 적용) 결과 ---")
print("Best Params:", clf2.best_params_, "| CV Score:", round(clf2.best_score_, 4))
get_confusion_matrix(y_test2, clf2.predict(X_test2))


#%% [4. 전략 확장: 정상성 피처 기반 국내 삼성전자 앙상블 모델 & 백테스트]
"""
[전략 확장 포인트]
- 비정상성 가격 레벨 대신 이격도·수익률·변화율 피처 사용
- RandomForest vs XGBoost 비교 및 실제 거래비용(10bp) 반영 누적 수익률·샤프비율·MDD 검증
"""
def run_custom_tree_strategy(ticker: str = '005930', threshold: float = 0.0005, cost_bp: float = 0.001):
    kr = load_sql(f"SELECT 날짜 AS Dates, 종가, 거래량 FROM kor_price WHERE 종목코드 = '{ticker}' AND 날짜 >= '2012-01-01' ORDER BY 날짜 ASC")
    kr['Dates'] = pd.to_datetime(kr['Dates'])
    kr = kr.set_index('Dates').sort_index()

    cd = load_sql("SELECT 날짜 AS Dates, 금리 AS cd91 FROM cd91_rate ORDER BY 날짜 ASC")
    cd['Dates'] = pd.to_datetime(cd['Dates'])
    cd = cd.set_index('Dates').sort_index()

    glb = load_sql("SELECT Date AS Dates, SPY, GLD, TLT FROM sample_etf ORDER BY Date ASC")
    glb['Dates'] = pd.to_datetime(glb['Dates'])
    glb = glb.set_index('Dates').apply(pd.to_numeric, errors='coerce').sort_index()

    data = kr.join(cd, how='left').join(glb, how='left').ffill()

    feat = pd.DataFrame(index=data.index)
    feat['ret_1d'] = data['종가'].pct_change(1)
    feat['ret_5d'] = data['종가'].pct_change(5)
    feat['ma_gap_45'] = data['종가'] / data['종가'].rolling(45).mean() - 1
    feat['vma_ratio_45'] = data['거래량'] / data['거래량'].rolling(45).mean().replace(0, np.nan)
    diff = data['종가'].diff()
    feat['rsi_14'] = diff.clip(lower=0).ewm(span=14, adjust=False).mean() / (
        diff.clip(lower=0).ewm(span=14, adjust=False).mean() + (-diff.clip(upper=0)).ewm(span=14, adjust=False).mean()
    )
    feat['cd91_diff_20d'] = data['cd91'].diff(20)
    feat['spy_ret_5d'] = data['SPY'].pct_change(5)
    feat['gld_ret_5d'] = data['GLD'].pct_change(5)
    feat['tlt_ret_5d'] = data['TLT'].pct_change(5)

    feat['next_ret'] = data['종가'].pct_change().shift(-1)
    feat['target'] = (feat['next_ret'] > threshold).astype(int)
    feat = feat.dropna()

    f_cols = [c for c in feat.columns if c not in ['next_ret', 'target']]
    X_tr, X_te, y_tr, y_te = train_test_split(feat[f_cols], feat['target'], test_size=0.3, shuffle=False)
    ret_te = feat['next_ret'].loc[X_te.index]

    rf = RandomForestClassifier(n_estimators=200, max_depth=4, min_samples_leaf=10, random_state=SEED, n_jobs=-1).fit(X_tr, y_tr)
    xgb = XGBClassifier(n_estimators=150, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, random_state=SEED, eval_metric='logloss').fit(X_tr, y_tr)

    rows = []
    for name, mdl in [('RandomForest', rf), ('XGBoost', xgb)]:
        prob = mdl.predict_proba(X_te)[:, 1]
        pred = (prob >= 0.5).astype(int)
        turnover = pd.Series(pred, index=X_te.index).diff().abs().fillna(0)
        s_ret = pred * ret_te - turnover * cost_bp
        cum = (1 + s_ret).cumprod()
        yrs = len(s_ret) / 252
        cagr = cum.iloc[-1] ** (1 / yrs) - 1
        vol = s_ret.std() * np.sqrt(252)
        rows.append({
            '모델': name, 'Accuracy': round(accuracy_score(y_te, pred), 4),
            'ROC-AUC': round(roc_auc_score(y_te, prob), 4),
            'CAGR(%)': round(cagr * 100, 2),
            '샤프비율': round((cagr - 0.03) / vol, 2) if vol > 0 else 0,
            'MDD(%)': round((cum / cum.cummax() - 1).min() * 100, 2)
        })
    print(f"\n--- [실전 확장] {ticker} 정상성 피처 트리 앙상블 백테스트 결과 ---")
    print(pd.DataFrame(rows).to_string(index=False))

run_custom_tree_strategy(ticker='005930', threshold=0.0005, cost_bp=0.001)