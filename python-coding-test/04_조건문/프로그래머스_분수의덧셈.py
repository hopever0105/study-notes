# 프로그래머스 코딩테스트 입문 Day 2 - 분수의 덧셈
# 요약: 분수 두 개(분자1, 분모1, 분자2, 분모2)를 더해 기약분수 [분자, 분모]로 return
# 단원: 04 조건문 묶음에 둠 (실제 핵심은 수학: 통분·최대공약수 약분, 정수 나눗셈 //)


# %% 풀기 전에 알아야 할 것
#   ① a/b + c/d = (a×d + c×b) / (b×d)       예) 1/6 + 1/3 = (3 + 6)/18 = 9/18
#   ② 약분 = 분자·분모를 최대공약수로 나누기  gcd(9, 18) = 9 → 1/2
#   ③ /  는 소수(1.0),  // 는 정수 몫(1) → 답은 정수여야 하므로 //
import math
print(math.gcd(9, 18))   # 9
print(9 / 9, 9 // 9)     # 1.0 1


# %% 내 처음 풀이 — ZeroDivisionError
# def solution(numer1, denom1, numer2, denom2):
#     top = numer1 * denom2 + numer2 * denom1
#     bottom = denom1 * denom2
#     g = math.gcd()                  # ← 괄호가 비어 있음 → 0이 나옴
#     answer = [top//g, bottom//g]    # ← 0으로 나눠서 에러
#     return answer
print(math.gcd())        # 0  (재료를 안 넣으면 0)


# %% 고친 풀이
def solution(numer1, denom1, numer2, denom2):
    top = numer1 * denom2 + numer2 * denom1   # 분자: a×d + c×b
    bottom = denom1 * denom2                  # 분모: b×d
    g = math.gcd(top, bottom)                 # 최대공약수를 구할 두 수를 넣음
    answer = [top // g, bottom // g]          # 둘 다 최대공약수로 나눠 약분
    return answer

print(solution(1, 2, 3, 4))   # [5, 4]   10/8 → gcd 2 → 5/4
print(solution(9, 2, 1, 3))   # [29, 6]  29/6 → gcd 1 → 그대로
print(solution(1, 6, 1, 3))   # [1, 2]   9/18 → gcd 9 → 1/2
