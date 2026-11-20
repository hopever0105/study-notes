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
[파일 05] 비지도 학습 클러스터링 기반 종목 분류 및 분산 포트폴리오 전략
--------------------------------------------------------------------------------
1. 비지도 학습 군집화(K-Means · 계층적 군집) 원리 및 금융 포트폴리오 활용
2. 다종목 수익률 행렬 전치(.T) 및 정규화(Normalizer · StandardScaler)
3. 엘보 기법(Elbow Method) & 실루엣 계수를 통한 최적 군집 수 탐색
4. K-Means 종목 군집화 시각화 및 군집 대표 종목 기반 분산 포트폴리오 백테스트
================================================================================
"""

#%% [1. 공통 환경 설정 및 SQL DB 연결 헤더]
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine

from sklearn.preprocessing import Normalizer, StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

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

print("[05] 환경 설정 및 stock_db 연결 완료!")

#%% 
"""
[비지도 학습 클러스터링 기반 종목 분류 및 분산 포트폴리오 철학]
1. 예측(Prediction)에서 포트폴리오 조정(Portfolio Adjustment)으로의 관점 전환:
   - 주식 투자에서 누구나 수익률이 높을 종목만 고르고 싶지만, 어떤 자산이 오르고 내릴지 완벽히 확신하기는 불가능에 가까움.
   - 따라서 전문 투자자들은 "예측의 장인이라기보다는 포트폴리오 조정의 명인"이며, 리스크 분산을 위해 자산을 일정 기준으로 군집화함.
   - 특히 현대 주식시장은 기존 산업 분류(GICS 섹터: IT, 금융, 헬스케어 등) 간 수익률 동조화가 심해져 섹터별 분산만으로는
     차별화가 어려우므로, 변동성·수익률 패턴·재무제표 등 실제 데이터 움직임을 기준으로 군집화하는 머신러닝 클러스터링이 매우 유용함.

2. 대표 클러스터링 알고리즘 비교:
   - K-Means (평균 이동 군집화):
     * 사전에 군집 개수(K)를 지정하고, 각 군집의 중심점(Centroid)과 데이터 간 거리 제곱합(SSE, inertia_)이 최소가 되도록 반복 갱신.
     * 계산이 빠르고 직관적이지만 K를 직접 정해야 하며 이상치(Outlier)에 민감함.
   - 계층적 군집화 (Hierarchical Clustering):
     * K를 미리 정하지 않고 가장 가까운 종목 쌍부터 순차적으로 병합하며 나무 모양의 덴드로그램(Dendrogram)을 생성.
     * 자산배분(HRP: 계층적 리스크 패리티) 모델에서 공분산 행렬의 불안정성을 해결하는 핵심 도구로 활용됨.
   - DBSCAN (밀도 기반 군집화):
     * 데이터가 밀집된 영역을 하나의 군집으로 묶고, 어느 군집에도 속하지 않는 극단적 움직임 종목을 '노이즈(이상치)'로 자동 분리.

3. 금융 시계열 패턴과 도메인 인사이트 결합 (Bulkowski 차트 패턴 예시):
   - 주가 움직임에는 (a) 통합 패턴(Consolidation), (b) 손잡이가 달린 컵 모양 패턴(Cup with Handle),
     (c) 이중 바닥 패턴(Double Bottom), (d) 접시 패턴(Saucer) 등 다양한 시각적·구조적 패턴이 존재함.
   - 머신러닝 클러스터링은 사람이 직관적으로 파악하기 어려운 고차원 공간의 분포를 자동으로 군집화해 주지만,
     무작정 모든 데이터를 넣기보다는 '주가 움직임 패턴을 볼지, 변동성을 볼지, 재무제표·거래량을 볼지' 투자자의 독자적 인사이트를 반영해
     기준 변수를 설계해야 유의미한 군집이 도출됨.

4. 실무 전처리 핵심 및 로보어드바이저 활용:
   - 전처리 핵심: K-Means는 행(Row) 단위로 개체를 묶으므로 [날짜 × 종목] 행렬을 전치(.T)해 [종목 × 날짜]로 바꾸고,
     Normalizer()로 각 종목 벡터의 L2 Norm을 1로 정규화하여 가격 크기가 아닌 수익률 변화 패턴 중심으로 군집화함.
   - 포트폴리오 및 추천 서비스 응용: A군과 패턴이 상이한 B군의 종목을 상호 보완적 분산 자산으로 선별하거나 고객에게 추천하는 서비스에 활용 가능.
     (단, 실제 금융 상품/서비스로 출시하려면 상품 정의, 알고리즘 안정성, 규제 등에 대한 철저한 사전 검증이 필수적임.)
"""

#%% [2.  재현: 미국 주식 수익률 패턴 K-Means 클러스터링 (2017~2020)]
meta_us = load_sql("SELECT DISTINCT Symbol, Name, Sector FROM global_ticker WHERE country = 'United States' AND Sector IS NOT NULL")
avail_df = load_sql("""
    SELECT 티커, COUNT(*) AS cnt FROM us_price
    WHERE 날짜 >= '2017-01-01' AND 날짜 <= '2020-02-28'
    GROUP BY 티커 HAVING cnt >= 750 LIMIT 60
""")
tickers = avail_df['티커'].tolist()
meta_map = meta_us.drop_duplicates('Symbol').set_index('Symbol')
security = [meta_map.loc[t, 'Name'] if t in meta_map.index else t for t in tickers]
sector = [meta_map.loc[t, 'Sector'] if t in meta_map.index else 'Unknown' for t in tickers]

ticker_in = "', '".join(tickers)
raw_us = load_sql(f"""
    SELECT 날짜 AS Date, 티커, 수정종가 AS Adj_Close FROM us_price
    WHERE 티커 IN ('{ticker_in}') AND 날짜 >= '2017-01-01' AND 날짜 <= '2020-02-28'
    ORDER BY 날짜 ASC
""")
prices_df = raw_us.pivot(index='Date', columns='티커', values='Adj_Close').sort_index()

# 수익률 계산 및 전치(.T) -> [종목 x 날짜]
df = prices_df.pct_change().iloc[1:].T
row_mask = df.isnull().any(axis=1)
if row_mask.any():
    valid_t = df.index[~row_mask].tolist()
    df = df.loc[valid_t]
    idx_keep = [i for i, t in enumerate(tickers) if t in valid_t]
    tickers = [tickers[i] for i in idx_keep]
    security = [security[i] for i in idx_keep]
    sector = [sector[i] for i in idx_keep]

companies = list(df.index)

# Normalizer 정규화
normalize = Normalizer()
array_norm = normalize.fit_transform(df)
final_df = pd.DataFrame(array_norm, columns=df.columns, index=df.index)

# 엘보 기법(Elbow Method) 탐색
num_of_clusters = range(2, 12)
error = []
for k in num_of_clusters:
    km_tmp = KMeans(n_clusters=k, random_state=SEED, n_init=10).fit(final_df)
    error.append(km_tmp.inertia_ / 100)

table = pd.DataFrame({"Cluster_Numbers": num_of_clusters, "Error_Term": error})
plt.figure(figsize=(10, 4))
plt.plot(table.Cluster_Numbers, table.Error_Term, marker="D", color='red')
plt.xlabel('Number of Clusters')
plt.ylabel('SSE (inertia / 100)')
plt.title('[ 재현] K-Means 엘보 기법 (SSE 변화 추이)')
plt.tight_layout()
plt.show()

# 7개 클러스터 분류 및 결과 시각화
clusters = KMeans(n_clusters=7, random_state=SEED, n_init=10).fit(final_df)
labels = clusters.predict(final_df)

clustered_result = pd.DataFrame({'labels': labels, 'tickers': companies, 'full-name': security, 'sector': sector})
print("\n=== [ 재현] 미국 주식 7개 클러스터 분류 결과 (일부) ===")
print(clustered_result.sort_values('labels').head(15).to_string(index=False))

final_df['Cluster'] = clusters.labels_
plt.figure(figsize=(10, 4))
sns.countplot(x='Cluster', data=final_df, palette='magma')
plt.title('[ 재현] 클러스터별 종목 수 분포 (Cluster_count)')
plt.tight_layout()
plt.show()

# 클러스터 전체 종목 출력
cluster_0 = clustered_result[clustered_result['labels'] == 0]
print(f"\n=== 0번 클러스터 전체 종목 ({len(cluster_0)}개) ===")
print(cluster_0.to_string(index=False))
for cid, grp in clustered_result.groupby('labels'):
    print(f"\n=== 클러스터 {cid}번 ({len(grp)}개) ===")
    print(grp[['tickers', 'full-name', 'sector']].to_string(index=False))
#%% [3. 실전 확장: 국내 대형주 100종목 멀티팩터 군집화 & 분산 포트폴리오 백테스트]
def run_custom_kr_clustering(top_n: int = 100, n_clusters: int = 6):
    latest_dt = load_sql("SELECT MAX(기준일) AS dt FROM kor_ticker")['dt'].iloc[0]
    universe = load_sql(f"""
        SELECT 종목코드, 종목명, 시가총액 FROM kor_ticker
        WHERE 기준일 = '{latest_dt}' AND 종목구분 = '보통주' AND 시가총액 > 0
        ORDER BY 시가총액 DESC LIMIT {top_n}
    """)
    codes = universe['종목코드'].tolist()
    code_in = "', '".join(codes)

    sec_df = load_sql(f"SELECT CMP_CD AS 종목코드, SEC_NM_KOR AS 업종 FROM kor_sector WHERE CMP_CD IN ('{code_in}')").drop_duplicates('종목코드')
    universe = universe.merge(sec_df, on='종목코드', how='left')

    # 중복 제거하여 조회 (삼성전자 '005930'을 시장 대용 벤치마크로 활용)
    query_codes = list(dict.fromkeys(codes + ['005930']))
    query_in = "', '".join(query_codes)

    px_raw = load_sql(f"""
        SELECT 날짜, 종목코드, 종가 FROM kor_price
        WHERE 종목코드 IN ('{query_in}')
          AND 날짜 >= DATE_SUB((SELECT MAX(날짜) FROM kor_price WHERE 종목코드 = '005930'), INTERVAL 3 YEAR)
        ORDER BY 날짜 ASC
    """)
    px_piv = px_raw.pivot(index='날짜', columns='종목코드', values='종가').sort_index()
    valid_codes = [c for c in codes if c in px_piv.columns and px_piv[c].isna().mean() < 0.05]

    # 컬럼 중복 방지를 위해 dict.fromkeys 사용
    all_cols = list(dict.fromkeys(valid_codes + ['005930']))
    ret_df = px_piv[all_cols].ffill().dropna().pct_change().dropna()

    split = int(len(ret_df) * 0.7)
    ret_in, ret_out = ret_df[valid_codes].iloc[:split], ret_df[valid_codes].iloc[split:]
    mkt_in = ret_df['005930'].iloc[:split]

    # 수익·위험·시장베타·밸류에이션 멀티팩터 행렬 생성
    ann_ret = (1 + ret_in).prod() ** (252 / len(ret_in)) - 1
    ann_vol = ret_in.std() * np.sqrt(252)
    sharpe = (ann_ret - 0.03) / ann_vol.replace(0, np.nan)
    cum_in = (1 + ret_in).cumprod()
    mdd = (cum_in / cum_in.cummax() - 1).min()
    beta = ret_in.apply(lambda s: s.cov(mkt_in) / mkt_in.var())

    feat_mat = pd.DataFrame({'연수익률': ann_ret, '연변동성': ann_vol, '샤프비율': sharpe, 'MDD': mdd, '베타': beta}, index=valid_codes)

    val_df = load_sql(f"""
        SELECT v.종목코드, v.PBR, v.배당수익률 FROM kor_value_daily v
        INNER JOIN (SELECT 종목코드, MAX(날짜) AS max_dt FROM kor_value_daily WHERE 종목코드 IN ('{code_in}') GROUP BY 종목코드) l
        ON v.종목코드 = l.종목코드 AND v.날짜 = l.max_dt
    """).drop_duplicates('종목코드').set_index('종목코드')

    feat_mat = feat_mat.join(val_df[['PBR', '배당수익률']], how='left')
    feat_mat['PBR'] = pd.to_numeric(feat_mat['PBR'], errors='coerce').clip(0.1, 20)
    feat_mat['배당수익률'] = pd.to_numeric(feat_mat['배당수익률'], errors='coerce').fillna(0).clip(0, 15)
    feat_mat = feat_mat.fillna(feat_mat.median())

    X_scaled = StandardScaler().fit_transform(feat_mat)
    feat_mat['Cluster'] = KMeans(n_clusters=n_clusters, random_state=SEED, n_init=20).fit_predict(X_scaled)
    sil = silhouette_score(X_scaled, feat_mat['Cluster'])

    res_df = universe.set_index('종목코드').loc[feat_mat.index].join(feat_mat)
    selected = res_df.sort_values('샤프비율', ascending=False).groupby('Cluster').head(1)

    port_cluster = ret_out[selected.index].mean(axis=1)
    port_ew = ret_out.mean(axis=1)

    print(f"\n=== [실전 확장] 국내 대형주 {len(res_df)}종목 멀티팩터 군집화 (실루엣={sil:.3f}) ===")
    print(res_df.groupby('Cluster')[['연수익률', '연변동성', '샤프비율', '베타', 'PBR', '배당수익률']].mean().round(3).to_string())

    for label, r in [(f'클러스터 대표 {n_clusters}종목 분산 포트폴리오', port_cluster), ('전체 대형주 동일가중 벤치마크', port_ew)]:
        cum = (1 + r).cumprod()
        yrs = len(r) / 252
        cagr = cum.iloc[-1] ** (1 / yrs) - 1
        vol = r.std() * np.sqrt(252)
        print(f"• {label}: OOS수익={(cum.iloc[-1]-1)*100:.2f}%, CAGR={cagr*100:.2f}%, 샤프={(cagr-0.03)/vol:.2f}, MDD={(cum/cum.cummax()-1).min()*100:.2f}%")

run_custom_kr_clustering(top_n=100, n_clusters=6)