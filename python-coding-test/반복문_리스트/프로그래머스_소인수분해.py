# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 12 · 소인수분해
# 문제: n의 소인수를 중복 없이 오름차순 리스트로
# Spyder: F5 전체 실행

# %% 정답
def solution(n):
    answer = []
    d = 2                              # 2부터 나눠 보기
    while n > 1:
        if n % d == 0:                 # d로 나누어떨어지면 d는 소인수
            if d not in answer:        #   중복 없이
                answer.append(d)
            n = n // d                 #   나누고 같은 d로 다시
        else:
            d = d + 1                  # 안 나눠지면 다음 수
    return answer

# %% 확인
print(solution(12))    # [2, 3]      12 → 6 → 3 → 1
print(solution(17))    # [17]
print(solution(420))   # [2, 3, 5, 7]

# %% 포인트
# - 작은 수부터 나눠 가면 4, 6 같은 합성수로는 안 나눠짐 (2·3으로 이미 다 나눴기 때문)
