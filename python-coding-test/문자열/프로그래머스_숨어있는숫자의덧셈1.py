# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 12 · 숨어있는 숫자의 덧셈 (1)
# 문제: 문자열 my_string 안의 한 자리 숫자를 모두 더하기
# Spyder: F5 전체 실행

# %% 정답
def solution(my_string):
    answer = 0
    for ch in my_string:
        if ch.isdigit():
            answer = answer + int(ch)
    return answer

# %% 확인
print(solution('aAb1B2cC34oOp'))    # 10
print(solution('1a2b3c4d123'))      # 16
