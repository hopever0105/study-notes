# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 11 · 합성수 찾기
# 문제: n 이하 자연수 중 합성수(약수가 3개 이상인 수) 개수
# Spyder: F5 전체 실행

# %% 정답
def solution(n):
    answer = 0
    for x in range(1, n + 1):              # 1 ~ n
        count = 0                          # x의 약수 개수
        for d in range(1, x + 1):
            if x % d == 0:                 # 나누어떨어지면 약수
                count = count + 1
        if count >= 3:                     # 약수 3개 이상 = 합성수
            answer = answer + 1
    return answer

# %% 확인
print(solution(10))    # 5  (4, 6, 8, 9, 10)
print(solution(15))    # 8

# %% 포인트
# - for 안에 for: 바깥은 숫자 하나씩, 안쪽은 그 숫자의 약수 세기
