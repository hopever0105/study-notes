

#%% [Sector 5] Chapter 18. 문자열 패턴을 찾아주는 정규 표현식 (re) (Images 96~97)
"""
수집한 자료(인터넷 스크래핑 등)에서 원하는 부분만 골라낼 때 유용한 라이브러리가 정규 표현식 모듈(re)입니다[cite: 96].

<주요 명령어>[cite: 97]
- re.match(패턴, 문자열): 문자열의 **시작**이 패턴과 일치하는지 조사 (없으면 None 반환)
- re.search(패턴, 문자열): 문자열 **전체**에서 패턴과 일치하는 부분이 있는지 조사 (첫 인덱스 반환)
- re.findall(패턴, 문자열): 일치하는 부분을 모두 찾아 **리스트**로 반환
- re.split(구분자, 문자열): 구분자 기준으로 자른 후 리스트로 반환
- re.sub(패턴, 대체문자, 문자열): 문자열에서 패턴을 찾아 대체
- re.compile(패턴): 패턴을 미리 해석해두어 가독성/속도 향상
"""

# 실습 문자열 세팅[cite: 97]
target_str = '이사원,오대리,구과장,육차장,정부장'[cite: 97]

# 1. re.match: 시작점 검사[cite: 97]
# target_str이 '이사원'으로 시작하므로 매치 객체와 인덱스 (0,3)을 반환[cite: 97]
print(re.match('이사원', target_str)) 

# '오대리'로 시작하지 않으므로 None(반환값 없음)을 반환[cite: 97]
print(re.match('오대리', target_str)) 

# 2. re.search: 전체 문자열에서 처음 나오는 패턴 위치 반환[cite: 97]
# '이사원'은 맨 앞에 있으므로 match와 동일하게 (0,3) 반환[cite: 97]
print(re.search('이사원', target_str))

# match와 달리 전체를 뒤지므로 '오대리' 패턴을 찾아내어 인덱스 (4,7)을 반환[cite: 97]
print(re.search('오대리', target_str))


import re

#%% [Sector 1] 정규 표현식 간편식을 이용한 패턴 정의 (Images 108~110)
"""
복잡한 패턴(예: [0-9], [^0-9] 등)을 매번 길게 쓰지 않도록 파이썬에서는 간편식(단축어)을 제공합니다[cite: 109].
데이터 정제 작업(생선 가시 발라내기)을 굵은 가시를 한꺼번에 발라내는 것처럼 쉽게 만들어주는 치트키 역할을 합니다[cite: 110].

<간편식 기호 표>[cite: 109]
- \d : 숫자 (일반식: [0-9])
- \D : 숫자를 제외한 전체 (일반식: [^0-9])
- \w : 문자 + 숫자 (일반식: [A-Za-z0-9])
- \W : 문자 및 숫자를 제외한 전체 (일반식: [^A-Za-z0-9])
- \s : 공백 (스페이스, 탭, 엔터 등) (일반식: [ \t\n\r])
- \S : 공백 제외 전체 (일반식: [^ ])
"""
test_str = 'ABcd12!@ 가나'[cite: 109]

# print('숫자:', re.findall('\d', test_str))      # 결과: ['1', '2'][cite: 109]
# print('숫자X:', re.findall('\D', test_str))     # 숫자 1, 2를 제외한 모든 문자, 기호, 공백 반환[cite: 109]
# print('문자:', re.findall('\w', test_str))      # 결과: ['A', 'B', 'c', 'd', '1', '2', '가', '나'][cite: 109]
# print('문자X:', re.findall('\W', test_str))     # 결과: ['!', '@', ' '][cite: 109]
# print('공백:', re.findall('\s', test_str))      # 결과: [' '][cite: 109]

# 앞선 핸드폰 번호 정제 예시에서 숫자가 아닌 것을 지울 때 [^0-9] 대신 \D를 써도 동일하게 동작합니다[cite: 108, 109].
# p = re.sub('[^0-9]', '', p)  # 이 코드는 아래와 같습니다[cite: 108].
# p = re.sub('\D', '', p)      # \D도 같은 표현[cite: 108]


#%% [Sector 2] Chapter 19. 대한민국 대표 펀드 따라잡기 (K10 펀드 모델 기획) (Images 111~113)
"""
이전에 만든 K10 인덱스를 이용해, KOSPI200 지수의 수익률을 따라가는(추적하는) 인덱스 펀드 모델을 만듭니다[cite: 111].
KODEX200, TIGER200 등 실제 대표 펀드의 투자설명서를 참고하여 아래와 같이 기획 및 가정합니다[cite: 111, 112].

<K10 펀드 투자설명서 및 실습 가정>[cite: 112, 113]
1. 투자 목표/전략: KOSPI200 상위 10개 종목을 매수하여 KOSPI200 지수의 변동률과 유사하게 운용[cite: 112].
2. 포트폴리오 조정: 2017년 1년간 운용하며 별도의 리밸런싱(종목 교체)은 없음[cite: 112].
3. 운용 기간 중 K10 구성종목 및 유동주식 수는 변하지 않는다고 가정[cite: 113].
4. 제반 비용(운용 보수, 수수료 등) 및 주식 배당은 고려하지 않음 (서로 상쇄된다고 가정)[cite: 113].
5. 이자율은 변동 없으며, 최초 100만 좌로 시작해 50만 좌 이하로 내려가지 않음[cite: 113].
"""


#%% [Sector 3] K10 펀드 구성을 위한 사전 준비 및 크롤링 세팅 (Images 114~116)
import datetime as dt[cite: 114]
from urllib.request import urlopen[cite: 114]
import bs4[cite: 114]
import pandas as pd[cite: 114]

# K10 지수 구성종목 10개 (2018년 4월 15일 시가총액 기준)[cite: 114]
# 삼성전자, SK하이닉스, 셀트리온, 삼성바이오로직스, 현대차, POSCO, LG화학, 삼성물산, NAVER, 현대모비스[cite: 114]
k10_component = ['005930', '000660', '068270', '207940', '005380', 
                 '005490', '051910', '028260', '035420', '012330'][cite: 115]

# 수집할 데이터를 담을 빈 딕셔너리 선언[cite: 116]
k10_outstanding = dict() # 발행주식 수[cite: 116]
k10_floating = dict()    # 유동비율[cite: 116]
k10_name = dict()        # 종목명[cite: 116]


#%% [Sector 4] 구성종목 기본정보 수집 함수 (Images 115~116)
def stock_info(stock_cd):
    # 네이버 금융(컴퍼니가이드) URL에 종목코드를 붙여 호출[cite: 115]
    url_float = 'http://companyinfo.stock.naver.com/v1/company/c1010001.aspx?cmp_cd=' + stock_cd[cite: 115]
    source = urlopen(url_float).read()[cite: 115]
    soup = bs4.BeautifulSoup(source, 'lxml')[cite: 115]
    
    # 해당 id 및 태그 위치에서 텍스트(발행주식수/유동비율) 추출 후 줄바꿈, 탭 등의 잉여 문자열 제거[cite: 115]
    tmp = soup.find(id='cTB11').find_all('tr')[6].td.text[cite: 115]
    tmp = tmp.replace('\r', '')[cite: 115]
    tmp = tmp.replace('\n', '')[cite: 115]
    tmp = tmp.replace('\t', '')[cite: 115]
    
    # '/' 기호를 기준으로 분리하여 tmp 리스트에 담음 (tmp[0]=발행주식수, tmp[1]=유동비율)[cite: 115]
    tmp = re.split('/', tmp)[cite: 115]
    
    # 1. 발행주식수 정제 및 정수형 변환[cite: 115]
    outstanding = tmp[0].replace(',', '')[cite: 115]
    outstanding = outstanding.replace('주', '')[cite: 115]
    outstanding = outstanding.replace(' ', '')[cite: 115]
    outstanding = int(outstanding)[cite: 115]
    
    # 2. 유동비율 정제 및 실수형 변환[cite: 115]
    floating = tmp[1].replace(' ', '')[cite: 115]
    floating = floating.replace('%', '')[cite: 115]
    floating = float(floating)[cite: 115]
    
    # 3. 종목명 추출[cite: 115]
    name = soup.find(id='pArea').find('div').find('div').find('tr').find('td').find('span').text[cite: 115]
    
    # 전역 딕셔너리에 종목코드를 키값으로 하여 저장[cite: 115, 116]
    k10_outstanding[stock_cd] = outstanding[cite: 115]
    k10_floating[stock_cd] = floating[cite: 116]
    k10_name[stock_cd] = name[cite: 116]

# 위에서 정의한 함수를 이용해 10개 종목 순환하며 데이터 수집[cite: 116]
# for stock_cd in k10_component:
#     stock_info(stock_cd)[cite: 116]

# 수집된 데이터를 판다스 데이터프레임으로 변환하여 확인[cite: 116]
# tmp = {'Outstanding' : k10_outstanding, 
#        'Floating' : k10_floating, 
#        'Name' : k10_name}[cite: 116]
# k10_info = pd.DataFrame(tmp)[cite: 116]
# print(k10_info)[cite: 116]


#%% [Sector 5] 일자별 주가 수집을 위한 날짜 포맷 함수 (Image 117)
"""
종목의 일자별 주가를 네이버에서 가져오기 전, 입력받은 날짜 문자열을 datetime 객체로 변환해주는 함수입니다[cite: 117].
"""
def date_format(d):
    d = str(d)[cite: 117]
    d = d.replace('/', '-')[cite: 117]
    d = d.replace('.', '-')[cite: 117]
    
    yyyy = int(d.split('-')[0])[cite: 117]
    # 연도가 2자리로 들어올 경우를 대비한 처리[cite: 117]
    if yyyy < 50:
        yyyy = yyyy + 2000[cite: 117]
    elif yyyy >= 50 and yyyy < 100:
        yyyy = yyyy + 1900[cite: 117]
        
    mm = int(d.split('-')[1])[cite: 117]
    dd = int(d.split('-')[2])[cite: 117]
    
    return dt.date(yyyy, mm, dd)[cite: 117]

# 과거 시세를 수집하는 메인 함수 구조 (크롤링 세부 로직은 다음 페이지로 이어짐)[cite: 117]
def historical_stock_naver(stock_cd, start_date='', end_date='', page_n=1, last_page=0):
    if start_date:
        start_date = date_format(start_date)[cite: 117]
    else:
        start_date = dt.date.today()[cite: 117]
        
    if end_date:
        end_date = date_format(end_date)[cite: 117]
    else:
        end_date = dt.date.today()[cite: 117]
        
    # 네이버 금융 시세 URL 구성[cite: 117]
    naver_stock = 'http://finance.naver.com/item/sise_day.nhn?code=' + stock_cd + '&page=' + str(page_n)[cite: 117]
    
    import datetime as dt
from urllib.request import urlopen
import bs4
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# (이전 채팅에서 만든 date_format, historical_stock_naver 함수의 뼈대가 있다고 가정합니다)
# 아래는 historical_stock_naver 함수의 내부 크롤링 핵심 로직입니다[cite: 118].
"""
# BeautifulSoup을 이용해 네이버 금융 시세 페이지(naver_stock)의 태그를 분석합니다[cite: 118].
source = urlopen(naver_stock).read()[cite: 118]
source = bs4.BeautifulSoup(source, 'lxml')[cite: 118]

# 'tah p10 gray03' 클래스를 가진 span 태그에서 날짜를, 'num' 클래스를 가진 td 태그에서 종가를 수집합니다[cite: 118].
dates = source.find_all('span', class_='tah p10 gray03')[cite: 118]
prices = source.find_all('td', class_='num')[cite: 118]

# 수집된 날짜와 종가를 매칭하여 historical_prices 딕셔너리에 저장합니다[cite: 118, 119].
# (페이지 내비게이션 및 다음 페이지 호출 로직은 생략합니다)[cite: 118, 119]
"""


#%% [Sector 1] K10 종목 주가 수집 및 결측치 보간 (Images 119~120)
"""
k10_component(10개 종목)를 순환하며 2017년 1년 치 시세를 수집하고 데이터프레임으로 만듭니다[cite: 119].
"""
# k10_historical_prices = dict()[cite: 119]
# for stock_cd in k10_component:
#     # start_date='2017-1-1', end_date='2017-12-31'로 수집[cite: 119]
#     historical_prices = historical_stock_naver(stock_cd, '2017-1-1', '2017-12-31')[cite: 119]
#     k10_historical_prices[stock_cd] = historical_prices[cite: 119]

# k10_historical_price = pd.DataFrame(k10_historical_prices)[cite: 119]

# 주가 데이터의 구멍(결측치, NaN)을 메우기 위해 보간(fill)을 수행합니다[cite: 119].
# method='ffill'은 앞의 데이터로 뒤를 채우는 방식이며, 혹시 맨 앞이 비어있을 경우를 대비해 'bfill'도 수행합니다[cite: 119, 120].
# k10_historical_price = k10_historical_price.fillna(method='ffill')[cite: 119]
# if k10_historical_price.isnull().values.any():[cite: 119]
#     k10_historical_price = k10_historical_price.fillna(method='bfill')[cite: 119]

# 삼성전자의 경우 2018년에 50대 1 액면분할을 했으므로, 과거 데이터(2017년)를 현재 기준에 맞추기 위해 50으로 나눕니다[cite: 120].
# k10_historical_price['005930'] = k10_historical_price['005930'] / 50[cite: 120]


#%% [Sector 2] K10 지수(Index) 산출하기 (Images 120~122)
"""
KOSPI200과 같은 방식의 '유동주식 비율을 반영한 시가총액' 비중을 구하여 지수를 산출합니다[cite: 120].
"""
# 1. 종목별 일자별 유동 시가총액 = 주가 * 발행주식수(Outstanding) * 유동비율(Floating) * 0.01[cite: 120]
# k10_historical_mc = k10_historical_price * k10_info['Outstanding'] * k10_info['Floating'] * 0.01[cite: 120]

# 2. 10개 종목의 시가총액 합(Market Cap) 구하기[cite: 120]
# k10 = pd.DataFrame()[cite: 120]
# k10['Market Cap'] = k10_historical_mc.sum(axis=1)[cite: 120]

# 3. 기준일(2017년 1월 2일) 시가총액을 100으로 설정하여 일자별 K10 인덱스 계산[cite: 121]
base_date = dt.date(2017, 1, 2)[cite: 121]
# k10['Index'] = k10['Market Cap'] / k10['Market Cap'][base_date] * 100[cite: 121]


#%% [Sector 3] KOSPI200 지수 수집 및 기준점 맞추기 (Images 123~125)
"""
K10 지수와 비교하기 위해 KOSPI200 지수도 크롤링합니다. (7장에서 만든 historical_index_naver 함수 재사용)[cite: 123, 124]
"""
# KOSPI200 수집 결과가 k200 데이터프레임의 'Index' 컬럼에 있다고 가정합니다[cite: 124, 125].
# k200 = pd.DataFrame({'Index' : kospi200})[cite: 124]

# 비교를 쉽게 하기 위해 K10 지수의 시작 기준값을 KOSPI200의 2017년 1월 2일 값(260.36)과 동일하게 맞춰 'Adj Index'에 저장합니다[cite: 125].
# k10['Adj Index'] = k10['Market Cap'] / k10['Market Cap'][base_date] * k200['Index'][base_date][cite: 125]


#%% [Sector 4] 두 지수의 그래프 비교 (Images 122~126)
"""
그래프를 그려 KOSPI200과 K10 지수(Adj Index)의 추이를 비교합니다[cite: 125].
"""
plt.rcParams['font.family'] = 'Malgun Gothic'[cite: 122]
plt.rcParams['axes.unicode_minus'] = False[cite: 122]
plt.rcParams['figure.figsize'] = (10, 5)[cite: 122]
plt.rcParams['lines.linewidth'] = 1[cite: 122] # 책에서는 '--' 오타로 보임[cite: 122]

# plt.plot(k10['Adj Index'], color='orange', label='K10')[cite: 125]
# plt.plot(k200['Index'], color='blue', label='KOSPI200')[cite: 125]
# plt.legend(loc=0)[cite: 125]
# plt.grid(True)[cite: 125]
# plt.show()
# 결과: 2017년 한 해 동안 KOSPI200보다 K10 지수가 수익률이 더 높은 것을 확인할 수 있습니다[cite: 126].


#%% [Sector 5] K10 펀드 운용 시뮬레이션 기본 세팅 (Images 126~127)
"""
본격적으로 펀드를 운용(설정 및 환매, 비중 산정)하는 단계입니다[cite: 126].
"""
# 1. 펀드 기본 정보 세팅[cite: 126]
CU = 50000              # Creation Unit: 설정과 환매의 기본 단위[cite: 126]
base_date = dt.date(2017, 1, 2) # 설정 기준일[cite: 126]
volume = 1000000        # 최초 설정 수량 (100만 좌)[cite: 126]
interest_rate = 0.02    # 펀드가 보유할 현금에 대한 이자율 (2%)[cite: 126]

# 2. 일일 설정 및 환매 시뮬레이션 함수[cite: 127]
# 펀드 운용 기간 중 매일 설정과 환매가 일어날 수 있으므로 random 함수를 이용해 가상의 수량을 발생시킵니다[cite: 127].
# np.random.randint(0, 5)는 0~4 사이의 임의의 정수를 반환합니다[cite: 127].
def creation_redemption(v):
    creation = np.random.randint(0, 5) * CU  # 0~4 단위의 임의의 설정 발생[cite: 127]
    
    # 펀드 수량이 최소 50만 좌 이상은 유지되도록 조건(if v > 500000)을 추가합니다[cite: 127].
    if v > 500000:
        redemption = np.random.randint(0, 5) * CU # 환매 발생[cite: 127]
    else:
        redemption = 0 # 50만 좌 이하면 환매 없음[cite: 127]
        
    volume = v + creation - redemption # 총 좌수 = 기존 좌수 + 설정 - 환매[cite: 127]
    return (creation, redemption, volume)[cite: 127]

# 3. 매일 주가 변동에 따른 종목별 보유 비중(Ratio) 산정[cite: 127]
# k10_stock_ratio = pd.DataFrame()[cite: 127]
# for s in k10_info.index:
#     # 각 종목의 시가총액을 K10 전체 시가총액으로 나눈 비중[cite: 127]
#     k10_stock_ratio[s] = k10_historical_mc[s] / k10_historical_mc.sum(axis=1)[cite: 127]

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# (이전 채팅의 k10_historical_price, k10_stock_ratio, base_date, k200 등의 변수가 메모리에 있다고 가정합니다.)

#%% [Sector 1] 일자별 펀드 NAV 및 설정/환매 변동 시뮬레이션 (Images 128~133)
Fund_NAV = pd.DataFrame() # 일자별 순자산가치 저장용[cite: 128]
Fund_Chg = pd.DataFrame() # 일자별 설정/환매 좌수 정보 저장용[cite: 128]

for d in k10_historical_price.index:
    # 1. 당일 주가 및 포트폴리오 비중 로드[cite: 128]
    stock_price = np.array(k10_historical_price.loc[d])[cite: 128]
    stock_weight = np.array(k10_stock_ratio.loc[d])[cite: 128]
    
    # 2. 전일까지의 주식 포트폴리오 NAV 계산[cite: 128, 129]
    if (d <= base_date): 
        # 기준일 이전 및 당일: 최초 주식 포트폴리오 보유량은 0[cite: 129]
        stock_holdings = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])[cite: 129]
        NAV_cash = 0 # 최초 현금 보유량 0[cite: 129]
    else: 
        # 기준일 이후: 전일까지 보유한 주식 수량 * 당일 주가 = 당일 주식 잔고[cite: 129]
        NAV_stock = sum(stock_holdings * stock_price)[cite: 129]
        NAV = NAV_stock + NAV_cash # 펀드 전체 잔고 = 주식 잔고 + 현금 잔고[cite: 129]
        
    # 3. 기준가격 산정[cite: 130]
    if (d <= base_date):
        # 비교가 쉽도록 기준일의 펀드 기준가를 KOSPI200 지수 * 100으로 맞춤[cite: 129, 130]
        price = k200['Index'][base_date] * 100[cite: 130]
    else:
        # 이후 기준가 = 전체 순자산가치(NAV) / 총 좌수(volume)[cite: 129, 130]
        price = NAV / volume[cite: 130]
        
    # 4. 신규 펀드 설정 및 환매 반영[cite: 130]
    if (d == base_date):
        volume = 0 # 펀드 시작 전[cite: 130]
        volume_chg = 1000000 # 첫날 100만 주 설정[cite: 130]
    else:
        # 임의의 값으로 설정/환매 수량 발생[cite: 130]
        vol = creation_redemption(volume)[cite: 130]
        volume_chg = vol[0] - vol[1] # 좌수 변동 = 설정 - 환매[cite: 130]
        
    volume = volume + volume_chg # 당일 변동분을 총 펀드 좌수에 반영[cite: 130]
    aum_chg = price * volume_chg # 펀드 입출금액 = 당일 기준가 * 변동 좌수[cite: 130]
    
    # 5. 당일 신규 주식 거래량 및 매매 금액 계산[cite: 130, 131]
    # 종목별 거래량 = 입출금액 * 종목비중 / 종목주가 (소수점 버림)[cite: 130, 131]
    stock_trade = np.floor(price * volume_chg * stock_weight / stock_price)[cite: 131]
    trade_amt = sum(stock_trade * stock_price) # 실제 주식 매매 금액[cite: 131]
    cash_chg = aum_chg - trade_amt # 현금 잔고 변동 = 펀드 입출금액 - 주식 매매 금액[cite: 131]
    
    # 6. 총 보유량 및 NAV 업데이트[cite: 131]
    stock_holdings = stock_holdings + stock_trade # 총 주식 보유량 누적[cite: 131]
    cash_holdings = np.floor(NAV_cash * np.exp(interest_rate/365)) # 이자율을 반영한 전일 현금 잔고 증가분[cite: 131]
    
    NAV_stock = sum(stock_holdings * stock_price) # 마감 기준 당일 주식 잔고[cite: 131]
    NAV_cash = cash_holdings + cash_chg # 마감 기준 당일 현금 잔고[cite: 131]
    NAV = NAV_stock + NAV_cash # 펀드 전체 순자산가치(NAV) 확정[cite: 131]
    
    # 7. 결과를 데이터프레임에 누적 저장[cite: 131, 132]
    date = pd.Series(d)[cite: 131]
    NAV_tmp = {'Stock': NAV_stock, 'Cash': NAV_cash, 'Total': NAV, 'Price': price}[cite: 132]
    tmp = pd.DataFrame(NAV_tmp, index=date)[cite: 132]
    Fund_NAV = Fund_NAV.append(tmp) # NAV 정보 누적[cite: 132]
    
    Chg_tmp = {'Amount Change': aum_chg, 'Trade Amount': trade_amt, 'Cash Change': cash_chg}[cite: 132]
    tmp = pd.DataFrame(Chg_tmp, index=date)[cite: 132]
    Fund_Chg = Fund_Chg.append(tmp) # 입출금 변동 정보 누적[cite: 132]


#%% [Sector 2] 펀드 수익률 vs 지수 수익률 비교 (Images 134~135)
"""
기준일(2017년 1월 2일)부터의 YTD(Year to Date) 누적 수익률을 그래프로 확인합니다[cite: 134].
수익률 공식 = (당일 지수 - 기준일 지수) / 기준일 지수 * 100[cite: 134]
"""
# Earnings = pd.DataFrame()[cite: 134]
# Earnings['K10'] = (k10['Index'] - k10['Index'][base_date]) / k10['Index'][base_date] * 100[cite: 134]
# Earnings['KOSPI200'] = (k200['Index'] - k200['Index'][base_date]) / k200['Index'][base_date] * 100[cite: 134]
# Earnings['Fund'] = (Fund_NAV['Price'] - Fund_NAV['Price'][base_date]) / Fund_NAV['Price'][base_date] * 100[cite: 134]

# ax = Earnings.plot(color=['orange', 'blue', 'red'])[cite: 134]
# ax.set_ylabel('(수익률, %)')[cite: 134]
# ax.grid(True)[cite: 134]
# plt.show()
# 해석: K10 지수와 K10 펀드의 수익률은 거의 일치(선이 겹침)하며, 둘 다 KOSPI200 수익률보다 높은 움직임을 보였습니다[cite: 135].


#%% [Sector 3] 일간 수익률 비교 (Image 136)
"""
펀드는 YTD 누적 수익률뿐만 아니라 단기 투자자를 위한 '일간 수익률' 추이도 중요합니다[cite: 136].
- 일간 수익률 공식 = (당일 기준가격 - 전일 기준가격) / 전일 기준가격 * 100[cite: 136]
- 판다스의 .shift(1) 메서드를 사용해 전일 데이터를 쉽게 가져와 계산합니다[cite: 136].
"""
# Daily = pd.DataFrame()[cite: 136]
# Daily['K10'] = (k10['Index'] - k10['Index'].shift(1)) / k10['Index'].shift(1) * 100[cite: 136]
# Daily['K200'] = (k200['Index'] - k200['Index'].shift(1)) / k200['Index'].shift(1) * 100[cite: 136]
# Daily['Fund'] = (Fund_NAV['Price'] - Fund_NAV['Price'].shift(1)) / Fund_NAV['Price'].shift(1) * 100[cite: 136]

# ax = Daily.plot(color=['orange', 'blue', 'red'], alpha=0.7)[cite: 136]
# ax.set_ylabel('(%)')[cite: 136]
# ax.grid(True)[cite: 137]
# plt.show()
# 해석: KOSPI200(200개 종목)보다 K10 펀드(10개 종목)가 분산 효과가 작아 변동성(상하 폭)이 더 큼을 확인할 수 있습니다[cite: 137].


#%% [Sector 4] 추적오차 (Tracking Error) 분석 (Images 137~138)
"""
추적오차(Tracking Error)는 펀드가 벤치마크 지수를 얼마나 잘 쫓아가는지를 나타내는 지표입니다[cite: 137].
- 매일매일의 일간 추적오차율 = 펀드 일간 수익률 - 지수 일간 수익률[cite: 137]
"""
# 1. KOSPI200 대비 K10 펀드의 일간 추적오차율[cite: 137]
# fig = plt.figure()[cite: 137]
# ax = fig.add_subplot(1, 1, 1)[cite: 137]
# Daily['TE200'] = Daily['Fund'] - Daily['K200'][cite: 137]
# Daily['TE200'].plot(ax=ax)[cite: 137]
# ax.grid(True)[cite: 137]
# plt.show()
# 해석: 오차가 주로 ±1.0 이내, 최대 ±1.8 정도 벌어집니다. 10개 종목만으로도 200개 종목 지수를 어느 정도 따라가며 운용이 가능함을 시사합니다.

# 2. 본래 벤치마크인 K10 지수 대비 추적오차율
# Daily['TE10'] = Daily['Fund'] - Daily['K10']
# Daily['TE10'].plot()
# plt.show()
# 해석: K10 지수와의 추적오차는 최대 ±0.02 수준으로 아주 미미하게 나타납니다 (거의 완벽하게 추적).