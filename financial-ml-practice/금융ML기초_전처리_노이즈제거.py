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
    
#%%     
"""
================================================================================
[파일 01] 금융 머신러닝 기초, 시계열 노이즈 제거 및 피처 전처리 모듈
--------------------------------------------------------------------------------
1. DB 연결 헤더 & 사이킷런(Scikit-learn) 핵심 모듈 전체 치트시트
2. 금융 머신러닝의 개념적 차별점 & 투자 전략 설계 4대 원칙
3. 금융 시계열의 구조적 한계(Lagging)와 5대 노이즈 제거 기법 (SVD·이동평균·웨이블릿·PCA)
4. 쿠션 데이터(Cushion Data) 확보 및 기술·거시지표 피처 생성 함수 (교재 원문 + DB 실전)
================================================================================
"""

#%% [1. 공통 환경 설정 및 SQL DB 연결 헤더]
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.preprocessing import StandardScaler

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

print("[01] 환경 설정 및 stock_db 연결 완료!")
#%%
"""
[사이킷런(Scikit-learn) 금융 머신러닝 핵심 모듈 전체 정리]
1. 데이터 전처리 및 스케일링 (sklearn.preprocessing):
   - StandardScaler: 평균 0, 표준편차 1로 표준화 (SVM, KNN, 선형회귀, PCA 전 필수)
   - MinMaxScaler: 최솟값 0, 최댓값 1 범위로 변환 (신경망 입력, 이상치가 적을 때 유용)
   - RobustScaler: 중앙값(Median)과 사분위수(IQR)를 사용해 금융 데이터의 극단적 이상치(폭등/폭락일) 영향을 최소화
   - Normalizer: 각 행(샘플) 벡터의 길이(L2 Norm)를 1로 정규화 (클러스터링 시 종목 간 수익률 방향성 비교에 활용)

2. 차원 축소 및 노이즈 제거 (sklearn.decomposition):
   - PCA (주성분 분석): 상관관계가 높은 다수 변수에서 분산을 극대화하는 직교 주성분 추출
   - TruncatedSVD (절단 특잇값 분해): 희소 행렬이나 수익률 행렬에서 상위 특잇값만 남겨 노이즈 제거
   - FastICA (독립 성분 분석): 통계적으로 서로 독립적인 잠재 요인(신호) 분리

3. 데이터 분할, 교차 검증 및 하이퍼파라미터 튜닝 (sklearn.model_selection):
   - train_test_split: 훈련셋/테스트셋 분할 (시계열에서는 반드시 shuffle=False 지정)
   - TimeSeriesSplit: 시간 순서를 보존하는 전진 분석(Walk-Forward) 시계열 교차 검증기
   - GridSearchCV: 지정한 모든 하이퍼파라미터 조합을 교차 검증으로 전수 탐색
   - RandomizedSearchCV: 파라미터 공간에서 무작위 샘플링으로 빠르게 최적 조합 탐색

4. 지도 학습 알고리즘 (분류 / 회귀):
   - 선형 모델 (sklearn.linear_model): LinearRegression, Ridge(L2 규제), Lasso(L1 규제·변수선택), ElasticNet, LogisticRegression
   - 거리·커널 모델 (sklearn.neighbors / sklearn.svm): KNeighborsClassifier, KNeighborsRegressor, SVC, SVR
   - 트리·앙상블 (sklearn.ensemble): DecisionTreeClassifier, RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier, AdaBoostClassifier
   *(외부 부스팅 라이브러리: xgboost.XGBClassifier, lightgbm.LGBMClassifier, catboost.CatBoostClassifier)*

5. 비지도 학습 알고리즘 (sklearn.cluster):
   - KMeans: K개 중심점 기반 군집화 / AgglomerativeClustering: 계층적 병합 군집화 / DBSCAN: 밀도 기반 군집화

6. 모델 평가 지표 (sklearn.metrics) 및 파이프라인 (sklearn.pipeline):
   - 분류 평가: confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, log_loss
   - 회귀 평가: mean_squared_error(MSE), root_mean_squared_error(RMSE), mean_absolute_error(MAE), r2_score
   - 군집 평가: silhouette_score (실루엣 계수: -1 ~ 1, 높을수록 군집 분리도 우수)
   - 파이프라인: Pipeline([('scaler', StandardScaler()), ('model', SVC())]) → 교차 검증 시 검증셋 데이터 누설 원천 차단
"""
#%%
"""
[금융 머신러닝의 개념과 전통 계량경제학과의 차별점]
1. 전통적 계량경제/통계 모델(회귀분석, ARIMA 등) vs 금융 머신러닝:
   - 전통 통계 모델:
     * 변수 간 '선형성(Linearity)'과 오차항의 정규분포·독립성 등 엄격한 사전 가정을 전제함
     * 설명 변수가 많아지면 다중공선성(Multicollinearity) 문제로 추정이 불안정해져 소수의 검증된 팩터만 사용 가능
   - 금융 머신러닝:
     * 데이터 분포에 대한 사전 가정 없이 변수 간의 복잡한 '비선형(Non-linear) 상호작용'을 스스로 학습
     * 수십~수백 개의 기술지표·거시지표·재무·비정형(텍스트/이미지) 데이터를 동시에 투입 가능
     * 단점: 내부 작동 원리를 직관적으로 설명하기 어려운 '블랙박스(Black-box)' 성향이 강하고,
       금융 데이터의 노이즈까지 학습하는 '과적합(Overfitting)' 위험이 매우 높음

2. 머신러닝 학습 방식의 3대 분류와 금융 적용:
   - 지도 학습(Supervised Learning): 정답 레이블(Y)이 있는 학습
     * 분류(Classification): 주가 상승/하락 방향 예측, 부도 여부 예측 (트리 앙상블, KNN, SVM, 로지스틱)
     * 회귀(Regression): 기대 수익률, 변동성, 적정 주가 예측 (릿지/라쏘, SVR, 트리 회귀)
   - 비지도 학습(Unsupervised Learning): 정답 레이블 없이 데이터 구조·패턴을 스스로 발견
     * 군집화(Clustering): 유사 주가/재무 패턴 종목 그룹화 (K-Means, 계층적 군집화)
     * 차원 축소(Dimensionality Reduction): 다수 자산의 공통 리스크 요인 추출 및 노이즈 제거 (PCA, SVD, 오토인코더)
   - 강화 학습(Reinforcement Learning): 에이전트가 시장 환경과 상호작용하며 누적 보상(수익/샤프비율)을 극대화하는 행동(매수/매도/비중) 학습 (동적 자산배분, 주문 집행 최적화)

3. 금융 데이터가 일반 머신러닝 데이터(이미지·음성·고객 이탈)와 다른 4가지 이유:
   - ① 극도로 낮은 신호 대 잡음비(Low Signal-to-Noise Ratio): 차익거래자들로 인해 예측 가능한 신호(알파)가 미미함
   - ② 비정상성(Non-stationarity): 시간에 따라 평균·분산·상관관계가 계속 변하므로 가격(Level) 자체를 학습하면 실패함
   - ③ 시계열 자기상관과 중복 레이블: 관측치들이 독립적이지 않고 시간적으로 얽혀 있어 무작위 분할(K-Fold) 불가
   - ④ 알파 소멸(Alpha Decay): 특정 패턴이 시장에 알려지면 참여자들이 몰려 해당 패턴의 초과수익이 사라짐
"""
#%%
"""
--------------------------------------------------------------------------------
[머신러닝 투자 전략의 3차원 분류 체계 및 설계 4대 원칙]
1. 금융 머신러닝 예측 문제의 3차원 구조 ([상품] × [토픽] × [데이터]):
   - 투자 상품(Asset Class): 주식, 외환(FX), 원자재, 부동산, 주가지수(Index), 암호화폐 등
   - 예측 토픽(Topic): ① 가격 예측(회귀), ② 방향성/트렌드 예측(분류), ③ 종목 선택(랭킹/군집), ④ 변동성 예측(리스크 관리)
   - 활용 데이터(Data): 가격·거래량(OHLCV), 기술적 지표, 거시경제 지표, 재무제표, 비정형 데이터(뉴스 텍스트, 차트 이미지 등)

2. 머신러닝 기반 투자 전략 설계 4대 핵심 원칙:
   - 원칙 ① 문제 정의(Label Definition)가 알고리즘보다 먼저다:
     * 단순히 "주가가 오를까?"가 아니라, '전일 종가 대비 상승'인지, '한 달 전 대비 상승'인지, '3일간 특정 수익률 이상 상승'인지를
       실제 트레이딩 가능 여부(체결 시점, 거래비용, 유동성)를 고려해 정밀하게 정의해야 함.
   - 원칙 ② 도메인 인사이트(Domain Insight)와 퀀트 커리어 로드맵:
     * 타이타닉 생존 예측이나 이미지 분류와 달리 금융은 데이터 종류가 제한적이고 노이즈가 극심함.
     * 설명 변수를 무작정 많이 집어넣는다고 성능이 오르지 않으며, 시장 메커니즘에 대한 트레이더의 인사이트를 피처로 녹여내야 함.
     * 주니어 퀀트 실무 성장 경로: 먼저 학계/실무 논문을 코드로 직접 구현해 보며 프로그래밍과 ML 테크닉을 익힌 뒤,
       점차 자신만의 시장 인사이트를 결합해 독자적인 전략으로 발전시켜야 함.
   - 원칙 ③ 서로 다른 관점의 결합 = 앙상블 트리 전략의 아이디어:
     * 트레이더 A(기술적 분석가): 주가 이동평균, 거래량 이동평균, RSI 등 가격·수급 기반 지표로 매매
     * 트레이더 B(거시경제 분석가): 금리, 물가, 장단기 금리차 등 매크로 지표로 시장 국면 판단
     * 트레이더 C(이종 자산 분석가): 금, 달러, 원유, 채권 등 타 자산군과의 상관관계를 통해 주식시장 방향 추론
     * 단일 의사결정나무(Decision Tree)는 깊어질수록 훈련 데이터에 과적합되므로,
       여러 피처와 샘플을 무작위로 추출해 다수결로 투표하는 '배깅(랜덤 포레스트)'과
       이전 트리의 오차를 순차적으로 보완하는 '부스팅(XGBoost)'으로 세 트레이더의 의견을 통합함.
   - 원칙 ④ 실무 상품화를 위한 팀플레이(분업):
     * 실제 금융기관에서 머신러닝 전략을 상품화할 때는 혼자 모든 것을 처리하기보다
       NLP 전문가, 데이터 엔지니어, 데이터 과학자, 현업 포트폴리오 매니저(PM) 간의 유기적 협업이 필수임.
"""
#%%
"""
[금융 시계열 데이터의 한계와 5대 노이즈 제거 기법]
1. 주가 가격(Price Level) 직접 예측의 구조적 함정 (Lagging 현상):
   - 주가는 기하 브라운 운동(GBM)이나 랜덤워크에 가까워 '내일 주가는 오늘 주가 근처'에 형성됨
   - 따라서 주가 가격 자체를 회귀(Regression) 모델로 학습시키면, 모델이 실제 미래 방향을 예측하는 것이 아니라
     단순히 '전일 종가를 한 칸 뒤로 복사해 따라가는 지연 현상(Lagging)'만 보이고도 R2 점수가 0.99처럼 높게 나오는 착시가 발생함
   - 해결책: 가격 레벨 대신 차분(Diff), 수익률(Return), 이격도 등 정상성(Stationarity)을 띤 데이터로 변환해야 함


2. 금융 시계열의 5대 노이즈 제거(Denoising) 기법:
   - ① 특잇값 분해 (SVD, Singular Value Decomposition):
     * 행렬을 특잇값 크기에 따라 분해한 뒤, 작은 특잇값(단기 무작위 노이즈)을 0으로 제거하고 큰 특잇값(핵심 추세)만으로 행렬을 재구성
     
     
   - ② 이동평균 평활화 (SMA · EMA):
     * 단순이동평균(SMA)은 과거 N일 동일 가중치로 노이즈를 줄이나 지연(Lag)이 크고,
       지수이동평균(EMA)은 최근 데이터에 더 큰 가중치를 부여해 지연을 줄이면서 추세를 추출
       
       
   - ③ 웨이블릿 변환 (Wavelet Transform):시간-주파수 동시 분석 기반 노이즈 제거:
     * 시계열을 다양한 주파수 대역으로 분해한 뒤, 고주파 영역(단기 시장 노이즈)에 임계값(Thresholding)을 적용해 제거하고
       역변환하여 원 신호의 급변점(변곡점)은 보존하면서 잔파도 노이즈만 깔끔하게 제거

     * 기존 푸리에 변환(Fourier Transform)의 한계:
       푸리에 변환은 시계열 신호를 무한히 이어지는 사인(sin)·코사인(cos) 파동의 합으로 분해하여
       '어떤 주파수(주기) 성분이 존재하는지'는 알려주지만, 그 사건이 '언제(Time) 발생했는지'에 대한 시간 정보가 소멸됨.
       또한 데이터가 정상성(Stationarity)을 띤다고 가정하므로, 갑작스러운 폭락·급등(변곡점)이 빈번한 금융 시계열에 부적합함.
       
     * 웨이블릿 변환의 핵심 원리:
       무한한 사인파 대신, 특정 시간 구간에만 짧게 진동하다가 0으로 사라지는 작은 파동인 '마더 웨이블릿(Mother Wavelet, 예: Haar, Daubechies db4)'을
       크기(Scale, 늘리고 줄임)와 위치(Translation, 시간축 이동)를 바꿔가며 원본 주가에 대입함.
       이를 통해 '언제(시간)' '어떤 주기의 움직임(주파수)'이 발생했는지를 동시에 포착할 수 있음.
       
       
     * 4단계 노이즈 제거(Wavelet Denoising) 작동 과정:
       1단계 [다중 해상도 분해(DWT)]: 원본 주가를 저주파 성분인 '근사 계수(Approximation, cA: 거시적 장기 추세)'와
             고주파 성분인 '상세 계수(Detail, cD: 단기 잔파도 변동성)'로 여러 단계(Level)에 걸쳐 반복 분해함.
             
       2단계 [노이즈 수준 추정]: 가장 미세한 고주파 상세 계수(cD1)의 중앙값 절대편차(MAD)를 이용해 시장의 순수 노이즈 표준편차(σ)를 계산하고,
             임계값(Universal Threshold, λ = σ * sqrt(2 * ln(N)))을 산출함.
             
       3단계 [임계값 처리(Thresholding)]: 분해된 고주파 상세 계수(cD) 중 임계값(λ)보다 작은 계수들은 '무작위 시장 노이즈'로 간주하여
             0으로 제거(Hard Thresholding)하거나 크기를 축소(Soft Thresholding)하고, 임계값을 넘는 큰 계수(실제 급등락 이벤트)는 살려둠.
             
       4단계 [역웨이블릿 변환(IDWT)]: 살아남은 저주파 추세(cA)와 정제된 상세 계수(cD)를 다시 합쳐 원본 시계열로 복원함.
       
     * 이동평균(SMA/EMA) 대비 결정적 장점:
       이동평균은 과거 N일 평균을 내기 때문에 주가 급변 시 신호가 뒤늦게 따라오는 '지연 현상(Lagging)'이 필연적으로 발생하지만,
       웨이블릿 변환은 급격한 변곡점(고주파 중 진폭이 큰 신호)은 그대로 보존하면서 자잘한 잔노이즈만 걷어내므로 지연이 거의 없음.
       
       
   - ④ 주성분 분석 (PCA, Principal Component Analysis):
     * 수십~수백 개 종목/지표의 공분산 행렬에서 분산을 가장 크게 설명하는 소수의 직교 주성분(시장 공통 요인)만 추출하고
       나머지 고유 노이즈 성분을 제거
     * 선형인 대상에만 확실한 효과가 있고 비선형의 경우에는 효과가 약함. 
     
     
     
   - ⑤ 오토인코더 (Autoencoder -딥러닝 기반 비선형 차원 축소 및 노이즈 제거:):
     * 입력 데이터를 병목 은닉층(Latent Space)으로 강제 압축(Encoder)했다가 다시 원본으로 복원(Decoder)하도록 학습시켜,
       복원 과정에서 불필요한 미세 노이즈를 버리고 핵심 비선형 패턴만 남기는 신경망 기법
       
     * 기본 구조 (비지도 학습 신경망):
       정답 레이블(Y) 없이 입력 데이터(X)를 넣었을 때 출력층에서 입력과 똑같은 데이터(X_hat)를 복원하도록 학습하는 신경망.
       구조는 크게 [입력층(Input) → 인코더(Encoder) → 병목 은닉층(Bottleneck / Latent Space) → 디코더(Decoder) → 출력층(Output)]으로 구성됨.
       
     * 노이즈가 제거되는 핵심 원리 (정보의 병목 현상):
       입력층의 변수(예: 100개 종목의 수익률 또는 50개 기술·거시지표)보다 병목 은닉층의 노드 수(예: 5개)를 훨씬 적게 강제 제한함.
       신경망은 100개 변수의 모든 정보를 5개 노드에 다 우겨넣을 수 없으므로, 복원 오차(MSE = ||X - X_hat||^2)를 최소화하기 위해
       '무작위로 튀는 일시적 노이즈'는 과감히 버리고, 시장 전체를 관통하는 '가장 핵심적인 비선형 구조·공통 패턴'만 압축(Encoding)하여 저장한 뒤
       이를 바탕으로 디코더(Decoding)가 깨끗한 신호(X_hat)를 재구성함.
       
     * PCA(주성분 분석)와의 차이점 및 금융 활용:
       - PCA는 데이터를 '선형(직선)' 결합으로만 압축하지만, 오토인코더는 활성화 함수(ReLU, Tanh 등)를 통해
         금융 변수 간의 복잡한 '비선형 상호작용'까지 포착하여 노이즈를 제거함.
       - 디노이징 오토인코더(Denoising Autoencoder): 학습 시 입력 데이터에 일부러 인위적인 가우시안 노이즈나 마스킹(0 처리)을 섞어 넣고
         정답은 '노이즈가 없는 깨끗한 원본'을 주면, 실전에서도 오염된 금융 데이터에서 순수 신호만 복원해내는 능력이 극대화됨.
       - 이상 탐지(Anomaly Detection): 정상 시장 국면으로 학습된 오토인코더에 금융위기나 플래시 크래시 데이터가 들어오면
         복원 오차(Reconstruction Error)가 급증하므로 시장 국면 전환(Regime Shift) 경보 지표로도 활용됨.
 
       
       
       엄청나게 딱 확실한 효과가 입증된 기법은 아직까지는 없다고 보는게 맞음 
"""

#%% [3. 금융 시계열의 한계와 5대 노이즈 제거 기법 구현]
# 주가 가격 자체를 회귀 예측하면 전일 종가를 그대로 따라가는 '지연 현상(Lagging)'이 발생한다.
# 이를 완화하기 위해 수익률 변환 후 SVD, 이동평균, 웨이블릿 변환, PCA 등을 활용해 노이즈를 걸러낸다.

from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.preprocessing import StandardScaler

def demo_noise_reduction():
    seed = globals().get('SEED', 42)

    # 1) KODEX 200('069500') 조회 후, 테이블에 없으면 삼성전자('005930')로 자동 대체
    px = load_sql("""
        SELECT 날짜 AS Date, 종가 AS Close
        FROM kor_price
        WHERE 종목코드 = '069500' AND 날짜 >= '2020-01-01'
        ORDER BY 날짜 ASC
    """)
    target_name = "KODEX 200 (069500)"

    if px.empty:
        px = load_sql("""
            SELECT 날짜 AS Date, 종가 AS Close
            FROM kor_price
            WHERE 종목코드 = '005930' AND 날짜 >= '2020-01-01'
            ORDER BY 날짜 ASC
        """)
        target_name = "삼성전자 (005930)"

    px['Date'] = pd.to_datetime(px['Date'])
    px = px.dropna(subset=['Close']).set_index('Date').sort_index()
    close = px['Close'].astype(float)

    if len(close) == 0:
        raise ValueError("kor_price 테이블에서 조회된 주가 데이터가 없습니다. 테이블명과 종목코드를 확인하세요.")

    # 2) 이동평균 평활화 (SMA & EMA)
    sma_20 = close.rolling(20).mean()
    ema_20 = close.ewm(span=20, adjust=False).mean()

    # 3) 웨이블릿 변환 (Wavelet Denoising - 데이터 길이에 맞춰 레벨 자동 조정)
    try:
        import pywt
        wavelet = pywt.Wavelet('db4')
        use_lvl = min(3, pywt.dwt_max_level(len(close), wavelet.dec_len))
        coeffs = pywt.wavedec(close.values, wavelet, level=use_lvl)
        sigma = np.median(np.abs(coeffs[-1])) / 0.6745
        uthresh = sigma * np.sqrt(2 * np.log(len(close)))
        coeffs_thresh = [coeffs[0]] + [pywt.threshold(c, value=uthresh, mode='soft') for c in coeffs[1:]]
        wavelet_clean = pd.Series(pywt.waverec(coeffs_thresh, wavelet)[:len(close)], index=close.index)
    except ImportError:
        wavelet_clean = close.ewm(span=10).mean()

    # 4) 다종목 수익률 행렬 기반 SVD & PCA 노이즈 제거 (공통 시장 요인만 추출)
    multi_raw = load_sql("""
        SELECT 날짜 AS Date, 종목코드, 종가
        FROM kor_price
        WHERE 종목코드 IN ('005930', '000660', '035420', '051910', '005380', '068270', '105560', '055550')
          AND 날짜 >= '2021-01-01'
        ORDER BY 날짜 ASC
    """)
    ret_mat = multi_raw.pivot(index='Date', columns='종목코드', values='종가').pct_change().dropna()

    # TruncatedSVD로 상위 2개 주성분만 남겨 노이즈 제거 후 복원
    svd = TruncatedSVD(n_components=2, random_state=seed)
    ret_svd_recon = pd.DataFrame(
        svd.inverse_transform(svd.fit_transform(ret_mat)),
        index=ret_mat.index, columns=ret_mat.columns
    )
    orig_vol = ret_mat['005930'].std()
    recon_vol = ret_svd_recon['005930'].std()
    print(f"[SVD 노이즈 제거] 삼성전자 일간 변동성: 원본 {orig_vol:.4f} -> 복원 {recon_vol:.4f}")

    # PCA 설명분산비율 확인
    pca = PCA(n_components=3, random_state=seed)
    pca.fit(StandardScaler().fit_transform(ret_mat))
    print(f"[PCA 분석 - {target_name}] 상위 3개 주성분 설명분산비율: {np.round(pca.explained_variance_ratio_, 4)} (합계: {pca.explained_variance_ratio_.sum():.2%})")

    plt.figure(figsize=(12, 4))
    plt.plot(close[-150:], label='원본 종가 (노이즈 포함)', alpha=0.5, color='gray')
    plt.plot(sma_20[-150:], label='SMA(20) 단순이동평균', linestyle='--', linewidth=1.2)
    plt.plot(ema_20[-150:], label='EMA(20) 지수이동평균', linewidth=1.5)
    plt.plot(wavelet_clean[-150:], label='Wavelet 노이즈 제거', linewidth=2, color='crimson')
    plt.title(f'금융 시계열 노이즈 제거 비교 - {target_name} (SMA vs EMA vs Wavelet)')
    plt.legend()
    plt.tight_layout()
    plt.show()

demo_noise_reduction()

#%% [4. 쿠션 데이터 확보 및 기술·거시지표 피처 전처리 함수]
# N일 이동평균/RSI 계산 시 앞부분 N-1개 행에 NaN이 발생하므로, 실제 분석 시작일 이전의 '쿠션 데이터'를 미리 포함해 조회한다.

# [4-A] 기술적 지표 함수 (MA, VMA, RSI)
def moving_average(df: pd.DataFrame, n: int, col: str = 'CLOSE') -> pd.DataFrame:
    MA = pd.Series(df[col].rolling(n, min_periods=n).mean(), name=f'MA_{n}')
    return df.join(MA)

def volume_moving_average(df: pd.DataFrame, n: int, col: str = 'VOLUME') -> pd.DataFrame:
    VMA = pd.Series(df[col].rolling(n, min_periods=n).mean(), name=f'VMA_{n}')
    return df.join(VMA)

def relative_strength_index(df: pd.DataFrame, n: int) -> pd.DataFrame:
    i = 0
    UpI, DoI = [0], [0]
    while i + 1 <= df.index[-1]:
        UpMove = df.loc[i + 1, 'HIGH'] - df.loc[i, 'HIGH']
        DoMove = df.loc[i, 'LOW'] - df.loc[i + 1, 'LOW']
        UpI.append(UpMove if (UpMove > DoMove and UpMove > 0) else 0)
        DoI.append(DoMove if (DoMove > UpMove and DoMove > 0) else 0)
        i += 1
    PosDI = pd.Series(UpI).ewm(span=n, min_periods=n).mean()
    NegDI = pd.Series(DoI).ewm(span=n, min_periods=n).mean()
    RSI = pd.Series(PosDI / (PosDI + NegDI), name=f'RSI_{n}')
    return df.join(RSI)

# [4-B] stock_db 맞춤형 통합 전처리 파이프라인 (주가 + 금리 + 매크로 + 쿠션데이터 처리)
def build_feature_dataset(ticker: str = '005930', analysis_start: str = '2015-01-01', cushion_days: int = 90) -> pd.DataFrame:
    """
    analysis_start 이전 cushion_days만큼의 데이터를 먼저 불러와 지표를 계산한 뒤,
    NaN을 제거하고 analysis_start 이후 구간만 깔끔하게 반환하는 실전 전처리 함수
    """
    fetch_start = (pd.to_datetime(analysis_start) - pd.Timedelta(days=cushion_days)).strftime('%Y-%m-%d')

    px = load_sql(f"""
        SELECT 날짜 AS Dates, 시가 AS OPEN, 고가 AS HIGH, 저가 AS LOW, 종가 AS CLOSE, 거래량 AS VOLUME
        FROM kor_price
        WHERE 종목코드 = '{ticker}' AND 날짜 >= '{fetch_start}'
        ORDER BY 날짜 ASC
    """).dropna().reset_index(drop=True)

    # 기술적 지표 적용
    px = moving_average(px, 45, col='CLOSE')
    px = volume_moving_average(px, 45, col='VOLUME')
    px = relative_strength_index(px, 14)

    px['Dates'] = pd.to_datetime(px['Dates'])
    px = px.set_index('Dates').sort_index()

    # 비정상성 가격 레벨을 정상성 비율 피처로 확장
    px['MA_45_gap'] = px['CLOSE'] / px['MA_45'] - 1
    px['VMA_45_ratio'] = px['VOLUME'] / px['VMA_45'].replace(0, np.nan)

    # CD91일물 금리(cd91_rate) 결합
    cd = load_sql(f"SELECT 날짜 AS Dates, 금리 AS cd91_rate FROM cd91_rate WHERE 날짜 >= '{fetch_start}' ORDER BY 날짜 ASC")
    if not cd.empty:
        cd['Dates'] = pd.to_datetime(cd['Dates'])
        px = px.join(cd.set_index('Dates'), how='left')
        px['cd91_rate'] = px['cd91_rate'].ffill()
        px['cd91_chg_20d'] = px['cd91_rate'].diff(20)

    # 쿠션 구간 NaN 제거 후 실제 분석 시작일 이후로 슬라이싱
    px = px.dropna()
    px = px.loc[analysis_start:]
    return px

df_features = build_feature_dataset(ticker='005930', analysis_start='2015-01-01', cushion_days=90)
print(f"\n[01] 쿠션 데이터 처리 완료 데이터셋: {df_features.index.min().date()} ~ {df_features.index.max().date()} ({len(df_features):,}행)")
print(df_features[['CLOSE', 'MA_45_gap', 'VMA_45_ratio', 'RSI_14']].tail(3))