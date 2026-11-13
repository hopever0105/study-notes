# %% 0. 필요한 도구 불러오기 (F5 전체 실행 때 맨 먼저 돌아야 함)
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import MultiComparison, pairwise_tukeyhsd
from statsmodels.graphics.factorplots import interaction_plot

#%%
# ================================================================

# ================================================================
# 실제 시세가 아니라 난수로 만든 연습 데이터(seed 고정 → 매번 같은 숫자).
# 전략마다 60개월(5년), 월수익률 단위 %.
#   모멘텀: 평균 1.2%, 변동 큼(표준편차 6)  → 꼬리가 두꺼운 t분포로 만들어 정규성이 깨지게
#   가치  : 평균 0.6%, 표준편차 4
#   저변동: 평균 0.7%, 표준편차 2.5

# %% 2-1. 연습 데이터 만들기
rng = np.random.default_rng(42)
n_month = 60

mom = 1.2 + 6 * rng.standard_t(df=3, size=n_month) / np.sqrt(3)   # t분포(자유도 3) → 가끔 큰 손실·이익
val = rng.normal(0.6, 4.0, n_month)
lowvol = rng.normal(0.7, 2.5, n_month)

ret = pd.DataFrame({
    'strategy': ['모멘텀'] * n_month + ['가치'] * n_month + ['저변동'] * n_month,
    'ret': np.concatenate([mom, val, lowvol])
})
print(ret.head())
print(ret.groupby('strategy')['ret'].agg(['count', 'mean', 'std']).round(2))

# %% 2-2. 정규성(Shapiro)·등분산성(Levene)
mom_r = ret[ret['strategy'] == '모멘텀']['ret']
val_r = ret[ret['strategy'] == '가치']['ret']
low_r = ret[ret['strategy'] == '저변동']['ret']

for name, r in [('모멘텀', mom_r), ('가치', val_r), ('저변동', low_r)]:
    print(f"{name} 정규성 p-value: {stats.shapiro(r).pvalue:.4f}")

print(f"등분산성 p-value: {stats.levene(mom_r, val_r, low_r).pvalue:.4f}")
# 해석: 모멘텀은 꼬리가 두꺼워 정규성이 깨질 가능성이 큼(실제 주식 수익률도 대부분 이렇다),
#      표준편차가 6 / 4 / 2.5로 달라 등분산도 깨짐 → 일반 분산분석보다 비모수 쪽이 맞음

# %% 2-3. (비교용) 일반 일원배치 분산분석 f_oneway
# 가정이 깨졌지만, 숫자가 어떻게 나오는지 보려고 같이 돌려 봄
f_stat, p_anova = stats.f_oneway(mom_r, val_r, low_r)
print(f"일원배치 분산분석 F = {f_stat:.3f}, p-value = {p_anova:.4f}")

# %% 2-4. (참고) Welch 분산분석: 정규는 OK인데 분산만 다를 때
# 직접 계산: 집단마다 가중치 w = n / 분산 (분산 작은 집단 평균을 더 믿음)
def welch_anova(*groups):
    k = len(groups)
    n = np.array([len(g) for g in groups])
    m = np.array([np.mean(g) for g in groups])
    v = np.array([np.var(g, ddof=1) for g in groups])
    w = n / v
    m_w = np.sum(w * m) / np.sum(w)                    # 가중 전체 평균
    a = np.sum(w * (m - m_w) ** 2) / (k - 1)
    tmp = np.sum((1 - w / np.sum(w)) ** 2 / (n - 1))
    b = 1 + 2 * (k - 2) / (k ** 2 - 1) * tmp
    f = a / b
    df1 = k - 1
    df2 = (k ** 2 - 1) / (3 * tmp)
    p = stats.f.sf(f, df1, df2)
    return f, df1, df2, p

f_w, d1, d2, p_w = welch_anova(mom_r, val_r, low_r)
print(f"Welch 분산분석 F = {f_w:.3f}, 자유도 ({d1}, {d2:.1f}), p-value = {p_w:.4f}")

# %% 2-5. 정규성이 깨졌으니 Kruskal-Wallis (책과 같은 길)
stat, p_kw = stats.kruskal(mom_r, val_r, low_r)
print(f"Kruskal-Wallis p-value: {p_kw:.4f}")

# %% 2-6. 사후검정 두 가지
# (1) 비모수: Mann-Whitney + 본페로니 (책 방식)
mc = MultiComparison(ret['ret'], ret['strategy'])
print(mc.allpairtest(stats.mannwhitneyu, method='bonf')[0])

# (2) 모수: Tukey HSD (정규·등분산이 맞을 때 표준 사후검정)
print(pairwise_tukeyhsd(ret['ret'], ret['strategy'], alpha=0.05))
# reject 열이 True인 쌍만 "평균이 다르다"

# %% 2-7. 해석할 때 주의 (퀀트 관점)
print(ret.groupby('strategy')['ret'].agg(['mean', 'median', 'std']).round(2))
"""
- 월수익률 표준편차 6%면 60개월 평균의 표준오차 = 6 / √60 = 0.77%p.
  평균이 1.2% vs 0.6%로 0.6%p 차이 나도 표준오차보다 작아서 '유의하지 않음'이 자주 나온다.
  → 수익률 평균 차이를 검정으로 확인하려면 기간이 아주 길어야 한다는 게 핵심 교훈.
- 월수익률은 시간 순서가 있는 데이터. 달마다 독립이라는 가정이 깨지면(자기상관) p-value가 너무 작게 나옴.
- 전략을 많이 만들어 놓고 제일 좋은 셋만 골라 검정하면 다중검정 문제 → 본페로니처럼 α를 엄격하게.
"""
#%%
# ================================================================
# 3. 금융판 이원배치: 전략 × 시장 국면(상승장·하락장)
# ================================================================
# 질문: 전략에 따라 수익률이 다른가? 국면에 따라 다른가? 그리고
#       "어떤 전략이 좋은지가 국면에 따라 뒤바뀌는가"(= 교호작용)?
# 연습 데이터: 저변동은 하락장에서 덜 빠지고, 모멘텀은 상승장에서 강하게 만듦

# %% 3-1. 연습 데이터 만들기 (조합마다 30개월)
rng = np.random.default_rng(7)
mean_table = {                       # (전략, 국면): 평균 월수익률 %
    ('모멘텀', '상승장'): 3.0, ('모멘텀', '하락장'): -3.0,
    ('가치',   '상승장'): 2.0, ('가치',   '하락장'): -1.5,
    ('저변동', '상승장'): 1.0, ('저변동', '하락장'): -0.5,
}
rows = []
for (stg, regime), mu in mean_table.items():
    r = rng.normal(mu, 3.0, 30)
    for x in r:
        rows.append({'strategy': stg, 'regime': regime, 'ret': x})
ret2 = pd.DataFrame(rows)
print(ret2.pivot_table(index='strategy', columns='regime', values='ret', aggfunc='mean').round(2))

# %% 3-2. 조합별 정규성·전체 등분산성 (책 1-4와 같은 틀)
for (stg, regime), g in ret2.groupby(['strategy', 'regime']):
    print(f"[{stg} - {regime}] 정규성 p-value: {stats.shapiro(g['ret']).pvalue:.4f}")
groups2 = [g['ret'] for _, g in ret2.groupby(['strategy', 'regime'])]
print(f"등분산성 p-value: {stats.levene(*groups2).pvalue:.4f}")

# %% 3-3. 이원배치 분산분석 + 교호작용 그래프
model2 = ols('ret ~ C(strategy) * C(regime)', data=ret2).fit()
print(anova_lm(model2, typ=2))
# 읽는 법
#   C(strategy)            p < 0.05 → 전략에 따라 평균이 다름
#   C(regime)              p < 0.05 → 상승장·하락장 평균이 다름 (당연히 크게 나옴)
#   C(strategy):C(regime)  p < 0.05 → 국면에 따라 전략 효과가 다름 = 교호작용
#   교호작용이 유의하면 "모멘텀이 제일 좋다" 같은 한 줄 결론은 틀림 → 국면별로 나눠서 말해야 함

fig = interaction_plot(x=ret2['regime'], trace=ret2['strategy'], response=ret2['ret'])
plt.title('전략 × 시장 국면 평균 월수익률')
plt.show()
# 선이 평행하지 않음: 상승장에선 모멘텀·가치가 저변동보다 높고, 하락장에선 모멘텀이 제일 많이 빠짐
# → 교호작용 p ≈ 0.007. 반면 전략 단독 효과 p ≈ 0.40 → 국면을 섞어 평균 내면 전략 차이가 묻혀 버림


# 세 집단 이상 평균 차이 검정 (분산분석)
# 언제 쓰나: 전략 3개 이상의 월수익률 평균이 정말 다른지, 증권사 3곳 체결 지연이 다른지,
#            전략 × 시장 국면(상승장·하락장)처럼 두 기준을 같이 볼 때

# ================================================================
# 0. 개념 정리 (숫자 예시)
# ================================================================
"""
왜 t검정을 세 번 하지 않나
  - A-B, A-C, B-C 세 번 t검정(각 α=0.05)을 하면, 실제로는 차이가 없어도
    셋 중 하나라도 '차이 있음'이 나올 확률 = 1 - 0.95^3 = 0.143 (14.3%)
  - 그래서 한 번에 "세 평균이 모두 같은가"를 묻는 분산분석을 먼저 한다.

분산분석:
    집단 간 분산과 집단 내 분산을 이용하여 평균을 검정하는 방법
    집단간 분산 : 집단 평균 간 차이
    집단 내 분산: 동일 집단 내 관측값의 변동
    집단간 분산의 차이가 집단 내 분산의 차이보다 충분히 크면 다르다고 본다. 
    
분산분석 종류

종류                독립변수 개수   종속변수 개수    주요 질문 
일원배치 분산분석 /  1개          / 연속형 1개 /  집단 간 평균 차이가 존재 하는가?
이원배치 분산분석 / 2개           / 연속형 1개 /  두 요인이 평균에 영향을 미치는가? 



F 통계량 = 집단 사이 흩어짐 / 집단 안 흩어짐
  예: 전략 3개, 각 3개월 수익률(%)
      모멘텀 [1, 2, 3]  평균 2
      가치   [3, 4, 5]  평균 4
      저변동 [5, 6, 7]  평균 6      전체 평균 4
  1) 집단 사이 제곱합(SSB) = 3×(2-4)² + 3×(4-4)² + 3×(6-4)² = 12 + 0 + 12 = 24
     자유도 = 집단 수 - 1 = 2 → 평균제곱 MSB = 24 / 2 = 12
  2) 집단 안 제곱합(SSW) = 각 집단에서 (1-2)²+(2-2)²+(3-2)² = 2 → 3집단 합 6
     자유도 = 전체 개수 - 집단 수 = 9 - 3 = 6 → MSW = 6 / 6 = 1
  3) F = 12 / 1 = 12 → F(2, 6) 분포에서 p ≈ 0.008 → 0.05보다 작으니 "평균이 모두 같다" 기각
  F가 1 근처면 집단 사이 차이가 그냥 우연한 흩어짐 수준이라는 뜻.

순서 (시험에서 그대로)
  1) 정규성: 집단마다 Shapiro (p ≥ 0.05면 정규로 봄)
  2) 등분산: Levene (p ≥ 0.05면 분산 같음)
  3) 둘 다 OK → 일원배치 분산분석(f_oneway) → 차이 있으면 사후검정 Tukey
     정규성 깨짐 → Kruskal-Wallis(순위로 하는 비모수) → 사후검정 Mann-Whitney + 본페로니
     정규 OK, 등분산만 깨짐 → Welch 분산분석 (아래 2-4 참고)
  4) 사후검정: "어느 쌍이 다른지". 본페로니 = 쌍이 3개면 α를 0.05/3 = 0.0167로 엄격하게
"""

# ================================================================

# ================================================================

#%% 일원 배치 분산분석 (One - way ANOVA)
"""
여러 집단 비교 시 t-검정 반복하면 제1종 오류 증가함 
분산분석은 이러한 오류를 통제 

1_ 개념
one-way anova는 하나의 독립변수에 따라 세 개 이상 집단의 평균이 동일한지 검정하는 방법

2_ 분석단계 
1) 가설 수립: 귀무사설(HO)와 대립가설(H1) 설정
2) 유의수준 설정: 일반적으로 0.05
3) 전제조건 확인 : 각 집단의 정규성과 집단 간 등분산성 반드시 확인
4) 데이터에 알맞은 모델 선택 및 p-value 산출, 사후검정 실시 

3_ 종류
1) 일반 ANOVA
사용조건: 정규성과 등분산성 만족
사후검정도구 : Tukey HSD
파이썬 라이브러리 함수 : statsmodels.stats.multicomp.pairwise_tukeyhsd())

2) KrusKal-Wallis(비모수 검정)
사용조건: 정규성 불만족 (하나라도 깨질 떄)
사후검정 도구 : Mann-Whitney U (+Bonferroni)
파이썬: statsmodels.stats.multicomp.allparitest()

3) Welch's ANOVA 
사용조건 : 정규성은 만족하나 등분산성 만족이 안되는 경우(그래서 정규성부터 검사하는게 맞음)
사후검정 도구 : Games-Howell
파이썬: scikit-posthocs.Games_Howell
    
"""


# %% 1-1. 데이터 불러오기·집단 나누기·정규성·등분산성
import pandas as pd 
import scipy.stats as stats

df = pd.read_csv('https://raw.githubusercontent.com/ADPclass/ADP_book_ver01/main/data/delivery_data.csv')

a_time = df[df['company'] == 'A']['delivery_time']
b_time = df[df['company'] == 'B']['delivery_time']
c_time = df[df['company'] == 'C']['delivery_time']

# 정규성 검정 (Shapiro)
print("A사 정규성 p-value:", stats.shapiro(a_time).pvalue)
print("B사 정규성 p-value:", stats.shapiro(b_time).pvalue)
print("C사 정규성 p-value:", stats.shapiro(c_time).pvalue)

# 등분산성 검정 (Levene): 모든 집단의 분산이 같은지
stat, p_levene = stats.levene(a_time, b_time, c_time)
print(f"등분산성 검정 p-value: {p_levene:.4f}")

# B사 0.05이하인바 정규성이 인정되지 않음. 
# %% 1-2. 정규성이 깨졌으므로 비모수 검정(Kruskal-Wallis) + 사후검정
from statsmodels.stats.multicomp import MultiComparison

# 비모수검정 실시, f_oneway대신 kruskal 함수 사용
stat, p_val = stats.kruskal(a_time, b_time, c_time)
print(f"Kruskal-Wallis 검정 결과 p-value: {p_val:.4f}")
#검정결과 0.000
#%% 

# 사후검정: 모든 쌍에 Mann-Whitney U 검정, 본페로니 교정
# 사후검정을 위핸 객체 만들기
# (데이터 종속변수, 데이터 독립변수 순서대로 넣기)
mc = MultiComparison(df['delivery_time'], df['company'])

# 모든 조합에 MAnn-Whitney U 검정 실시(본페로니 교정 저용)
# allpairtest(검정함수, method = '교정방법')
result = mc.allpairtest(stats.mannwhitneyu, method='bonf')

# 결과테이블 확인 
print(result[0])

# %% 1-3. 그룹별 평균·중앙값 (누가 얼마나 빠른지는 이 숫자로 말함)
print(df.groupby('company')['delivery_time'].agg(['mean', 'median']))

#%% 결과해석
"""
분석결과 : shapiro-wilk 검정 결과 b 정규성 충족 x -> kruskal-wallis 검정 수행
검정결과:  검정결과 p-value(0.000) < a(0.05) 이므로 Ho 기각함 
사후분석: Mann-Whitney U 검정 활용 집단 간 쌍별 비교 수행 보정 p-value로 유의성 판단
    모든 조합 pval_corr이 0.05보다 작게 나타나 True임
    Ture란 모든 회산 실력 차이가 명확함이 확인된 것을 의미함. 
    
구체적인 실력차이 분석
A: 134.7분
B: 127.6분
C: 155.8분

각각은 모두 유의미한 차이 있고 배송속도는 C사 A사 B사 순으로 유리

다중 비교 보정의 필요성
Kruskal -walls는 집단 간 차이의 존재여부만 판단 사후분석 통해 집단 간 개별비교 피룡
Mann-Whitney U 검정은 반복하면 제 1종 오류 증가 -> 
Bonferroni보정 적용 유의수준 조정: 파이선에는 사후분석 시 method = 'boni'

"""


# %% 1-4. 이원배치 전에: 조합별 정규성·전체 등분산성
print("## 조합별 정규성 검정 결과 ##")
for (comp, loc), group in df.groupby(['company', 'area']):
    p_val = stats.shapiro(group['delivery_time']).pvalue
    print(f"[{comp} - {loc}] p-value: {p_val:.4f}")

groups = [group['delivery_time'] for _, group in df.groupby(['company', 'area'])]
print(f"\n등분산성 p-value: {stats.levene(*groups).pvalue:.4f}")
#%%
"""
이원배치 분산분석
두 개의 독립 변수가 하나의 종속변수에 미치는 영향을 동시에 분석하는 방법
일원 배치는 하나 요인 따른 평균 차이 검정
이원 배치는 추가적 요인을 함께 고려

1. 개념
주효과와 교효작용을 해석행 함. 
1) 주효과: 각 독립변수가 종속변수에 미치는 개별적인 영향을 의미함.
2) 교호작용 : 두 독립변수가 결합될 때 종속변수에 미치는 영향이 달라지는 현상을 의미함.
    
2. 분석단계
1) 가설 수립
가설 1: 독립변수 1에 따른 종속 변수 차이는 없다(주효과)
가설 2 : 독립변수 2에 따른 종속변수 차이는 없다.(주효과)
가설 3 : 두 독립변수 간 interaction Effect는 없다. (교호작용)

2) 유의수준 설정 : ex) 0.05

3) 전제조건 확인
전제조건 : 정규성, 등분산성, 균형성 (각 집단 표본 수 동일해야함)
전제조건 미충족 시 
- 데이터 변환: 로그 변환(np.log), 제곱근 변환(np.sqrt) 등 적용
- CLT(중심극한 정리 활용)
보통 n>30  정규성 만족 안해도 사용하는 경우들이 있긴한데 코시분포등을 주의 

4) 모델 선택 및 결과 산출 
statsmodels의 ols함수와 anava_lm을 사용

5) 결과 해석
교호 작용의 p-value를 우선적으로 확인한 후 , 주효과를 해석한다. 

 """

# %% 1-5. 이원배치 분산분석: 회사 × 지역
# C() = 범주형이라고 알려 줌, * = 두 요인 + 교호작용(회사와 지역이 같이 작용하는 효과)까지
# 책은 './data/delivery_data.csv'로 읽지만 Spyder 위치 상관없이 돌게 위 1-1에서 읽은 df를 그대로 씀
#1 가설수립
# 가설 1: 택배사 따른 배송 시간 차이 없음. 
# 가설 2: 지역에 따른 배송 시간 차이 없음.
# 가설 3: 택배사와 지역간에는 상호작용 효과가 없다 (교호작용)

#2. 2단계 유의수준 설정 
# a= 0.05(95% 신뢰수준)

#3. 전제조건 확인
# 각 집단의 정규성과 등분산성을 만족한다고 가정

# 4단계 모델 결과 및 결과 산출
import pandas as pd
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.graphics.factorplots import interaction_plot
import matplotlib.pyplot as plt 

# a모델 구축 : c() 는 범주형 * 교호작용 의미
model = ols('delivery_time ~ C(company) * C(area)', data=df).fit()

# ANOVA 테이블 출력 
aov_table = anova_lm(model, typ=2)    # typ=2가 시험장 표준
print(aov_table)


# 교호작용 그래프 시각화: 선이 평행하면 교호작용 없음, 엇갈리면 있음
fig = interaction_plot(x=df['area'], trace=df['company'], response=df['delivery_time'])
plt.title('Two-way ANOVA Interaction Plot')
plt.show()

#5. 결과해석
"""
anova 결과 교호작용 p-value 0.05보다 작은 바 교호작용 효과가 통계적 유의미함. 
교호작용: 교호작용 그래프에서 각 집단의 선이 서로 평항하지 않은 바, 두 독립변수 간 상호작용 존재함 확인 가능ㅎㅁ. 

주효과: 교호작용이 유의하므로 주의 해야하나
전반적인 평균 수준 C사가 가장 낮고 B사가 가장 높은 평균
이는 택배사에 따른 주효과 존재 시사함. 

결론: 지역과 택배사 결합의 의한 효과도 있지만, 택배사 자체가 느린 부분도 없지 않나? 라는 정도의 생각으로 결론 

"""

