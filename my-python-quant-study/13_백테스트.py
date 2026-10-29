# bt 패키지 백테스트: 자산배분, 추세추종, 평균회귀
#%% 설정: 데이터 수집 여부 + DB 연결
RUN_DOWNLOAD = False

import os
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, inspect

db_pw = os.environ['DB_PW']
engine_url = f'mysql+pymysql://root:{db_pw}@127.0.0.1:3306/stock_db'


#%% ETF 데이터 다운로드 후 DB 저장
if RUN_DOWNLOAD:
    import yfinance as yf

    tickers = [
        'SPY',
        'IEV',
        'EWJ',
        'EEM',
        'TLT',
        'IEF',
        'IYR',
        'RWX',
        'GLD',
        'DBC',
    ]

    all_data = {}
    for ticker in tickers:
        all_data[ticker] = yf.download(ticker, start='1993-01-22', auto_adjust=False)

    prices = pd.DataFrame(
        {tic: (data['Adj Close'].squeeze() if isinstance(data.columns, pd.MultiIndex)
               else data['Adj Close'])
         for tic, data in all_data.items()}
    )

    engine = create_engine(engine_url)
    prices.to_sql(name='sample_etf', con=engine, index=True, if_exists='replace')
    engine.dispose()


#%% 필요한 테이블 확인
engine = create_engine(engine_url)
need_tables = ['sample_etf']
exist_tables = inspect(engine).get_table_names()
missing = [t for t in need_tables if t not in exist_tables]
engine.dispose()

if missing:
    raise RuntimeError(f'DB에 없는 테이블: {missing} -> 위쪽 셀에서 RUN_DOWNLOAD = True 로 바꾸고 다시 실행하세요.')


#%% 데이터의 수집
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(engine_url)
price = pd.read_sql('select * from sample_etf;', con=engine,
                    index_col='Date', parse_dates=['Date'])
engine.dispose()

price.tail()


#%% 전략의 정의
import bt

strategy = bt.Strategy("Asset_EW", [
    bt.algos.SelectAll(),
    bt.algos.WeighEqually(),
    bt.algos.RunMonthly(),
    bt.algos.Rebalance()
])


#%% 전략의 백테스트
data = price.dropna()

backtest = bt.Backtest(strategy, data)

result = bt.run(backtest)


#%% . 결과에 대한 평가
result.prices


#%%
result.prices.to_returns()


#%%
import matplotlib.pyplot as plt

result.plot(figsize=(10, 6), legend=False)
plt.show()


#%%
result.get_security_weights().head()


#%% 종목별 투자 비중 그래프
from matplotlib import cm

ax = result.get_security_weights().plot.area(figsize=(10, 6),
                                             ylim=[0, 1],
                                             legend=False,
                                             colormap=cm.jet)
handles, labels = ax.get_legend_handles_labels()
plt.margins(0, 0)
plt.legend(reversed(handles),
           reversed(labels),
           loc='lower right',
           bbox_to_anchor=(1.15, 0))
plt.show()


#%% 성과지표 확인
result.display()


#%% 올웨더 백테스트
import bt
import matplotlib.pyplot as plt

data = price[['SPY', 'TLT', 'IEF', 'GLD', 'DBC']].dropna()

aw = bt.Strategy('All Weather', [
    bt.algos.SelectAll(),
    bt.algos.WeighSpecified(SPY=0.3, TLT=0.4, IEF=0.15, GLD=0.075, DBC=0.075),
    bt.algos.RunQuarterly(),
    bt.algos.Rebalance()
])
aw_backtest = bt.Backtest(aw, data)
aw_result = bt.run(aw_backtest)

aw_result.plot(figsize=(10, 6), title='All Weather', legend=False)
plt.show()


#%% 올웨더 투자비중 확인
from matplotlib import cm

ax = aw_result.get_security_weights().plot.area(figsize=(10, 6),
                                                ylim=[0, 1],
                                                legend=False,
                                                colormap=cm.jet)
handles, labels = ax.get_legend_handles_labels()
plt.margins(0, 0)
plt.legend(reversed(handles),
           reversed(labels),
           loc='lower right',
           bbox_to_anchor=(1.15, 0))
plt.show()


#%% 올웨더 주요 성과지표
aw_result.stats.loc[[
    'total_return', 'cagr', 'daily_vol', 'max_drawdown', 'calmar', 'daily_sharpe'
]]


#%% 동적 자산배분 백테스트
import bt
import matplotlib.pyplot as plt

data = price.dropna()

gdaa = bt.Strategy('GDAA', [
    bt.algos.SelectAll(),
    bt.algos.SelectMomentum(n=5, lookback=pd.DateOffset(years=1)),
    bt.algos.WeighERC(lookback=pd.DateOffset(years=1)),
    bt.algos.RunMonthly(),
    bt.algos.Rebalance()
])

gdaa_backtest = bt.Backtest(gdaa, data)
gdaa_result = bt.run(gdaa_backtest)

gdaa_result.plot(figsize=(10, 6),
                 title='Global Dynamic Asset Allocation',
                 legend=False)
plt.show()


#%% 거래 비용 고려하기
from matplotlib import cm

wt = gdaa_result.get_security_weights().reindex(columns=price.columns)
ax = wt.plot.area(figsize=(10, 6), ylim=[0, 1], legend=False, colormap=cm.jet)
handles, labels = ax.get_legend_handles_labels()
plt.margins(0, 0)
plt.legend(reversed(handles),
           reversed(labels),
           loc='lower right',
           bbox_to_anchor=(1.15, 0))
plt.show()


#%% 턴오버 확인
gdaa_backtest.turnover.plot(figsize=(10, 6), legend=False)
plt.show()


#%% 거래 비용을 반영한 백테스트
gdaa_backtest_net = bt.Backtest(gdaa,
                                data,
                                name='GDAA_net',
                                commissions=lambda q, p: abs(q) * p * 0.002)
gdaa_result = bt.run(gdaa_backtest, gdaa_backtest_net)


#%%
gdaa_result.prices.plot(figsize=(10, 6),
                        title='Global Dynamic Asset Allocation')
plt.show()


#%% 추세추종 전략 백테스트


import pandas_ta as ta

data = price[['SPY']].dropna()
sma = data.apply(lambda x: ta.sma(x, 200))


#%%
import bt

bt_sma = bt.Strategy('Timing', [
    bt.algos.SelectWhere(data > sma),
    bt.algos.WeighEqually(),
    bt.algos.Rebalance()
])

bt_sma_backtest = bt.Backtest(bt_sma, data)


#%% 비교용 매수 후 보유 전략
def buy_and_hold(data, name):

    bt_strategy = bt.Strategy(name, [
        bt.algos.SelectAll(),
        bt.algos.WeighEqually(),
        bt.algos.RunOnce(),
        bt.algos.Rebalance()
    ])

    return bt.Backtest(bt_strategy, data)


stock = buy_and_hold(data[['SPY']], name='stock')

bt_sma_result = bt.run(bt_sma_backtest, stock)


#%%
import matplotlib.pyplot as plt

bt_sma_result.prices.iloc[201:, ].rebase().plot(figsize=(10, 6))
plt.show()


#%% 낙폭(drawdown) 확인
bt_sma_result.prices.iloc[201:, ].rebase().to_drawdown_series().plot(
    figsize=(10, 6))
plt.show()


#%% 성과 비교
bt_sma_result.stats.loc[[
    'total_return', 'cagr', 'daily_vol', 'max_drawdown', 'calmar', 'daily_sharpe', 'daily_sortino'
]]


#%% 파라미터 최적화
import bt
import pandas_ta as ta

data = price[['SPY']].dropna()


def timing(price, n):

    sma = price.apply(lambda x: ta.sma(x, n))
    stragety = bt.Strategy(n, [
        bt.algos.SelectWhere(price > sma),
        bt.algos.WeighEqually(),
        bt.algos.Rebalance()
    ])

    backtest = bt.Backtest(stragety, price)

    return (backtest)


n_20 = timing(data, 20)
n_60 = timing(data, 60)
n_100 = timing(data, 100)
n_150 = timing(data, 150)
n_200 = timing(data, 200)
n_250 = timing(data, 250)

result = bt.run(n_20, n_60, n_100, n_150, n_200, n_250)


#%%
from matplotlib import cm

result.prices[250:].rebase().plot(figsize=(10, 6), colormap=cm.jet)
plt.show()


#%% 롱 숏 전략
import pandas_ta as ta

data = price[['SPY']]
SMA_200 = data.apply(lambda x: ta.sma(x, 200))
SMA_60 = data.apply(lambda x: ta.sma(x, 60))


#%% 롱 숏 신호 만들기
signal = SMA_200.copy()
signal[SMA_60 >= SMA_200] = 1
signal[SMA_60 < SMA_200] = -1
signal[signal.isnull()] = 0


#%% 주가 / 이동평균 / 신호 그래프
import matplotlib.pyplot as plt

bind = pd.concat([data, SMA_200, SMA_60, signal], axis=1)
bind.columns = ['SPY', 'SMA 200', 'SMA 60', 'signal']
bind.loc['2018':].plot(figsize=(10, 6), secondary_y=['signal'])
plt.show()


#%% 롱 숏 백테스트
import bt

strategy = bt.Strategy(
    'SMA_crossover',
    [bt.algos.SelectAll(),
     bt.algos.WeighTarget(signal),
     bt.algos.Rebalance()])
backtest = bt.Backtest(strategy, data)
result = bt.run(backtest)

result.plot(figsize=(10, 6))
plt.show()


#%% 월별, 연도별 수익률
result.display_monthly_returns()


#%% 년 구간 확인
pd.concat([bind, result.prices],
          axis=1).loc['2020'].plot(figsize=(10, 6),
                                   secondary_y=['signal'],
                                   alpha=0.8)
plt.show()


#%% RSI를 이용한 전략
import pandas_ta as ta

data = price[['SPY']]
spy_rsi = data.apply(lambda x: ta.rsi(x, 14))

signal = spy_rsi.copy()
signal[spy_rsi > 70] = -1
signal[spy_rsi < 30] = 1
signal[(spy_rsi <= 70) & (spy_rsi >= 30)] = 0
signal[signal.isnull()] = 0


#%% 주가와 RSI 그래프
from matplotlib import gridspec

fig = plt.subplots(figsize=(10, 6), sharex=True)
gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[2, 1])

ax1 = plt.subplot(gs[0])
ax1 = data['SPY'].plot()
ax1.set_xlabel('')
ax1.axes.xaxis.set_ticks([])

ax2 = plt.subplot(gs[1])
ax2 = spy_rsi['SPY'].plot(color='black', ylim=[0, 100])
ax2 = plt.axhline(y=30, color='red', linestyle='-')
ax2 = plt.axhline(y=70, color='red', linestyle='-')

plt.subplots_adjust(wspace=0, hspace=0)
plt.show()


#%% RSI 백테스트
import bt

strategy = bt.Strategy('RSI_MeanReversion',
                       [bt.algos.WeighTarget(signal),
                        bt.algos.Rebalance()])
backtest = bt.Backtest(strategy, data)
result = bt.run(backtest)

result.plot(figsize=(10, 6))
plt.show()


#%% RSI 성과지표
result.stats.loc[['total_return', 'cagr', 'daily_vol', 'max_drawdown', 'calmar', 'daily_sharpe']]


#%% 볼린저 밴드를 이용한 전략
band = ta.bbands(data['SPY'], length=20, std=2)

bb = pd.concat([band.iloc[:, 0:3], data['SPY']], axis=1)
bb.columns = ['Lower Band', 'Mid Band', 'Upper Band', 'SPY']


#%% 볼린저 밴드 신호
import numpy as np

signal = data.copy()
signal['SPY'] = np.nan

signal[bb['SPY'] > bb['Upper Band']] = -1
signal[bb['SPY'] < bb['Lower Band']] = 1
signal[signal.isnull()] = 0


#%% 볼린저 밴드 백테스트
strategy = bt.Strategy('BB',
                       [bt.algos.WeighTarget(signal),
                        bt.algos.Rebalance()])
backtest = bt.Backtest(strategy, data)
result = bt.run(backtest)

result.plot(figsize=(10, 6))
plt.show()


#%% 볼린저 밴드 성과지표
result.stats.loc[['total_return', 'cagr', 'daily_vol', 'max_drawdown', 'calmar', 'daily_sharpe']]
