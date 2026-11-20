# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 14 · 암호 해독
# 문제: 문자열 cipher에서 code의 배수 번째 글자(1번부터 셈)만 이어 붙이기
# Spyder: F5 전체 실행

# %% 정답
def solution(cipher, code):
    answer = ''
    for i in range(code - 1, len(cipher), code):   # code번째 = 인덱스 code-1, 거기서 code칸씩
        answer = answer + cipher[i]
    return answer

# %% 정답 2: 슬라이싱 한 줄 [시작:끝:간격]
def solution2(cipher, code):
    return cipher[code - 1::code]

# %% 확인
print(solution('dfjardstddetckdaccccdegk', 4), solution2('dfjardstddetckdaccccdegk', 4))   # attack
print(solution('pfqallllabwaoclk', 2))                                                       # fallback
