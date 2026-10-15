# 이동평균, RSI, 볼린저 밴드 계산
#%% 단순 이동평균 - 데이터 다운로드
import yfinance as yf
import pandas as pd

stock_data = yf.download('^GSPC', start='2015-01-01', auto_adjust=False)
print(len(stock_data))

#%% 최신 yfinance 는 컬럼이 (항목, 티커) MultiIndex 로 나온다.
if isinstance(stock_data.columns, pd.MultiIndex):
    stock_data.columns = stock_data.columns.droplevel(1)

stock_data = stock_data.tail(500)
print(len(stock_data))


#%% 단순 이동평균 - 계산 및 그래프
import pandas_ta as ta
import matplotlib.pyplot as plt

stock_data['SMA_20'] = ta.sma(stock_data['Close'],
                              length=20)
stock_data['SMA_60'] = ta.sma(stock_data['Close'],
                              length=60)

stock_data[['Close', 'SMA_20', 'SMA_60']].plot(figsize=(10, 6))
plt.show()

#%% 지수 이동평균
stock_data['EMA_60'] = ta.ema(stock_data['Close'], 60)
stock_data[['Close', 'SMA_60', 'EMA_60']].plot(figsize=(10, 6))
plt.show()

#%% 상대강도지수 계산 및 그래프
from matplotlib import gridspec

stock_data['RSI_14'] = ta.rsi(stock_data['Close'], length=14)
stock_data.loc[:, 'RSI_14'] = stock_data['RSI_14'].fillna(0)

fig = plt.figure(figsize=(10, 6))
gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[2, 1])

ax1 = plt.subplot(gs[0])
ax1 = stock_data['Close'].plot()
ax1.set_xlabel('')
ax1.axes.xaxis.set_ticks([])

ax2 = plt.subplot(gs[1])
ax2 = stock_data['RSI_14'].plot(color='black', ylim=[0, 100])
ax2.axhline(y=70, color='r', linestyle='-')
ax2.axhline(y=30, color='r', linestyle='-')
ax2.set_xlabel('Date')

plt.subplots_adjust(wspace=0, hspace=0)

plt.show()

#%% 볼린저 밴드 계산 및 그래프
import pandas as pd

band = ta.bbands(stock_data["Close"], length=20, std=2)

print(band.columns)

bb = pd.concat([band.iloc[:, 0:3],
                stock_data['Close']], axis=1)
bb.columns = ['Lower Band', 'Mid Band', 'Upper Band', 'Close']

bb.plot(figsize=(10, 6),
        color={
            'Upper Band': 'red',
            'Lower Band': 'blue',
            'Mid Band': 'green',
            'Close': 'black'
        })
plt.show()
