# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 16 · 문자열 계산하기
# 문제: "3 + 4" 처럼 숫자와 +, - 가 공백 하나로 구분된 문자열을 계산한 값
# Spyder: F5 전체 실행

# %% 정답
def solution(my_string):
    parts = my_string.split()          # '3 + 4 - 2' → ['3', '+', '4', '-', '2']
    answer = int(parts[0])             # 첫 숫자로 시작
    for i in range(1, len(parts), 2):  # 1, 3, 5 ... 번째 칸이 기호
        op = parts[i]                  # 기호
        num = int(parts[i + 1])        # 기호 바로 다음 칸이 숫자
        if op == '+':
            answer = answer + num
        else:
            answer = answer - num
    return answer

# %% 확인
print(solution('3 + 4'))           # 7
print(solution('10 - 3 + 25'))     # 32

# %% 포인트
# - split()은 공백 기준으로 잘라 리스트로 → 숫자는 짝수 칸, 기호는 홀수 칸
# - range(1, len(parts), 2) : 1부터 2칸씩 → 기호 칸만 돈다 (암호 해독의 range(시작, 끝, 간격)과 같음)
