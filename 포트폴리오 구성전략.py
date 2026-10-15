# riskfolio 포트폴리오 최적화
#%% 공통 import 및 DB 연결 설정
import os
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display
from sqlalchemy import create_engine

db_pw = os.environ['DB_PW']
engine_url = f'mysql+pymysql://root:{db_pw}@127.0.0.1:3306/stock_db'

#%% ETF 데이터 다운로드 후 DB 저장
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

#%% DB에서 불러오기
engine = create_engine(engine_url)
prices = pd.read_sql('select * from sample_etf;', con=engine,
                     index_col='Date', parse_dates=['Date'])
engine.dispose()

prices.tail()

#%% 수익률 계산
rets = prices.pct_change(1).dropna()
rets.tail().round(4)

#%% 상관관계 확인
plt.figure(figsize=(12, 10))
sns.heatmap(rets.corr().round(2), annot=True, annot_kws={"size": 16}, cmap='coolwarm')
plt.show()

#%% 최대샤프지수 포트폴리오
import riskfolio as rp

port = rp.Portfolio(returns=rets)

method_mu = 'hist'
method_cov = 'hist'

port.assets_stats(method_mu=method_mu, method_cov=method_cov)

model = 'Classic'
rm = 'MV'
obj = 'Sharpe'
hist = True
rf = 0
l = 0

w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)

round(w.T, 4)

#%% 효율적 투자선
points = 50
frontier = port.efficient_frontier(model=model,
                                   rm=rm,
                                   points=points,
                                   rf=rf,
                                   hist=hist)

frontier.T.head().round(4)

#%% 효율적 투자선 그래프
label = 'Max Risk Adjusted Return Portfolio'
mu = port.mu
cov = port.cov
returns = port.returns

ax = rp.plot_frontier(w_frontier=frontier,
                      mu=mu,
                      cov=cov,
                      returns=returns,
                      rm=rm,
                      rf=rf,
                      alpha=0.05,
                      cmap='viridis',
                      w=w,
                      label=label,
                      marker='*',
                      s=16,
                      c='r',
                      height=6,
                      width=10,
                      ax=None)

#%% 최소분산 포트폴리오
import riskfolio as rp

port = rp.Portfolio(returns=rets)
method_mu = 'hist'
method_cov = 'hist'
port.assets_stats(method_mu=method_mu, method_cov=method_cov)

model = 'Classic'
rm = 'MV'
obj = 'MinRisk'
hist = True
rf = 0
l = 0

w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)

round(w.T, 4)

#%% 최소분산 포트폴리오 - 비중 그래프
ax = rp.plot_bar(w=w, title='Portfolio', kind='h', ax=None)


#%% 최소 및 최대 투자비중 제약조건 - 유니버스
asset_classes = {
    'Asset':
    ['SPY', 'IEV', 'EWJ', 'EEM', 'TLT', 'IEF', 'IYR', 'RWX', 'GLD', 'DBC'],
    'Class': [
        'stock', 'stock', 'stock', 'stock', 'bond', 'bond', 'alternative',
        'alternative', 'alternative', 'alternative'
    ]
}

asset_classes = pd.DataFrame(asset_classes)
asset_classes

#%% 최소 및 최대 투자비중 제약조건 - constraints
constraints = {'Disabled': [False, False],
               'Type': ['All Assets', 'All Assets'],
               'Set': ['', ''],
               'Position': ['', ''],
               'Sign': ['>=', '<='],
               'Weight': [0.05, 0.2],
               'Type Relative': ['', ''],
               'Relative Set': ['', ''],
               'Relative': ['', ''],
               'Factor': ['', '']}

constraints = pd.DataFrame(constraints)
constraints

#%% 최소 및 최대 투자비중 제약조건 - 최적화
A, B = rp.assets_constraints(constraints, asset_classes)

port.ainequality = A
port.binequality = B

w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)

w.T

#%% 최소 및 최대 투자비중 제약조건 - 그래프
ax = rp.plot_bar(w=w, title='Portfolio', kind='h', ax=None)

#%% 각 종목별 제약조건
constraints = {
    'Disabled': [
        False, False, False, False, False, False, False, False, False, False,
        False, False, False, False, False, False, False, False, False, False
    ],
    'Type': [
        'Assets', 'Assets', 'Assets', 'Assets', 'Assets', 'Assets', 'Assets',
        'Assets', 'Assets', 'Assets', 'Assets', 'Assets', 'Assets', 'Assets',
        'Assets', 'Assets', 'Assets', 'Assets', 'Assets', 'Assets'
    ],
    'Set': [
        'Asset', 'Asset', 'Asset', 'Asset', 'Asset', 'Asset', 'Asset',
        'Asset', 'Asset', 'Asset', 'Asset', 'Asset', 'Asset', 'Asset',
        'Asset', 'Asset', 'Asset', 'Asset', 'Asset', 'Asset'
    ],
    'Position': [
        'SPY', 'IEV', 'EWJ', 'EEM', 'TLT', 'IEF', 'IYR', 'RWX', 'GLD', 'DBC',
        'SPY', 'IEV', 'EWJ', 'EEM', 'TLT', 'IEF', 'IYR', 'RWX', 'GLD', 'DBC'
    ],
    'Sign': [
        '>=', '>=', '>=', '>=', '>=', '>=', '>=', '>=', '>=', '>=', '<=', '<=',
        '<=', '<=', '<=', '<=', '<=', '<=', '<=', '<='
    ],
    'Weight': [
        0.10, 0.10, 0.05, 0.05, 0.10, 0.10, 0.05, 0.05, 0.03, 0.03, 0.25, 0.25,
        0.20, 0.20, 0.20, 0.20, 0.10, 0.10, 0.08, 0.08
    ],
    'Type Relative': [
        '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
        '', ''
    ],
    'Relative Set': [
        '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
        '', ''
    ],
    'Relative': [
        '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
        '', ''
    ],
    'Factor': [
        '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
        '', ''
    ]
}

constraints = pd.DataFrame(constraints)
display(constraints)

#%% 각 종목별 제약조건 - 최적화 및 그래프
A, B = rp.assets_constraints(constraints, asset_classes)

port.ainequality = A
port.binequality = B

w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)

w.T

#%% 제약조건에서 정한 정한 최소/최대 범위 안에 해가 들어오는지 확인한다.
ax = rp.plot_bar(w=w, title='Portfolio', kind='h', ax=None)

#%% 자산군별 비중
constraints = {
    'Disabled': [False, False, False, False, False, False, False, False],
    'Type': [
        'All Assets', 'All Assets', 'Classes', 'Classes', 'Classes', 'Classes',
        'Classes', 'Classes'
    ],
    'Set': ['', '', 'Class', 'Class', 'Class', 'Class', 'Class', 'Class'],
    'Position':
    ['', '', 'stock', 'bond', 'alternative', 'stock', 'bond', 'alternative'],
    'Sign': ['>=', '<=', '>=', '>=', '>=', '<=', '<=', '<='],
    'Weight': [0.03, 0.20, 0.40, 0.30, 0.10, 0.70, 0.50, 0.20],
    'Type Relative': ['', '', '', '', '', '', '', ''],
    'Relative Set': ['', '', '', '', '', '', '', ''],
    'Relative': ['', '', '', '', '', '', '', ''],
    'Factor': ['', '', '', '', '', '', '', '']
}

constraints = pd.DataFrame(constraints)
display(constraints)

#%% 자산군별 비중 - 최적화
A, B = rp.assets_constraints(constraints, asset_classes)

port.ainequality = A
port.binequality = B

w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)

w.T

#%% 자산군별 비중 - 제약조건 확인
w_concat = pd.concat([asset_classes.set_index('Asset'), w], axis=1)
w_concat.groupby(['Class']).sum().sort_values(['weights'], ascending=False)

#%% 위험균형 포트폴리오


import riskfolio as rp

port = rp.Portfolio(returns=rets)
method_mu = 'hist'
method_cov = 'hist'
port.assets_stats(method_mu=method_mu, method_cov=method_cov)

model = 'Classic'
rm = 'MV'
hist = True
rf = 0
b = None

w_rp = port.rp_optimization(model=model, rm=rm, rf=rf, b=b, hist=hist)

w_rp.T

#%% 위험균형 포트폴리오 - 위험기여도 확인
ax = rp.plot_risk_con(w_rp,
                      cov=port.cov,
                      returns=port.returns,
                      rm=rm,
                      rf=0,
                      alpha=0.01,
                      color="tab:blue",
                      height=6,
                      width=10,
                      ax=None)

#%% 위험예산 포트폴리오

import numpy as np

b = np.array([0.15, 0.15, 0.15, 0.15, 0.10, 0.10, 0.05, 0.05, 0.05, 0.05]).reshape(-1, 1)
print(b.shape, b.sum())

w_rp = port.rp_optimization(model=model, rm=rm, rf=rf, b=b, hist=hist)

w_rp.T

#%% 위험예산 포트폴리오 - 위험기여도 확인
ax = rp.plot_risk_con(w_rp,
                      cov=port.cov,
                      returns=port.returns,
                      rm=rm,
                      rf=0,
                      alpha=0.01,
                      color="tab:blue",
                      height=6,
                      width=10,
                      ax=None)
