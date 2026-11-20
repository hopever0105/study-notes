#%%

# 오픈 API 데이터 받기와 라이브러리 내부 살펴보기

#%%
# ==========================================
# 0. 목적
# ==========================================
# 특정 API 하나를 외우는 게 아니라 "오픈 API로 데이터를 받아 내 형식으로 가공하는 흐름"에 익숙해지기.
# API는 언제든 바뀌거나 없어진다 (아래 Quandl이 실제로 이름이 바뀐 예).
# 그래서 한 API에만 기대지 말고, 라이브러리 속을 열어 보고 필요하면 고쳐 쓸 수 있어야 한다.

import os
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

#%%
# ==========================================
# 1. Quandl -> Nasdaq Data Link
# ==========================================
# Quandl : 금융·경제 데이터를 모아 파는 플랫폼. 2018년 나스닥에 인수됐고 지금 이름은 Nasdaq Data Link.
#   - 핵심 금융 데이터(Core Financial Data) + 대체 데이터(Alternative Data)
#   - 다른 데이터 회사도 자기 데이터를 올려 파는 오픈마켓 구조
#   - 무료(Free) / 유료(Premium) 데이터가 나뉨
#   - 한국 시장 데이터는 거의 없음 -> 국내는 FinanceDataReader, yfinance, DART, ECOS 쪽이 낫다
#
# 사용 순서
#   1) 홈페이지 무료 가입 -> API 키 발급
#   2) pip install nasdaq-data-link   (예전 이름: pip install quandl, 사용법 거의 같음)
#   3) 키는 코드에 직접 쓰지 말고 환경변수로 (GitHub에 키가 올라가는 사고 방지)
#      Windows: 시스템 환경 변수에 NASDAQ_DATA_LINK_API_KEY 추가
#
# 키 없이 부르면 호출 횟수 제한에 걸려 LimitExceededError 가 난다.

API_KEY = os.environ.get('NASDAQ_DATA_LINK_API_KEY', '')

try:
    import nasdaqdatalink as ndl
    ndl.ApiConfig.api_key = API_KEY
    HAS_NDL = True
except ImportError:
    HAS_NDL = False
    print('nasdaq-data-link 미설치 -> 아래 Nasdaq Data Link 셀은 건너뜀 (pip install nasdaq-data-link)')

#%%
# ==========================================
# 2. get() 함수로 데이터 받기
# ==========================================
# 주요 인자
#   dataset    : 'DB코드/데이터코드' 문자열, 또는 그 리스트 (여러 개 한 번에)
#   api_key    : 키 직접 전달 (ApiConfig에 넣었으면 생략)
#   start_date, end_date : 기간 ('2015-01-01')
#   collapse   : 간격 daily / weekly / monthly / quarterly / annual
#   transform  : 미리 가공 diff(차이) / rdiff(변화율) / cumul(누적합) / normalize(시작=100)
#   rows       : 몇 행만 받을지
#   order      : asc(오름차순, 기본) / desc
#   returns    : 'pandas'(기본) / 'numpy'
#
# 주의: 예전 무료 미국 주가 DB인 'WIKI'는 2018년에 갱신이 멈춘 데이터다. 연습용으로만.

if HAS_NDL and API_KEY:
    # 미국 개별 주식 5행 (WIKI DB, 2018년까지만 있음)
    aapl = ndl.get('WIKI/AAPL', rows=5)
    print(type(aapl))       # pandas DataFrame
    print(aapl)

    # transform 예: 월별로 묶고 변화율로
    aapl_m = ndl.get('WIKI/AAPL', start_date='2015-01-01', end_date='2017-12-31',
                     collapse='monthly', transform='rdiff')
    print(aapl_m[['Adj. Close']].head())

    # 파일 저장 / 다시 읽기
    aapl.to_csv('aapl.csv')
    print(pd.read_csv('aapl.csv').head())

#%%
# ==========================================
# 3. 여러 종목을 한 번에 받으면 열 이름이 지저분해진다
# ==========================================
# dataset에 리스트를 넣으면 열 이름이 'WIKI/AAPL - Open', 'WIKI/AMZN - Close' ... 처럼 붙어서 나옴.
# -> 종목별로 잘라서, 열 이름에서 종목코드 부분을 지우고, 종목별 CSV로 저장하는 흐름을 연습.

code_list = ['WIKI/AAPL', 'WIKI/AMZN', 'WIKI/MSFT']

if HAS_NDL and API_KEY:
    multi = ndl.get(dataset=code_list, rows=5)
    print(multi.columns)

    # (1) 첫 종목 열만 고르기 : 열 이름에 'WIKI/AAPL'이 들어간 것만
    extract_code = [x for x in multi.columns if code_list[0] in x]
    one = multi.loc[:, extract_code]

    # (2) 열 이름에서 'WIKI/AAPL - ' 지우기
    one = one.rename(columns=lambda x: x.replace('WIKI/AAPL - ', ''))
    print(one)

    # (3) 모든 종목 반복 -> 종목별 CSV
    for code in code_list:
        print(code)
        extract_code = [x for x in multi.columns if code in x]
        part = multi.loc[:, extract_code]
        old_col = code + ' - '
        part = part.rename(columns=lambda x: x.replace(old_col, ''))
        save_file = code.split('/')[1] + '.csv'     # 'WIKI/AAPL' -> 'AAPL.csv'
        part.to_csv(save_file)

#%%
# ==========================================
# 4. 같은 가공 흐름을 키 없이 연습 (yfinance)
# ==========================================
# yfinance로 여러 종목을 받으면 열이 (가격항목, 티커) 2단 구조로 나온다.
# 위 3번과 문제가 같다: "한 표에 여러 종목이 섞여 있음 -> 종목별로 나누기"
import yfinance as yf

tickers = ['AAPL', 'AMZN', 'MSFT']
multi_yf = yf.download(tickers, start='2024-01-01', end='2024-03-01',
                       auto_adjust=True, progress=False)
print(multi_yf.columns[:6])

SAVE_DIR = 'yf_split'
os.makedirs(SAVE_DIR, exist_ok=True)

for tk in tickers:
    # 2단 열에서 두 번째 단(티커)이 tk인 것만 -> xs로 한 번에
    part = multi_yf.xs(tk, axis=1, level=1)
    part.to_csv(os.path.join(SAVE_DIR, tk + '.csv'))
    print(tk, part.shape)

# 같은 일을 리스트 컴프리헨션으로 (3번과 똑같은 방식)
flat = multi_yf.copy()
flat.columns = [tk + ' - ' + col for col, tk in flat.columns]    # 'AAPL - Close' 형태로 펴기
extract_code = [x for x in flat.columns if 'AAPL' in x]
aapl_only = flat.loc[:, extract_code].rename(columns=lambda x: x.replace('AAPL - ', ''))
print(aapl_only.head())

#%%
# ==========================================
# 5. 라이브러리는 데이터를 어디서 가져오나 : 설치 위치 찾기
# ==========================================
# 터미널(Anaconda Prompt)에서:
#   python -m site
# -> sys.path 목록이 나오고, 그 중 ...\envs\ta_env\lib\site-packages 가 라이브러리 설치 폴더.
#
# 파이썬 안에서 바로 찾기:
import sys
import site
import inspect

print('파이썬 실행 파일:', sys.executable)
print('site-packages:', site.getsitepackages())

#%%
# ==========================================
# 6. FinanceDataReader 속 열어 보기
# ==========================================
# DataReader('005930') 를 부르면 내부에서 "종목코드 모양"을 보고 어느 사이트에서 긁어올지 고른다.
#   - 6자리 숫자 + 한국 -> 네이버 등 국내 소스
#   - 그 밖의 티커     -> 해외 소스
# StockListing('KRX') 같은 종목 목록 함수는 KRX를 부른다 -> 이건 krx_guard 켜고 써야 함.
#
# 버전마다 내부 구조가 바뀌므로 예전 코드를 외우지 말고 직접 열어 본다.
import FinanceDataReader as fdr

print('FDR 버전:', fdr.__version__)
print('FDR 설치 위치:', os.path.dirname(fdr.__file__))
print('DataReader가 정의된 파일:', inspect.getsourcefile(fdr.DataReader))

# 함수 소스 앞부분 출력 (어떤 조건으로 어떤 Reader를 고르는지 확인)
src = inspect.getsource(fdr.DataReader)
print(src[:2000])

# 폴더 안 하위 모듈 목록 (naver, yahoo, investing, krx ... 등 소스별 폴더)
print(sorted(os.listdir(os.path.dirname(fdr.__file__))))

#%%
# ==========================================
# 7. 직접 만들어 보기 : 네이버 일봉 리더의 핵심 구조
# ==========================================
# 국내 리더들이 하는 일은 결국 이 4단계다.
#   1) 종목코드로 URL 조립
#   2) requests.get 으로 응답 받기
#   3) 응답(텍스트/JSON/XML)에서 숫자 부분만 정규식·파서로 추출
#   4) DataFrame으로 만들고 날짜 인덱스 정렬, 기간 자르기
# 아래는 그 구조를 흉내 낸 함수다. (네이버가 주소·형식을 바꾸면 3)번이 깨진다 -> 그때 직접 고치면 됨)
import re
import requests
from io import StringIO


def naver_daily(symbol, start=None, end=None, count=3000):
    url = ('https://fchart.stock.naver.com/sise.nhn'
           '?timeframe=day&count=' + str(count) + '&requestType=0&symbol=' + symbol)
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)

    data_list = re.findall('<item data="(.*?)" />', r.text, re.DOTALL)
    if len(data_list) == 0:
        return pd.DataFrame()

    data = '\n'.join(data_list)
    out = pd.read_csv(StringIO(data), delimiter='|', header=None, dtype={0: str})
    out.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    out['Date'] = pd.to_datetime(out['Date'], format='%Y%m%d')
    out = out.set_index('Date').sort_index()
    out['Change'] = out['Close'].pct_change()

    if start is not None:
        out = out[out.index >= pd.Timestamp(start)]
    if end is not None:
        out = out[out.index <= pd.Timestamp(end)]
    return out


samsung = naver_daily('005930', start='2025-01-01')
print(samsung.tail())

# FDR 결과와 비교 (같은 숫자가 나오면 구조를 제대로 이해한 것)
samsung_fdr = fdr.DataReader('005930', '2025-01-01')
print(samsung_fdr.tail())

# 이렇게 리더를 직접 짜 보면
#   - 필요한 항목(예: 외국인 보유율, 시가총액)을 추가로 긁도록 고칠 수 있고
#   - 라이브러리가 고장 났을 때 스스로 고칠 수 있다.
