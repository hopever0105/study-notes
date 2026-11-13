# -*- coding: utf-8 -*-
# 범주끼리 관련 있는지 검정 (카이제곱)
# 언제 쓰나: 매수·매도 주문 비율이 반반인지, 매수 신호가 켜진 날과 다음 날 상승이 관련 있는지,
#            고객 투자성향과 고르는 상품 종류가 관련 있는지

# Spyder: 구역(# %%)마다 Ctrl+Enter, 전체는 F5


import numpy as np
import pandas as pd
from scipy.stats import chisquare, chi2_contingency, chi2

# %% 2-1. 매수·매도 주문 비율이 50:50인가
rng = np.random.default_rng(11)
orders = pd.DataFrame({'side': rng.choice(['매수', '매도'], size=300, p=[0.57, 0.43])})

side_cnt = orders['side'].value_counts()
print(side_cnt)

n = side_cnt.sum()
chi_side = chisquare(side_cnt, f_exp=[n / 2, n / 2])     # 기대도수는 합이 관측 합과 같아야 함
print('<매수·매도 50:50 적합도 검정>\n', chi_side)

# %% 2-2. 비율이 반반이 아닐 때: 주문이 시간대에 정해진 비율로 들어오나
# 귀무가설: 장 시작 30분 20%, 오전 30%, 점심 15%, 오후 25%, 장 마감 30분 10%
rng = np.random.default_rng(12)
slots = ['장시작', '오전', '점심', '오후', '장마감']
obs_slot = pd.Series(rng.choice(slots, size=500, p=[0.26, 0.28, 0.12, 0.22, 0.12])).value_counts()
obs_slot = obs_slot.reindex(slots)      # 순서를 기대 비율과 똑같이 맞춤 (안 맞추면 엉뚱한 칸끼리 비교)
print(obs_slot)

exp_ratio = np.array([0.20, 0.30, 0.15, 0.25, 0.10])
exp_slot = exp_ratio * obs_slot.sum()
print('기대도수:', exp_slot)

chi_slot = chisquare(obs_slot, f_exp=exp_slot)
print('<시간대 비율 적합도 검정>\n', chi_slot)
# 자유도 = 5 - 1 = 4, 임계값(α=0.05) = 9.49
print('임계값:', round(chi2.ppf(0.95, df=4), 2))


# ================================================================
# 3. 금융판 독립성 검정
# ================================================================

# %% 3-1. 매수 신호와 다음 날 방향 (2×2)
# 연습 데이터: 신호 켜진 날은 다음 날 상승 확률 55%, 꺼진 날은 50%로 만듦 (아주 약한 신호)
rng = np.random.default_rng(21)
n_day = 500
signal = rng.choice(['켜짐', '꺼짐'], size=n_day, p=[0.4, 0.6])
up_prob = np.where(signal == '켜짐', 0.55, 0.50)
next_up = np.where(rng.random(n_day) < up_prob, '상승', '하락')
sig = pd.DataFrame({'signal': signal, 'next_dir': next_up})

table_sig = pd.crosstab(sig['signal'], sig['next_dir'])
print(table_sig)
print(pd.crosstab(sig['signal'], sig['next_dir'], normalize='index').round(3))   # 행마다 비율

chi_s, p_s, dof_s, exp_s = chi2_contingency(table_sig)                  # 연속성 보정 O (기본)
chi_s2, p_s2, _, _ = chi2_contingency(table_sig, correction=False)      # 보정 X
print(f'보정 O: χ² = {chi_s:.3f}, p = {p_s:.4f}')
print(f'보정 X: χ² = {chi_s2:.3f}, p = {p_s2:.4f}')
print('기대도수:\n', np.round(exp_s, 1))
# 해석: 상승 확률 55% vs 50%처럼 5%p 차이는 500일로는 잘 안 잡힘.
#      퀀트에서 쓸 만한 신호도 대부분 이 정도로 약하다 → 표본이 몇 천 개는 있어야 검정에서 보임.
#      그리고 같은 데이터로 신호를 여러 개 만들어 보고 제일 좋은 것만 검정하면 p-value를 믿으면 안 됨.

# %% 3-2. 고객 투자성향 × 고른 상품 (3×3)
rng = np.random.default_rng(31)
prob = {                                 # 성향마다 상품 고를 확률 (채권형, 주식형, ETF)
    '안정형': [0.60, 0.15, 0.25],
    '중립형': [0.35, 0.30, 0.35],
    '공격형': [0.10, 0.50, 0.40],
}
rows = []
for kind, p_list in prob.items():
    picks = rng.choice(['채권형', '주식형', 'ETF'], size=120, p=p_list)
    for x in picks:
        rows.append({'성향': kind, '상품': x})
cust = pd.DataFrame(rows)

table_c = pd.crosstab(cust['성향'], cust['상품'])
print(table_c)

chi_c, p_c, dof_c, exp_c = chi2_contingency(table_c)    # 2×2가 아니면 보정 없음
print(f'χ² = {chi_c:.2f}, 자유도 = {dof_c}, p = {p_c:.6f}')
print('기대도수:\n', pd.DataFrame(exp_c, index=table_c.index, columns=table_c.columns).round(1))
# 자유도 = (3-1) × (3-1) = 4

# %% 3-3. 어느 칸이 차이를 만들었나: 표준화 잔차 = (관측 - 기대) / √기대
resid = (table_c - exp_c) / np.sqrt(exp_c)
print(resid.round(2))
# 절댓값 2 넘는 칸이 관련성을 만든 칸. 예: 안정형-채권형 +, 공격형-채권형 −

# %% 3-4. (참고) 기대도수가 작을 때: 피셔 정확검정 (2×2만)
from scipy.stats import fisher_exact
small = pd.DataFrame({'상승': [7, 2], '하락': [3, 8]}, index=['켜짐', '꺼짐'])
print(small)
print('기대도수:\n', np.round(chi2_contingency(small)[3], 1))     # 5 미만 칸이 생김
odds, p_f = fisher_exact(small)
print(f'피셔 정확검정 p = {p_f:.4f}')
#%%
# ================================================================
# 0. 개념 정리 (숫자 예시)
# ================================================================

#1. 검정의 목적
#t- test, ANOVa: 종속변수가 연속 변수인 경우에 사용
#카이제곱검정: 범주형 변수 같의 관계를 분석
#즉, 각 범주에 따른 빈도분포 분석이나 두 개 이상의 범주형 변수간 독립성 여부 검정

#2. 교차분석
#교차표(contingency table) 이용하여 범주형 변수 간의 관계를 분석하는 방법
#1) 관찰 빈도: 실제 데이터로부터 관측된 빈도
#2) 기대빈도 : 두 변수가 서로 독립이라는 가정하에서 기대되는 이론적 빈도

#-> 일반적으로 각 범주의 기대빈도는 5이상이여야 함 -> 아닌경우 피셔방법(tea) 이용

#3. 카이제곱 검정
#카이제곱 통계량 = Σ (관측도수 - 기대도수)² / 기대도수
#  '기대도수' = 귀무가설이 맞으면 나와야 하는 개수

#(1) 적합성 검정
#범주 하나의 비율이 내가 정한 비율과 맞나
#즉, 각 범주에 따른 데이터의 빈도분포가 이론적으로 기대하는 분포를 따르는지를 검정하는 방법
 
""" 파이선 패키지
scipy.stats.chisquare(f_obs,f_exp = None, ddof = 0, axis = 0)
f_obs : 관찰빈도로 pd.value_counts() 결과값을 입력(데이터 타입: array_like)
f_exp : 각 카테고리의 기대빈도 (데이터 타입: array_like)
ddof: p-value에 대한 자유도 보정값(데이터 타입: int(defaut=0))
자유도 : k-1-ddif(k:관찰된 범주의 수)

"""

#예: 한 달 주문 100건, 매수 62 · 매도 38. "매수:매도 = 50:50"인가?
#      기대도수 50, 50
#      χ² = (62-50)²/50 + (38-50)²/50 = 2.88 + 2.88 = 5.76
#      자유도 = 범주 수 - 1 = 1 → 임계값(α=0.05) 3.84
#      5.76 > 3.84 → 50:50 기각 (p ≈ 0.016)


# %% 1-1. 적합성 검정: 생존자 남녀 비율이 50:50인가
df = pd.read_csv("https://raw.githubusercontent.com/ADPclass/ADP_book_ver01/main/data/titanic.csv")
df.info()

# titanic 데이터의 sex 변수를 대상으로 적합성 검정 수행
# 귀무가설: 타이타닉호 생존자의 남녀 비율은 5:5이다.
# 대립가설: 타이타닉호 생존자의 남녀 비율은 5:5가 아니다. 


#%%
df_t = df[df['survived'] == 1]
table = df_t[['sex']].value_counts()
print(table)

# sex변수의 도수분포표 생성하여 범주별 관찰빈도 확인
# 이후 기대빈도 설정하고 적합성 검정 수행


#%% 유의수준 0.05로 적합성 검정 수행 
# 생존자 342명 → 50:50이면 171, 171
chi = chisquare(table, f_exp=[171, 171])
print('<적합도 검정>\n', chi)

# Power_divergenceResult(statistic=np.float64(44.95906432748538), 
# pvalue=np.float64(2.0119672574477235e-11))
# 책 해석: 통계량 약 44.96, p < 0.05 → 생존자 남녀 비율은 50:50이라 보기 어려움

#%%
# (2) 독립성 검정: 범주 두 개가 서로 관련 있나 (교차표)
"""  
      예: 200일 동안 매수 신호와 다음 날 방향
                 다음날 상승  다음날 하락   합
      신호 켜짐        60          40       100
      신호 꺼짐        45          55       100
      합              105          95       200
"""
 # 기대도수 = 행 합 × 열 합 / 전체
 
 #     신호 켜짐·상승 = 100 × 105 / 200 = 52.5    신호 켜짐·하락 = 47.5
 
 #     신호 꺼짐·상승 = 52.5                       신호 꺼짐·하락 = 47.5
 
 # χ² = (60-52.5)²/52.5 + (40-47.5)²/47.5 + (45-52.5)²/52.5 + (55-47.5)²/47.5
 #    = 1.071 + 1.184 + 1.071 + 1.184 = 4.51
 
 # 자유도 = (행 2 - 1) × (열 2 - 1) = 1 → p ≈ 0.034
 
 # ※ 2×2 표는 chi2_contingency가 기본으로 연속성 보정(Yates)을 함:
 #    칸마다 |관측-기대|에서 0.5를 빼고 제곱 → (7.5-0.5)² = 49
 #    χ² = 49/52.5 + 49/47.5 + 49/52.5 + 49/47.5 = 3.93 → p ≈ 0.047
 
 #    보정 안 한 값을 원하면 correction=False

#주의: 기대도수가 5보다 작은 칸이 20% 넘으면 카이제곱이 부정확 → 2×2면 피셔 정확검정(fisher_exact)

"""패키지 
scipy.stats.chi2_contingency((observed,correction = True, lambda_None))


observed: 관찰 빈도로 pd.crosstab 결과값을 입력 (데이터 타입 : array_like)

반환값 
chi2: 카이제곱 통꼐량
p: p-value
df: 자유도
expected: 기대빈도 

"""



#%%  독립성 검정: 좌석 등급과 생존 여부
# titanic 데이터에서 좌석등급(class)와 생존여부 (survived)가 서로 독립인지 검정 
# H0: class 변수와 survived 변수는 독립이다.
# H1: class 변수와 survived 변수는 독립이 아니다. 

df = pd.read_csv("https://raw.githubusercontent.com/ADPclass/ADP_book_ver01/main/data/titanic.csv")
table = pd.crosstab(df['class'], df['survived'])
print(table)


#%%  # pd.crosstab이용 교차표 생성 후 독립성 검정 수행하기 

chi, p, dof, expect = chi2_contingency(table)

print('Statistic:', chi)
print('p-value:', p)
print('df:', dof)
print('expect: \n', expect)
# Statistic: 102.88898875696056
#p-value: 4.549251711298793e-23
#df: 2
#expect: 
# [[133.09090909  82.90909091]
# [113.37373737  70.62626263]
# [302.53535354 188.46464646]]

""" p-value 가 0.05보다 작으니 귀무가설 기각 
즉, 좌석등급과 생존여부는 독립이 아니고 유의한 관련성 존재함"""

# 