# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 15 · 약수 구하기
# 문제: 정수 n의 약수를 오름차순 리스트로
# Spyder: F5 전체 실행

# %% 정답
def solution(n):
    answer = []
    for d in range(1, n + 1):      # 1부터 n까지
        if n % d == 0:             # 나누어떨어지면 약수
            answer.append(d)       # 작은 수부터 넣으니 저절로 오름차순
    return answer

# %% 확인
print(solution(24))   # [1, 2, 3, 4, 6, 8, 12, 24]
print(solution(29))   # [1, 29]

# %% 포인트
# - 합성수 찾기(Day 12)의 안쪽 반복문과 같은 모양: n % d == 0 이면 약수
# - 1부터 차례로 돌기 때문에 따로 정렬할 필요가 없다
