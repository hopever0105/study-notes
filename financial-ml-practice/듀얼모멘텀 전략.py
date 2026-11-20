
#%%
"""
[듀얼 모멘텀 전략]
모멘텀(momentum)'은 물질의 운동량이나 가속도를 의미하는 물리학 용어로, 
투자 분야에서는 주가가 한 방향성을 유지하려는 힘

상대 모멘텀 전략:  투자 자산 가운데 상대적으로 상승 추세가 강한 종목에 투자
절대 모멘텀 전략: 과거 시점 대비 현재 시점의 절대적 상승세를 평가
듀얼 모멘텀 전략: 상대 모멘텀 전략과 절대 모멘텀 전략을 결합

ex)
절대 모멘텀 전략: 최근 N개월간 수익률이 양수(positive)이면 매수하고 음수(negative)이면 공매도하는 전략

상대 모덴텀 전략
 X축이 종목 코드이고 Y축이 날짜인 2차원 행렬이 있다고 가정할 때,
 N개월 날짜 간격으로 종목별 수익률을 계산한다.
 N개월은 전략을 구성하는 사람의 인사이트를 반영하여 정할 수 있고, 
 여러 가지 매개변수(parameter)를 조절하면서 
 백테스팅 결과를 기반으로 유의미한 성과를 보이는 변수를 선정할 수도 있다.

[모멘텀 유형 분류]

                       ┌──────────────────── 상대 모멘텀 (가로 방향 비교: 종목 간 상대 순위) ───────────────────┐
                       ▼                                                                                   ▼
   CODE      AAPL       AMZN       BND        GDX        GLD        GM         MSFT       SLV        SPY        USO        WMT
Date
2010-01-29   0.897435   0.936595   1.011692   0.855490   0.985327   NaN        0.916501   0.922809   0.947506   0.970022   0.985244
2010-02-26   1.055789   0.996046   1.003909   1.023124   1.009448   NaN        1.013871   0.992374   1.015404   1.049976   1.007190
  │ (세로 방향:
  │  절대 모멘텀 - 과거 시점 대비 시계열 수익률)
  ▼
2012-02-29   1.110058   1.001252   1.001432   0.979491   0.999930   1.047706   1.049883   1.053902   1.034346   0.922191   1.004765[cite: 13]
"""
#%%

import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# SPY 데이터 다운로드 (Adj Close 유지를 위해 auto_adjust=False)
read_df = yf.download('SPY', start='1993-01-01', auto_adjust=False)

# 멀티인덱스 컬럼 해제 및 Date를 일반 문자열 컬럼으로 변환
if isinstance(read_df.columns, pd.MultiIndex):
    read_df.columns = read_df.columns.get_level_values(0)
read_df = read_df.reset_index()
read_df['Date'] = read_df['Date'].dt.strftime('%Y-%m-%d')
read_df.head()

#%%
"""
종가 데이터를 사용할 것이므로 전체 변수에서 종가 변수만 선택"""

price_df = read_df.loc[:, ['Date', 'Adj Close']].copy()
price_df.head()

#%%
"""
이 전략에서는 추가로 월말 데이터를 사용
"""

price_df['STD_YM'] = price_df['Date'].map(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').strftime('%Y-%m'))
price_df.head()

#%% 
# 월말 종가에 접근하는 데이터프레임
month_list = price_df['STD_YM'].unique()
month_last_df = pd.DataFrame()
for m in month_list:
    # 기준 연월에 맞는 인덱스의 마지막 날짜 row를 데이터프레임에 추가한다
    last_row = price_df.loc[[price_df[price_df['STD_YM'] == m].index[-1]], :]
    month_last_df = pd.concat([month_last_df, last_row])

month_last_df.set_index(['Date'], inplace=True)
month_last_df.head()

#%% [데이터 가공]
# 모멘텀 지수를 계산하기 위한 이전 시점의 데이터 가공


month_last_df['BF_1M_Adj Close'] = month_last_df.shift(1)['Adj Close']
month_last_df['BF_12M_Adj Close'] = month_last_df.shift(12)['Adj Close']
month_last_df.fillna(0, inplace=True)
month_last_df.head(15)

#%%
"""
[포지션 기록]
이제 모멘텀 지수를 계산해서 거래가 생길 때 포지션을 기록할 데이터프레임
"""

book = price_df.copy()
book.set_index(['Date'], inplace=True)
book['trade'] = ''
book.head()
#%%
# trading 부분.
ticker = 'SPY'
for x in month_last_df.index:
    signal = ''
    # 절대 모멘텀을 계산한다
    momentum_index = month_last_df.loc[x, 'BF_1M_Adj Close'] / month_last_df.loc[x, 'BF_12M_Adj Close'] - 1
    # 절대 모멘텀 지표 True / False를 판단한다
    flag = True if ((momentum_index > 0.0) and (momentum_index != np.inf) and (momentum_index != -np.inf)) \
        else False \
        and True
    if flag:
        signal = 'buy ' + ticker  # 절대 모멘텀 지표가 Positive이면 매수 후 보유
    print('날짜 : ', x, ' 모멘텀 인덱스 : ', momentum_index, 'flag : ', flag, 'signal : ', signal)
    book.loc[x:, 'trade'] = signal


#월별 인덱스를 순회하면서 12개월 전 종가 대비 1개월 전 종가 수익률이 얼마인지 계산
#계산된 수익률은 momentum_index 변수에 저장해 0 이상인지 확인하고, 
#0 이상이면 모멘텀 현상이 나타난 것으로 판단해 매수 신호가 발생
#이 부분을 flag 변수에 처리했는데, 추가로 다른 조건을 넣을 수 있다는 것을 보여주고자 and 조건을 걸고 True로 남겨놨다. 
#signal 변수에 저장된 매수 신호를 거래 장부 데이터프레임에 저장한다.

#월말 종가를 기준으로 매수/매도 신호를 계산하므로 
#최소 1개월 이상 해당 포지션을 유지한다. (reblancing 주기)
#포지션을 유지하는 기간은 개인마다 다르지만 보통 1개월을 유지하기도 한다. 

#%% 수익률 함수
def returns(book, ticker):
    # 손익 계산
    rtn = 1.0
    book['return'] = 1.0
    book['acc return'] = 1.0
    buy = 0.0
    sell = 0.0
    for i in book.index:
        if book.loc[i, 'trade'] == 'buy ' + ticker and book.shift(1).loc[i, 'trade'] == '':
            # long 진입
            buy = book.loc[i, 'Adj Close']
            print('진입일 : ', i, 'long 진입가격 : ', buy)
        elif book.loc[i, 'trade'] == 'buy ' + ticker and book.shift(1).loc[i, 'trade'] == 'buy ' + ticker:
            # 보유중
            current = book.loc[i, 'Adj Close']
            rtn = (current - buy) / buy + 1
            book.loc[i, 'return'] = rtn

        elif book.loc[i, 'trade'] == '' and book.shift(1).loc[i, 'trade'] == 'buy ' + ticker:
            # long 청산
            sell = book.loc[i, 'Adj Close']
            rtn = (sell - buy) / buy + 1  # 손익 계산
            book.loc[i, 'return'] = rtn
            print('청산일 : ', i, 'long 진입가격 : ', buy, ' | long 청산가격 : ', \
                  sell, ' | return:', round(rtn, 4))

        if book.loc[i, 'trade'] == '':  # 제로 포지션
            buy = 0.0
            sell = 0.0
            current = 0.0

    acc_rtn = 1.0
    for i in book.index:
        if book.loc[i, 'trade'] == '' and book.shift(1).loc[i, 'trade'] == 'buy ' + ticker:
            # long 청산 시
            rtn = book.loc[i, 'return']
            acc_rtn = acc_rtn * rtn  # 누적 수익률 계산
            book.loc[i:, 'acc return'] = acc_rtn

    print('Accumulated return :', round(acc_rtn, 4))
    return (round(acc_rtn, 4))


#평균 회귀 전략에서 다룬, 수익률을 계산하는 함수와의 차이점은
# for-loop 중간 elif 절에서 current 변수를 선언해 포지션별로
# 현재까지 수익률을 계산하는 로직이 추가된 점이다.

# --- 추가된 보유중 수익률 계산 로직 구조 ---
# elif book.loc[i, 'trade'] == '' and book.shift(1).loc[i, 'trade'] == 'buy ' + ticker:
#     # long 청산
#     sell = book.loc[i, 'Adj Close']
#     rtn = (sell - buy) / buy + 1  # 손익 계산
#     book.loc[i, 'return'] = rtn


returns(book, ticker)

#%%
"""
[절대 모멘텀 전략 전체 스크립트]
다음은 이 장에서 살펴본 절대 모멘텀 전략의 전체 스크립트다.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import datetime

read_df = yf.download('SPY', start='1993-01-01', auto_adjust=False)
if isinstance(read_df.columns, pd.MultiIndex):
    read_df.columns = read_df.columns.get_level_values(0)
read_df = read_df.reset_index()
read_df['Date'] = read_df['Date'].dt.strftime('%Y-%m-%d')

price_df = read_df.loc[:, ['Date', 'Adj Close']].copy()
price_df['STD_YM'] = price_df['Date'].map(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').strftime('%Y-%m'))
month_list = price_df['STD_YM'].unique()

month_last_df = pd.DataFrame()
for m in month_list:
    last_row = price_df.loc[[price_df[price_df['STD_YM'] == m].index[-1]], :]
    month_last_df = pd.concat([month_last_df, last_row])

month_last_df.set_index(['Date'], inplace=True)
month_last_df['BF_1M_Adj Close'] = month_last_df.shift(1)['Adj Close']
month_last_df['BF_12M_Adj Close'] = month_last_df.shift(12)['Adj Close']
month_last_df.fillna(0, inplace=True)

book = price_df.copy()
book.set_index(['Date'], inplace=True)
book['trade'] = ''
ticker = 'SPY'
for x in month_last_df.index:
    signal = ''
    momentum_index = month_last_df.loc[x, 'BF_1M_Adj Close'] / month_last_df.loc[x, 'BF_12M_Adj Close'] - 1
    flag = True if ((momentum_index > 0.0) and (momentum_index != np.inf) and (momentum_index != -np.inf)) \
        else False \
        and True
    if flag:
        signal = 'buy ' + ticker
    print('날짜 : ', x, ' 모멘텀 인덱스 : ', momentum_index, 'flag : ', flag, 'signal : ', signal)
    book.loc[x:, 'trade'] = signal

returns(book, ticker)

#%% 31개 종목 데이터 다운로드 및 절대 모멘텀 일괄 백테스트
import matplotlib.pyplot as plt

tickers = [
    'SPY',
    'AAPL', 'MSFT', 'NVDA', 'AMZN', 'SPCX', 'GOOGL', 'META', 'AVGO', 'TSLA', 'WMT',
    'AMD', 'MU', 'ASML', 'COST', 'PLTR', 'CSCO', 'INTC', 'AMAT', 'TXN', 'LRCX',
    'PANW', 'AMGN', 'NFLX', 'LIN', 'CRWD', 'GILD', 'PEP', 'SHOP', 'KLAC', 'ARM'
]

raw_31_df = yf.download(tickers, start='1993-01-01', auto_adjust=False)['Adj Close']

abs_results_list = []
abs_acc_dict = {}

for t in tickers:
    if t not in raw_31_df.columns:
        continue
    s_close = raw_31_df[t].dropna()
    if len(s_close) < 260:  # 최소 12개월 이상 데이터 필요
        continue

    t_df = pd.DataFrame({'Adj Close': s_close})
    t_df['STD_YM'] = t_df.index.strftime('%Y-%m')

    # 월말 종가 및 1개월 전 / 12개월 전 종가 계산
    m_last = t_df.groupby('STD_YM').last()
    m_last['BF_1M'] = m_last['Adj Close'].shift(1)
    m_last['BF_12M'] = m_last['Adj Close'].shift(12)
    m_last.fillna(0, inplace=True)

    # 절대 모멘텀 신호 생성 (1개월 전 / 12개월 전 - 1 > 0)
    mom_idx = (m_last['BF_1M'] / m_last['BF_12M']) - 1
    m_sig = np.where((mom_idx > 0.0) & (~np.isinf(mom_idx)), 'buy', '')
    sig_map = dict(zip(m_last.index, m_sig))

    # 월말 리밸런싱 신호를 일별 데이터에 매핑 (해당 월말 이후 다음 월말까지 유지)
    t_df['trade'] = ''
    m_end_dates = t_df.reset_index().groupby('STD_YM')['Date'].last()
    for ym, end_dt in m_end_dates.items():
        t_df.loc[end_dt:, 'trade'] = sig_map[ym]

    # 손익 및 누적 수익률 고속 계산 (책의 returns 로직과 100% 동일)
    closes = t_df['Adj Close'].to_numpy()
    trades = t_df['trade'].to_numpy()
    n_len = len(closes)

    buy_p = 0.0
    acc_rtn = 1.0
    acc_arr = np.ones(n_len)
    trade_cnt = 0
    win_cnt = 0

    for idx in range(n_len):
        prev_tr = trades[idx - 1] if idx > 0 else None
        curr_tr = trades[idx]

        if curr_tr == 'buy' and prev_tr == '':
            buy_p = closes[idx]
        elif curr_tr == '' and prev_tr == 'buy':
            sell_p = closes[idx]
            rtn = (sell_p - buy_p) / buy_p + 1
            acc_rtn *= rtn
            trade_cnt += 1
            if rtn > 1.0:
                win_cnt += 1

        if curr_tr == '':
            buy_p = 0.0

        acc_arr[idx] = acc_rtn

    win_rate = round((win_cnt / trade_cnt * 100), 2) if trade_cnt > 0 else 0.0
    abs_acc_dict[t] = pd.Series(acc_arr, index=t_df.index)
    abs_results_list.append({
        'Ticker': t,
        'Start_Date': t_df.index[0].strftime('%Y-%m-%d'),
        'Trades': trade_cnt,
        'Win_Rate(%)': win_rate,
        'Acc_Return': round(acc_rtn, 4),
        'Total_Return(%)': round((acc_rtn - 1) * 100, 2)
    })

abs_summary_df = pd.DataFrame(abs_results_list).sort_values(by='Acc_Return', ascending=False).reset_index(drop=True)
abs_summary_df.index = abs_summary_df.index + 1

print("\n=== [절대 모멘텀 전략 (12M)] 31개 종목 백테스트 성과 순위 ===")
print(abs_summary_df.to_string())

#%% 31개 종목 절대 모멘텀 누적 수익률 비교 그래프
abs_all_df = pd.DataFrame(abs_acc_dict)

plt.figure(figsize=(14, 7))
for col in abs_all_df.columns:
    if col != 'SPY':
        plt.plot(abs_all_df.index, abs_all_df[col], color='lightgray', linewidth=1, alpha=0.7)

if 'SPY' in abs_all_df.columns:
    plt.plot(abs_all_df.index, abs_all_df['SPY'], color='crimson', linewidth=2.5, label='SPY (Benchmark)')

top3_abs = [t for t in abs_summary_df['Ticker'].head(3) if t != 'SPY']
colors = ['royalblue', 'forestgreen', 'darkorange']
for idx, t in enumerate(top3_abs):
    plt.plot(abs_all_df.index, abs_all_df[t], color=colors[idx], linewidth=1.8, linestyle='--', label=f"{t} (Top {idx+1})")

plt.yscale('log')  # 장기 누적수익률 격차가 크므로 로그 스케일 적용
plt.title('Absolute Momentum Strategy (12M): SPY vs Nasdaq Top 30 (Log Scale)', fontsize=13)
plt.xlabel('Date')
plt.ylabel('Accumulated Return (Log Scale)')
plt.legend(loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()