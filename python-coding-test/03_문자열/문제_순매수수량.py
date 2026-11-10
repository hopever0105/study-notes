# 문제 3. 순매수 수량
# 주문 기록이 쉼표로 이어진 문자열 orders로 주어진다.
# 각 주문은 'B'(매수) 또는 'S'(매도) 한 글자 뒤에 수량(양의 정수)이 붙어 있다.
# (매수 수량 합) - (매도 수량 합)을 return 한다.
# 제한: 주문 1~100개 / 수량 1~10,000 / 공백 없음 / 맨 앞·끝에 쉼표 없음
# 쓸 문법: ③ split(",")  ④ p[0], D), if / else

def solution(orders):
    answer = 0

print(solution("B10,S3,B5"))   # 12
print(solution("S7"))          # -7
print(solution("B100,S100"))   # 0


#%%
def solution(orders):
    answer = 0
    for p in orders.split(","):
      if p[0] =='B':
          answer = answer + int(p[1:])  
      elif p[0] =='S': 
          answer = answer - int(p[1:])
      else: print("error")
    return answer 

        


print(solution("B10,S3,B5"))   # 12
print(solution("S7"))          # -7
print(solution("B100,S100"))   # 0



