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
[파일 02] 금융 머신러닝 교차 검증, 레이블 설계, 편향 통제 및 백테스팅 원칙
--------------------------------------------------------------------------------
1. 시계열 교차 검증 3대 기법 (Walk-Forward, Blocking, Purging & Embargo)
2. 미래 시점 정렬(shift(-1)), 임계값 레이블 설계, 클래스 균형 및 샘플 가중치
3. 시계열 데이터 분할(shuffle=False) & 분류 혼동행렬 평가 지표 함수
4. 백테스트 3대 편향(생존·사전관찰·심리적 인내), 체결 시점(종가 vs 익일시가), 거래비용 반영 엔진
================================================================================
"""

#%% [1. 공통 환경 설정 및 SQL DB 연결 헤더]
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

from sklearn.model_selection import train_test_split, TimeSeriesSplit
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

print("[02] 환경 설정 및 stock_db 연결 완료!")


#%% [2. 시계열 교차 검증 3대 기법 (Walk-Forward, Blocking, Purging & Embargo)]

"""
[금융 머신러닝 교차 검증(Cross-Validation) 기법]
1. 일반 K-Fold 교차 검증이 금융에서 치명적인 이유:
   - 일반 K-Fold는 데이터를 무작위로 섞어(Shuffle) 분할하므로, 미래 시점의 데이터가 훈련셋에 포함되고
     그 직전/직후 시점의 데이터가 검증셋에 들어가 '사전 관찰 편향(Look-ahead Bias)'을 일으킴
   - 또한 금융 시계열은 자기상관(Autocorrelation)과 레이블 중첩이 존재해 검증 점수가 비정상적으로 부풀려짐

2. 금융 시계열 교차 검증 3대 표준 방법:
   - ① 전진 분석 (Walk-Forward Validation / TimeSeriesSplit):
     * 시간 순서를 엄격히 유지하며 과거 구간으로 학습하고 바로 다음 미래 구간으로 검증하는 과정을 전진 반복
     * 확장 창(Expanding Window): 훈련 시작일을 고정하고 검증이 끝난 데이터를 훈련셋에 계속 누적 추가 (데이터가 적을 때 유리)
     * 이동 창(Rolling Window): 훈련 기간 길이를 일정하게(예: 최근 3년) 유지하며 창을 옆으로 이동 (시장 국면 변화에 민감할 때 유리)
   - ② 블록 시계열 분할 (Blocking Time Series Split):
     * 전체 시계열을 시간 순서대로 여러 개의 연속된 블록으로 나눈 뒤, 각 블록 내부에서만 앞부분을 훈련·뒷부분을 검증으로 사용
     * 과거의 오래된 국면 데이터가 지나치게 쌓여 최근 시장 패턴을 희석시키는 현상을 방지함
   - ③ 퍼징과 엠바고 (Purging & Embargo - Marcos Lopez de Prado): 통용은 안됨 딱히 더 좋다고 말하기는 애매함 
     * 퍼징(Purging): 만약 레이블이 '향후 5일 수익률'이라면 훈련셋 마지막 5일치 샘플의 정답은 검증셋 기간의 가격을 포함함.
       이렇게 훈련셋과 검증셋 경계에서 레이블 기간이 겹치는 훈련 샘플을 과감히 삭제(Purge)하여 정보 누설 차단
     * 엠바고(Embargo): 검증셋 직후의 훈련 샘플에도 시장 충격의 여파(자기상관)가 남아 있으므로, 검증셋 직후 일정 기간(예: 전체의 1~2%)을
       훈련에서 제외하는 완충 지대(Embargo)를 설정 -> mlfinlab 라이브러리에서 쉽게 구현 가능. 
"""

#%%
class PurgedEmbargoTimeSeriesSplit:
    """훈련셋과 검증셋 사이에 purge_gap 및 embargo_gap을 두는 시계열 분할기"""
    def __init__(self, n_splits: int = 5, purge_gap: int = 5, embargo_gap: int = 5):
        self.n_splits = n_splits
        self.purge_gap = purge_gap
        self.embargo_gap = embargo_gap

    def split(self, X):
        n_samples = len(X)
        fold_size = n_samples // (self.n_splits + 1)
        for i in range(1, self.n_splits + 1):
            train_end = fold_size * i - self.purge_gap
            val_start = fold_size * i + self.embargo_gap
            val_end = min(fold_size * (i + 1), n_samples)
            if train_end > 0 and val_start < val_end:
                yield np.arange(0, train_end), np.arange(val_start, val_end)

# 분할 동작 확인 예시
dummy_idx = np.arange(1000)
pe_cv = PurgedEmbargoTimeSeriesSplit(n_splits=4, purge_gap=5, embargo_gap=5)
for fold, (tr_idx, va_idx) in enumerate(pe_cv.split(dummy_idx), 1):
    print(f"Fold {fold}: Train[0..{tr_idx[-1]}] -> (Purge/Embargo Gap 10일) -> Val[{va_idx[0]}..{va_idx[-1]}]")
#%% 
"""
[금융 레이블링(Labeling) 전략과 데이터 불균형·샘플 가중치 요약]
1. 고정 시간 기준(Fixed-Time Horizon) 레이블링과 한계:
   - "1일 후(또는 5일 후) 수익률이 0%보다 크면 1, 아니면 -1"로 정의하는 가장 기본적인 방식
   - 한계: ① +0.001% 같은 의미 없는 미세 변동과 +5% 급등을 똑같은 '1'로 취급함
     ② 시장 변동성이 큰 시기와 작은 시기에 동일한 고정 임계값을 쓰면 특정 시기에 레이블이 한쪽으로 쏠림
   - 보완: 거래비용을 감안한 임계값(예: > 0.0005)을 두거나, 일별 변동성(EWMA 표준편차)을 기준으로 동적 임계값을 설정

2. 트리플 배리어(Triple Barrier Method)와 메타 레이블링(Meta-Labeling):
   - 트리플 배리어: 고정된 날짜만 보지 않고 ① 상단 배리어(목표 익절선 터치 → 1), ② 하단 배리어(손절선 터치 → -1),
     ③ 수직 배리어(최대 보유 만기 도달 → 0 또는 만기 수익률 부호) 중 가장 먼저 닿는 이벤트로 레이블을 부여하는 실전형 기법
   - 메타 레이블링: 1차 모델(기존 퀀트 전략·추세추종 등)이 매수/매도 방향(Side)을 결정하면,
     2차 머신러닝 모델은 '이 신호에 실제로 진입할지 말지(1 또는 0) 및 베팅 비중(Size)'만 학습하여 전략의 승률과 샤프비율을 개선

3. 클래스 불균형(Class Imbalance)과 샘플 가중치(Sample Weight):
   - 강한 상승장 데이터에서는 상승(1) 비율이 60%를 넘어 모델이 무조건 '1(매수)'만 찍어도 정확도가 높게 나오는 착시 발생
   - 해결책: ① 정확도(Accuracy) 대신 정밀도(Precision)·재현율(Recall)·F1-Score·ROC-AUC를 평가 지표로 사용
     ② 언더샘플링/오버샘플링(SMOTE) 적용 또는 class_weight='balanced' 설정
     ③ 수익률 변동폭이 큰 중요한 사건이나 레이블 중복도가 낮은 고유 구간에 더 높은 샘플 가중치(sample_weight) 부여
"""
#%%
"""
[금융 레이블링(Labeling) 전략과 데이터 불균형·샘플 가중치 상세 정리]
1. 지도 학습에서 레이블 정의가 성패를 좌우하는 이유:
   - 머신러닝 모델은 주어진 정답(Y)을 맞히도록 최적화되므로, 
     금융 데이터를 어떤 기준으로 레이블링하느냐에 따라
     모델이 학습하는 전략의 성격, 승률, 손익비, 매매 빈도가 완전히 달라짐.


2. 고정 시간 기준(Fixed-Time Horizon) 레이블링과 2가지 치명적 한계:
   - 개념: 매수 시점(t)으로부터 고정된 기간(h일 뒤, 예: 1일 후 또는 20일 후)의 수익률(r)을 계산해,
     상승 임계값(+τ)을 넘으면 1(매수), 하락 임계값(-τ) 미만이면 -1(매도), 그 사이면 0(중립/관망)으로 부여하는 가장 흔한 방식.
     
   - 한계 ① 변동성 국면 무시 (고정 임계값의 함정):
     금융시장은 저변동성 횡보장(일평균 변동폭 0.3%)과 고변동성 위기장(일평균 변동폭 3%)이 번갈아 나타남.
     임계값을 고정(예: ±1%)해 두면 저변동성 기간에는 거의 모든 샘플이 '0'으로 쏠리고, 고변동성 기간에는 '1'과 '-1'만 쏟아져
     레이블 분포가 시간에 따라 극심하게 왜곡됨.
     
   - 한계 ② 경로 의존성(Path Dependency) 무시:
     예를 들어 10일 뒤 수익률이 +3%여서 '1(매수)'로 레이블링되었더라도, 실제로는 3일 차에 -15% 폭락하여 실전 계좌에서는
     이미 손절매(Stop-Loss)로 청산당했을 수 있음. 즉, 보유 기간 중간의 위험(경로)을 전혀 반영하지 못함.


3. 트리플 배리어 기법 (Triple Barrier Method — 마르코스 로페즈 데 프라도):
   - 개념: 고정된 만기 시점만 보지 않고, 진입 시점(t)을 기준으로 가격·시간 축에 3개의 장벽(Barrier)을 설정하여
     '가장 먼저 닿는 장벽'에 따라 레이블을 결정하는 실전 트레이딩 기반 레이블링 기법.
     * ① 상단 수평 배리어 (Profit-Taking, 익절선): 목표 수익률 도달 시 → 레이블 `1` 부여 (즉시 수익 확정)
     * ② 하단 수평 배리어 (Stop-Loss, 손절선): 허용 최대 손실 도달 시 → 레이블 `-1` 부여 (손실 제한)
     * ③ 수직 배리어 (Vertical Barrier, 최대 보유 만기): 지정된 기간(예: 10영업일) 동안 상·하단 배리어 중 어디에도 닿지 않고
       만기에 도달한 경우 → 레이블 `0`(관망)을 부여하거나 만기 시점 수익률의 부호(+1/-1)를 부여.
   - 동적 배리어 폭 설정 (Dynamic Thresholding):
     상·하단 배리어의 폭을 고정 퍼센트가 아니라 해당 시점의 일간 변동성(예: 지수가중이동표준편차, EWMA Volatility)의 배수
     (예: 상단 +2σ, 하단 -2σ)로 설정함으로써, 저변동성 장세와 고변동성 장세 모두에서 일관된 난이도와 균형 잡힌 레이블을 생성함.

4. 메타 레이블링 (Meta-Labeling — 방향성과 베팅 규모의 분리):
   - 개념: 하나의 머신러닝 모델에 '매수/매도 방향 예측'과 '진입 여부 결정'을 동시에 맡기면 과적합되기 쉬우므로 이를 2단계로 분리함.
     * 1단계 [기본 모델 (Primary Model)]: 기존의 전통적 퀀트 전략(이동평균 돌파, 모멘텀, 밸류 등)이나 기본 모델이
       우선 매수(+1) 또는 매도(-1)의 '방향(Side)'을 1차적으로 제안함.
     * 2단계 [메타 모델 (Secondary ML Model)]: 1차 모델이 신호를 발생시킨 시점의 시장 환경(변동성, 거래량, 거시지표 등)을 입력받아,
       이 거래가 실제로 수익을 낼 것인지(`1`: 진입 실행) 실패할 것인지(`0`: 거짓 신호이므로 진입 포기)만 이진 분류함.
   - 실전 효과:
     * 1차 전략의 고질적 약점인 '거짓 신호(False Positive, 휩소)'를 걸러내어 전략의 정밀도(Precision)와 샤프 비율을 크게 높임.
     * 메타 모델이 출력하는 예측 확률(predict_proba, 예: 0.52 vs 0.85)을 활용해 확신이 높을수록 투자 비중(Bet Size)을 크게 싣고
       확신이 낮으면 비중을 줄이는 정교한 자금 관리가 가능해짐.

5. 클래스 불균형(Class Imbalance) 및 중복 샘플 가중치(Sample Weight) 처리:
   - 클래스 불균형 문제:
     장기 우상향 지수(예: S&P 500)는 상승일(54~56%)이 하락일보다 많고, 폭락 경보 모델은 정상일(95%)이 위기일(5%)보다 압도적으로 많음.
     이 상태에서 모델을 그냥 학습시키면 모델이 다수 클래스(무조건 상승)만 찍어도 정확도가 높게 나오는 착시가 발생함.
   - 불균형 해결 4가지 방법:
     * ① 평가 지표 변경: 단순 정확도(Accuracy) 대신 정밀도(Precision), 재현율(Recall), F1-Score, ROC-AUC, PR-AUC를 사용.
     * ② 리샘플링(Resampling): 다수 클래스 데이터를 줄이는 언더샘플링(Under-sampling) 또는 소수 클래스를 복제·합성하는
       오버샘플링(Over-sampling, SMOTE) 적용 (단, 시계열에서는 미래 데이터 합성 방지를 위해 훈련셋 내부에서만 제한적 사용).
     * ③ 비용 민감 학습(Cost-Sensitive Learning): 모델 학습 시 소수 클래스 오분류에 더 큰 패널티를 부여 (`class_weight='balanced'`).
     * ④ 샘플 가중치(Sample Weight) 부여: 모든 거래일을 똑같은 1표로 취급하지 않고, 수익률 변동폭(|r|)이 큰 중요한 날이나
       다른 샘플과 레이블 계산 기간이 겹치지 않는 '고유성(Uniqueness)'이 높은 샘플에 더 큰 학습 가중치를 부여하여 과적합을 억제함.
"""
#%% [3. 미래 시점 정렬(shift(-1)), 임계값 레이블링, 클래스 균형 & 혼동행렬 평가 함수]

# 데이터 로드 (삼성전자 005930)
df = load_sql("""
    SELECT 날짜 AS Dates, 시가 AS Open, 고가 AS High, 저가 AS Low, 종가 AS Close, 거래량 AS Volume
    FROM kor_price
    WHERE 종목코드 = '005930' AND 날짜 >= '2014-01-01'
    ORDER BY 날짜 ASC
""")
df['Dates'] = pd.to_datetime(df['Dates'])
df = df.set_index('Dates').sort_index()

# 피처 생성
df['ret_1d'] = df['Close'].pct_change(1)
df['ma_gap'] = df['Close'] / df['Close'].rolling(20).mean() - 1
df['vol_ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()

# [핵심 1] 타겟 레이블링 & shift(-1)로 미래 시점 정렬
# 단순 > 0 대신 거래비용과 노이즈를 감안한 임계값(0.0005 = 0.05%) 적용 가능
threshold = 0.0005
df['next_ret'] = df['Close'].pct_change().shift(-1)
df['target'] = np.where(df['next_ret'] > threshold, 1, -1)

# [핵심 2] 샘플 가중치(Sample Weight): 수익률 변동폭이 큰 날(중요 사건)에 더 높은 학습 가중치 부여
df['sample_weight'] = df['next_ret'].abs() / df['next_ret'].abs().mean()
df = df.dropna()

# 클래스 비율 확인 (불균형이 심하면 정확도만 높게 나오는 착시 발생 주의)
up_ratio = (df['target'] == 1).mean()
print(f"\n[레이블 분포] 전체 데이터 {len(df):,}행 | 상승(1) 비율: {up_ratio:.2%}, 하락/보합(-1) 비율: {1-up_ratio:.2%}")

# [핵심 3] 시계열 분할 (shuffle=False 필수!)
feature_cols = ['ret_1d', 'ma_gap', 'vol_ratio']
X_train, X_test, y_train, y_test = train_test_split(
    df[feature_cols], df['target'], test_size=0.3, shuffle=False, random_state=3
)
print(f"Train 상승 비율: {(y_train == 1).mean():.2%} | Test 상승 비율: {(y_test == 1).mean():.2%}")

# [핵심 4] 혼동 행렬 및 종합 분류 지표 출력 함수
def get_confusion_matrix(y_true, pred, prob=None):
    """정확도(Accuracy) 외에 정밀도, 재현율, F1, ROC-AUC를 함께 평가"""
    confusion = confusion_matrix(y_true, pred)
    acc = accuracy_score(y_true, pred)
    prec = precision_score(y_true, pred, zero_division=0)
    rec = recall_score(y_true, pred, zero_division=0)
    f1 = f1_score(y_true, pred, zero_division=0)
    roc = roc_auc_score(y_true, prob if prob is not None else pred)
    print("confusion matrix:\n", confusion)
    print(f"accuracy:{acc:.4f}, precision:{prec:.4f}, recall:{rec:.4f}, F1:{f1:.4f}, ROC AUC score:{roc:.4f}")
    return {'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1, 'roc_auc': roc}
#%%
"""
[금융 머신러닝 백테스팅의 6대 편향과 실전 적용 필수 원칙]
머신러닝 모델이 테스트셋에서 높은 예측 정확도를 보였더라도, 실제 트레이딩 수익으로 연결하려면
백테스팅 과정에 숨어 있는 구조적 편향과 현실 시장의 마찰 비용을 철저히 통제해야 한다.

1. 백테스트 결과를 왜곡하는 6대 핵심 편향 및 함정:
   - ① 생존 편향 (Survivorship Bias):
     * 문제: 현재 시점에 거래소에 상장되어 살아남은 종목들(예: 현재 KOSPI 200 구성종목)만을 대상으로 과거 10년을 백테스트하는 오류.
     * 왜곡: 과거에 상장폐지·부도·관리종목 지정으로 큰 손실을 입혔던 기업들이 데이터에서 자동으로 빠져 있으므로,
       전략의 과거 수익률은 실제보다 과대평가되고 최대낙폭(MDD)은 과소평가됨.
     * 해결: 반드시 각 과거 시점(Point-in-Time)에 실제로 거래 가능했던 상장폐지 종목 포함 유니버스를 구축해야 함.

   - ② 사전 관찰 편향 (Look-ahead Bias / 미래 참조 편향):
     * 문제: 매수·매도 의사결정을 내리는 그 순간에는 물리적으로 알 수 없었던 미래의 정보가 입력 피처나 기준값에 섞여 들어가는 오류.
     * 대표적 실수 사례:
       (a) t일 장 마감 후 확정되는 '당일 종가(Close)'로 기술적 지표를 계산해 놓고, 매수 체결도 't일 종가'에 이루어졌다고 가정하는 경우
       (b) 기업 실적 발표일(공시일)이 아니라 회계 결산 기준일(예: 12월 31일)에 재무제표 수치가 이미 공개된 것처럼 매매하는 경우
       (c) 전체 기간(훈련+테스트) 데이터에 대해 먼저 StandardScaler 정규화나 PCA를 수행한 뒤 훈련/테스트를 나누어
           미래 테스트셋의 평균·분산 정보가 훈련셋에 스며드는 경우 (Data Leakage)
     * 해결: 모든 피처는 t일 장 마감 시점 확정치만 사용하고, 실제 체결은 최소 t+1일 시가(Open) 또는 t+1일 종가로 지연(Lag) 적용하며,
       스케일러는 반드시 훈련셋에서만 fit() 해야 함.

   - ③ 백테스트 과최적화 및 데이터 스누핑 편향 (Backtest Overfitting / Data Snooping):
     * 문제: 동일한 과거 데이터셋을 두고 수백 가지 피처 조합, 모델, 하이퍼파라미터를 반복 실험한 뒤
       가장 우상향 곡선이 예쁘게 나온 단 하나의 결과만 채택하는 행위(다중 검정 문제, Multiple Testing).
     * 왜곡: 1,000번 동전을 던지면 우연히 10번 연속 앞면이 나오는 동전이 하나쯤 생기듯, 과거 데이터의 우연한 노이즈에 딱 맞춘
       모델은 테스트 기간(Out-of-Sample)이나 실전 투입 즉시 처참하게 무너짐.
     * 해결: 파라미터 개수를 최소화(오컴의 면도날)하고, 검증셋(Validation)과 완전히 격리된 최종 테스트셋(Out-of-Sample)은
       단 한 번만 최종 확인용으로 사용하며, 전진 분석(Walk-Forward)으로 여러 시장 국면에서의 일관성을 검증해야 함.

   - ④ 거래비용, 슬리피지 및 시장 충격 무시 (Transaction Costs & Slippage):
     * 문제: 증권사 위탁수수료, 증권거래세(매도 시 부과), 매수·매도 호가 스프레드(Bid-Ask Spread)를 0으로 가정하는 오류.
     * 왜곡: 특히 일간 방향성을 예측해 매일 포지션을 사고파는 단기 머신러닝 전략은 매매 회전율(Turnover)이 극도로 높기 때문에,
       왕복 0.1~0.3%(10~30bp)의 거래비용만 반영해도 누적 수익률이 우상향에서 급격한 우하향으로 뒤집히는 경우가 허다함.
     * 추가 고려사항: 소형주나 호가가 얇은 종목에 큰 금액을 주문할 때 내 주문 때문에 가격이 밀려 불리하게 체결되는
       '슬리피지(Slippage) 및 시장 충격(Market Impact)'과 일평균 거래대금 대비 주문 한도(유동성 제약)도 반드시 반영해야 함.

   - ⑤ 심리적 인내 한계와 경로 리스크 (Psychological Tolerance & Path Risk):
     * 문제: 백테스트 결과표의 최종 연평균 수익률(CAGR)과 샤프 비율만 보고, 그 과정의 고통(Drawdown)을 간과하는 문제.
     * 실전 현실: 아무리 10년 장기 CAGR이 20%인 전략이라도 중간에 -45%의 최대낙폭(MDD)을 겪거나 벤치마크 대비 2~3년 연속
       부진한 횡보 구간(Underwater Period)을 만나면, 개인 투자자는 공포에 질려 전략을 포기하고 기관 펀드매니저는 고객 환매로
       전략이 강제 청산됨. 따라서 백테스트 단계에서 MDD, 회복 기간(Recovery Time), 월별/연도별 승률을 반드시 검증해야 함.

   - ⑥ 시장 국면 전환과 알파 소멸 (Regime Shift & Alpha Decay):
     * 문제: 과거 10년간의 저금리·양적완화 국면에서 학습된 패턴이 고금리·인플레이션 국면에서도 그대로 작동할 것이라 맹신하는 오류.
     * 실전 현실: 거시경제 체제가 바뀌면 자산 간 상관관계가 역전되고, 시장에 널리 알려진 머신러닝 패턴은 참여자들이 몰리면서
       수익률이 점차 사라짐(알파 소멸). 이를 막기 위해 최신 데이터를 반영해 모델을 주기적으로 재학습(Rolling Retraining)하고
       전략 성능 저하를 감지하는 모니터링 체계를 갖추어야 함.

2. 실전 퀀트 운용을 위한 3대 핵심 체크리스트:
   - ① 예측 정확도의 현실적 기준: 금융 방향성 예측에서 테스트 정확도가 54~56% 수준만 안정적으로 유지되어도 매우 훌륭한 알파 모델임.
     반대로 테스트 정확도가 56~60%를 훌쩍 넘어가면 기뻐하기 전에 '사전 관찰 편향(미래 데이터 누설)'이나 '과적합'을 가장 먼저 의심할 것.
   - ② 확률 기반 자금 관리: 모델의 단순 이진 예측(1/-1)만 쓰지 말고 예측 확률(predict_proba)의 강도에 따라 포지션 비중을 조절하고,
     변동성 타겟팅(Volatility Targeting)이나 손절 규칙을 결합해 꼬리 위험(Tail Risk)을 통제할 것.
   - ③ 포트폴리오 다각화 부품으로 활용: 단일 머신러닝 전략에 전체 자산을 올인하지 말고, 전통적 계량 팩터(밸류·모멘텀·퀄리티) 및
     이종 자산배분 전략과 결합하여 전체 포트폴리오의 샤프 비율을 높이고 MDD를 낮추는 핵심 엔진 중 하나로 운용할 것.
"""

#%% [4. 백테스트 3대 편향 통제 및 체결 시점·거래비용 반영 백테스트 엔진]
"""
[실전 백테스팅에서 반드시 경계해야 할 3대 편향]
1. 생존 편향(Survivorship Bias): 현재 상장 유지 중인 우량 종목만으로 과거를 백테스트하는 오류 (상장폐지 종목 포함 필요)
2. 사전 관찰 편향(Look-ahead Bias): 장 마감 후 확정되는 종가 피처를 이용해 '당일 종가'에 매수했다고 가정하는 오류
   → 현실적 체결 가정: t일 종가 피처로 예측 → t+1일 시가(Open) 진입 후 t+1일 종가(Close) 청산 또는 t+1일 종가 진입
3. 심리적 인내(Psychological Tolerance)와 MDD: 백테스트상 높은 CAGR이라도 중간에 -40% MDD를 겪으면 실전 운용 중단 발생

[머신러닝 전략 실전 운용 원칙]
- 테스트 정확도 54~56% 수준만 안정적으로 나와도 우수한 모델이며, 56%를 크게 넘기면 데이터 누설/과적합을 먼저 의심할 것
- 단일 ML 모델만 단독 운용하기보다 추세추종/모멘텀/자산배분 등 다른 전략과 결합해 포트폴리오 분산 효과를 극대화할 것
"""
#%% 
def run_realistic_backtest(
    df_bt: pd.DataFrame,
    signal_col: str,
    exec_mode: str = 'next_open_to_close',
    cost_bp: float = 0.001
) -> pd.DataFrame:
    """
    exec_mode:
      - 'next_open_to_close': t일 장마감 시그널 -> t+1일 시가 매수, t+1일 종가 청산 (단기 매매)
      - 'next_close_to_close': t일 장마감 시그널 -> t+1일 종가 기준 보유 유지 (포지션 변경 시에만 거래비용 발생)
    """
    res = df_bt.copy()
    sig = (res[signal_col] == 1).astype(int)  # 1: Long, 0: Cash

    if exec_mode == 'next_open_to_close':
        # 익일 시가 대비 익일 종가 수익률
        raw_ret = (res['Close'].shift(-1) - res['Open'].shift(-1)) / res['Open'].shift(-1)
        strat_ret = sig * (raw_ret - cost_bp)
    else:
        # 익일 종가 대비 그 다음날 종가 수익률 (리밸런싱 회전율만큼만 비용 차감)
        raw_ret = res['Close'].pct_change().shift(-1)
        turnover = sig.diff().abs().fillna(sig)
        strat_ret = sig * raw_ret - turnover * cost_bp

    res['strat_ret'] = strat_ret.fillna(0)
    res['bh_ret'] = res['Close'].pct_change().shift(-1).fillna(0)
    res['strat_cum'] = (1 + res['strat_ret']).cumprod()
    res['bh_cum'] = (1 + res['bh_ret']).cumprod()

    yrs = len(res) / 252
    cagr = res['strat_cum'].iloc[-1] ** (1 / yrs) - 1
    vol = res['strat_ret'].std() * np.sqrt(252)
    sharpe = (cagr - 0.03) / vol if vol > 0 else 0
    mdd = (res['strat_cum'] / res['strat_cum'].cummax() - 1).min()

    print(f"\n[백테스트 요약 ({exec_mode}, 비용 {cost_bp*100:.2f}%)]")
    print(f"CAGR: {cagr*100:.2f}% | 연변동성: {vol*100:.2f}% | 샤프비율: {sharpe:.2f} | MDD: {mdd*100:.2f}%")
    return res

# 이동평균 상회 시그널 예시로 백테스트 엔진 작동 검증
df['demo_sig'] = np.where(df['ma_gap'] > 0, 1, -1)
_ = run_realistic_backtest(df.loc[X_test.index], signal_col='demo_sig', exec_mode='next_close_to_close', cost_bp=0.001)