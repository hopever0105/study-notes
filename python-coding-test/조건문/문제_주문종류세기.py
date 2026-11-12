# -*- coding: utf-8 -*-
# 문제: 주문 리스트(매수/매도/취소)를 종류별 개수 딕셔너리로 (딕셔너리로 개수 세기)
# 틀렸던 것: 함수를 def 없이 count_orders(orders) = ... 로 씀, orders[] 빈 괄호

# %% 풀이
def count_orders(orders):
    count = {}                      # 빈 딕셔너리: 여기에 {종류: 개수}를 모음
    for x in orders:                # 주문 하나씩 꺼냄
        if x in count:              # 이미 나온 종류면
            count[x] = count[x] + 1 #   꺼낸 개수에 1 더해서 다시 넣기
        else:                       # 처음 나온 종류면
            count[x] = 1            #   1로 새로 넣기
    return count

# %% 확인
print(count_orders(["매수", "매도", "매수", "취소", "매수"]))  # {'매수': 3, '매도': 1, '취소': 1}
print(count_orders(["매도", "매도"]))                          # {'매도': 2}
