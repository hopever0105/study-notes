# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 9 · 개미 군단
# 문제: 장군개미 공격력 5, 병정개미 3, 일개미 1. 체력 hp를 딱 맞추는 개미 수의 최솟값.
# Spyder: F5 전체 실행

# %% 정답
def solution(hp):
    general = hp // 5          # 장군개미를 최대한: 23 // 5 = 4마리 (20)
    rest = hp % 5              # 남은 체력: 23 % 5 = 3
    soldier = rest // 3        # 병정개미: 3 // 3 = 1마리
    rest = rest % 3            # 남은 체력: 0
    worker = rest              # 나머지는 일개미 1씩
    answer = general + soldier + worker
    return answer

# %% 확인
print(solution(23))     # 5  (5×4 + 3×1)
print(solution(24))     # 6  (5×4 + 3×1 + 1×1)
print(solution(999))    # 201

# %% 포인트
# - 큰 것부터 최대한 쓰기 = '그리디' (거스름돈 문제와 같은 틀)
# - // 몫, % 나머지 (문법_버림_몫나머지_문자열곱하기_입력받기.py)
