# 프로그래머스 코딩테스트 입문 Day 2 - 숫자 비교하기
# 요약: 정수 두 개가 같으면 1, 다르면 -1을 return
# 단원: 04 조건문 (if / elif / else)


# %% 내 처음 풀이 — SyntaxError
# def solution(num1, num2):
#     if num1 == num2 :
#         answer = 1
#     else num1 != num2:      # ← else 뒤에 조건을 붙여서 에러
#         answer = -1
#     return answer


# %% 고친 풀이
def solution(num1, num2):
    if num1 == num2:      # 같으면
        answer = 1
    else:                 # else는 "위 조건이 아니면 전부" → 조건 없이 콜론만
        answer = -1
    return answer

print(solution(2, 3))     # -1
print(solution(11, 11))   # 1


# %% if / elif / else 정리
# if 조건1:     → 조건1이 참이면 실행
# elif 조건2:   → 조건1이 거짓이고 조건2가 참이면 실행 (조건 붙임 O)
# else:         → 위가 전부 거짓이면 실행           (조건 붙임 X)
def sign(x):
    if x > 0:
        return "양수"
    elif x < 0:
        return "음수"
    else:
        return "0"

print(sign(5), sign(-3), sign(0))   # 양수 음수 0


# %% 짧게 쓰는 법 — 한 줄 if
def solution_short(num1, num2):
    return 1 if num1 == num2 else -1

print(solution_short(2, 3), solution_short(11, 11))   # -1 1
