# -*- coding: utf-8 -*-

# 기술통계와 추론통계 
# 모수추정 분석 프로세스
# 1. 데이터 로드 및 탐색
# pandas로 데이터 불러오고 기초통계랑 확인하여 데이터 분포 파악

# 2. 분석 대상 필터링
# 전체 문제가 요구하는 특정집단 또는 필욯나 변수만을 추출

# 3. 점추정
# 표본으로부터 계산된 값 ㅣㅇ용 모수를 하나의 수치로 추정
# 평군 : data.mean(), 비율: 성공/전체

# 4. 구간추정
#statsmodels(sms) 함수 활용 신뢰구간 계산
# 분석 대상 따라 tconfint_mean 또는 proportion_confit 함수 사용

# 5. 결과 해석 

#%% 
# 통계도구 선정
# 1. 모평균 분석 
# (1) 모분산을 모를 때 (일반적)
# 점추정: data.mean()
# 신뢰구간: sms.DescrStatsW(data).tconfint)mean()

# (2) 모분산 알 떄 
# 점추정 : data.mean()
# 신뢰구간: sms.DescrStatsW(data).zconfint_mean()


#2. 모비율 분석
# 표본이 충분한 경우 
# 점추정: count/nobs
# 신뢰구간: sms/proportion_confint(count, nobs, alpha, ...)


#%% 
# 신뢰구간 
#1. 모평균의 신뢰구간
# sms.DescrStatsW()

#(1) 파라미터: alpha
# 유의수준(1-cl), 95%면 0.05 입력

#(2) 파라미터: alternative 
# 검정방향(양측/단축) , 기본값 two-sided임.


#2. 모비율의 신뢰구간
# sms.proportion_confint()
# (1) 파라미터 count
# 관심 사건의 발생 횟수 ex: 불량품 수, 찬성인원 등

# (2) 파라미터 nobs 
# 전체 표본의 크기 ,  ex: 데이터 전체개수

# (3) 파라미터 alpha
# 유의수준 (1-cl), 95신뢰구간일 경우 0.05

# (4) 파라미터 method 
# 계산방식, 일반적으로 normal(정규근사) 사용


#%% 모수추정 데이터 불러오기 
# 삼성전자 2025년 일간 수익률 평균 신뢰구간 / 오른 날 비율 신뢰구간
import pandas as pd
import statsmodels.stats.api as sms

# 0. 데이터 불러오기 — code는 글자로 읽어야 앞자리 0이 안 사라짐 (005930)
df = pd.read_csv("../data/prices.csv",   # adp-python/04_통계분석 폴더에서 실행 기준
                 dtype={'code': str}, parse_dates=['date'])
s = df[df['code'] == '005930'].sort_values('date').set_index('date')['close']   # 삼성전자 종가
r = s.pct_change().dropna() * 100          # 일간 수익률(%) = (오늘/전날 - 1) × 100, 첫날은 빈칸이라 제거
r25 = r['2025-01-01':'2025-12-31']         # 2025년만
print(len(r25))                            # 242 (거래일 수)

# pct_change() = 각 칸을 바로 앞 칸과 비교한 변화율을 구하는 함수 
# %% ① 평균의 점추정·구간추정 (
point_mean = r25.mean()
print(f"점추정치(평균 일간 수익률): {point_mean:.4f}%")      # 0.3596%

res = sms.DescrStatsW(r25)                     # 데이터를 통계 계산용 상자에 담기
ci = res.tconfint_mean(alpha=0.05)             # t분포로 평균의 95% 신뢰구간
print(f"95% 신뢰구간: [{ci[0]:.4f}%, {ci[1]:.4f}%]")        # [0.0855%, 0.6336%]

# 손으로 계산하면: 평균 ± t값 × (표준편차 / √표본수)
#   표준편차 2.1641, 표본수 242 → 표준오차 = 2.1641 / √242 = 0.1391
#   t값(자유도 241, 95%) ≈ 1.97
#   0.3596 ± 1.97 × 0.1391 = 0.3596 ± 0.274 → [0.086, 0.634]
# 해석: 2025년 삼성전자의 "진짜" 평균 일간 수익률은 0.09%~0.63% 사이라고 95% 믿을 수 있다.
#       구간이 0보다 위에 있다 → 2025년엔 평균적으로 오른 해였다고 말할 수 있음


# %% ② 비율의 점추정·구간추정 (교재의 불량률 예시와 같은 방법)
n_total = len(r25)                   # 전체 거래일 242
n_up = int((r25 > 0).sum())          # 오른 날 수 131  (True를 더하면 1로 셈)
p_hat = n_up / n_total
print(f"오른 날 비율 점추정치: {p_hat:.4f}")              # 0.5413

ci_p = sms.proportion_confint(count=n_up, nobs=n_total, alpha=0.05, method='normal')
print(f"95% 신뢰구간: [{ci_p[0]:.4f}, {ci_p[1]:.4f}]")   # [0.4785, 0.6041]

# 손으로 계산하면: p ± 1.96 × √(p(1-p)/n)
#   √(0.5413 × 0.4587 / 242) = 0.0320 → 0.5413 ± 1.96 × 0.0320 = 0.5413 ± 0.0628
# 해석: 구간 안에 0.5(반반)가 들어 있다
#   → "오른 날이 내린 날보다 많다"고 95% 수준에서 말할 수 없음
#   평균 수익률은 플러스로 확실한데, 오른 날 비율은 반반과 구별이 안 됨
#   → 2025년 상승은 "자주 오른 것"보다 "오를 때 크게 오른 것"에 가까움


# %% 모평균 
# a 택배사가 배송 서비스 품질 개선 위해 실제 배송소요 시간 분석 원함
# 무작위로 추출된 50개 배송기록으로 전체 배송 시간 평균 추정 
# 유의수준 0.05 
# 구할것은 A사 배송시간 평균에 대한 점추정치와
# 전체 배송시간 평균에 대한 95% 신뢰구간 산출 해석

import pandas as pd
import statsmodels.stats.api as sms

# 1. 데이터 로드
df = pd.read_csv('https://raw.githubusercontent.com/ADPclass/ADP_book_ver01/main/data/delivery_data.csv')
a_time = df[df['company'] == 'A']['delivery_time']

# 2. 점추정 (pandas 활용)
point_mean = a_time.mean()
print(f"점추정치(평균): {point_mean:.2f}분")

# 3. 구간추정 (statsmodels의 DescrStatsW 활용)
# 데이터를 DescrStatsW에 담고, .tconfint_mean()만 호출하면 끝!
res = sms.DescrStatsW(a_time)
conf_int_mean = res.tconfint_mean(alpha=0.05)

print(f"95% 신뢰구간: {conf_int_mean}")
# 표본표준편차 사용 (모집단분산모름) 자유도 n-1 =49인 t-분포 신뢰구간 사용 [131.51,137.90]
# %% 모비율
# 품질 검사 위해 100개 샘플 무작위 추출 8개 불량품 판정 유의수준 0.05
# 1. 생산라인 전체 불량률 점추정치 구하기
# 2. 전체 불량률 95% 신뢰구간 산출하기 

import pandas as pd
import statsmodels.stats.api as sms

# 데이터 로드
df = pd.read_csv('https://raw.githubusercontent.com/ADPclass/ADP_book_ver01/main/data/manufacturing_quality.csv')

#%% 1. 빈도 파악
n_total = 100
n_fail = 8

#%% 2. 점추정
p_hat = n_fail / n_total
print(f"불량률 점추정치: {p_hat:.4f}")

#%% 3. 구간추정
# alpha=0.05는 95% 신뢰구간을 의미합니다.
conf_int_prop = sms.proportion_confint(count=n_fail, 
                                       nobs=n_total, 
                                       alpha=0.05, 
                                       method='normal')

print(f"불량률 95% 신뢰구간: {conf_int_prop}")

# %% [markdown]
# [소문항 1 답안]표본 100개 중 불량품이 8개이므로 표본 비율 p = 8/100 = 0.08이다. \
# 표본 비율은 모비율의 불편추정량이므로, 해당 생산 라인 전체의 불량률에 대한 **점추정치는 0.08(또는 8%)**이다.

# %% [markdown]
# [소문항 2 답안]95% 신뢰수준 하에서 전체 불량률에 대한 신뢰구간을 산출한 결과 [0.0268, 0.1332]이다. \
# 이는 모집단인 생산 라인 전체의 실제 불량률이 약 2.68%에서 13.32% 사이에 존재할 것이라고 95% 신뢰할 수 있음을 의미한다.


