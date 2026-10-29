# =====================================================================
# 가격 데이터 수집, 수익률, 변동성
# 목적: 수정주가를 받아 수익률/누적수익률/변동성을 계산
# 주의: Yahoo Finance는 비공식 경로라 가끔 실패함 -> tryCatch로 방어
# =====================================================================

library(quantmod)               # getSymbols, Ad, SMA 등
library(PerformanceAnalytics)   # Return.calculate, 성과지표
library(xts)


# 1. 한 종목 받기 ------------------------------------------------------
# 한국 종목은 코드 뒤에 .KS(코스피) / .KQ(코스닥)
# auto.assign = FALSE 로 하면 변수명 대신 반환값으로 받음
samsung <- tryCatch(
  getSymbols("005930.KS", src = "yahoo",
             from = "2024-01-01", to = "2026-10-28",
             auto.assign = FALSE),
  error = function(e) { message("다운로드 실패: ", e$message); NULL }
)
stopifnot(!is.null(samsung))

head(samsung)        # Open High Low Close Volume Adjusted
class(samsung)       # xts: 날짜가 인덱스인 시계열


# 2. xts 기본 -----------------------------------------------------------
adj <- Ad(samsung)               # 수정종가만 추출
adj["2026-10"]                   # 특정 월
adj["2026-10-01/2026-10-28"]     # 구간
last(adj, 5)                     # 마지막 5개
index(adj)[1:3]                  # 날짜
coredata(adj)[1:3]               # 값만


# 3. 수익률 ------------------------------------------------------------
ret <- Return.calculate(adj, method = "discrete") |> na.omit()
head(ret)

cum_ret <- cumprod(1 + ret) - 1       # 누적 수익률
last(cum_ret)


# 4. 변동성 ------------------------------------------------------------
# 연율화 변동성 = 일간 표준편차 * sqrt(거래일 수)
ann_vol <- sd(ret) * sqrt(252)
ann_vol

# 20일 롤링 변동성
roll_vol <- rollapply(ret, width = 20, FUN = sd) * sqrt(252)
last(roll_vol)


# 5. 여러 종목 합치기 ---------------------------------------------------
tickers <- c("005930.KS", "000660.KS", "035420.KS")

get_adj <- function(tk) {
  x <- tryCatch(
    getSymbols(tk, src = "yahoo", from = "2024-01-01", to = "2026-10-28",
               auto.assign = FALSE),
    error = function(e) NULL
  )
  if (is.null(x)) return(NULL)
  Sys.sleep(1)
  Ad(x)
}

price_list <- Filter(Negate(is.null), setNames(lapply(tickers, get_adj), tickers))
prices <- do.call(merge, price_list)
colnames(prices) <- names(price_list)
head(prices)

rets <- Return.calculate(prices, method = "discrete") |> na.omit()


# 6. 성과 요약 ---------------------------------------------------------
table.AnnualizedReturns(rets)    # 연율 수익률, 변동성, 샤프비율

chart.CumReturns(rets, legend.loc = "topleft",
                 main = "누적 수익률 비교")


# 7. 저장과 불러오기 ---------------------------------------------------
dir.create("data", showWarnings = FALSE)
write.zoo(prices, "data/prices.csv", sep = ",")

prices2 <- as.xts(read.zoo("data/prices.csv", sep = ",", header = TRUE,
                           index.column = 1, format = "%Y-%m-%d"))


# =====================================================================
# 20일/60일 이동평균 교차 전략의 일간 수익률을 계산하고 단순 보유와 비교
# (위에서 받은 adj, ret 사용)
# =====================================================================


adj_c <- na.omit(adj)                                   # 중간 결측 제거
ret_c <- Return.calculate(adj_c, method = "discrete") |> na.omit()

sma20 <- SMA(adj_c, n = 20)
sma60 <- SMA(adj_c, n = 60)

signal <- ifelse(sma20 > sma60, 1, 0)
signal <- xts(signal, order.by = index(adj_c))
signal[is.na(signal)] <- 0                              # 이동평균을 못 구하는 초반은 현금

# 오늘 신호는 내일 수익률에 적용 (stats::lag로 dplyr::lag와 충돌 방지)
strat_ret <- stats::lag(signal, 1) * ret_c
strat_ret <- na.omit(strat_ret)
colnames(strat_ret) <- "MA_cross"

compare <- merge(strat_ret, ret_c)
colnames(compare) <- c("MA_cross", "Buy_Hold")
compare <- na.omit(compare)

table.AnnualizedReturns(compare)
chart.CumReturns(compare, legend.loc = "topleft",
                 main = "이동평균 교차 vs 단순 보유")