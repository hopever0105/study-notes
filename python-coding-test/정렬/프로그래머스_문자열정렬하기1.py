# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 12 · 문자열 정렬하기 (1)
# 문제: 문자열 my_string 안의 숫자만 골라 오름차순 정수 리스트로
# Spyder: F5 전체 실행

# %% 정답
def solution(my_string):
    answer = []
    for ch in my_string:
        if ch.isdigit():              # '0'~'9' 글자면 True
            answer.append(int(ch))    # 숫자로 바꿔 넣기
    return sorted(answer)             # 오름차순

# %% 확인
print(solution('hi12392'))     # [1, 2, 2, 3, 9]
print(solution('p2o4i8gj2'))   # [2, 2, 4, 8]
