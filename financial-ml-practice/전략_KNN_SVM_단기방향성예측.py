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
[파일 04] 거리·커널 기반 알고리즘(KNN · SVM) 단기 주가 방향성 예측 전략
--------------------------------------------------------------------------------
1. KNN과 SVM의 작동 원리, 피처 스케일링 필수 원칙 및 차원의 저주
2. 장중 변동폭(Open-Close, High-Low) 피처와 익일 시가-종가 방향성 타겟 생성
3. 이웃 수(k=1~14) 변화에 따른 과적합 곡선 탐색 및 누적 로그수익률·샤프 비율 산출
4. 정규화 파이프라인(StandardScaler) + 비율(%) 피처 기반 국내 ETF 실전 백테스트
================================================================================
"""

#%% [1. 공통 환경 설정 및 SQL DB 연결 헤더]
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, roc_auc_score

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

print("[04] 환경 설정 및 stock_db 연결 완료!")
#%%
"""
[거리·커널 기반 알고리즘: K-최근접 이웃(KNN)과 서포트 벡터 머신(SVM)]
1. K-최근접 이웃 (KNN, K-Nearest Neighbors):
   - 핵심 원리: "유사한 특성을 가진 데이터는 특성 공간에서 가까운 거리에 위치한다"는 가정하에,
     새로운 데이터가 들어오면 가장 가까운 k개 이웃(과거 국면)을 찾아 다수결(분류) 또는 평균(회귀)으로 예측
   - 비모수적(Non-parametric) 모델: 데이터 분포를 가정하지 않아 유연하지만, 충분한 데이터 샘플이 없으면 분산이 커짐
   - 거리 척도: 주로 유클리드 거리(Euclidean Distance) 또는 맨해튼 거리 사용
   - 하이퍼파라미터 k의 역할:
     * k가 너무 작으면(예: k=1): 훈련 데이터의 노이즈까지 완벽히 외워버리는 극심한 과적합 발생
     * k가 너무 크면: 결정 경계가 지나치게 단순해져 국소적 패턴을 놓치는 과소적합 발생

2. 서포트 벡터 머신 (SVM, Support Vector Machine):
   - 핵심 원리: 두 클래스를 구분하는 수많은 경계선(초평면) 중, 각 클래스의 가장 가까운 데이터 포인트(서포트 벡터)와의
     거리인 '마진(Margin)'을 최대화하는 결정 경계를 탐색 → 일반화 성능이 우수함
   - 커널 트릭(Kernel Trick): 직선으로 나눌 수 없는 비선형 금융 데이터를 고차원 공간으로 매핑하여 분리
     (Linear 커널, RBF[가우시안] 커널, Polynomial 커널 등)
   - 규제 파라미터 C: 오분류를 얼마나 허용할지 제어 (C가 크면 마진이 좁아지며 과적합 위험, 작으면 마진이 넓어짐)

3. KNN·SVM 금융 실전 적용 시 3대 필수 주의사항:
   - ① 피처 스케일링(StandardScaler / MinMaxScaler) 필수: 거래량(수백만)과 수익률(0.01)을 그대로 넣으면
     단위가 큰 변수가 거리와 마진을 독점하므로 반드시 정규화 수행
   - ② 차원의 저주(Curse of Dimensionality): 입력 피처가 많아질수록 데이터 간 거리가 모두 비슷해져 변별력이 급감하고
     연산 비용이 폭증하므로 핵심 피처만 엄선하거나 PCA 차원 축소 후 적용
   - ③ 추세(Trend)와 계절성 취약성: 주가 절대 레벨 차이(예: Open-Close)는 지수가 2배 오르면 거리도 2배 왜곡되므로
     비율(%) 피처나 추세 분해 데이터 사용 권장
"""


#%% [2. SPY 장중 변동 피처 기반 KNN 전략 (2012~2016)]
df = load_sql("""
    SELECT 날짜 AS Date, 고가 AS High, 저가 AS Low, 시가 AS Open, 종가 AS Close, 거래량 AS Volume
    FROM us_price
    WHERE 티커 = 'SPY' AND 날짜 >= '2012-01-01' AND 날짜 <= '2017-01-01'
    ORDER BY 날짜 ASC
""")
if df.empty:
    df = load_sql("""
        SELECT Date, High, Low, Open, Close, Volume
        FROM global_price
        WHERE ticker = 'SPY' AND Date >= '2012-01-01' AND Date <= '2017-01-01'
        ORDER BY Date ASC
    """)
df['Date'] = pd.to_datetime(df['Date'])
df = df.set_index('Date').dropna()

tmp_df = df[['Open', 'High', 'Low', 'Close']].copy()
tmp_df['Open-Close'] = tmp_df['Open'] - tmp_df['Close']
tmp_df['High-Low'] = tmp_df['High'] - tmp_df['Low']
tmp_df = tmp_df.dropna()

X = tmp_df[['Open-Close', 'High-Low']]
# 익일 시가 대비 익일 종가가 높으면 1(매수), 아니면 -1(매도)
Y = np.where(tmp_df['Close'].shift(-1) > tmp_df['Open'].shift(-1), 1, -1)

split = int(0.7 * len(tmp_df))
X_train, Y_train = X[:split], Y[:split]
X_test, Y_test = X[split:], Y[split:]

# k=1 ~ 14 탐색 및 과적합 곡선 시각화
train_acc, test_acc = [], []
for n in range(1, 15):
    clf = KNeighborsClassifier(n_jobs=-1, n_neighbors=n)
    clf.fit(X_train, Y_train)
    train_acc.append(clf.score(X_train, Y_train))
    test_acc.append((clf.predict(X_test) == Y_test).mean())

plt.figure(figsize=(10, 4))
plt.plot(range(1, 15), train_acc, label='TRAIN set')
plt.plot(range(1, 15), test_acc, label='TEST set')
plt.xlabel("n_neighbors")
plt.ylabel("accuracy")
plt.xticks(np.arange(0, 16, 1))
plt.title('[ 재현] KNN 이웃 수(k) 변화에 따른 훈련/테스트 정확도')
plt.legend()
plt.tight_layout()
plt.show()

# k=11 모델 학습 및 누적 로그수익률·샤프 비율 산출
knn = KNeighborsClassifier(n_neighbors=11)
knn.fit(X_train, Y_train)
print(f"[ 재현] 훈련 정확도: {accuracy_score(Y_train, knn.predict(X_train)):.2f} | 테스트 정확도: {accuracy_score(Y_test, knn.predict(X_test)):.2f}")

tmp_df['Predicted_Signal'] = knn.predict(X)
tmp_df['SPY_ret'] = np.log(tmp_df['Close'] / tmp_df['Close'].shift(1))
cum_spy_ret = tmp_df[split:]['SPY_ret'].cumsum() * 100

tmp_df['st_ret'] = tmp_df['SPY_ret'] * tmp_df['Predicted_Signal'].shift(1)
cum_st_ret = tmp_df[split:]['st_ret'].cumsum() * 100

sharpe = ((cum_st_ret - cum_spy_ret) / cum_st_ret.std()).mean()
print(f"Sharpe ratio ( 산식): {sharpe:.2f}")


#%% [3. 실전 확장: StandardScaler 파이프라인 + 비율 피처 기반 KNN & SVM 비교]
def run_custom_knn_svm_strategy(ticker: str = '005930', start_date: str = '2012-01-01', cost_bp: float = 0.001):
    kr = load_sql(f"""
        SELECT 날짜 AS Date, 시가 AS Open, 고가 AS High, 저가 AS Low, 종가 AS Close, 거래량 AS Volume
        FROM kor_price WHERE 종목코드 = '{ticker}' AND 날짜 >= '{start_date}' ORDER BY 날짜 ASC
    """)
    kr['Date'] = pd.to_datetime(kr['Date'])
    kr = kr.set_index('Date').sort_index()

    # 주가 레벨 변화에 강건한 비율(%) 피처 설계
    feat = pd.DataFrame(index=kr.index)
    feat['oc_ret'] = (kr['Close'] - kr['Open']) / kr['Open']
    feat['hl_range'] = (kr['High'] - kr['Low']) / kr['Open']
    feat['gap_ret'] = kr['Open'] / kr['Close'].shift(1) - 1
    feat['ret_5d'] = kr['Close'].pct_change(5)
    feat['vol_ratio'] = kr['Volume'] / kr['Volume'].rolling(20).mean().replace(0, np.nan)

    feat['next_oc_ret'] = (kr['Close'].shift(-1) - kr['Open'].shift(-1)) / kr['Open'].shift(-1)
    feat['target'] = (feat['next_oc_ret'] > 0).astype(int)
    feat = feat.dropna()

    f_cols = ['oc_ret', 'hl_range', 'gap_ret', 'ret_5d', 'vol_ratio']
    split = int(len(feat) * 0.7)
    X_tr, y_tr = feat[f_cols].iloc[:split], feat['target'].iloc[:split]
    X_te, y_te = feat[f_cols].iloc[split:], feat['target'].iloc[split:]
    oc_ret_te = feat['next_oc_ret'].iloc[split:]

    models = {
        'KNN (Scaled, k=15)': Pipeline([('scaler', StandardScaler()), ('clf', KNeighborsClassifier(n_neighbors=15, weights='distance', n_jobs=-1))]),
        'SVM (Scaled, RBF)': Pipeline([('scaler', StandardScaler()), ('clf', SVC(C=1.0, kernel='rbf', probability=True, random_state=SEED))])
    }

    rows = []
    for name, pipe in models.items():
        pipe.fit(X_tr, y_tr)
        prob = pipe.predict_proba(X_te)[:, 1]
        pred = (prob >= 0.5).astype(int)
        net_ret = pred * (oc_ret_te - cost_bp)
        cum = (1 + net_ret).cumprod()
        yrs = len(net_ret) / 252
        cagr = cum.iloc[-1] ** (1 / yrs) - 1
        vol = net_ret.std() * np.sqrt(252)
        rows.append({
            '모델': name, 'Accuracy': round(accuracy_score(y_te, pred), 4),
            'ROC-AUC': round(roc_auc_score(y_te, prob), 4),
            '진입비중(%)': round(pred.mean() * 100, 1),
            '순CAGR(%)': round(cagr * 100, 2),
            '연환산샤프': round((cagr - 0.03) / vol, 2) if vol > 0 else 0,
            'MDD(%)': round((cum / cum.cummax() - 1).min() * 100, 2)
        })
    print(f"\n--- [실전 확장] {ticker} 정규화 KNN vs SVM 장중 매매 검증 (비용 10bp 차감) ---")
    print(pd.DataFrame(rows).to_string(index=False))

run_custom_knn_svm_strategy(ticker='005930', start_date='2012-01-01', cost_bp=0.001)