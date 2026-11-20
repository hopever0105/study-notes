#%%
"""
[전통 퀀트 투자 전략]
퀀트(Quant) 투자를 달리 표현하면 데이터 기반(data-driven) 전략
머신러닝이나 딥러닝을 활용하는 투자 방법도 데이터 기반의 투자 전략 
1. 평균 회귀 전략
2. 듀얼 모멘텀 전략을 구현하기 위한 절대 및 상대 모멘텀 투자전략
3. 가치 투자 전략을 이용한 '마법공식'
"""

#%%
"""
[전통 퀀트 방법론 소개]

퀀트는 정량적(quantitative) 방법론을 기반으로 투자 의사를 결정하는 것이며,  모든 것을 수치화하는 것을 의미

머신러닝 관점에서는 입력 데이터(input data)가 매우 중

사용하는 데이터에 따라 주가를 사용해 기술 지표를 만들고 이를 투자에 활용하는 '기술 지표 투자 전략'

기업 재무제표를 사용하는 '가치 투자 전략'

기술 지표를 활용한 투자 전략은 퀀트에서 가장 많이 사용하는 전략이다. 

주가 데이터로 만든 지표(indicator)에만 의존해 투자 의사결정을 내리는 경우 사용하는 지표에는 주식시장에 대한 트레이더의 철학이 담겨있다고도 볼 수 있다.

ex)  

'올라가는 주식이 계속 오른다'고 믿는 트레이더들은 모멘텀 지표를 활용하는 전략을 선호

'올라간 주식은 반드시 내려온다(혹은 평균으로 회귀한다)'는 주가나 수익률의 평균 회귀(mean-reversion) 특성을 믿는 트레이더들은 평균 회귀 지표를 선호 

자주사용 지표 이동 평균선(moving average), 상대 강도 지수(relative strength index), 스토캐스틱 오실레이터(stochastic oscillator) 등


기술 지표를 활용한 퀀트 투자 전략 구현에서 관건은 주가 데이터를 활용해 기술 지표를 만드는 것이다. 
많은 파이썬 라이브러리에서 해당 기능을 제공
그다음에는 해당 지표들로 신호를 발생시켜 종목을 매매하고 전략의 수익률이나 승률(hit rate) 등을 살펴보기 
무릇 수익률이 초미의 관심사겠으나, 상승과 하락을 얼마나 정확하게 예측하는지도 전략 평가의 승패를 가르는 결정적 요소

게다가 샤프 비율 같은 지표를 우선시하는 투자자들도 있다. 
전략 평가는 전적으로 트레이더에 좌우됨. 


기술 지표를 활용한 퀀트 투자 방법
모멘텀 전략과 평균 회귀 전략은 상반된 개념
그럼에도 두 전략을 선별한 것은 두 전략의 상관관계가 낮고 전략이 초점을 맞추는 시간대(장, 단기)도 다름


가치 투자 전략
당기순이익, 영업이익, 영업이익률, 매출액, 부채비율, PER, PBR, PSR, PCR, ROE, ROA 등 기업의 가치 판단에 기준이 되는 재무제표 데이터를 기초
만약 자신이 CEO의 능력을 보고 투자하는 (조금은 극단적인) 가치 투자자라고 한다면,이 데이터를 정량화해 사용. 

ex) 
CEO 출신 대학의 랭킹별로 점수를 매기고 연령이나 직군별로 정량화해 점수를 주는 등

지표를 계산하는 작업보다 기준이 되는 데이터에서 순위(rank)를 매겨 분위별로 자르는 작업이 매우 중요 
전략 평가는 기술 지표를 활용한 퀀트 투자 방법과 유사하다.

"""

#%%
"""
[평균 회귀 전략]

평균으로의 회귀(regression to mean)란 많은 자료를 토대로 결과를 예측할 때 평균에 가까워지려는 경향
한번 평균보다 큰 값이 나오면 다음번에는 평균보다 작은 값이 나와 전체적으로는 평균 수준을 유지한다는 의미


주식시장에서도 평균 회귀 현상이 통용되는지 검증하려는 많은 시도
이 현상에 의하면, 가격이 평균보다 높아지면 다음번에는 평균보다 낮아질(혹은 평균이 될) 확률이 높다.
투자했을 때 투자 수익률이 낮았다면 그 후 수익률이 높은 기간이 이어진다는 의미로 해석할 수도 있다. 
일반화할 수는 없지만, 주가가 몇몇 종목에서는 별다른 이유 없이 일렁이는 파도처럼 올라갔다 내려가기를 되풀이하는 현상
마치 어느 적정 지점을 두고 주가의 등락이 반복되면서 평균 회귀 현상을 보이는 것과 같이 관찰된다.

이 방법은 단순 선형 회귀 문제와 비슷.
1개의 독립변수와 1개의 종속변수가 주어졌을 때 두 변수 관계를 잘 설명할 회귀 계수를 찾듯이, 
평균 회귀 전략도 특정 종목의 평균 가격에 수렴할 것이라고 가정

평균 회귀 속성을 이용한 전략
주가의 평균가격을 계산해 일정 범위를 유지하느냐 이탈하느냐에 따라 매매를 결정
현재 주가가 평균가격보다 낮으면 앞으로 주가가 상승할 것으로 기대해 주식을 매수
현재 주가가 평균가격보다 높으면 앞으로 주가가 하락할 것으로 예상해 주식을 매도. 
평균 회귀 속성을 계량화할 수 있는 보조지표인 볼린저 밴드(Bollinger band) 기법을 활용해 평균 회귀 전략을 세우기
어느 시점에 진입/청산하는지 직접 구현
"""

#%%
"""
[볼린저 밴드]

1980년대 존 볼린저(John A. Bollinger)에 의해 개발된 볼린저 밴드는 단순하면서도 강력한 지표
볼린저 밴드는 현재 주가가 상대적으로 높은지 낮은지를 판단할 때 사용하는 보조지표
볼린저 밴드는 3개 선으로 구성되는데, 중심선인 이동 평균(moving average)선, 상단선과 하단선을 구성하는 표준 편차(standard deviation) 밴드다.


[그림: 볼린저 밴드를 이용한 투자 전략]

                            [최적의 매도 시점]
                                   │
                [매도 시점 고려]    ▼     [전략적 매도 시점]
                      │         ╭──●──╮         │
                      ▼       ╭─╯     ╰─╮       ▼
                    ╭─●─╮   ╭─╯ · · · · ╰─●─╮         ┄┄┄ 밴드 상한선
                  ╭─╯   ╰─●─╯  ───────    ╰─╮
                 ╭╯     · ·  ╱         ╲    ╰─╮       ─── 20일 이동 평균선
   [매수 시점 고려]  ·      ╱           ╲     ╰─╮
  (중심선 상향 전환)       ╱   ▲         ╲      ╰─    ┄┄┄ 밴드 하한선
         │               ╱    │           ╲
         ▼              ╱  [적극 매수 시점]  ╲
  ┄┄╮  ╭─●─╮          ╱   (밴드의 상향 이탈)
  ──╰──╯   ╰─╮      ╱
  ┄┄╮ ╭──╮   ╰─●──╱
    ╰─╯  ╰───╯

볼린저 밴드를 사용하는 이유는 이동 평균선으로 추세를 관찰하고 상단선과 하단선으로 밴드 내에서 현재 가격의 상승과 하락폭을 정량적으로 계산가능. 
볼린저 밴드는 '추세'와 '변동성'을 분석해주어 기술 분석에서 활용도가 높움
평균 회귀 현상을 관찰하는 데도 매우 유용
보통 중심선을 이루는 이동 평균선을 계산할 땐 20일을 사용하고 상·하위 밴드는 20일 이동 평균선 ± 2 * 20일 이동 표준 편차(σ)를 사용한다.

- 상단 밴드 = 중간 밴드 + 2 * 20일 이동 표준 편차
- 중간 밴드 = 20일 이동 평균선
- 하단 밴드 = 중간 밴드 - 2 * 20일 이동 표준 편차

[볼린저 밴드 수식]
- 표준편차(σ) = sqrt( Σ(j=1 to N) (X_j - X̄)^2 / N )
- 평균(X̄)     = Σ(j=1 to N) X_j / N
- 상단 밴드   = X̄ + 2σ
- 중간 밴드   = X̄
- 하단 밴드   = X̄ - 2σ
"""


#%% 1. 데이터 다운로드 : 엑슨모빌(XOM) + 나스닥 시총 Top 30 (총 31개)
import yfinance as yf
import pandas as pd
import numpy as np

tickers = [
    'SPY', # 기존 분석 기준 종목 (엑슨모빌)
    'AAPL', 'MSFT', 'NVDA', 'AMZN', 'SPCX', 'GOOGL', 'META', 'AVGO', 'TSLA', 'WMT',
    'AMD', 'MU', 'ASML', 'COST', 'PLTR', 'CSCO', 'INTC', 'AMAT', 'TXN', 'LRCX',
    'PANW', 'AMGN', 'NFLX', 'LIN', 'CRWD', 'GILD', 'PEP', 'SHOP', 'KLAC', 'ARM'
]

# 1990-01-01부터 현재까지 수정종가(Close) 다운로드
df = yf.download(tickers, start='1993-01-01', auto_adjust=True)
close_df = raw_df['Close']

#%% 
df_1 = yf.download(tickers, start='1993-01-01', auto_adjust=True)

df_1 = df.xs('SPY', axis=1, level=1)

#%% 데이터프레임
df_1.describe()

#%% 데이터 가공
df_1 = df_1.reset_index()  # 인덱스에 있는 Date를 일반 컬럼으로 변환
price_df = df_1.loc[:, ['Date', 'Close']].copy()


#%%
price_df.set_index(['Date'], inplace=True)  # 'date' -> 'Date'로 수정
price_df.head()

#%% 볼리저밴드 만들기
# rolling 이용하기 
price_df['center'] = price_df['Close'].rolling(window=20).mean()
price_df.iloc[4020:4034]

# 'center' 는 20일 이동 평균선을 의미

#%% 상하단 밴드 만들기
price_df['ub'] = price_df['center']+ 2* price_df['Close'].rolling(window=20).std()
price_df.iloc[4020:4034]

price_df['lb'] = price_df['center'] - 2* price_df['Close'].rolling(window=20).std()
price_df.iloc[4020:4034]

#%% 볼리저 밴드 함수 만들기
n = 20 
sigma = 2

def bollinger_band(price_df, n, sigma):
    bb = price_df.copy()
    bb['center'] = bb['Close'].rolling(n).mean()  # 중앙 이동평균선
    bb['ub'] = bb['center'] + sigma * bb['Close'].rolling(n).std()  # price_df['center'] -> bb['center']로 수정
    bb['lb'] = bb['center'] - sigma * bb['Close'].rolling(n).std()  # price_df['center'] -> bb['center']로 수정
    return bb

#%% 전략성과 확인
base_date = '2008-12-01'
sample = bollinger.loc[base_date:]
sample.head()


#%% 거래내역 컬럼 만들기
book = sample[['Close']].copy()
book['trade'] = '' # 거래내역 컬럼
book.head()

#%% r거래내역 함수만들기
def create_trade_book(sample) : 
    book = sample[['Close']].copy()
    book['trade'] = ''
    return (book)



#%% 볼리저 밴드 활용 거래 전략
def tradings(sample, book):
    for i in sample.index:
        if sample.loc[i, 'Close'] > sample.loc[i, 'ub']:  # 상단 밴드 이탈시 동작 안함
            book.loc[i, 'trade'] = '' # 동작안함이란 제로포지션 이행 보유 포지션있으면 청산 
        elif sample.loc[i, 'lb'] > sample.loc[i, 'Close']:  # 하단 밴드 이탈시 매수
            if book.shift(1).loc[i, 'trade'] == 'buy':  # 이미 매수상태
                book.loc[i, 'trade'] = 'buy'  # 매수 상태 유지 매수 상태시 상태 유지, 제로 포지션 새 포지션 잡기
            else:
                book.loc[i, 'trade'] = 'buy'
        elif sample.loc[i, 'ub'] >= sample.loc[i, 'Close'] and sample.loc[i, 'Close'] >= sample.loc[i, 'lb']:  # 볼리저 밴드 안에 있는 경우 (smaple 수정)
            if book.shift(1).loc[i, 'trade'] == 'buy':
                book.loc[i, 'trade'] = 'buy'  # 매수상태 유지
            else:
                book.loc[i, 'trade'] = ''  # 동작안함
    return book

book = tradings(sample,book)
book.tail(10)


#%% 수익률 계산 
def returns(book):
    # 손익 계산
    rtn = 1.0
    book['return'] = 1.0  # 1 -> 1.0으로 수정 (소수점 수익률 저장을 위해 필수)
    buy = 0.0
    sell = 0.0
    for i in book.index:
        # long 진입
        if book.loc[i, 'trade'] == 'buy' and book.shift(1).loc[i, 'trade'] == '':
            buy = book.loc[i, 'Close']
            print('진입일 : ', i, 'long 진입가격 : ', buy)
        # long 청산
        elif book.loc[i, 'trade'] == '' and book.shift(1).loc[i, 'trade'] == 'buy':
            sell = book.loc[i, 'Close']
            rtn = (sell - buy) / buy + 1  # 손익 계산
            book.loc[i, 'return'] = rtn
            print('청산일 : ', i, 'long 진입가격 : ', buy, ' | long 청산가격 : ', \
                  sell, ' | return:', round(rtn, 4))

        if book.loc[i, 'trade'] == '':  # 제로 포지션
            buy = 0.0
            sell = 0.0

    acc_rtn = 1.0
    for i in book.index:
        rtn = book.loc[i, 'return']
        acc_rtn = acc_rtn * rtn  # 누적 수익률 계산
        book.loc[i, 'acc return'] = acc_rtn

    print('Accumulated return :', round(acc_rtn, 4))
    return (round(acc_rtn, 4))
#%%
"""수익률을 저장할 변수와 book 변수에 수익률 컬럼을 만든다.
 for-loop 문을 돌면서 포지션 여부에 따라 수익률을 계산해 데이터프레임에 저장하고, 
 최종적으로 누적 수익률을 계산"""

# 첫번째 for-loop 문
for i in book.index:
     # long 진입
     if book.loc[i, 'trade'] == 'buy' and book.shift(1).loc[i, 'trade'] == '':
         buy = book.loc[i, 'Close']
         print('진입일 : ', i, 'long 진입가격 : ', buy)
    # long 청산
     elif book.loc[i, 'trade'] == '' and book.shift(1).loc[i, 'trade'] == 'buy':
         sell = book.loc[i, 'Close']
         rtn = (sell - buy) / buy + 1 # 손익 계산
         book.loc[i, 'return'] = rtn
         print('청산일 : ', i, 'long 진입가격 : ', buy, ' | long 청산가격 : ', \
               sell, ' | return:', round(rtn, 4))

     if book.loc[i, 'trade'] == '': # 제로 포지션
         buy = 0.0
         sell = 0.0

# 날짜별로 매수 신호가 있을 때 롱 포지션 진입
# if 조건문이 걸려있으며 매수 금액을 저장한다. 
# elif 문에 롱 포지션 청산 조건을 확인한다. 
#청산 조건이 참(True)일 때 매도 금액을 가져와 수익률을 계산하고 수익률 컬럼에 저장
# 그리고 포지션이 정리되면 매수, 매도 금액을 저장하는 변수값을 초기화한다.

#%% 누적 수익률을 계산
acc_rtn = 1.0 
for i in book.index:
     rtn = book.loc[i, 'return']
     acc_rtn = acc_rtn * rtn # 누적 수익률 계산
     book.loc[i, 'acc return'] = acc_rtn



print(returns(book))

# 완성된 returns() 함수를 수행하면, 전체 포지션 보유건별 수익률과 최종 누적 수익률을 확인


#%% 백테스트 그래프
import matplotlib.pylab as plt
book['acc return'].plot()




#%% 전체 종목 백테스트 실행
import io
import contextlib
import matplotlib.pyplot as plt

close_df = df['Close']  # 위에서 다운받은 df에서 전체 종목 종가 바로 추출
n = 20
sigma = 2
base_date = '2008-12-01'

results_list = []
acc_rtn_dict = {}

for ticker in tickers:
    if ticker not in close_df.columns:
        continue

    t_price_df = close_df[[ticker]].dropna().copy()
    t_price_df.columns = ['Close']

    if len(t_price_df) <= n:
        continue

    # 1) 볼린저 밴드 계산
    t_price_df['center'] = t_price_df['Close'].rolling(n).mean()
    t_price_df['ub'] = t_price_df['center'] + sigma * t_price_df['Close'].rolling(n).std()
    t_price_df['lb'] = t_price_df['center'] - sigma * t_price_df['Close'].rolling(n).std()

    t_sample = t_price_df.loc[base_date:].copy()
    if t_sample.empty:
        continue

    # 2) 위쪽에 정의된 기존 함수 그대로 사용 (거래 로그 출력만 잠시 숨김)
    t_book = create_trade_book(t_sample)
    t_book = tradings(t_sample, t_book)
    with contextlib.redirect_stdout(io.StringIO()):
        final_acc_rtn = returns(t_book)

    # 3) 매매 횟수 및 승률 집계
    trade_count = (t_book['return'] != 1.0).sum()
    win_count = (t_book['return'] > 1.0).sum()
    win_rate = round((win_count / trade_count * 100), 2) if trade_count > 0 else 0.0

    acc_rtn_dict[ticker] = t_book['acc return']
    results_list.append({
        'Ticker': ticker,
        'Start_Date': t_sample.index[0].strftime('%Y-%m-%d'),
        'Trades': trade_count,
        'Win_Rate(%)': win_rate,
        'Acc_Return': final_acc_rtn,
        'Total_Return(%)': round((final_acc_rtn - 1) * 100, 2)
    })

#%% 전체 종목 고속 백테스트 실행
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

close_df = df['Close']
n = 20
sigma = 2
base_date = '2008-12-01'

results_list = []
acc_rtn_dict = {}

for ticker in tickers:
    if ticker not in close_df.columns:
        continue

    t_price_df = close_df[[ticker]].dropna().copy()
    t_price_df.columns = ['Close']

    if len(t_price_df) <= n:
        continue

    # 1) 볼린저 밴드 계산
    t_price_df['center'] = t_price_df['Close'].rolling(n).mean()
    t_price_df['ub'] = t_price_df['center'] + sigma * t_price_df['Close'].rolling(n).std()
    t_price_df['lb'] = t_price_df['center'] - sigma * t_price_df['Close'].rolling(n).std()

    t_sample = t_price_df.loc[base_date:]
    if t_sample.empty:
        continue

    # 2) 고속 연산을 위해 배열(NumPy)로 추출
    close_arr = t_sample['Close'].to_numpy()
    ub_arr = t_sample['ub'].to_numpy()
    lb_arr = t_sample['lb'].to_numpy()
    m = len(close_arr)

    trade_arr = [''] * m
    rtn_arr = np.ones(m)
    acc_arr = np.ones(m)

    # 3) 매매 신호 생성 (tradings와 동일 로직)
    prev_trade = None
    for idx in range(m):
        c, u, l = close_arr[idx], ub_arr[idx], lb_arr[idx]
        if c > u:
            curr = ''
        elif l > c:
            curr = 'buy'
        elif u >= c and c >= l:
            curr = 'buy' if prev_trade == 'buy' else ''
        else:
            curr = ''
        trade_arr[idx] = curr
        prev_trade = curr

    # 4) 수익률 및 누적수익률 계산 (returns와 동일 로직)
    buy, sell, acc_rtn = 0.0, 0.0, 1.0
    prev_trade = None
    for idx in range(m):
        curr = trade_arr[idx]
        if curr == 'buy' and prev_trade == '':
            buy = close_arr[idx]
        elif curr == '' and prev_trade == 'buy':
            sell = close_arr[idx]
            rtn = (sell - buy) / buy + 1
            rtn_arr[idx] = rtn

        if curr == '':
            buy, sell = 0.0, 0.0

        acc_rtn *= rtn_arr[idx]
        acc_arr[idx] = acc_rtn
        prev_trade = curr

    # 5) 결과 집계
    final_acc_rtn = round(acc_rtn, 4)
    trade_count = int((rtn_arr != 1.0).sum())
    win_count = int((rtn_arr > 1.0).sum())
    win_rate = round((win_count / trade_count * 100), 2) if trade_count > 0 else 0.0

    acc_rtn_dict[ticker] = pd.Series(acc_arr, index=t_sample.index)
    results_list.append({
        'Ticker': ticker,
        'Start_Date': t_sample.index[0].strftime('%Y-%m-%d'),
        'Trades': trade_count,
        'Win_Rate(%)': win_rate,
        'Acc_Return': final_acc_rtn,
        'Total_Return(%)': round((final_acc_rtn - 1) * 100, 2)
    })

#%% 전체 종목 성과 순위표 출력
summary_df = pd.DataFrame(results_list).sort_values(by='Acc_Return', ascending=False).reset_index(drop=True)
summary_df.index = summary_df.index + 1

print("\n=== [볼린저 밴드 평균 회귀 전략] 전체 종목 백테스트 성과 순위 ===")
print(summary_df.to_string())

#%% 전체 종목 누적 수익률 비교 그래프
all_acc_df = pd.DataFrame(acc_rtn_dict)

plt.figure(figsize=(14, 7))

for col in all_acc_df.columns:
    if col != 'SPY':
        plt.plot(all_acc_df.index, all_acc_df[col], color='lightgray', linewidth=1, alpha=0.7)

if 'SPY' in all_acc_df.columns:
    plt.plot(all_acc_df.index, all_acc_df['SPY'], color='crimson', linewidth=2.5, label='SPY (Benchmark)')

top3_tickers = [t for t in summary_df['Ticker'].head(3) if t != 'SPY']
colors = ['royalblue', 'forestgreen', 'darkorange']
for idx, t in enumerate(top3_tickers):
    plt.plot(all_acc_df.index, all_acc_df[t], color=colors[idx], linewidth=1.8, linestyle='--', label=f"{t} (Top {idx+1})")

plt.title(f'Bollinger Band Mean-Reversion Strategy: SPY vs Nasdaq Top 30 (Since {base_date})', fontsize=13)
plt.xlabel('Date')
plt.ylabel('Accumulated Return (Multiple)')
plt.legend(loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
