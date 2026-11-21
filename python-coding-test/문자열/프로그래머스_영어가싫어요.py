# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 15 · 영어가 싫어요
# 문제: "zero"~"nine" 영단어가 붙어 있는 문자열을 숫자(정수)로 바꾸기
# Spyder: F5 전체 실행

# %% 정답
def solution(numbers):
    words = ['zero', 'one', 'two', 'three', 'four',
             'five', 'six', 'seven', 'eight', 'nine']     # 인덱스 = 그 단어의 숫자
    for i in range(10):                                   # 0부터 9까지
        numbers = numbers.replace(words[i], str(i))       # 'one' → '1' 처럼 전부 바꿈
    return int(numbers)                                   # 문자열 '14067' → 정수 14067

# %% 확인
print(solution('onetwothreefourfivesixseveneightnine'))   # 123456789
print(solution('onefourzerosixseven'))                    # 14067

# %% 포인트
# - replace(찾을것, 바꿀것)은 해당 글자를 '전부' 바꾼 새 문자열을 돌려준다 → 다시 numbers에 담아야 함
# - 단어 목록의 인덱스가 곧 숫자라서 str(i)로 바로 바꿀 수 있다
