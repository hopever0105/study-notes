# -*- coding: utf-8 -*-
# 프로그래머스 코딩테스트 입문 Day 4 - 배열의 평균값
# 요약: 정수 리스트의 평균을 돌려준다.

# %% 풀이: 합 ÷ 개수 (불러올 것 없음)
def solution(numbers):
    return sum(numbers) / len(numbers)

print(solution([1, 2, 3, 4, 5]))   # 3.0
print(solution([89, 90, 91]))      # 90.0

# %% 다른 방법
import statistics
def solution(numbers):
    return statistics.mean(numbers)

# 틀렸던 것
#   import math 후 mean(numbers) ✗ → mean은 math에 없음, statistics에 있음
#
# 함수 vs 메서드
#   statistics.mean(numbers) : 함수, 재료를 괄호 안에
#   numbers.mean()           : 메서드, numpy 배열·pandas 열만 가능. 기본 리스트는 에러
#
# 모듈별 위치
#   math       : ceil(올림), gcd(최대공약수), sqrt(제곱근)
#   statistics : mean, median, multimode
#   기본 함수  : sum, len, max, min, sorted (불러올 필요 없음)
