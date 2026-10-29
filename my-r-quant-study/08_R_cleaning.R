# =====================================================================
# 수집한 데이터 정리하기
# 흐름: 가격 -> 재무제표 -> 가치지표 -> 하나의 마스터 표로 결합
# =====================================================================

library(dplyr)
library(tidyr)
library(xts)
library(zoo)


# 1. 연습용 가상 데이터 만들기 -----------------------------------------
set.seed(7)

dates <- seq(as.Date("2026-06-01"), as.Date("2026-10-28"), by = "day")
dates <- dates[!format(dates, "%u") %in% c("6", "7")]   # 주말 제외 (%u: 월=1 ... 일=7)
n <- length(dates)

make_path <- function(start) start * cumprod(1 + rnorm(n, 0, 0.015))
px_mat <- cbind(A = make_path(100), B = make_path(50), C = make_path(20))
px <- xts(px_mat, order.by = dates)

# 현실에서 흔한 문제를 일부러 심기: 결측, 이상값
px[10:11, "B"] <- NA          # 이틀 연속 결측
px[30, "C"]    <- px[30, "C"] * 1.5   # 하루만 튀는 값

# 재무제표 (DART 응답과 비슷한 긴 형태). 금액은 억원 -> 원 문자열로
fin_src <- tribble(
  ~stock_code, ~sj_div, ~account_nm,        ~eok,
  "A", "IS",  "매출액",                      1000,
  "A", "IS",  "영업이익",                     200,
  "A", "IS",  "당기순이익",                   150,
  "A", "BS",  "자산총계",                    2000,
  "A", "BS",  "부채총계",                     800,
  "A", "BS",  "자본총계",                    1200,
  "B", "IS",  "수익(매출액)",                3000,
  "B", "IS",  "영업이익(손실)",               300,
  "B", "IS",  "당기순이익(손실)",             250,
  "B", "BS",  "자산총계",                    5000,
  "B", "BS",  "부채총계",                    3000,
  "B", "BS",  "자본총계",                    2000,
  "C", "IS",  "매출액",                       500,
  "C", "IS",  "영업이익",                     -20,
  "C", "IS",  "당기순이익",                   -50,
  "C", "BS",  "자산총계",                     900,
  "C", "BS",  "부채총계",                     700,
  "C", "BS",  "자본총계",                     200
)
fin_raw <- fin_src |>
  mutate(thstrm_amount = format(eok * 1e8, big.mark = ",",
                                scientific = FALSE, trim = TRUE)) |>
  select(-eok)

# 시가총액 (억원)
mkt <- tibble(stock_code = c("A", "B", "C"),
              market     = "KOSPI",
              mktcap_eok = c(1000, 3000, 400))


# 2. 가격 정리 ---------------------------------------------------------
# 2-1. xts -> 긴 형태 표 (ggplot, dplyr 작업에 유리)
px_long <- tibble(date = index(px)) |>
  bind_cols(as_tibble(coredata(px))) |>
  pivot_longer(-date, names_to = "ticker", values_to = "close")

# 2-2. 결측 처리: 직전 값으로 채우되 연속 3일까지만 허용
colSums(is.na(px))                          # 처리 전 결측 개수
px_f <- na.locf(px, maxgap = 3, na.rm = FALSE)
colSums(is.na(px_f))                        # 처리 후

# 2-3. 일간 수익률과 이상치 표시
ret_long <- tibble(date = index(px_f)) |>
  bind_cols(as_tibble(coredata(px_f))) |>
  pivot_longer(-date, names_to = "ticker", values_to = "close") |>
  arrange(ticker, date) |>
  group_by(ticker) |>
  mutate(ret = close / lag(close) - 1,
         is_outlier = abs(ret) > 0.30) |>   # 하루 30% 이상 변동은 확인 대상
  ungroup()

ret_long |> filter(is_outlier)              # 눈으로 확인 후 처리 방침 결정

# 2-4. 월말 가격과 월간 수익률 (진행 중인 마지막 달 포함)
month_end   <- apply.monthly(px_f, last)
monthly_ret <- na.omit(month_end / stats::lag(month_end, k = 1) - 1)
monthly_ret


# 3. 재무제표 정리 -----------------------------------------------------
# 3-1. 문자열 금액 -> 숫자, 계정명 표준화
fin_std <- fin_raw |>
  mutate(
    amount = as.numeric(gsub(",", "", thstrm_amount)),
    item = case_when(
      grepl("^(수익\\(매출액\\)|매출액)", account_nm) ~ "revenue",
      grepl("^영업이익",   account_nm) ~ "op_income",
      grepl("^당기순이익", account_nm) ~ "net_income",
      grepl("^자산총계",   account_nm) ~ "assets",
      grepl("^부채총계",   account_nm) ~ "liabilities",
      grepl("^자본총계",   account_nm) ~ "equity",
      TRUE ~ NA_character_
    )
  ) |>
  filter(!is.na(item))

# 3-2. 중복 확인 -> 종목당 항목 하나로
fin_std |> count(stock_code, item) |> filter(n > 1)    # 중복이 있으면 확인
fin_wide <- fin_std |>
  group_by(stock_code, item) |>
  slice(1) |>
  ungroup() |>
  select(stock_code, item, amount) |>
  pivot_wider(names_from = item, values_from = amount)

# 3-3. 파생 지표
fin_wide <- fin_wide |>
  mutate(
    roe        = net_income / equity,
    debt_ratio = liabilities / equity,
    op_margin  = op_income / revenue
  )
fin_wide


# 4. 가치지표 정리 -----------------------------------------------------
value_tbl <- fin_wide |>
  inner_join(mkt, by = "stock_code") |>
  mutate(
    mktcap = mktcap_eok * 1e8,                           # 억원 -> 원
    PER = if_else(net_income > 0, mktcap / net_income, NA_real_),
    PBR = if_else(equity     > 0, mktcap / equity,     NA_real_),
    PSR = if_else(revenue    > 0, mktcap / revenue,    NA_real_),
    loss_making = net_income <= 0                        # 적자 표시 (PER 결측 이유)
  )

# 무한대/비정상 값 점검
value_tbl |>
  summarise(across(c(PER, PBR, PSR), list(na = ~ sum(is.na(.x)),
                                          inf = ~ sum(is.infinite(.x)))))


# 5. 마스터 표로 결합 --------------------------------------------------
last_px <- tibble(ticker = colnames(px_f),
                  last_close = as.numeric(last(px_f)))

ret3m <- tibble(ticker = colnames(monthly_ret),
                ret_3m = apply(tail(monthly_ret, 3), 2, function(r) prod(1 + r) - 1))

master <- value_tbl |>
  select(stock_code, market, mktcap_eok, roe, debt_ratio, op_margin,
         PER, PBR, PSR, loss_making) |>
  left_join(last_px, by = c("stock_code" = "ticker")) |>
  left_join(ret3m,   by = c("stock_code" = "ticker"))

# 결합 후 점검: 키 중복 없는지, 행 수 유지되는지
stopifnot(!anyDuplicated(master$stock_code), nrow(master) == nrow(mkt))
master

dir.create("data", showWarnings = FALSE)
saveRDS(master, "data/master.rds")


# =====================================================================
# master에서 PBR < 1 이고 ROE > 10% 인 종목을 3개월 수익률 높은 순으로 정렬하고,
# 가격 이상치(is_outlier)가 한 번이라도 있었던 종목은 'check' 표시를 붙이기
# =====================================================================

flag_tbl <- ret_long |>
  group_by(ticker) |>
  summarise(has_outlier = any(is_outlier, na.rm = TRUE))

screen <- master |>
  filter(PBR < 1, roe > 0.10) |>
  left_join(flag_tbl, by = c("stock_code" = "ticker")) |>
  mutate(note = if_else(has_outlier, "check", "")) |>
  arrange(desc(ret_3m)) |>
  select(stock_code, PBR, roe, ret_3m, note)

screen
stopifnot("A" %in% screen$stock_code)    # 가상 데이터 기준 A가 통과해야 함