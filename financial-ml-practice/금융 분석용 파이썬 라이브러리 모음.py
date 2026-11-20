#%%

# 금융 분석용 파이썬 라이브러리 모음

#%%
# ==========================================
# 0. 목록
# ==========================================
# 1. statsmodels              : 회귀분석·통계검정
# 2. matplotlib / seaborn     : 기본 시각화
# 3. plotly                   : 마우스로 움직이는 인터랙티브 차트 (캔들차트)
# 4. BeautifulSoup            : HTML 파싱 (정적 크롤링)
# 5. Selenium                 : 브라우저 조작 (동적 크롤링)
# 6. TA-Lib                   : 기술적 지표 150여 개
# 7. QuantEcon                : 마르코프 체인 등 계량경제 모델링
# 8. 거래소 캘린더             : 휴장일·개장 시간 (pandas_market_calendars, exchange_calendars)
#
# 설치 (Anaconda Prompt, ta_env)
#   pip install statsmodels matplotlib seaborn plotly
#   pip install beautifulsoup4 lxml html5lib selenium
#   pip install TA-Lib quantecon
#   pip install pandas-market-calendars exchange-calendars

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

#%%
# ==========================================
# 1. statsmodels : 회귀분석
# ==========================================
# scipy.stats가 "검정 하나"를 해 준다면, statsmodels는 회귀표(계수·t값·p값·R²)까지 한 번에 보여준다.
import statsmodels.api as sm
import statsmodels.formula.api as smf

# (1) 예제 데이터 : 19세기 프랑스 지역별 통계 (R 데이터셋을 인터넷에서 받아옴)
dat = sm.datasets.get_rdataset('Guerry', 'HistData').data

# 수식 문법: '종속변수 ~ 독립변수1 + 독립변수2', 함수도 바로 넣을 수 있음(np.log)
results = smf.ols('Lottery ~ Literacy + np.log(Pop1831)', data=dat).fit()
print(results.summary())

#%%
# (2) 금융 예 : 종목 수익률을 시장 수익률로 회귀 -> 베타(시장 민감도) 구하기
#   r_종목 = 알파 + 베타 x r_시장 + 오차
#   베타 1.3 = 시장이 1% 오를 때 평균 1.3% 오름
import yfinance as yf

px = yf.download(['AAPL', 'SPY'], start='2021-01-01', end='2025-12-31',
                 auto_adjust=True, progress=False)['Close']
ret = px.pct_change().dropna()
ret.columns = ['AAPL', 'SPY']

beta_model = smf.ols('AAPL ~ SPY', data=ret).fit()
print(beta_model.params)          # Intercept = 일별 알파, SPY = 베타
print('R² : {:.3f}'.format(beta_model.rsquared))

#%%
# ==========================================
# 2. matplotlib / seaborn : 기본 시각화
# ==========================================
# matplotlib : 선·막대·산점도 등 모든 그림의 바탕 (세밀하게 손볼 수 있음)
# seaborn    : matplotlib 위에 통계 그림(분포·히트맵)을 쉽게
import seaborn as sns

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].plot((1 + ret).cumprod())
axes[0].set_title('누적 수익 (시작 = 1)')
axes[0].legend(ret.columns)

sns.histplot(ret['AAPL'], bins=60, kde=True, ax=axes[1])
axes[1].set_title('AAPL 일별 수익률 분포')
plt.tight_layout()
plt.show()

#%%
# ==========================================
# 3. plotly : 인터랙티브 캔들차트
# ==========================================
# 확대·축소·마우스 올려 값 보기가 된다. Spyder에서는 브라우저 창으로 열림.
import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = 'browser'

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv')

fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                                     open=df['AAPL.Open'],
                                     high=df['AAPL.High'],
                                     low=df['AAPL.Low'],
                                     close=df['AAPL.Close'])])
fig.update_layout(title='AAPL 캔들차트', xaxis_rangeslider_visible=True)
fig.show()

# 파일로 저장해서 나중에 열기
fig.write_html('aapl_candle.html')

#%%
# ==========================================
# 4. BeautifulSoup : HTML 파싱
# ==========================================
# HTML을 트리 구조로 읽어서 원하는 태그만 꺼낸다.
#
# 파서 4종류
#   | 파서              | 선언                                   | 장점                          | 단점              |
#   | html.parser       | BeautifulSoup(markup, 'html.parser')   | 설치 불필요, 적당한 속도       | -                 |
#   | lxml (HTML)       | BeautifulSoup(markup, 'lxml')          | 매우 빠름                      | lxml 설치 필요     |
#   | lxml (XML)        | BeautifulSoup(markup, 'xml')           | 매우 빠름, 유일한 XML 파서     | lxml 설치 필요     |
#   | html5lib          | BeautifulSoup(markup, 'html5lib')      | 브라우저와 같은 방식으로 파싱  | 설치 필요, 느림    |
from bs4 import BeautifulSoup

html = """
<table id="price">
  <tr><th>종목</th><th>종가</th></tr>
  <tr><td>A종목</td><td>12,300</td></tr>
  <tr><td>B종목</td><td>45,600</td></tr>
</table>
"""
soup = BeautifulSoup(html, 'html.parser')
rows = soup.select('#price tr')[1:]          # 머리글 행 빼고
for tr in rows:
    tds = tr.find_all('td')
    name = tds[0].get_text(strip=True)
    price = int(tds[1].get_text(strip=True).replace(',', ''))
    print(name, price)

# 표 모양이면 판다스가 더 간단 (내부에서 lxml/bs4 사용)
from io import StringIO
print(pd.read_html(StringIO(html))[0])

#%%
# ==========================================
# 5. Selenium : 브라우저 직접 조작
# ==========================================
# 자바스크립트로 나중에 그려지는 페이지(동적 페이지)는 requests로 받으면 내용이 비어 있다.
# Selenium은 실제 크롬을 띄워 클릭·스크롤·입력을 한 뒤 완성된 HTML을 가져온다.
#
# 예전에는 크롬 버전에 맞는 chromedriver.exe를 직접 받아 경로를 지정해야 했지만,
# Selenium 4.6 이후로는 드라이버를 자동으로 받아 준다 (Selenium Manager).
RUN_SELENIUM = False      # 크롬 창이 뜨므로 필요할 때만 True

if RUN_SELENIUM:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    opts.add_argument('--headless=new')       # 창 안 띄우고 실행
    driver = webdriver.Chrome(options=opts)   # 드라이버 경로 지정 불필요
    driver.get('https://finance.naver.com/sise/')
    print(driver.title)
    kospi = driver.find_element(By.ID, 'KOSPI_now').text
    print('코스피:', kospi)
    driver.quit()

#%%
# ==========================================
# 6. TA-Lib : 기술적 지표
# ==========================================
# MACD, RSI, 스토캐스틱, 볼린저 밴드 등 150개 이상 지표를 C로 구현해 빠르다.
# 설치: 최근 버전은 pip install TA-Lib 로 바로 되는 경우가 많다.
#       안 되면 내 파이썬 버전·윈도우 비트에 맞는 .whl 파일을 받아
#       pip install TA_Lib-버전-cp3xx-cp3xx-win_amd64.whl
# 함수 목록: https://ta-lib.org/functions/
spy = yf.download('SPY', start='2024-01-01', auto_adjust=True, progress=False)
if isinstance(spy.columns, pd.MultiIndex):
    spy.columns = spy.columns.get_level_values(0)
close = spy['Close'].astype('float64')

try:
    import talib
    spy['MA5'] = talib.SMA(close, timeperiod=5)
    spy['MA10'] = talib.SMA(close, timeperiod=10)
    spy['RSI14'] = talib.RSI(close, timeperiod=14)
    macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    spy['MACD'] = macd
    upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
    spy['BB_upper'] = upper
    spy['BB_lower'] = lower
except ImportError:
    # TA-Lib이 없을 때 판다스로 같은 값 만들기
    print('TA-Lib 미설치 -> 판다스로 계산')
    spy['MA5'] = close.rolling(5).mean()
    spy['MA10'] = close.rolling(10).mean()
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    spy['MACD'] = ema12 - ema26
    mid = close.rolling(20).mean()
    sd = close.rolling(20).std(ddof=0)
    spy['BB_upper'] = mid + 2 * sd
    spy['BB_lower'] = mid - 2 * sd

print(spy.tail())

#%%
# ==========================================
# 7. QuantEcon : 마르코프 체인
# ==========================================
# 마르코프 체인 : "다음 상태는 지금 상태에만 달려 있다"는 확률 모형.
# 전이행렬 P[i, j] = 지금 i 상태일 때 다음에 j 상태로 갈 확률 (각 행의 합 = 1)
from quantecon.markov import MarkovChain

# (1) 6개 상태짜리 예 : 한 번 들어가면 못 나오는 상태(흡수 상태)가 있는 체인
P = np.zeros((6, 6))
P[0, 0] = 1                 # 0번은 자기 자신으로만 감 -> 흡수 상태
P[1, 4] = 1
P[2, [2, 3, 4]] = 1 / 3
P[3, [0, 5]] = 1 / 2
P[4, [1, 4]] = 1 / 2
P[5, [0, 3]] = 1 / 2

mc1 = MarkovChain(P)
print('모든 상태가 서로 오갈 수 있나(기약)?', mc1.is_irreducible)
print('서로 오가는 묶음:', mc1.communication_classes)
print('빠져나올 수 없는 묶음:', mc1.recurrent_classes)

#%%
# (2) 금융 예 : 시장 국면 2개 (상승장 / 하락장)
#   상승장이면 다음 달도 상승장일 확률 90%, 하락장으로 바뀔 확률 10%
#   하락장이면 다음 달도 하락장일 확률 70%, 상승장으로 바뀔 확률 30%
P2 = np.array([[0.9, 0.1],
               [0.3, 0.7]])
mc2 = MarkovChain(P2, state_values=['상승장', '하락장'])

# 장기적으로 각 국면에 머무는 비율 (정상분포)
#   손으로 풀기: 상승장 비율을 x라 하면 x = 0.9x + 0.3(1-x) -> 0.4x = 0.3 -> x = 0.75
print('장기 비율:', mc2.stationary_distributions)      # [0.75, 0.25]

# 120개월 시뮬레이션
path = mc2.simulate(ts_length=120, init='상승장', random_state=42)
print(pd.Series(path).value_counts())

# 국면이 평균 몇 달 지속되나: 1 / (1 - 머물 확률)
#   상승장 1 / 0.1 = 10개월, 하락장 1 / 0.3 = 약 3.3개월

#%%
# ==========================================
# 8. 거래소 캘린더 : 휴장일·개장 시간
# ==========================================
# 주가 시계열을 다룰 때 "그날 장이 열렸나"를 알아야 결측과 휴장을 구분할 수 있다.
#
# (1) pandas_market_calendars
import pandas_market_calendars as mcal

nyse = mcal.get_calendar('NYSE')
print('시간대:', nyse.tz)
holidays = nyse.holidays()
print('NYSE 휴장일 마지막 5개:', holidays.holidays[-5:])

# 기간 내 실제 개장·폐장 시각 (조기 폐장일 포함)
sched = nyse.schedule(start_date='2026-11-20', end_date='2026-12-31')
print(sched.tail(10))
print('기간 내 거래일 수:', len(sched))

# 한국거래소
krx_cal = mcal.get_calendar('XKRX')
krx_days = krx_cal.valid_days(start_date='2026-01-01', end_date='2026-12-31')
print('2026년 한국 거래일 수:', len(krx_days))

#%%
# (2) exchange_calendars
#   Zipline과 같이 쓰던 trading_calendars는 개발이 멈췄고, 그 후속이 exchange_calendars.
#   거래소 코드는 ISO 시장코드(MIC)를 쓴다.
import exchange_calendars as xcals

codes = {'미국(NYSE)': 'XNYS', '런던': 'XLON', '토론토': 'XTSE',
         '도쿄': 'XTKS', '프랑크푸르트': 'XFRA', '한국': 'XKRX'}
for name, code in codes.items():
    cal = xcals.get_calendar(code)
    sessions = cal.sessions_in_range('2026-01-01', '2026-12-31')
    print(name, code, '2026년 거래일 수:', len(sessions))

# 특정 날짜가 거래일인지
xkrx = xcals.get_calendar('XKRX')
print('2026-12-25 한국 거래일?', xkrx.is_session('2026-12-25'))

# 활용: 주가 데이터에서 "거래일인데 데이터가 없는 날" = 진짜 결측 찾기
# missing = xkrx.sessions_in_range(start, end).difference(price_df.index)
