# -*- coding: utf-8 -*-
# 프로그래머스 입문 · 양꼬치
# 문제: 양꼬치 n인분, 음료 k개 주문 시 총금액 반환. 양꼬치 12000원, 음료 2000원, 10인분마다 음료 1개 서비스
# Spyder: F5 전체 실행

# %%
def solution(n, k):
    service = n // 10                     # 서비스 음료 수 (10인분마다 1개)
    drink_pay = k - service               # 실제로 내는 음료 수
    answer = 12000 * n + 2000 * drink_pay
    return answer

# %%
print(solution(10, 3))    # 124000
print(solution(64, 6))    # 768000 + 2000*0 = 768000
