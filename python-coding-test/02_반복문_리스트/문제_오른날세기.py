# 문제 1. 오른 날 세기
# 종가가 날짜순으로 담긴 리스트 prices가 주어진다.
# 전날보다 종가가 "올라간" 날이 며칠인지 return 한다.
# - 같으면 오른 게 아님
# - 첫날은 전날이 없으니 세지 않음
# 제한: 1 ≤ len(prices) ≤ 1,000 / 1 ≤ prices[i] ≤ 1,000,000 (정수)
# 예: [100, 102, 101, 105, 105] → 102(↑) 101(↓) 105(↑) 105(=) → 2
# 쓸 문법: ① range(1, len()), prices[i-1], count += 1

def solution(prices):
    answer = 0
    
    
    return answer

print(solution([100, 102, 101, 105, 105]))  # 2
print(solution([500]))                      # 0
print(solution([10, 9, 8, 7]))              # 0


#%% 정답 
# 문제 1. 오른 날 세기
# 종가가 날짜순으로 담긴 리스트 prices가 주어진다.
# 전날보다 종가가 "올라간" 날이 며칠인지 return 한다.
# - 같으면 오른 게 아님
# - 첫날은 전날이 없으니 세지 않음
# 제한: 1 ≤ len(prices) ≤ 1,000 / 1 ≤ prices[i] ≤ 1,000,000 (정수)
# 예: [100, 102, 101, 105, 105] → 102(↑) 101(↓) 105(↑) 105(=) → 2
# 쓸 문법: ① range(1, len()), prices[i-1], count += 1

def solution(prices):
    answer = 0
    for i in range(1, len(prices)):
        if prices[i] > prices[i-1]:
            answer = answer +1 
    
    return answer

print(solution([100, 102, 101, 105, 105]))  # 2
print(solution([500]))                      # 0
print(solution([10, 9, 8, 7]))              # 0