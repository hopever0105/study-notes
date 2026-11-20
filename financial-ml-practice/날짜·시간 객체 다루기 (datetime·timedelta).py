#%%

# 날짜·시간 객체 다루기 (datetime·timedelta)

#%%
# ==========================================
# 왜 필요한가
# ==========================================
# 주가 데이터는 전부 "날짜가 붙은 숫자"다.
# 리밸런싱 날짜 계산, 보유 기간(며칠 들고 있었나), 장 마감 시각 비교 같은 걸 하려면
# 파이썬 표준 라이브러리 datetime의 객체 4개를 알아야 한다.
#
#   time      : 시각만   (시, 분, 초, 마이크로초)          예) 15:30:00
#   date      : 날짜만   (년, 월, 일)                       예) 2026-11-20
#   datetime  : 날짜+시각 (date + time 합친 것)             예) 2026-11-20 15:30:00
#   timedelta : 두 시점 사이의 "간격"                        예) 31일, 3시간
#
# 객체 구조 (파이썬 공식 문서 기준)
#   object
#       timedelta
#       tzinfo
#           timezone
#       time
#       date
#           datetime      <- date를 상속받아 시각 정보까지 붙인 것

import datetime

#%%
# ==========================================
# 1. time 객체 : 날짜와 상관없는 시각
# ==========================================
# 매개변수 이름을 써도 되고, 순서대로(시, 분, 초, 마이크로초) 넣어도 된다.
t1 = datetime.time(hour=4, minute=3, second=10, microsecond=1000)
t2 = datetime.time(4, 3, 10)
print(t1)          # 04:03:10.001000
print(t2)          # 04:03:10

# 허용 범위
#   0 <= hour        < 24
#   0 <= minute      < 60
#   0 <= second      < 60
#   0 <= microsecond < 1,000,000   (1초 = 100만 마이크로초)
#
# 범위를 넘으면 ValueError가 난다.
try:
    datetime.time(24, 0, 0)
except ValueError as e:
    print('에러:', e)

# 활용 예: 장 마감(15:30) 이후 데이터인지 판단
market_close = datetime.time(15, 30)
now_time = datetime.time(16, 5)
print('장 마감 후인가?', now_time > market_close)   # True

#%%
# ==========================================
# 2. date 객체 : 달력 날짜
# ==========================================
d1 = datetime.date(year=2019, month=1, day=10)
d2 = datetime.date(2019, 2, 10)
print(d1, d2)

# 허용 범위
#   MINYEAR(1) <= year <= MAXYEAR(9999)
#   1 <= month <= 12
#   1 <= day   <= 그 해 그 달의 일 수 (윤년 2월은 29일)
print('MINYEAR =', datetime.MINYEAR, '/ MAXYEAR =', datetime.MAXYEAR)

# 2월 30일 같은 없는 날짜는 에러
try:
    datetime.date(2019, 2, 30)
except ValueError as e:
    print('에러:', e)

# 자주 쓰는 속성·메서드
today = datetime.date.today()
print('오늘:', today)
print('년/월/일:', today.year, today.month, today.day)
print('요일(월=0 ... 일=6):', today.weekday())    # 5, 6이면 주말 -> 장 안 열림
print('ISO 문자열:', today.isoformat())           # '2026-11-20' 형태

#%%
# ==========================================
# 3. datetime 객체 : 날짜 + 시각
# ==========================================
dt = datetime.datetime(year=2019, month=10, day=24,
                       hour=4, minute=3, second=10, microsecond=1000)
print(dt)    # 2019-10-24 04:03:10.001000

# 매개변수 범위는 date의 년/월/일 + time의 시/분/초/마이크로초를 그대로 따른다.
# datetime은 하루를 정확히 3600 * 24 = 86,400초로 가정한다 (윤초 무시).

# date 부분, time 부분 따로 꺼내기
print('날짜 부분:', dt.date())
print('시각 부분:', dt.time())

# date + time 을 합쳐서 datetime 만들기
merged = datetime.datetime.combine(datetime.date(2026, 11, 20), datetime.time(15, 30))
print('합친 것:', merged)

# 문자열 <-> datetime 변환 (데이터 파일 날짜 열 처리할 때 가장 많이 씀)
#   strptime : 문자열 -> datetime   (p = parse)
#   strftime : datetime -> 문자열   (f = format)
s = '20261120'
parsed = datetime.datetime.strptime(s, '%Y%m%d')
print('문자열 -> datetime:', parsed)
print('datetime -> 문자열:', parsed.strftime('%Y-%m-%d'))

#%%
# ==========================================
# 4. timedelta 객체 : 두 시점 사이의 간격
# ==========================================
# (1) timedelta를 직접 만들어 날짜에 더하기
td = datetime.timedelta(days=100)               # 100일
after_100 = datetime.datetime(2019, 1, 1) + td
print('2019-01-01 + 100일 =', after_100)        # 2019-04-11 00:00:00

# 숫자로 확인:
#   1월 남은 날 30일(2~31일) + 2월 28일 + 3월 31일 = 89일 -> 3월 31일
#   100 - 89 = 11일 더 -> 4월 11일

# (2) 두 datetime을 빼면 timedelta가 나온다
dt1 = datetime.datetime(2019, 1, 1, 14)
dt2 = datetime.datetime(2019, 2, 1, 14)
gap = dt2 - dt1
print('간격:', gap, '/ 타입:', type(gap))       # 31 days, <class 'datetime.timedelta'>
print('일 수:', gap.days)
print('총 초:', gap.total_seconds())             # 31 * 86400 = 2,678,400초

# timedelta 내부 저장 범위 (days, seconds, microseconds 세 칸으로 정규화됨)
#   -999,999,999 <= days <= 999,999,999
#   0 <= seconds < 86,400 (하루 안의 초)
#   0 <= microseconds < 1,000,000
# 예) timedelta(hours=25) -> days=1, seconds=3600 으로 저장됨
x = datetime.timedelta(hours=25)
print('25시간 =', x.days, '일', x.seconds, '초')

# 음수 간격은 days만 음수로 두고 seconds는 양수로 맞춘다
y = datetime.timedelta(hours=-1)
print('-1시간 =', y.days, '일', y.seconds, '초')   # -1일 + 82,800초 = -3,600초

#%%
# ==========================================
# 5. 퀀트에서 쓰는 예 : 보유 기간과 연환산 수익률
# ==========================================
# 매수 2025-03-10 100원 -> 매도 2025-09-22 112원
buy_date = datetime.date(2025, 3, 10)
sell_date = datetime.date(2025, 9, 22)
buy_price = 100
sell_price = 112

hold_days = (sell_date - buy_date).days
period_return = sell_price / buy_price - 1
annual_return = (1 + period_return) ** (365 / hold_days) - 1

print('보유 일수:', hold_days)                              # 196일
print('기간 수익률: {:.2%}'.format(period_return))           # 12.00%
print('연환산 수익률: {:.2%}'.format(annual_return))         # 약 23.5%
# 계산 과정: 1.12 ^ (365/196) = 1.12 ^ 1.862 = 약 1.235 -> 23.5%

#%%
# ==========================================
# 6. 판다스에서 같은 일 하기 (실제 데이터는 대부분 여기서 처리)
# ==========================================
import pandas as pd

# 날짜 문자열 열을 datetime으로
df = pd.DataFrame({'Date': ['2026-11-16', '2026-11-17', '2026-11-18',
                            '2026-11-19', '2026-11-20'],
                   'Close': [100, 102, 101, 105, 107]})
df['Date'] = pd.to_datetime(df['Date'])
df = df.set_index('Date')

# 요일, 월말 여부 같은 정보 뽑기
df['요일'] = df.index.dayofweek          # 월=0
df['월'] = df.index.month
print(df)

# pd.Timedelta, pd.DateOffset
print(pd.Timestamp('2026-11-20') + pd.Timedelta(days=30))
print(pd.Timestamp('2026-11-20') + pd.DateOffset(months=1))   # 달력 기준 한 달 뒤

# 영업일(주말 제외) 날짜 목록 : 공휴일은 따로 빼야 함 (거래소 캘린더 파일 참고)
bdays = pd.bdate_range('2026-11-16', '2026-11-30')
print('영업일 수:', len(bdays))

# 월말 리밸런싱 날짜 뽑기 : 각 달의 마지막 거래일
idx = pd.bdate_range('2026-01-01', '2026-06-30')
month_end = pd.Series(idx, index=idx).groupby([idx.year, idx.month]).last()
print(month_end.values)
