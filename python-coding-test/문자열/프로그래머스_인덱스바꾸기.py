# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 15 · 인덱스 바꾸기
# 문제: 문자열 my_string에서 인덱스 num1, num2 글자를 서로 바꾼 문자열
# Spyder: F5 전체 실행

# %% 정답
def solution(my_string, num1, num2):
    chars = list(my_string)                                 # 문자열은 못 고침 → 글자 리스트로
    chars[num1], chars[num2] = chars[num2], chars[num1]     # 두 칸을 한 번에 맞바꿈
    return ''.join(chars)                                   # 리스트 → 다시 문자열

# %% 확인
print(solution('hello', 1, 2))         # hlelo
print(solution('I love you', 3, 6))    # I l veoyou

# %% 포인트
# - 문자열은 my_string[1] = 'x' 처럼 직접 못 바꾼다 → list()로 바꾸고 ''.join()으로 되돌린다
# - a, b = b, a : 임시 변수 없이 두 값을 맞바꾸는 파이썬 문법
