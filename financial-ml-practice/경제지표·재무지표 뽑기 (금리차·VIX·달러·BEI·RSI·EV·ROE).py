#%%

# 경제지표·재무지표 뽑기 (금리차·VIX·달러·BEI·RSI·EV·ROE)

#%%
# ==========================================
# 0. 이 파일에서 하는 것
# ==========================================
# 머신러닝 시장 예측에 피처(설명변수)로 자주 넣는 지표들을
#   (1) 뜻을 숫자 예시로 정리하고
#   (2) 실제로 파이썬으로 받아서 표 하나로 합친다.
#
# 데이터 출처 (전부 무료, 키 필요 없음)
#   - FRED (미국 세인트루이스 연준 경제 데이터) : 금리, 금리차, VIX, 달러지수, 기대인플레이션
#       주소 하나로 CSV를 바로 받을 수 있다: https://fred.stlouisfed.org/graph/fredgraph.csv?id=시리즈코드
#   - yfinance (야후 파이낸스) : 금 선물, 달러 인덱스(DXY), VIX, ETF 시세·거래량, 미국 기업 재무제표
#
# KRX는 부르지 않는다 (국내 지수도 야후 티커로 받음).

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

START = '2010-01-01'
SAVE_DIR = 'macro_features'
os.makedirs(SAVE_DIR, exist_ok=True)

#%%
# ==========================================
# 1. 공통 함수 : FRED 시리즈 받기, 야후 종가 받기
# ==========================================
def get_fred(series_id, start=START):
    """FRED에서 시리즈 하나를 받아 날짜 인덱스 Series로 돌려준다. 결측('.')은 NaN."""
    url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=' + series_id
    df = pd.read_csv(url, index_col=0, parse_dates=True, na_values='.')
    s = pd.to_numeric(df.iloc[:, 0], errors='coerce')
    s.name = series_id
    return s[s.index >= pd.Timestamp(start)]


def get_yahoo(ticker, start=START, field='Close'):
    """야후에서 한 종목의 가격 열 하나를 Series로."""
    raw = yf.download(ticker, start=start, auto_adjust=True, progress=False)
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    s = raw[field].copy()
    s.name = ticker
    return s

# 참고: pandas_datareader 로도 같은 걸 받을 수 있다
#   import pandas_datareader.data as web
#   web.DataReader(['DGS10', 'DGS2'], 'fred', START)

#%%
# ==========================================
# 2. 장단기 금리차 (미국 국채 10년 - 2년 / 10년 - 3개월)
# ==========================================
# 금리 스프레드 : 위험도가 다른 두 금리의 차이.
#   - 기간 위험 -> 장단기 금리차 (같은 국채인데 만기만 다름)
#   - 신용 위험 -> 신용 스프레드 (만기는 같고 발행자 신용만 다름, 아래 4번)
#
# 숫자 예시
#   10년물 4.5%, 2년물 4.0% -> 금리차 +0.5%p : 정상 (장기가 더 높음, 경기 확장 기대)
#   10년물 3.8%, 2년물 4.7% -> 금리차 -0.9%p : 역전 (단기가 더 높음)
#   역전은 "시장이 앞으로 금리 인하 = 경기 둔화를 예상한다"는 뜻이라 경기침체 선행 신호로 본다.
#   보통 10년-2년 또는 10년-3개월(연준이 더 신뢰하는 쪽)을 쓴다.

dgs10 = get_fred('DGS10')      # 10년물 금리
dgs2 = get_fred('DGS2')        # 2년물 금리
t10y2y = get_fred('T10Y2Y')    # FRED가 계산해 둔 10년-2년 금리차
t10y3m = get_fred('T10Y3M')    # 10년-3개월 금리차

# 직접 계산한 것과 FRED 계산값이 같은지 확인
check = pd.concat([dgs10, dgs2, t10y2y], axis=1).dropna()
check['직접계산'] = check['DGS10'] - check['DGS2']
print(check.tail())
print('최대 오차:', (check['직접계산'] - check['T10Y2Y']).abs().max())

# 역전 구간 비율
print('10년-2년 역전 일 비율: {:.1%}'.format((t10y2y.dropna() < 0).mean()))

#%%
# ==========================================
# 3. VIX : S&P500 변동성 지수
# ==========================================
# S&P500 옵션 가격에서 역산한 "앞으로 30일 동안 예상되는 연간 변동성(%)".
# 숫자 예시
#   VIX = 20 -> 연 변동성 20% 예상 -> 한 달로 바꾸면 20 / sqrt(12) = 약 5.8%
#             -> "한 달 뒤 지수가 ±5.8% 안에 있을 확률 약 68%" 정도로 해석
#   VIX 30 이상: 공포 구간, 12 이하: 매우 안정
# VIX 자체는 직접 살 수 없어서 선물을 담은 ETF/ETN(예: VIXY)이 있지만,
# 이런 상품은 선물 롤오버 비용 때문에 장기로 보면 지수와 크게 달라진다.
# -> 피처로는 지수 값(VIXCLS 또는 ^VIX)을 그대로 쓰는 게 낫다.

vix_fred = get_fred('VIXCLS')
vix_yahoo = get_yahoo('^VIX')
print(pd.concat([vix_fred, vix_yahoo], axis=1).dropna().tail())

#%%
# ==========================================
# 4. TED 스프레드와 그 대체 지표 (신용경색)
# ==========================================
# TED 스프레드 = 3개월 리보(LIBOR) 금리 - 3개월 미국 국채(T-Bill) 금리
#   - 국채: 가장 안전한 돈 / 리보: 은행끼리 빌려줄 때 금리 (은행 신용위험 포함)
#   - 차이가 벌어짐 = 은행들이 서로 못 믿음 = 자금 조달이 어려워짐 (유동성 위험)
#   숫자 예시: 평소 0.2~0.5%p, 2008년 10월 금융위기 때 4%p 이상
#
# 리보는 조작 사건 이후 폐지 수순을 밟았고, FRED의 TEDRATE도 2022년 1월에 끝났다.
# -> 과거 연구용으로만 쓰고, 지금 피처로는 회사채 신용 스프레드를 대신 쓴다.
#    BAMLH0A0HYM2 : 미국 하이일드 회사채 - 국채 금리차 (옵션조정 스프레드)
#    (FRED에는 데이터 제공사 정책으로 최근 약 3년치만 올라와 있음)

ted = get_fred('TEDRATE', start='2000-01-01')
print('TED 마지막 날짜:', ted.dropna().index[-1].date())
hy_spread = get_fred('BAMLH0A0HYM2', start='2000-01-01')
print('하이일드 스프레드 시작 날짜:', hy_spread.dropna().index[0].date())

#%%
# ==========================================
# 5. 금 가격 : 대표 안전자산
# ==========================================
# 안전자산 선호가 커짐 = 시장 불안이 커짐. 금 가격 상승은 위험회피 신호로 쓴다.
# (금 현물 가격 시리즈는 FRED에서 내려갔으므로 야후의 금 선물 GC=F 사용,
#  또는 금 ETF GLD 사용)
gold = get_yahoo('GC=F')
gold.name = 'GOLD'
print(gold.tail())

#%%
# ==========================================
# 6. 달러 지수
# ==========================================
# 달러 인덱스(DXY) : 주요 6개 통화(유로, 엔, 파운드, 캐나다 달러, 스웨덴 크로나, 스위스 프랑) 대비
#   달러 가치를 가중평균한 지수. 1973년 3월 = 100.
#   가중치는 무역 비중 기준으로 정해졌고 유로 비중이 절반 이상(약 57.6%).
#   숫자 예시: DXY 100 -> 105 : 6개 통화 대비 달러가 평균 5% 강해짐
#   달러 강세는 위험자산 회피, 신흥국 자금 유출 신호로 해석하는 경우가 많다.
#
# FRED의 DTWEXBGS 는 무역가중 "광의" 달러지수 (중국 위안, 원화 등 26개 통화 포함, 2006-01 = 100)
#   -> 한국 입장에서는 이쪽이 더 넓게 반영된다.

dxy = get_yahoo('DX-Y.NYB')
dxy.name = 'DXY'
dollar_broad = get_fred('DTWEXBGS')
print(pd.concat([dxy, dollar_broad], axis=1).dropna().tail())

#%%
# ==========================================
# 7. 기대 인플레이션율 (BEI, Breakeven Inflation Rate)
# ==========================================
# 시장이 예상하는 앞으로의 평균 물가상승률.
#   BEI = 명목 국채 금리 - 물가연동 국채(TIPS) 금리   (같은 만기)
#
# 숫자 예시 (10년물)
#   명목 국채 10년 4.3%, 물가연동 국채 10년 2.0% -> BEI = 2.3%
#   물가연동채는 원금이 물가만큼 불어나므로 "물가를 뺀 실질금리"만 준다.
#   두 채권이 같은 값이 되려면 앞으로 10년 평균 물가가 2.3%여야 함 -> 이게 시장의 기대 인플레이션.
#   인플레이션 전망이 높아지면 물가연동채를 더 사려고 해서 그 금리가 더 많이 떨어짐 -> BEI 확대.

dfii10 = get_fred('DFII10')     # 10년 물가연동 국채 금리 (실질금리)
t10yie = get_fred('T10YIE')     # FRED가 계산해 둔 10년 BEI

bei = pd.concat([dgs10, dfii10, t10yie], axis=1).dropna()
bei['BEI_직접계산'] = bei['DGS10'] - bei['DFII10']
print(bei.tail())

#%%
# ==========================================
# 8. 한국 금리차 (월별, OECD 자료를 FRED에서)
# ==========================================
# IRLTLT01KRM156N : 한국 장기금리(국채 10년, 월평균)
# IR3TIB01KRM156N : 한국 3개월 단기금리 (월평균)
kr_long = get_fred('IRLTLT01KRM156N', start='2001-01-01')
kr_short = get_fred('IR3TIB01KRM156N', start='2001-01-01')
kr_spread = (kr_long - kr_short).dropna()
kr_spread.name = 'KR_10Y_3M'
print(kr_spread.tail())

#%%
# ==========================================
# 9. 가격 기반 기술 지표 : 이동평균, 거래량 이동평균, RSI
# ==========================================
# 대상: SPY (S&P500 ETF) 가격·거래량
spy_raw = yf.download('SPY', start=START, auto_adjust=True, progress=False)
if isinstance(spy_raw.columns, pd.MultiIndex):
    spy_raw.columns = spy_raw.columns.get_level_values(0)
spy = spy_raw[['Close', 'Volume']].copy()

# (1) 60일 이동평균 : 최근 60거래일 종가 평균
#   예) 최근 60일 종가 합이 30,000이면 MA60 = 500. 종가 520 > MA60 500 -> 중기 상승 흐름
#   60은 정해진 답이 아니다. 10, 20, 120일 등 바꿔 가며 써 보기.
spy['MA60'] = spy['Close'].rolling(60).mean()
spy['종가/MA60'] = spy['Close'] / spy['MA60'] - 1        # 이격도 (스케일이 없는 피처라 ML에 더 좋음)

# (2) 거래량 30일 이동평균 : 평소보다 거래가 몰리는지
#   예) 오늘 거래량 1억 주, 30일 평균 6천만 주 -> 비율 1.67배 = 평소보다 67% 많음
spy['VOL_MA30'] = spy['Volume'].rolling(30).mean()
spy['거래량비율'] = spy['Volume'] / spy['VOL_MA30']

# (3) RSI(14) : Wilder 방식
#   1) 오늘 종가 - 어제 종가 = 변화량
#   2) 양수는 상승폭, 음수는 하락폭(부호 바꿔 양수로)
#   3) 각각 14일 지수평활 평균 (alpha = 1/14)
#   4) RS = 평균상승 / 평균하락, RSI = 100 - 100 / (1 + RS)
#   예) 평균상승 1.0, 평균하락 0.5 -> RS 2 -> RSI = 100 - 100/3 = 66.7
def rsi_wilder(close, period=14):
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_up = up.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_down = down.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_up / avg_down
    return 100 - 100 / (1 + rs)

spy['RSI14'] = rsi_wilder(spy['Close'])
print(spy.tail())

#%%
# ==========================================
# 10. 전부 하나의 피처 표로 합치기
# ==========================================
# 주의할 점
#   - 날짜 기준은 SPY 거래일로 맞춘다 (FRED는 미국 공휴일·주말이 비어 있음)
#   - 결측은 앞의 값으로 채운다 (ffill). 뒤의 값으로 채우면(bfill) 미래 정보가 섞인다.
#   - 월별 자료(한국 금리차)는 그 달 값이 발표된 뒤에야 알 수 있으므로 한 달 미뤄서 붙인다.
#   - 예측에 쓸 때는 "오늘까지 알 수 있는 정보로 내일을 맞히는" 구조가 되도록 피처를 하루 밀어(shift(1)) 쓴다.

features = pd.concat([
    spy[['Close', '종가/MA60', '거래량비율', 'RSI14']],
    t10y2y.rename('금리차_10Y2Y'),
    t10y3m.rename('금리차_10Y3M'),
    vix_fred.rename('VIX'),
    hy_spread.rename('하이일드스프레드'),
    gold.rename('금'),
    dxy.rename('달러인덱스'),
    t10yie.rename('BEI_10Y'),
], axis=1)

features = features.loc[spy.index]          # SPY 거래일만 남기기
features = features.ffill()                 # 앞 값으로 채우기 (미래 정보 X)

# 한국 금리차 : 월 자료 -> 한 달 뒤부터 쓸 수 있다고 보고 붙이기
kr_lag = kr_spread.copy()
kr_lag.index = kr_lag.index + pd.offsets.MonthBegin(1)
features['한국금리차_10Y3M'] = kr_lag.reindex(features.index, method='ffill')

# 가격 수준 대신 변화율로 바꾼 피처 (정상성 확보)
features['금_20일수익률'] = features['금'].pct_change(20)
features['달러_20일수익률'] = features['달러인덱스'].pct_change(20)

print(features.tail())
print(features.isna().sum())

features.to_csv(os.path.join(SAVE_DIR, 'macro_features.csv'), encoding='utf-8-sig')

#%%
# ==========================================
# 11. 한눈에 보기
# ==========================================
fig, axes = plt.subplots(4, 1, figsize=(11, 12), sharex=True)

axes[0].plot(features['Close'])
axes[0].set_title('SPY 종가')

axes[1].plot(features['금리차_10Y2Y'], label='10년-2년')
axes[1].plot(features['금리차_10Y3M'], label='10년-3개월')
axes[1].axhline(0, color='black', lw=0.8)
axes[1].set_title('미국 장단기 금리차 (0 아래 = 역전)')
axes[1].legend()

axes[2].plot(features['VIX'])
axes[2].axhline(30, color='red', ls='--', lw=0.8)
axes[2].set_title('VIX (빨간선 30 = 공포 구간)')

axes[3].plot(features['BEI_10Y'])
axes[3].set_title('미국 10년 기대 인플레이션(BEI)')

plt.tight_layout()
plt.show()

# 지표끼리 상관 (변화율·수준 섞어 대략 보기)
corr_cols = ['종가/MA60', '거래량비율', 'RSI14', '금리차_10Y2Y', 'VIX',
             'BEI_10Y', '금_20일수익률', '달러_20일수익률']
print(features[corr_cols].corr().round(2))

#%%
# ==========================================
# 12. 재무지표 : EBIT, EV, 운전자본, ROA, ROE, EPS, PER
# ==========================================
# [EBIT, 이자·법인세 차감 전 이익]
#   EBIT ≒ 영업이익 = 매출액 - 매출원가 - 판매관리비
#   이자비용·법인세를 빼기 전이라 "본업으로 번 돈"을 회사끼리 비교할 때 씀.
#   예) 매출 1,000 - 원가 600 - 판관비 250 = EBIT 150
#
# [EV, 기업가치]
#   회사를 통째로 살 때 드는 돈 = 주식을 다 사는 돈 + 갚아 줘야 할 빚 - 회사가 가진 현금
#   EV = 시가총액 + 차입금(이자 붙는 부채) - 현금성자산
#   예) 시총 1,000 + 차입금 300 - 현금 100 = EV 1,200
#   (부채총계 전체를 더하는 설명도 보이지만, 매입채무 같은 영업부채는 빼고
#    이자 붙는 차입금만 더하는 게 일반적이다. 그래서 '순차입금 = 차입금 - 현금'을 더한다고 외우면 편함)
#   EV/EBIT = 1,200 / 150 = 8배 -> 마법공식에서 쓰는 이익수익률은 그 역수 EBIT/EV = 12.5%
#
# [고정자산 / 유동자산 / 운전자본]
#   고정(비유동)자산 : 1년 안에 현금으로 바꾸기 어려운 자산 (공장, 설비, 토지)
#   유동자산         : 1년 안에 현금화 가능한 자산 (현금, 매출채권, 재고)
#   운전자본(Working Capital) = 유동자산 - 유동부채
#   예) 유동자산 500 - 유동부채 300 = 운전자본 200 (단기 지급 여력)
#
# [ROA, 총자산이익률] = 당기순이익 / 총자산
# [ROE, 자기자본이익률] = 당기순이익 / 자기자본
#   총자산 = 부채 + 자기자본 이므로 분모 차이가 "부채를 포함하느냐"다.
#   예) 순이익 100, 총자산 1,000(부채 600 + 자본 400)
#       ROA = 100 / 1,000 = 10%
#       ROE = 100 / 400   = 25%
#   부채를 많이 쓰면 ROA는 그대로여도 ROE가 커진다 (레버리지 효과).
#   -> 빚과 상관없이 자산을 얼마나 효율적으로 굴리는지는 ROA, 주주 입장 수익률은 ROE.
#   분모는 기초 또는 기초·기말 평균을 쓰는 게 정석 (한 해 동안 굴린 자산으로 번 이익이므로).
#
# [EPS, 주당순이익] = 당기순이익 / 발행주식수
# [PER, 주가수익비율] = 주가 / EPS = 시가총액 / 순이익
#   예) 순이익 100억, 주식 1,000만 주 -> EPS 1,000원, 주가 15,000원 -> PER 15배
#   "지금 이익이 그대로면 15년 벌어야 시총만큼 번다"

def pick(df, names, col=0):
    """재무제표 행 이름이 회사·버전마다 조금씩 달라서, 후보 중 처음 있는 것을 고른다."""
    for n in names:
        if n in df.index:
            v = df.loc[n].iloc[col]
            if pd.notna(v):
                return float(v)
    return np.nan


def fundamentals_us(ticker):
    t = yf.Ticker(ticker)
    inc = t.income_stmt          # 연간 손익계산서 (열 = 결산연도, 최신이 맨 왼쪽)
    bs = t.balance_sheet         # 연간 재무상태표
    info = t.info

    revenue = pick(inc, ['Total Revenue'])
    ebit = pick(inc, ['EBIT', 'Operating Income'])
    net_income = pick(inc, ['Net Income', 'Net Income Common Stockholders'])
    eps = pick(inc, ['Diluted EPS', 'Basic EPS'])

    total_assets_end = pick(bs, ['Total Assets'], col=0)
    total_assets_begin = pick(bs, ['Total Assets'], col=1)       # 전년말 = 올해 기초
    equity_end = pick(bs, ['Stockholders Equity', 'Common Stock Equity'], col=0)
    equity_begin = pick(bs, ['Stockholders Equity', 'Common Stock Equity'], col=1)
    total_debt = pick(bs, ['Total Debt'])
    cash = pick(bs, ['Cash And Cash Equivalents',
                     'Cash Cash Equivalents And Short Term Investments'])
    current_assets = pick(bs, ['Current Assets'])
    current_liab = pick(bs, ['Current Liabilities'])

    market_cap = info.get('marketCap', np.nan)
    price = info.get('currentPrice', info.get('regularMarketPrice', np.nan))

    ev = market_cap + total_debt - cash
    out = {
        '결산기준일': str(inc.columns[0].date()),
        '매출액': revenue,
        'EBIT': ebit,
        '당기순이익': net_income,
        '시가총액': market_cap,
        '총차입금': total_debt,
        '현금성자산': cash,
        'EV': ev,
        'EV/EBIT': ev / ebit,
        '이익수익률(EBIT/EV)': ebit / ev,
        '운전자본': current_assets - current_liab,
        'ROA(기초자산)': net_income / total_assets_begin,
        'ROA(평균자산)': net_income / ((total_assets_begin + total_assets_end) / 2),
        'ROE(기초자본)': net_income / equity_begin,
        'EPS': eps,
        '주가': price,
        'PER(주가/EPS)': price / eps,
        'PER(시총/순이익)': market_cap / net_income,
    }
    return pd.Series(out, name=ticker)

#%%
# 미국 대형주 몇 개 비교
fund = pd.concat([fundamentals_us(tk) for tk in ['AAPL', 'MSFT', 'GOOGL']], axis=1)
pd.set_option('display.float_format', lambda x: '{:,.3f}'.format(x))
print(fund)

# 두 가지 PER이 거의 같은지 확인
#   주가/EPS 와 시총/순이익 은 같은 개념이지만 EPS 계산 주식수(가중평균·희석)와
#   현재 발행주식수가 달라서 조금 차이 난다.

# ROE가 매우 높게 나오는 회사(예: 자사주 매입을 많이 해서 자기자본이 작은 회사)는
# ROE만 보면 착시가 생긴다 -> ROA와 같이 봐야 하는 이유.

fund.to_csv(os.path.join(SAVE_DIR, 'fundamentals_us.csv'), encoding='utf-8-sig')

#%%
# ==========================================
# 13. 국내 기업은?
# ==========================================
# - 재무제표: DART 오픈API (opendart.fss.or.kr, 무료 키) -> OpenDartReader 라이브러리
#     pip install opendartreader
#     import OpenDartReader
#     dart = OpenDartReader(os.environ['DART_API_KEY'])
#     fs = dart.finstate('005930', 2025)        # 삼성전자 2025 사업보고서 주요 계정
# - 시가총액: 상장주식수 x 종가 (종가는 FinanceDataReader 네이버 소스, 주식수는 DART)
# - 위 12번 공식은 그대로 적용하면 된다.
