# -*- coding: utf-8 -*-
# 종목별 평균 수익률 상위 고르기 (11/20 목표 문제 정답)
# 언제 쓰나: 분석 과제 첫 단계 — 종목별로 묶어 수익률 계산 → 순위. 라온지아이 분석 시험에 제일 먼저 나오는 형태.
# Spyder: F5 전체 실행

# %% 정답
import pandas as pd

def top_mean_return(df, k=10):
    d = df.sort_values(['code', 'date']).copy()               # ① 종목별·날짜순 정렬 (섞여 있을 수 있음)
    d['ret'] = d.groupby('code')['close'].pct_change()         # ② 같은 종목 안에서만 전날 대비 → 첫 날은 NaN
    mean_ret = d.groupby('code')['ret'].mean()                 # ③ 종목별 평균 (mean은 NaN을 알아서 뺌)
    return mean_ret.sort_values(ascending=False).head(k).round(4)   # ④ 큰 순서 k개

# %% 확인: 작은 예시 (행 순서 섞임)
toy = pd.DataFrame({
    'date': pd.to_datetime(['2026-01-03', '2026-01-01', '2026-01-02'] * 3),
    'code': ['A'] * 3 + ['B'] * 3 + ['C'] * 3,
    'close': [99, 100, 110, 55, 50, 50, 20.9, 20, 19],
})
print(top_mean_return(toy, 2))     # B 0.050, C 0.025
print(top_mean_return(toy, 1))     # B 0.05

# %% 틀린 버전: 정렬·groupby 없이 → A가 1등으로 잘못 나옴
wrong = toy.copy()
wrong['ret'] = wrong['close'].pct_change()      # 99→100, 50→55(다른 종목끼리)까지 이어서 계산해 버림
print(wrong.groupby('code')['ret'].mean().round(4))

# %% 실제 데이터
PATH = r'C:\Users\arlo0\OneDrive\바탕 화면\취업\06_퀀트공부\연습데이터\prices.csv'
df = pd.read_csv(PATH, dtype={'code': str}, parse_dates=['date'], encoding='utf-8-sig')
top10 = top_mean_return(df, 10)
print(top10)

# %% 덤: 평균 일별 수익률 1등 = 누적 수익률 1등? → 아닐 수 있음
#   숫자 예시: +50% 다음 날 -50% → 평균 0%인데 실제로는 100 → 150 → 75, 25% 손실
#   변동성이 큰 종목은 평균 일별 수익률이 높아도 누적은 낮을 수 있음 (변동성 손실)
d = df.sort_values(['code', 'date'])
cum = d.groupby('code')['close'].agg(lambda s: s.iloc[-1] / s.iloc[0] - 1)
comp = pd.DataFrame({'평균일별': top10, '누적': cum.loc[top10.index].round(3)})
comp['누적순위'] = cum.rank(ascending=False).loc[top10.index].astype(int)
print(comp)
