
#%%
# ==========================================
# 금융 데이터 수집 방법 4가지 및 API 개념 정리
# ==========================================
# [기타 판다스 주요 기능]
# concat, append, merge (데이터프레임 합치기), unique (유일한 값 추출),
# map, apply (빠른 함수 연산), groupby, join, drop, del, reset_index, rename 등

# [금융 및 주가 데이터를 가져오는 4가지 방법]
# 1) 데이터 구매: 코스콤 데이터 몰(일별 Interday, 일 중 Intraday), 블룸버그/톰슨 로이터 등. 데이터 수집 최소화 및 문제 해결 요청이 용이하나 구독 비용 고려 필요
# 2) 증권사 API 이용: 개인 사용자가 애용. 직접 프로그래밍하는 유연성이 있으나 초기 진입이 어렵고 데이터 적재 검증이 번거로움
# 3) 금융 웹 페이지 크롤링: 네이버, 구글, 에프앤가이드 등에서 수집. 단시간 과다 요청 시 서버 접근 차단 주의
# 4) 금융 데이터 제공 오픈 API 사용: 파이썬 환경에 라이브러리를 설치해 사용. 간단한 작업이나 아이디어 검증에 가장 편리하나 내부적으로 크롤링을 사용하므로 과다 사용 시 접근 차단 및 접근 데이터 제한 단점 존재

# [API(Application Programming Interface)의 개념]
# - 응용프로그램에서 데이터를 주고받기 위한 규격이자 프로그래밍적 권한을 가진 기능
# - 오픈 API는 누구나 사용할 수 있도록 공개된 API를 의미함

#%%
# ==========================================
# 파이썬 구조 개념: 모듈, 패키지, 라이브러리, API
# ==========================================
# 1) 모듈(Module): file.py처럼 전역변수, 함수, 클래스 등을 모아둔 파일 (파일명이 곧 모듈명)
# [예시: hello.py 파일 내용]
# name = '철수'
# def hello():
#     print('안녕 ', name)

# 모듈 임포트 및 함수 호출
import hello
hello.hello()

#%%
# 2) 패키지(Package): 모듈을 디렉터리 형식으로 묶어 놓은 것 (패키지 내 __init__.py 파일 존재가 특징)
# [예시: tools 패키지 구조]
# tools/
#   ├── calc_fomula.py
#   ├── logger.py
#   ├── visualize.py
#   └── __init__.py

# [__init__.py 파일 내용 예시] - 패키지 임포트 시 제일 먼저 호출됨
# from . import visualize
# from . import logger
# from . import calc_formula

# [visualize.py 파일 내용 예시]
# def visual():
#     print('visual() 함수 호출 ')

# 방법 1: 패키지 전체 임포트 후 하위 모듈 및 함수 호출 (__init__.py가 정의되어 있어 직접 접근 가능)
import tools
tools.visualize.visual()

# 방법 2: 패키지 디렉터리에서 특정 모듈만 직접 임포트하여 호출
from tools import visualize
visualize.visual()

#%%
# 3) 라이브러리(Library): 다른 프로그램에서 사용하기 위해 미리 만들어놓은 모듈/패키지들의 집합체 (예: 파이썬 표준 라이브러리)
# 4) API: 특정 프로그램을 만들기 위해 제공되는 기능의 묶음(모듈/라이브러리 형태) + 기능 사용 설명서

# [라이브러리 및 API 설치 명령어 (터미널/프롬프트)]
# pip install "라이브러리명"
# ex) pip install numpy
# ex) pip install pandas

# 라이브러리 호출 및 as 별칭(alias) 지정
import numpy
import numpy as np
import pandas
import pandas as pd

#%%
# ==========================================
# FinanceDataReader 사용법 - 상장 종목 리스트 조회
# ==========================================
# FinanceDataReader: pandas-datareader의 불안정성(야후/구글 파이낸스 API 중단 등)을 보완하고자 만든 API
# 제공 데이터: 한국/미국 주식 가격, 지수, 환율, 암호화폐 가격, 종목 리스트 등

# [설치 명령어]
# pip install -U finance-datareader

import FinanceDataReader as fdr

# 한국 거래소(KRX: KOSPI, KODAQ, KONEX)에 상장된 모든 종목 리스트 가져오기
df_krx = fdr.StockListing('KRX')
print(len(df_krx))
df_krx.head()

# 미국 S&P 500에 등록된 모든 종목 리스트 가져오기 (그 외 NASDAQ, NYSE, AMEX 지원)
df_spx = fdr.StockListing('S&P500')
df_spx.head()
print(len(df_spx))
df_spx.head()

#%%
# ==========================================
# FinanceDataReader 사용법 - 국내외 주가 및 금융 데이터 조회
# ==========================================
# 한국 거래소 상장 종목은 단축 코드(여섯 자리)를 전달하여 가격 데이터 조회
df = fdr.DataReader('001250', '2025')  # GS글로벌, 2025년
df.head(10)
df['Close'].plot()

# 미국 종목은 티커(Ticker, 네 자리 제한)명을 사용하여 가격 데이터 조회
df = fdr.DataReader('AAPL', '2025')  # 애플(AAPL), 2025년
df.head(10)
df['Close'].plot()

#%%
# [DataReader() 주요 지원 자산 및 심볼 정리]
# - 국내 주식: 005930(삼성전자), 091990(셀트리온헬스케어) 등
# - 해외 주식: AAPL(애플), AMZN(아마존), GOOG(구글) 등 (미국 외 해외 주식은 인베스팅닷컴 활용 가능)
# - 각종 지수: KS11(코스피 지수), KQ11(코스닥 지수), DJI(다우 지수), IXIC(나스닥 지수), US500(S&P500)
# - 환율 데이터: USD/KRX(원달러 환율), USD/EUR(달러당 유로화 환율), CNY/KRW(위안화 원화 환율)
# - 암호화폐 가격: BTC/USD(비트코인 달러 가격, 비트파이넥스), BTC/KRW(비트코인 원화 가격, 빗썸)

df = fdr.DataReader('AAPL', '2025-01-01', '2025-03-30')  # 애플(AAPL), 2025-01-01 ~ 2025-03-30
df = fdr.DataReader('KS11', '2025')                      # KS11 (KOSPI 지수), 2025년~현재
df = fdr.DataReader('USD/KRW', '2025')                   # 원달러 환율, 2025년~현재
df = fdr.DataReader('BTC/KRW', '2025')                   # 비트코인 원화 가격 (빗썸), 2025년~현재

#%%
# ==========================================
# 인베스팅닷컴(Investing.com) 해외 종목 조회 및 거래소 코드
# ==========================================
# 미국 이외의 해외 주식 종목명을 모를 경우 인베스팅닷컴(Markets -> Stocks -> Asia 등)의
# 국가별 주식시장 콤보 박스에서 각 시장에 상장된 종목 리스트와 심볼을 확인할 수 있음
# 현재 API를 통해 한국, 미국, 중국, 일본, 홍콩 거래소에 상장된 종목 조회 가능

# API에서 제공하는 거래소 코드 매핑
exchange_map = {
    'KRX': 'Seoul', '한국 거래소': 'Seoul',
    'NASDAQ': 'NASDAQ', '나스닥': 'NASDAQ',
    'NYSE': 'NYSE', '뉴욕증권거래소': 'NYSE',
    'AMEX': 'AMEX', '미국증권거래소': 'AMEX',
    'SSE': 'Shanghai', '상해': 'Shanghai', '상하이': 'Shanghai',
    'SZSE': 'Shenzhen', '심천': 'Shenzhen',
    'HKEX': 'Hong Kong', '홍콩': 'Hong Kong',
    'TSE': 'Tokyo', '도쿄': 'Tokyo',
}

#%%
# ==========================================
# 해외 주식 데이터 조회 - 일본(TSE) 및 중국(SSE)
# ==========================================
# 일본 도쿄 거래소(TSE)에 상장된 캐논(Canon Inc., 7751) 주가 조회
# exchange 매개변수에 영문 거래소 코드('TSE') 또는 한글명('도쿄') 모두 전달 가능
jp_df1 = fdr.DataReader(symbol='7751', start='2025-01-01', exchange='TSE')  # 캐논
jp_df2 = fdr.DataReader(symbol='7751', start='2025-01-01', exchange='도쿄')  # 캐논

# 종가(Close) 선 그래프 시각화 (홈페이지 차트와 일치 확인)
jp_df2['Close'].plot()

#%%
# 중국 상해 거래소(SSE)에 상장된 중국 철도 건설 공사(601186) 주가 조회
# 중국 철도 건설 공사(601186)
ch_df1 = fdr.DataReader(symbol='601186', start='2025-01-01', exchange='SSE')
# 중국 철도 건설 공사(601186)
ch_df2 = fdr.DataReader(symbol='601186', start='2025-01-01', exchange='상해')

# 종가(Close) 선 그래프 시각화
ch_df1['Close'].plot()

# [오픈 API 활용 시 참고사항]
# - FinanceDataReader는 한국어 매뉴얼과 예제가 잘 되어 있어 쉽게 배울 수 있음
# - 다만 외부 웹페이지에서 데이터를 가져오는 구조상 서비스 중단이나 URL 요청 포맷 변경 시
#   직접 코드를 수정·보완하여 유연하게 대응할 수 있어야 함