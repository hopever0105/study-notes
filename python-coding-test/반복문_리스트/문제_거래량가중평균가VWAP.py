# -*- coding: utf-8 -*-
# 거래량 가중 평균가 VWAP (Lv1)
# 문제: (체결가, 수량) 튜플 리스트 → (가격×수량 합) ÷ (수량 합), 둘째 자리 반올림. 체결 없으면 None.
# 예: [(100, 10), (200, 30)] → 175.0  ((1000 + 6000) / 40)
# Spyder: F5 전체 실행

# %% 정답
def vwap(trades):
    amount = 0     # 가격 × 수량의 합 (거래대금)
    volume = 0     # 수량의 합 (거래량)
    for price, qty in trades:              # (100, 10) → price=100, qty=10
        amount = amount + price * qty
        volume = volume + qty
    if volume == 0:                        # 체결이 없으면 0으로 나누게 됨 → 먼저 막기
        return None
    return round(amount / volume, 2)

# %% 확인
print(vwap([(100, 10), (200, 30)]))   # 175.0
print(vwap([(50, 1), (60, 1)]))       # 55.0
print(vwap([]))                       # None

# %% 포인트
# - 그냥 평균 (100+200)/2 = 150 과 다름: 200원에 30주로 더 많이 거래됐으니 200 쪽으로 끌려가 175
# - 실무: 기관 주문 집행 성적을 "오늘 VWAP보다 싸게 샀나"로 매김 (라온지아이 같은 트레이딩 회사 면접 단골)
