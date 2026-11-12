# -*- coding: utf-8 -*-
# 문제: {종목: 거래대금} → 거래대금 큰 순서 종목명 리스트 (.items() + key=lambda + for append)

# %% 풀이
def rank_by_amount(amounts):
    pairs = sorted(amounts.items(), key=lambda x: x[1], reverse=True)
    # amounts.items() → [("삼성전자", 1500), ("카카오", 300), ("NAVER", 800)]
    # key=lambda x: x[1] → 두 번째 칸(거래대금)으로 비교, reverse=True → 큰 순서
    # pairs = [("삼성전자", 1500), ("NAVER", 800), ("카카오", 300)]
    answer = []
    for name, amt in pairs:     # 묶음을 이름·거래대금으로 나눠 담기
        answer.append(name)     # 이름만 모으기
    return answer

# %% 확인
print(rank_by_amount({"삼성전자": 1500, "카카오": 300, "NAVER": 800}))  # ['삼성전자', 'NAVER', '카카오']
print(rank_by_amount({"현대차": 50, "기아": 70}))   # ['기아', '현대차']
print(rank_by_amount({"LG화학": 10}))              # ['LG화학']
