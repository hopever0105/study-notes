#%%

# 백테스트 라이브러리 비교와 Backtrader RSI 전략

#%%
# ==========================================
# 1. 파이썬 백테스트 라이브러리 비교
# ==========================================
# 백테스트 코드를 직접 짤 수도 있지만, 주문·체결·수수료·잔고 계산을 대신 해 주는
# 라이브러리를 쓰면 전략 규칙에만 집중할 수 있다.
#
# [Zipline]
#   - Quantopian이 만든 가장 유명한 이벤트 방식 백테스트 엔진
#   - Quantopian 회사는 2020년에 서비스를 닫았고, 지금은 커뮤니티판(zipline-reloaded)이 이어받음
#   - 장점: 성숙한 구조, 관련 자료가 많음
#   - 단점: 설치가 까다롭고 데이터 번들(ingest) 준비가 번거로움, 실거래 연결은 특정 브로커 한정
#
# [QuantConnect (LEAN 엔진)]
#   - 클라우드 기반 플랫폼. 파이썬·C# 지원, 데이터 제공
#   - 장점: 클라우드에서 실시간 자동매매까지 연결 가능
#   - 단점: 본격적으로 쓰려면 구독료, 코드가 플랫폼 서버에 남음, 미국 시장 위주
#
# [Quantiacs]
#   - 시스템 트레이딩·포트폴리오 최적화용 라이브러리와 전략 대회 플랫폼
#   - 장점: 클라우드 사용, 전략 소유권 보장, 미국 주식·원자재 선물 데이터
#   - 단점: 실시간 매매 지원은 불분명
#
# [Backtrader]
#   - 내 PC에서 돌리는 오픈소스 라이브러리 (무료, GPLv3)
#   - 장점: 문서화가 잘 됨, 추가 비용 없음, 코드가 내 소유, 외부 의존성이 거의 없음
#   - 단점: 데이터는 직접 구해야 함, 대회·상금 같은 건 없음
#
# 정리
#   - 해외 플랫폼들은 미국 시장 기준이라 국내 증권사 자동매매와 바로 연결하기는 불편
#   - "백테스트만" 목적이면 로컬은 Backtrader, 클라우드는 QuantConnect가 무난
#   - 국내 주식은 FinanceDataReader·yfinance로 받은 데이터를 Backtrader에 넣어 쓰면 됨

#%%
# ==========================================
# 2. 설치
# ==========================================
# Anaconda Prompt (ta_env 환경)에서:
#   pip install backtrader
#   pip install yfinance
# 그림까지 그리려면 matplotlib 필요 (보통 이미 설치돼 있음)

import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

#%%
# ==========================================
# 3. Backtrader 전략 구조
# ==========================================
# 전략은 bt.Strategy 를 상속받아 만든다.
#   __init__() : 지표(이동평균, RSI 등)를 미리 정의
#   next()     : 봉(하루) 하나가 지날 때마다 호출 -> 여기서 매수/매도/아무것도 안 함 결정
#
# 가장 단순한 뼈대 : 15일 이동평균과 종가 비교

class MyStrategy(bt.Strategy):                 # ① 상위 클래스 Strategy 상속

    def __init__(self):
        self.sma = bt.indicators.SimpleMovingAverage(period=15)   # ② 15일 단순 이동평균

    def next(self):
        if self.sma > self.data.close:         # ③ 이동평균이 종가보다 위 (하락 흐름)
            # 여기에 매도 등 동작
            pass

        elif self.sma < self.data.close:       # ④ 이동평균이 종가보다 아래 (상승 흐름)
            # 여기에 매수 등 동작
            pass

#%%
# ==========================================
# 4. RSI 개념 (숫자 예시)
# ==========================================
# RSI(Relative Strength Index, 상대강도지수) : 최근 N일(보통 14일) 동안
# 오른 폭이 내린 폭에 비해 얼마나 큰지를 0~100으로 나타낸 모멘텀 지표.
#
#   RS  = 평균 상승폭 / 평균 하락폭
#   RSI = 100 - 100 / (1 + RS)
#
# 예) 14일 동안 상승한 날의 상승폭 평균 = 1.0원, 하락한 날의 하락폭 평균 = 2.0원
#     RS = 1.0 / 2.0 = 0.5
#     RSI = 100 - 100 / 1.5 = 100 - 66.7 = 33.3
#   -> 30 근처: 많이 빠졌다(과매도), 70 이상: 많이 올랐다(과매수)로 보는 게 관례
#
# 아래 전략 규칙
#   - 포지션 없음 + RSI < 30  -> 매수
#   - 포지션 있음 + RSI > 70  -> 매도(청산)

#%%
# ==========================================
# 5. RSI 매매 전략 클래스
# ==========================================
class RSIStrategy(bt.Strategy):
    params = (('rsi_period', 14),
              ('buy_level', 30),
              ('sell_level', 70),
              ('size', 50))

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=15)       # ① 이동평균 (참고용)
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.p.rsi_period)     # ② RSI

    # 주문 상태가 바뀔 때마다 호출됨
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return    # 접수만 된 상태 -> 아직 할 일 없음

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY 체결, 가격: %.2f, 금액: %.2f, 수수료: %.2f' % (
                    order.executed.price, order.executed.value, order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log('SELL 체결, 가격: %.2f, 금액: %.2f, 수수료: %.2f' % (
                    order.executed.price, order.executed.value, order.executed.comm))
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('주문 취소/증거금 부족/거부')

        self.order = None

    # 매매 한 번(진입~청산)이 끝날 때 호출됨
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('거래 손익: 수수료 전 %.2f, 수수료 후 %.2f' % (trade.pnl, trade.pnlcomm))

    def next(self):
        if self.order:                                   # ③ 아직 체결 안 된 주문이 있으면 대기
            return

        if not self.position:                            # ④ 보유 포지션 없음
            if self.rsi[0] < self.p.buy_level:           # ⑤ RSI 30 미만 -> 매수
                self.log('BUY 주문, %.2f' % self.dataclose[0])
                self.order = self.buy(size=self.p.size)  # ⑥ 정해진 수량 매수

        else:
            if self.rsi[0] > self.p.sell_level:          # ⑦ RSI 70 초과 -> 매도
                self.log('SELL 주문, %.2f' % self.dataclose[0])
                self.order = self.sell(size=self.p.size) # ⑧ 같은 수량 매도

#%%
# ==========================================
# 6. 데이터 준비 (QQQ : 나스닥100 추종 ETF)
# ==========================================
TICKER = 'QQQ'
START = '2018-01-01'
END = '2024-12-31'

raw = yf.download(TICKER, start=START, end=END, auto_adjust=True, progress=False)

# yfinance 최신 버전은 단일 종목도 열이 2단(가격항목, 티커)으로 나올 수 있음 -> 1단으로 정리
if isinstance(raw.columns, pd.MultiIndex):
    raw.columns = raw.columns.get_level_values(0)

df = raw[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
df.index = pd.to_datetime(df.index)
print(df.tail())

# CSV로 저장해 두고 쓰고 싶으면:
# df.to_csv('QQQ.csv')
# df = pd.read_csv('QQQ.csv', index_col='Date', parse_dates=['Date'])

#%%
# ==========================================
# 7. 백테스트 실행
# ==========================================
data = bt.feeds.PandasData(dataname=df)              # ② 판다스 표 -> Backtrader 데이터 형식

cerebro = bt.Cerebro()                               # ③ 전략을 실제로 돌리는 엔진
cerebro.addstrategy(RSIStrategy)                     # ④ 전략 추가
cerebro.broker.setcommission(commission=0.001)       # ⑤ 수수료 0.1%
cerebro.adddata(data, name=TICKER)                   # ⑥ 데이터 추가 (name에 쓸 TICKER 변수를 위에서 먼저 만들어 둬야 함)
cerebro.broker.setcash(100000.0)                     # ⑦ 시작 현금 10만 달러

# 성과 분석기 추가 (샤프·낙폭·거래 통계를 숫자로 보기)
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0)
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='dd')
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')

start_value = cerebro.broker.getvalue()
print('시작 평가금액: %.2f' % start_value)
results = cerebro.run()                              # ⑧ 실행
end_value = cerebro.broker.getvalue()
print('최종 평가금액: %.2f' % end_value)
print('전략 수익률: {:.2%}'.format(end_value / start_value - 1))

#%%
# ==========================================
# 8. 결과 숫자 확인
# ==========================================
strat = results[0]
sharpe = strat.analyzers.sharpe.get_analysis()
dd = strat.analyzers.dd.get_analysis()
trades = strat.analyzers.trades.get_analysis()

print('샤프 비율:', sharpe.get('sharperatio'))
print('최대 낙폭(%):', round(dd['max']['drawdown'], 2))
total_closed = trades.get('total', {}).get('closed', 0)
won = trades.get('won', {}).get('total', 0)
print('청산된 거래 수:', total_closed)
if total_closed > 0:
    print('승률: {:.1%}'.format(won / total_closed))

# 비교 기준 : 같은 기간 QQQ 사서 들고 있기
bh_return = df['Close'].iloc[-1] / df['Close'].iloc[0] - 1
print('QQQ 바이앤홀드 수익률: {:.2%}'.format(bh_return))
# 주의: 이 전략은 한 번에 50주만 사므로 현금 대부분이 놀고 있다.
#       수익률 비교는 투입 금액 비중까지 감안해서 봐야 한다.

#%%
# ==========================================
# 9. 그림
# ==========================================
# (1) Backtrader 기본 그림 : 가격·매매 시점·RSI·평가금액이 한 화면에
#   - 맨 위: 현금/평가금액 변화
#   - 동그라미: 거래별 손익 (위=이익, 아래=손실)
#   - 가운데: 가격 차트, ▲ 매수 / ▼ 매도 시점
#   - 아래: RSI 시계열
# matplotlib 버전에 따라 cerebro.plot()이 에러를 내는 경우가 있어 try로 감쌈
try:
    figs = cerebro.plot(iplot=False, volume=False)
    figs[0][0].savefig('backtrader-plot.png', dpi=120)
    print('backtrader-plot.png 저장')
except Exception as e:
    print('Backtrader 기본 그림 실패 (버전 문제일 가능성):', e)

# (2) 직접 그리기 : 전략 평가금액 vs 바이앤홀드
tr = pd.Series(strat.analyzers.timereturn.get_analysis())
tr.index = pd.to_datetime(tr.index)
equity = start_value * (1 + tr).cumprod()
bh = start_value * df['Close'] / df['Close'].iloc[0]

plt.figure(figsize=(10, 5))
plt.plot(equity, label='RSI 전략 평가금액')
plt.plot(bh, label='QQQ 바이앤홀드', alpha=0.7)
plt.title('RSI(30/70) 전략 vs 바이앤홀드')
plt.legend()
plt.grid(alpha=0.3)
plt.show()

#%%
# ==========================================
# 10. 더 해볼 것
# ==========================================
# - size=50 대신 현금 비중으로 사기: cerebro.addsizer(bt.sizers.PercentSizer, percents=95)
# - RSI 기준선(30/70)을 25/75, 35/65로 바꿔 보고 결과가 얼마나 흔들리는지 확인
#   (기준선 하나에만 좋은 결과가 나오면 과적합 의심)
# - 국내 종목: FinanceDataReader로 받은 표를 같은 방식으로 PandasData에 넣으면 됨
#   (KRX를 직접 부르는 함수는 krx_guard 먼저 켜기)
