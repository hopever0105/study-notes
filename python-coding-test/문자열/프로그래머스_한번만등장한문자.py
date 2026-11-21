# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 15 · 한 번만 등장한 문자
# 문제: 문자열 s에서 딱 한 번 나온 글자만 사전 순으로 이어 붙이기 (없으면 빈 문자열)
# Spyder: F5 전체 실행

# %% 정답
def solution(s):
    answer = ''
    for ch in sorted(s):          # 글자를 사전 순으로 하나씩
        if s.count(ch) == 1:      # s 전체에서 1번만 나왔으면
            answer = answer + ch
    return answer

# %% 확인
print(solution('abcabcadc'))   # d
print(solution('abdc'))        # abcd
print(solution('hello'))       # eho

# %% 포인트
# - sorted('hello') → ['e', 'h', 'l', 'l', 'o'] : 문자열도 글자 리스트로 정렬된다
# - s.count(ch) : ch가 s 안에 몇 번 나오는지
