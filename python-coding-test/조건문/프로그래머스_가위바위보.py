# -*- coding: utf-8 -*-
# 프로그래머스 입문 Day 9 · 가위 바위 보
# 문제: 가위 2, 바위 0, 보 5. 숫자 문자열 rsp의 각 글자를 '이기는 것'으로 바꾼 문자열 반환.
# Spyder: F5 전체 실행

# %% 정답
def solution(rsp):
    win = {'2': '0', '0': '5', '5': '2'}    # 가위(2)는 바위(0)가, 바위(0)는 보(5)가, 보(5)는 가위(2)가 이김
    answer = ''
    for ch in rsp:                          # '205' → '2', '0', '5' 한 글자씩 (split 필요 없음)
        answer = answer + win[ch]
    return answer

# %% 확인
print(solution('2'))      # 0
print(solution('205'))    # 052

# %% 포인트
# - 키·값이 모두 '문자열' '2' (숫자 2 아님): rsp가 문자열이라 한 글자도 문자열
# - if/elif로도 되지만 '바꾸기 표'는 딕셔너리가 짧음
