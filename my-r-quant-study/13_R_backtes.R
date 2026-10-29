# =====================================================================
#  포트폴리오 백테스트
# 목적: 신호 생성 -> 리밸런싱 -> 비용 반영 -> 성과 비교, 그리고 흔한 함정 확인
# 가상 데이터 사용 (실제 데이터는 1번 섹션의 rets, dates만 교체)
# 약속: rets = (일자 x 종목) 일간 수익률 행렬, dates = 같은 길이의 날짜 벡터
# =====================================================================

pkgs <- c("quadprog", "dplyr", "tidyr", "ggplot2")
to_install <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(to_install) > 0) install.packages(to_install)

library(quadprog)
library(dplyr)
library(tidyr)
library(ggplot2)
FONT <- switch(Sys.info()[["sysname"]], Windows = "Malgun Gothic", Darwin = "AppleGothic", "NanumGothic")
theme_set(theme_minimal(base_family = FONT, base_size = 12))
set.seed(101)


# 1. 연습용 가상 데이터 ------------------------------------------------
n_stock <- 40
dates   <- seq(as.Date("2023-01-02"), as.Date("2026-10-28"), by = "day")
dates   <- dates[!format(dates, "%u") %in% c("6", "7")]
N       <- length(dates)

mkt   <- rnorm(N, 0.0003, 0.009)
drift <- rnorm(n_stock, 0.0003, 0.0004)       # 종목별 지속적 성향 (모멘텀이 약하게 통하도록)
beta  <- runif(n_stock, 0.6, 1.4)
rets  <- sapply(seq_len(n_stock), function(i)
  drift[i] + beta[i] * mkt + rnorm(N, 0, 0.012))
colnames(rets) <- sprintf("S%02d", seq_len(n_stock))


# 2. 리밸런싱 날짜 -----------------------------------------------------
# 각 월의 마지막 거래일을 리밸런싱일로 사용 (신호 계산에 필요한 252일 이후부터)
ym            <- format(dates, "%Y-%m")
month_end_idx <- which(!duplicated(ym, fromLast = TRUE))
rebal_monthly <- month_end_idx[month_end_idx >= 252 & month_end_idx < N]

# 분기 리밸런싱: 3, 6, 9, 12월 말만
rebal_quarterly <- rebal_monthly[format(dates[rebal_monthly], "%m") %in% c("03", "06", "09", "12")]


# 3. 종목 선택 규칙(신호) ----------------------------------------------
# 규칙은 "t일까지의 정보만 보고 비중 벡터를 반환하는 함수"로 만든다.
# 이 구조 덕분에 미래 정보가 섞이기 어렵다.

# 3-1. 12-1 모멘텀 상위 top_frac 동일가중
make_mom_picker <- function(rets, top_frac = 0.2, lookback = 252, skip = 21) {
  n <- ncol(rets)
  function(t) {
    idx <- (t - lookback + 1):(t - skip)                       # t 이전만 사용
    mom <- apply(rets[idx, , drop = FALSE], 2, function(r) prod(1 + r) - 1)
    k   <- ceiling(n * top_frac)
    w   <- rep(0, n)
    w[order(mom, decreasing = TRUE)[1:k]] <- 1 / k
    w
  }
}

# 3-2. 벤치마크: 전 종목 동일가중
make_equal_picker <- function(rets) {
  n <- ncol(rets)
  function(t) rep(1 / n, n)
}

# 3-3. (교육용) 미래를 훔쳐보는 잘못된 규칙: 다음 21일 수익률로 선택
make_peek_picker <- function(rets, top_frac = 0.2, horizon = 21) {
  n <- ncol(rets); N <- nrow(rets)
  function(t) {
    idx <- (t + 1):min(t + horizon, N)                         # t 이후 = 미래!
    fut <- apply(rets[idx, , drop = FALSE], 2, function(r) prod(1 + r) - 1)
    k   <- ceiling(n * top_frac)
    w   <- rep(0, n)
    w[order(fut, decreasing = TRUE)[1:k]] <- 1 / k
    w
  }
}


# 4. 백테스트 엔진 -----------------------------------------------------
# - t일 수익률은 t-1일 종가에 보유한 비중으로 얻는다 (비중은 매일 가격에 따라 드리프트)
# - 리밸런싱일 종가에 새 비중으로 교체 -> 효과는 다음 날부터
# - 회전율 = 교체 때 바뀌는 비중의 절대값 합, 비용 = 회전율 x 편도비용(bp)
run_backtest <- function(rets, dates, pick_fn, rebal_idx, cost_bps = 10) {
  N <- nrow(rets); n <- ncol(rets)
  w <- rep(0, n)
  gross <- net <- turn <- numeric(N)
  
  for (t in seq_len(N)) {
    r_t <- rets[t, ]
    pr  <- sum(w * r_t)                         # 오늘 포트폴리오 총수익률
    if (sum(w) > 0) w <- w * (1 + r_t) / (1 + pr)   # 가격 변동에 따른 비중 드리프트
    
    cost_t <- 0; to <- 0
    if (t %in% rebal_idx) {
      w_new  <- pick_fn(t)
      to     <- sum(abs(w_new - w))             # 이번 리밸런싱의 회전율
      cost_t <- to * cost_bps / 1e4
      w      <- w_new
    }
    gross[t] <- pr; turn[t] <- to; net[t] <- pr - cost_t
  }
  
  start <- rebal_idx[1] + 1                     # 첫 리밸런싱 다음 날부터 성과 측정
  tibble(date = dates, gross = gross, turnover = turn, net = net)[start:N, ]
}

# 간단 요약 (자세한 성과 지표는 ch14)
quick_summary <- function(bt, label) {
  yrs <- nrow(bt) / 252
  tibble(
    strategy      = label,
    ann_ret_net   = prod(1 + bt$net)^(1 / yrs) - 1,
    ann_vol       = sd(bt$net) * sqrt(252),
    turnover_year = sum(bt$turnover) / yrs,      # 연간 회전율
    cost_drag     = (prod(1 + bt$gross)^(1 / yrs) - 1) - (prod(1 + bt$net)^(1 / yrs) - 1)
  )
}


# 5. 실행: 전략 vs 벤치마크 --------------------------------------------
bt_mom <- run_backtest(rets, dates, make_mom_picker(rets, 0.2), rebal_monthly, cost_bps = 10)
bt_eq  <- run_backtest(rets, dates, make_equal_picker(rets),    rebal_monthly, cost_bps = 10)

bind_rows(quick_summary(bt_mom, "모멘텀 상위20%"),
          quick_summary(bt_eq,  "전체 동일가중"))

curve <- bind_rows(
  tibble(date = bt_mom$date, value = cumprod(1 + bt_mom$net), strategy = "모멘텀 상위20%"),
  tibble(date = bt_eq$date,  value = cumprod(1 + bt_eq$net),  strategy = "전체 동일가중")
)
ggplot(curve, aes(date, value, color = strategy)) +
  geom_line() +
  labs(title = "누적 성과 (순수익 기준, 거래비용 10bp 반영)", x = NULL, y = "시작=1", color = NULL)


# 6. 거래비용 민감도 ---------------------------------------------------
cost_grid <- c(0, 10, 30, 60)
bind_rows(lapply(cost_grid, function(cb) {
  bt <- run_backtest(rets, dates, make_mom_picker(rets, 0.2), rebal_monthly, cost_bps = cb)
  quick_summary(bt, paste0("비용 ", cb, "bp"))
}))


# 7. 흔한 함정 ① 미래 정보 사용(look-ahead) ---------------------------
# 같은 엔진에 '미래를 보는' 규칙을 넣으면 비현실적으로 좋은 성과가 나온다.
# 이런 결과가 보이면 대개 코드에 미래 정보가 섞인 것이다.
bt_peek <- run_backtest(rets, dates, make_peek_picker(rets, 0.2), rebal_monthly, cost_bps = 10)
bind_rows(quick_summary(bt_mom,  "정상 모멘텀"),
          quick_summary(bt_peek, "미래참조(잘못된 규칙)"))


# 8. 흔한 함정 ② 파라미터 과최적화 확인 ------------------------------
# 상위 비율을 바꿔가며 보되, 한 값만 유독 좋은지(불안정) 주변 값과 함께 본다.
bind_rows(lapply(c(0.10, 0.20, 0.30, 0.50), function(fr) {
  bt <- run_backtest(rets, dates, make_mom_picker(rets, fr), rebal_monthly, cost_bps = 10)
  quick_summary(bt, paste0("상위 ", fr * 100, "%"))
}))


# 9. 최적화 기반 규칙을 백테스트에 넣기 -------------------------------
# 같은 엔진에 '비중 벡터를 돌려주는 함수'만 바꿔 끼우면 된다.
# 최적화 입력(공분산)은 반드시 t일까지의 데이터로만 추정한다.

# 9-1. 최소분산 (공분산 축소 + 종목당 최대 cap)
make_minvar_picker <- function(rets, window = 252, cap = 0.10, lambda = 0.2) {
  n <- ncol(rets)
  function(t) {
    est <- rets[(t - window + 1):t, , drop = FALSE]
    S0  <- cov(est)
    S   <- (1 - lambda) * S0 + lambda * diag(diag(S0))
    A   <- cbind(rep(1, n), diag(n), -diag(n))
    b   <- c(1, rep(0, n), rep(-cap, n))
    solve.QP(2 * S + diag(1e-10, n), rep(0, n), A, b, meq = 1)$solution
  }
}

# 9-2. 역변동성 가중 (위험균형의 단순 근사)
make_invvol_picker <- function(rets, window = 126) {
  function(t) {
    v <- apply(rets[(t - window + 1):t, , drop = FALSE], 2, sd)
    w <- 1 / v
    w / sum(w)
  }
}

bt_minvar <- run_backtest(rets, dates, make_minvar_picker(rets), rebal_monthly, cost_bps = 10)
bt_invvol <- run_backtest(rets, dates, make_invvol_picker(rets), rebal_monthly, cost_bps = 10)

bind_rows(quick_summary(bt_mom,    "모멘텀 상위20%"),
          quick_summary(bt_eq,     "전체 동일가중"),
          quick_summary(bt_minvar, "최소분산(10%캡)"),
          quick_summary(bt_invvol, "역변동성"))


# 10. 표본 내 / 표본 외 분리 (walk-forward의 가장 단순한 형태) ------------
# 파라미터는 앞 절반 기간에서만 고르고, 뒤 절반에서 성과를 확인한다.
cand <- c(0.10, 0.20, 0.30, 0.50)
bts  <- lapply(cand, function(fr)
  run_backtest(rets, dates, make_mom_picker(rets, fr), rebal_monthly, cost_bps = 10))

split_date <- bts[[1]]$date[floor(nrow(bts[[1]]) / 2)]
ann_ret <- function(x) prod(1 + x$net)^(252 / nrow(x)) - 1

split_tbl <- tibble(
  top_frac      = cand,
  in_sample     = sapply(bts, function(b) ann_ret(b[b$date <= split_date, ])),
  out_of_sample = sapply(bts, function(b) ann_ret(b[b$date >  split_date, ]))
)
split_tbl

best_in <- split_tbl$top_frac[which.max(split_tbl$in_sample)]
cat("표본 내 최고 파라미터:", best_in, "\n")
cat("그 파라미터의 표본 외 순위:",
    rank(-split_tbl$out_of_sample)[split_tbl$top_frac == best_in], "/", length(cand), "\n")
# 표본 내 1등이 표본 외에서도 1등이 아니라면 과최적화를 의심한다


# 11. 저장 -------------------------------------------------------------
dir.create("data", showWarnings = FALSE)
saveRDS(list(mom = bt_mom, eq = bt_eq), "data/backtest_results.rds")


# ====================================================================
# 월간 vs 분기 리밸런싱을 (비용 20bp) 비교하여 순수익, 연간 회전율, 비용 drag를 한 표로.
# 그리고 어느 쪽이 "비용 대비 효율적"인지 한 줄로 결론을 출력하기
# =====================================================================

bt_m <- run_backtest(rets, dates, make_mom_picker(rets, 0.2), rebal_monthly,   cost_bps = 20)
bt_q <- run_backtest(rets, dates, make_mom_picker(rets, 0.2), rebal_quarterly, cost_bps = 20)

cmp <- bind_rows(quick_summary(bt_m, "월간 리밸런싱"),
                 quick_summary(bt_q, "분기 리밸런싱"))
cmp

best <- cmp$strategy[which.max(cmp$ann_ret_net)]
cat("순수익 기준으로 더 나은 쪽:", best, "\n")
stopifnot(cmp$turnover_year[1] > cmp$turnover_year[2])   # 월간이 회전율이 더 높아야 정상