# -*- coding: utf-8 -*-
# 프로그래머스 입문 · 배열 자르기
# 문제: 리스트 numbers에서 인덱스 num1부터 num2까지(포함) 잘라 반환
# Spyder: F5 전체 실행

# %%
def solution(numbers, num1, num2):
    answer = numbers[num1:num2 + 1]    # 슬라이싱 끝은 빠지므로 +1
    return answer

# %%
print(solution([1, 2, 3, 4, 5], 1, 3))    # [2, 3, 4]
print(solution([9, 8, 7], 0, 0))          # [9]
