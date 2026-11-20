# -*- coding: utf-8 -*-
# 연속 상승 최장 길이 (Lv1)
# 문제: 종가 리스트에서 '전날보다 오른 날'이 연속으로 몇 번 이어졌는지의 최댓값. 보합은 오른 게 아님.
# 예: [100, 101, 102, 101, 103, 104, 105, 99] → 3 (103→104→105)
# Spyder: F5 전체 실행

# %% 정답
def longest_up_streak(closes):
    best = 0      # 지금까지 가장 길었던 연속 상승
    now = 0       # 지금 이어지고 있는 연속 상승
    for i in range(1, len(closes)):          # 1번부터: 0번은 전날이 없음
        if closes[i] > closes[i - 1]:        # 전날보다 올랐으면
            now = now + 1                    #   연속 하나 늘림
            if now > best:                   #   기록 갱신
                best = now
        else:                                # 내렸거나 보합이면
            now = 0                          #   연속 끊김 → 0부터 다시
    return best                              # for가 다 끝난 뒤에 return

# %% 확인
print(longest_up_streak([100, 101, 102, 101, 103, 104, 105, 99]))   # 3
print(longest_up_streak([5, 4, 3]))                                  # 0

# %% 손으로 따라가 보기 (첫 번째 예시)
# i=1 101>100 now=1 best=1
# i=2 102>101 now=2 best=2
# i=3 101<102 now=0
# i=4 103>101 now=1
# i=5 104>103 now=2
# i=6 105>104 now=3 best=3
# i=7  99<105 now=0      → 답 3
# 반복 한 번 → 종가 n개면 비교 n-1번 (100만 개여도 100만 번 정도라 빠름)
