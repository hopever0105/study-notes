# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 16 · 편지
# 문제: 한 글자(공백 포함)를 가로 2cm로 쓸 때, message를 쓰는 데 필요한 편지지 가로 길이
# Spyder: F5 전체 실행

# %% 정답
def solution(message):
    return len(message) * 2      # 글자 수 × 2cm

# %% 확인
print(solution('happy birthday!'))   # 30
print(solution('I love you~'))       # 22

# %% 포인트
# - len()은 공백·특수문자도 한 글자로 센다
