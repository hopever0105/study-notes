import yfinance as yf
import pandas as pd
import numpy as np

#%% 1. 데이터 다운로드 : 엑슨모빌(XOM) + 나스닥 시총 Top 30 (총 31개)
tickers = [
    'XOM', # 기존 분석 기준 종목 (엑슨모빌)
    'AAPL', 'MSFT', 'NVDA', 'AMZN', 'SPCX', 'GOOGL', 'META', 'AVGO', 'TSLA', 'WMT',
    'AMD', 'MU', 'ASML', 'COST', 'PLTR', 'CSCO', 'INTC', 'AMAT', 'TXN', 'LRCX',
    'PANW', 'AMGN', 'NFLX', 'LIN', 'CRWD', 'GILD', 'PEP', 'SHOP', 'KLAC', 'ARM'
]

# 1990-01-01부터 현재까지 수정종가(Close) 다운로드
raw_df = yf.download(tickers, start='1990-01-01', auto_adjust=True)
close_df = raw_df['Close']

#%% 2. 결측치 확인 (종목별 상장일이 다르므로 상장 전 데이터는 NaN으로 존재함)
print("=== 종목별 결측치(상장 전 기간 등) 개수 ===")
print(close_df.isnull().sum())
# 무한대(inf, -inf) 포함 행 확인
print(close_df[close_df.isin([np.inf, -np.inf]).any(axis=1)])

#%% 3. 전 종목 성과지표 일괄 계산 (다운로드 실패 종목 체크 추가)
base_date = '2011-01-03'
results = []
st_rtn_dict = {}
dd_dict = {}
failed_tickers = [] # 다운로드 실패 종목 기록

for ticker in tickers:
    # 컬럼에 아예 없거나 데이터가 2개 미만이면 실패 리스트에 기록
    if ticker not in close_df.columns:
        failed_tickers.append(ticker)
        continue
        
    price_df = close_df[[ticker]].dropna().copy()
    price_df.columns = ['Close']
    
    if len(price_df) < 2:
        failed_tickers.append(ticker)
        continue

    price_df['daily_rtn'] = price_df['Close'].pct_change()
    price_df['st_rtn'] = (1 + price_df['daily_rtn']).cumprod()
    st_rtn_dict[ticker] = price_df['st_rtn']
    final_st_rtn = price_df['st_rtn'].iloc[-1]

    if price_df.index[0] <= pd.to_datetime(base_date):
        valid_base_idx = price_df.loc[base_date:].index[0]
        tmp_df = price_df.loc[valid_base_idx:, ['st_rtn']] / price_df.loc[valid_base_idx, ['st_rtn']]
        base_rtn = tmp_df['st_rtn'].iloc[-1]
    else:
        base_rtn = np.nan

    CAGR = final_st_rtn ** (252.0 / len(price_df.index)) - 1

    historical_max = price_df['Close'].cummax()
    daily_drawdown = price_df['Close'] / historical_max - 1
    historical_dd = daily_drawdown.cummin()
    dd_dict[ticker] = historical_dd
    mdd = historical_dd.min()

    vari = np.std(price_df['daily_rtn']) * np.sqrt(252.0)
    sharpe = np.mean(price_df['daily_rtn']) / np.std(price_df['daily_rtn']) * np.sqrt(252.0)

    sharpe_eval = "우수(1 이상)" if sharpe >= 1.0 else "보통/미흡(1 미만)"
    mdd_eval = "상대적 안정" if mdd > -0.65 else "고위험(닷컴/금융위기 등 큰 낙폭 경험)"
    
    results.append({
        'Ticker': ticker,
        '상장(시작)일': price_df.index[0].strftime('%Y-%m-%d'),
        '전체누적(배수)': round(final_st_rtn, 2),
        f'{base_date}이후(배수)': round(base_rtn, 2) if not np.isnan(base_rtn) else np.nan,
        'CAGR(%)': round(CAGR * 100, 2),
        '샤프지수': round(sharpe, 3),
        '변동성(%)': round(vari * 100, 2),
        'MDD(%)': round(mdd * 100, 2),
        '자동진단요약': f"샤프 {sharpe_eval} / MDD {mdd_eval}"
    })

if failed_tickers:
    print(f"⚠️ 다운로드 누락/실패 종목: {failed_tickers}")
    #%% 일별 수익률 계산
    price_df['daily_rtn'] = price_df['Close'].pct_change()

    #%% 바이앤홀드 전략 누적 곱 계산 (pd.cumprod() 함수 이용)
    price_df['st_rtn'] = (1 + price_df['daily_rtn']).cumprod()
    st_rtn_dict[ticker] = price_df['st_rtn']
    
    # 최종 누적 수익률 배수 (예: XOM의 경우 1990년에 샀으면 약 45배 수익)
    final_st_rtn = price_df['st_rtn'].iloc[-1]

    #%% 다른 시점(2011-01-03) 기준으로 수익률 계산하기
    # 해당 기준일 이전에 상장된 종목만 계산 가능
    if price_df.index[0] <= pd.to_datetime(base_date):
        # 기준일 이후 첫 거래일 찾기 (휴장일 대비)
        valid_base_idx = price_df.loc[base_date:].index[0]
        tmp_df = price_df.loc[valid_base_idx:, ['st_rtn']] / price_df.loc[valid_base_idx, ['st_rtn']]
        base_rtn = tmp_df['st_rtn'].iloc[-1]
    else:
        base_rtn = np.nan  # 2011년 이후 상장 종목은 NaN 처리

    #%% 1. CAGR (연평균 복리 수익률)
    # 가지고 있는 데이터의 마지막 일자 기준 최종 누적 수익률의 누적 연도 제곱근 구하기
    # 일데이터인 바, 전체 데이터 기간은 252영업일로 계산한 것의 역수로 구하기
    # -1을 하면 수익률이 나옴
    CAGR = final_st_rtn ** (252.0 / len(price_df.index)) - 1
    print(CAGR)

    #%% 2. 최대낙폭 : MDD
    # 투자 기간에 고점부터 저점까지 떨어진 낙폭 중 최대값을 의미
    # 투자자의 고통을 측정, 낮을수록 좋다 : (최저점 - 최고점) / 최고점
    # 종가에 누적 최대값을 반환 (전체가 아닌 행별로 차례로 진행하며 누적값을 계산함)
    # 현재 종가에서 누적 최대값 대비 낙폭률 계산 후 cummin() 함수로 최대 하락률 계산
    historical_max = price_df['Close'].cummax()
    daily_drawdown = price_df['Close'] / historical_max - 1
    historical_dd = daily_drawdown.cummin()
    dd_dict[ticker] = historical_dd
    mdd = historical_dd.min()

    #%% 3. 변동성 (연율화 표준편차)
    vari = np.std(price_df['daily_rtn']) * np.sqrt(252.0)

    #%% 4. 샤프지수 : 위험 대비 수익성 지표 (사후적 샤프비율)
    # 보통 1이 넘으면 위험 대비 수익성이 좋은 기업으로 평가함
    sharpe = np.mean(price_df['daily_rtn']) / np.std(price_df['daily_rtn']) * np.sqrt(252.0)

    #%% 5. 결과 저장 및 기존 해석 기준에 맞춘 자동 코멘트 생성
    sharpe_eval = "우수(1 이상)" if sharpe >= 1.0 else "보통/미흡(1 미만)"
    mdd_eval = "상대적 안정" if mdd > -0.65 else "고위험(닷컴/금융위기 등 큰 낙폭 경험)"
    
    results.append({
        'Ticker': ticker,
        '상장(시작)일': price_df.index[0].strftime('%Y-%m-%d'),
        '전체누적(배수)': round(final_st_rtn, 2),
        f'{base_date}이후(배수)': round(base_rtn, 2) if not np.isnan(base_rtn) else np.nan,
        'CAGR(%)': round(CAGR * 100, 2),
        '샤프지수': round(sharpe, 3),
        '변동성(%)': round(vari * 100, 2),
        'MDD(%)': round(mdd * 100, 2),
        '자동진단요약': f"샤프 {sharpe_eval} / MDD {mdd_eval}"
    })

#%% 6. 최종 성과 분석 표 출력 (샤프지수 기준 내림차순 정렬)
summary_df = pd.DataFrame(results).set_index('Ticker')
summary_df_sorted = summary_df.sort_values(by='샤프지수', ascending=False)

print("\n=== [최종성과분석] 엑슨모빌(XOM) + 나스닥 Top 30 전체 비교표 ===")
print(summary_df_sorted.to_string())

#%% 7. 기준 종목(XOM) 및 특정 종목 상세 해석 출력
if 'XOM' in summary_df.index:
    xom = summary_df.loc['XOM']
    print(f"\n[기준 종목 XOM 상세 리포트]")
    print(f"엑슨모빌(XOM)은 복리수익률 {xom['CAGR(%)']}%로 성장했으며, 샤프지수는 {xom['샤프지수']}, "
          f"변동성은 {xom['변동성(%)']}%이고 MDD는 {abs(xom['MDD(%)'])}% 정도이다.")
    print("수익률 자체는 타 미국 기술주 대비 좋다고 보기는 어렵고 샤프지수도 보통 1이 넘으면 좋은 기업이라고 생각한다.")
    print("다만, 변동성 및 MDD가 기간 대비 타 자산군에 비해서 안정적인 편이다. (서브프라임 모기지, 닷컴버블, 코로나 모두 포함)")
else:
    print("\n⚠️ XOM 데이터가 누락되어 상세 리포트를 건너뜁니다. 1번 셀(yf.download)을 다시 실행해주세요.")
#%% 8. 시각화 : 누적 수익률(st_rtn) 및 최대낙폭(MDD) 차트
# 31개를 한 번에 그리면 겹치므로 XOM + 샤프지수 상위 4개 종목 비교 예시
target_tickers = ['XOM'] + summary_df_sorted.head(4).index.tolist()
target_tickers = list(dict.fromkeys(target_tickers)) # 중복 제거

# (1) 누적 수익률 차트 (격차가 크므로 로그 스케일 logy=True 적용)
pd.DataFrame({t: st_rtn_dict[t] for t in target_tickers}).plot(
    figsize=(16, 9), logy=True, title='Cumulative Return (st_rtn) - XOM vs Top Sharpe'
)

# (2) 최대낙폭(MDD) 추이 차트
pd.DataFrame({t: dd_dict[t] for t in target_tickers}).plot(
    figsize=(16, 9), title='Historical Drawdown (MDD) - XOM vs Top Sharpe'
)


#%% 9. 전체 종목 요약 + 엑슨모빌(XOM) 포지션 비교
import matplotlib.pyplot as plt

#%% 1. 전체 종목 순위표 계산 및 출력 (기존 summary_df 활용)
ranked_df = summary_df.sort_values(by='샤프지수', ascending=False).copy()
ranked_df['샤프_순위'] = range(1, len(ranked_df) + 1)
ranked_df['CAGR_순위'] = ranked_df['CAGR(%)'].rank(ascending=False).astype(int)
ranked_df['MDD_안정순위'] = ranked_df['MDD(%)'].rank(ascending=False).astype(int) # 낙폭이 작을수록(0에 가까울수록) 1위

# 보기 좋게 핵심 컬럼과 순위만 앞으로 배치해서 전체 출력
display_cols = ['샤프_순위', 'CAGR_순위', 'MDD_안정순위', '샤프지수', 'CAGR(%)', '변동성(%)', 'MDD(%)', '상장(시작)일']
print("=== [전체 31개 종목 순위표 (샤프지수 순)] ===")
print(ranked_df[display_cols].to_string())
#%% 2. 엑슨모빌(XOM) vs 전체 평균 / 중앙값 비교표
target_cols = ['CAGR(%)', '샤프지수', '변동성(%)', 'MDD(%)']
xom_stats = ranked_df.loc['XOM']

comp_df = pd.DataFrame({
    'ExxonMobil (XOM)': xom_stats[target_cols],
    '전체 종목 평균': ranked_df[target_cols].mean(),
    '전체 종목 중앙값': ranked_df[target_cols].median()
})

print(f"\n=== [XOM 포지션 분석] 총 {len(ranked_df)}개 중 샤프 {int(xom_stats['샤프_순위'])}위 / CAGR {int(xom_stats['CAGR_순위'])}위 ===")
print(comp_df.round(3))

#%% 3. 전체 누적 수익률 배경(회색) + XOM 하이라이트(빨간색) 차트 (2011-01-03 기준)
cum_rtn = pd.DataFrame(st_rtn_dict).loc[base_date:]
cum_rtn = cum_rtn.div(cum_rtn.bfill().iloc[0]) # 2011-01-03 시점을 1.0으로 통일

plt.figure(figsize=(14, 7))

for col in cum_rtn.columns:
    if col == 'XOM':
        continue
    plt.plot(cum_rtn.index, cum_rtn[col], color='lightgray', alpha=0.6, linewidth=1)

# 엑슨모빌 강조 및 나머지 평균선
plt.plot(cum_rtn.index, cum_rtn['XOM'], color='crimson', linewidth=2.5, label='ExxonMobil (XOM)')
plt.plot(cum_rtn.index, cum_rtn.drop(columns=['XOM']).mean(axis=1), color='navy', linestyle='--', linewidth=1.5, label='NASDAQ Top 30 Equal-Weight Avg')

plt.title(f'Cumulative Return: XOM vs NASDAQ Top 30 (Since {base_date})')
plt.yscale('log')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

#%% 4. 리스크-리턴 산점도 (변동성 vs CAGR)
plt.figure(figsize=(12, 7))

others = summary_df.drop('XOM')
plt.scatter(others['변동성(%)'], others['CAGR(%)'], color='steelblue', alpha=0.6, s=70, label='NASDAQ Top 30')
plt.scatter(summary_df.loc['XOM', '변동성(%)'], summary_df.loc['XOM', 'CAGR(%)'], color='crimson', s=180, zorder=5, label='ExxonMobil (XOM)')

for ticker, row in summary_df.iterrows():
    plt.annotate(ticker, (row['변동성(%)'], row['CAGR(%)']), fontsize=8.5, alpha=0.85)

plt.xlabel('Volatility (%)')
plt.ylabel('CAGR (%)')
plt.title('Risk-Return Profile: XOM vs NASDAQ Top 30')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
