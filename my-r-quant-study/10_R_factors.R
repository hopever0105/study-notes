# =====================================================================
# 팩터 지표 계산: 베타, 저변동성, 모멘텀, 밸류, 퀄리티
# 가상 데이터 사용 (실제 데이터는 1번 섹션의 rets, mkt, fund를 교체)
# 약속: rets = (일자 x 종목) 일간 수익률 행렬, mkt = 시장 일간 수익률 벡터
# =====================================================================

library(dplyr)
library(ggplot2)

FONT <- switch(Sys.info()[["sysname"]], Windows = "Malgun Gothic", Darwin = "AppleGothic", "NanumGothic")
theme_set(theme_minimal(base_family = FONT, base_size = 12))

set.seed(21)


# 1. 연습용 가상 데이터 ------------------------------------------------
n_stock <- 30
tickers <- sprintf("S%02d", 1:n_stock)

dates <- seq(as.Date("2024-01-01"), as.Date("2026-10-28"), by = "day")
dates <- dates[!format(dates, "%u") %in% c("6", "7")]
N <- length(dates)

mkt        <- rnorm(N, 0.0003, 0.009)               # 시장 수익률
true_beta  <- runif(n_stock, 0.5, 1.5)
idio_sd    <- runif(n_stock, 0.008, 0.02)
rets <- sapply(seq_len(n_stock),
               function(i) true_beta[i] * mkt + rnorm(N, 0.0001, idio_sd[i]))
colnames(rets) <- tickers

# 재무 항목 (현재 연도 + 전년도)
fund <- tibble(ticker = tickers) |>
  mutate(
    mktcap       = round(exp(rnorm(n_stock, 9, 1))),
    equity       = mktcap * exp(rnorm(n_stock, 0.2, 0.5)),
    revenue      = mktcap * exp(rnorm(n_stock, 0, 0.4)),
    revenue_prev = revenue * runif(n_stock, 0.85, 1.10),
    ni           = revenue * rnorm(n_stock, 0.06, 0.05),
    ni_prev      = revenue_prev * rnorm(n_stock, 0.055, 0.05),
    assets       = equity * runif(n_stock, 1.5, 3),
    assets_prev  = assets * runif(n_stock, 0.90, 1.05),
    cfo          = ni + revenue * rnorm(n_stock, 0, 0.02),
    ltdebt       = assets * runif(n_stock, 0.05, 0.30),
    ltdebt_prev  = ltdebt * runif(n_stock, 0.80, 1.20),
    cur_ratio    = runif(n_stock, 0.8, 2.2),
    cur_ratio_prev = cur_ratio * runif(n_stock, 0.85, 1.15),
    shares       = 1000 * runif(n_stock),
    shares_prev  = shares / sample(c(1, 1, 1, 1.02), n_stock, replace = TRUE),
    gp           = revenue * runif(n_stock, 0.20, 0.40),
    gp_prev      = revenue_prev * runif(n_stock, 0.20, 0.40)
  )


# 2. 공통 도구 ---------------------------------------------------------
# 2-1. 최근 k행만 자르기
last_n <- function(m, k) m[(nrow(m) - k + 1):nrow(m), , drop = FALSE]

# 2-2. 일간 수익률을 주간/월간 수익률로 합성 (로그를 더한 뒤 되돌리는 방식)
to_period <- function(ret, dates, fmt) {
  key <- format(dates, fmt)
  agg <- rowsum(log1p(ret), group = key, reorder = FALSE)
  expm1(agg)
}

# 2-3. 백분위 순위: 클수록 좋은 방향으로 0~1 사이 값
pct_rank <- function(x, higher_better = TRUE) {
  r <- rank(if (higher_better) x else -x, na.last = "keep", ties.method = "average")
  r / sum(!is.na(x))
}


# 3. 베타 ---------------------------------------------------------------
# 베타 = 종목과 시장의 공분산 / 시장의 분산
r1y <- last_n(rets, 252)
m1y <- tail(mkt, 252)

beta_d <- apply(r1y, 2, function(r) cov(r, m1y) / var(m1y))
round(head(beta_d), 3)

# 회귀로 검산: 기울기가 같아야 함
all.equal(unname(coef(lm(r1y[, "S01"] ~ m1y))[2]), unname(beta_d["S01"]))

# 주간 기준 (일간 노이즈가 줄어듦)
wk_r <- to_period(rets, dates, "%G-%V")
wk_m <- as.numeric(to_period(mkt, dates, "%G-%V"))
wk_r104 <- tail(wk_r, 104); wk_m104 <- tail(wk_m, 104)
beta_w <- apply(wk_r104, 2, function(r) cov(r, wk_m104) / var(wk_m104))

# 시각화: 일간 베타 vs 주간 베타 (대각선에 가까울수록 일관적)
tibble(daily = beta_d, weekly = beta_w, true = true_beta) |>
  ggplot(aes(daily, weekly)) +
  geom_point() +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed") +
  labs(title = "일간 베타 vs 주간 베타", x = "일간(1년)", y = "주간(2년)")


# 4. 저변동성 -----------------------------------------------------------
vol_d <- apply(r1y, 2, sd) * sqrt(252)                 # 일간 기준 연율화
vol_w <- apply(tail(wk_r, 52), 2, sd) * sqrt(52)       # 주간 기준 연율화

low_d <- names(sort(vol_d))[1:6]                       # 변동성 낮은 6종목
low_w <- names(sort(vol_w))[1:6]
low_d; low_w
intersect(low_d, low_w)                                # 두 방식에서 모두 뽑힌 종목


# 5. 모멘텀 -------------------------------------------------------------
# 12-1 모멘텀: 최근 1개월(약 21거래일)은 건너뛰고 직전 12개월 수익률
# (최근 1개월은 단기 반전 효과가 있어 제외하는 것이 일반적인 설계)
mom_window <- function(ret, lookback = 252, skip = 21) {
  Nr  <- nrow(ret)
  ret[(Nr - lookback + 1):(Nr - skip), , drop = FALSE]
}

w12    <- mom_window(rets, 252, 21)
mom12  <- apply(w12, 2, function(r) prod(1 + r) - 1)

# 위험조정 모멘텀: 같은 기간 수익률 / 같은 기간 연율화 변동성
mom_ra <- mom12 / (apply(w12, 2, sd) * sqrt(252))

top_mom    <- names(sort(mom12,  decreasing = TRUE))[1:6]
top_mom_ra <- names(sort(mom_ra, decreasing = TRUE))[1:6]
setdiff(top_mom, top_mom_ra)         # 위험조정 시 빠지는 종목 = 변동성 때문에 덜 매력적


# 6. 밸류 ---------------------------------------------------------------
fund <- fund |>
  mutate(
    PBR = mktcap / equity,
    PER = if_else(ni > 0, mktcap / ni, NA_real_),      # 적자면 PER 계산 안 함
    PSR = mktcap / revenue
  )

# 저PBR 상위 6개
fund |> arrange(PBR) |> select(ticker, PBR, PER, PSR) |> slice_head(n = 6)


# 7. 퀄리티: F-Score (9개 조건 중 충족 개수) ---------------------------
fund <- fund |>
  mutate(
    roa      = ni / assets,
    roa_prev = ni_prev / assets_prev,
    
    f1 = roa > 0,                                         # 수익성: ROA 흑자
    f2 = cfo > 0,                                         # 영업현금흐름 흑자
    f3 = roa > roa_prev,                                  # ROA 개선
    f4 = cfo > ni,                                        # 현금흐름이 순이익보다 큼(이익의 질)
    f5 = ltdebt / assets < ltdebt_prev / assets_prev,     # 장기부채 비중 감소
    f6 = cur_ratio > cur_ratio_prev,                      # 유동비율 개선
    f7 = shares <= shares_prev,                           # 신주 발행 없음
    f8 = gp / revenue > gp_prev / revenue_prev,           # 매출총이익률 개선
    f9 = revenue / assets > revenue_prev / assets_prev,   # 자산회전율 개선
    
    fscore = rowSums(across(f1:f9))
  )

table(fund$fscore)


# 8. 지표 합치기: 순위 점수 -------------------------------------------
factors <- tibble(ticker = tickers,
                  beta = beta_d, vol = vol_d,
                  mom = mom12, mom_ra = mom_ra) |>
  left_join(fund |> select(ticker, PBR, PER, PSR, fscore), by = "ticker")

scored <- factors |>
  mutate(
    s_lowvol  = pct_rank(vol, higher_better = FALSE),
    s_mom     = pct_rank(mom, higher_better = TRUE),
    s_value   = rowMeans(cbind(pct_rank(PBR, FALSE),
                               pct_rank(PER, FALSE),
                               pct_rank(PSR, FALSE)), na.rm = TRUE),
    s_quality = pct_rank(fscore, higher_better = TRUE),
    score     = (s_lowvol + s_mom + s_value + s_quality) / 4
  ) |>
  arrange(desc(score))

scored |> select(ticker, score, s_lowvol, s_mom, s_value, s_quality) |> slice_head(n = 8)

# 팩터 점수 사이의 상관: 서로 다른 정보를 주는지 확인
round(cor(scored[, c("s_lowvol", "s_mom", "s_value", "s_quality")],
          use = "pairwise.complete.obs"), 2)

dir.create("data", showWarnings = FALSE)
saveRDS(scored, "data/factor_scores.rds")


# 9. 실제 적용 시 주의 -------------------------------------------------
# - 미래 정보 사용(look-ahead): 그 시점에 공시되지 않은 재무 데이터를 쓰면 안 됨
# - 생존 편향: 상장폐지 종목이 빠진 데이터로 검증하면 성과가 부풀려짐
# - 거래 비용, 리밸런싱 주기, 유동성 제약은 백테스트(ch12)에서 반영
# - 순위 점수는 이상치에 덜 민감하지만 값의 크기 정보를 버림 -> ch11에서 보완


# =====================================================================
# 6개월 모멘텀(126거래일, 최근 21일 제외)을 계산하고
#  베타가 전체 중앙값보다 낮고 F-Score가 4 이상인 종목 중
#  모멘텀 상위 5개를 뽑기
# =====================================================================

mom6 <- apply(mom_window(rets, 126, 21), 2, function(r) prod(1 + r) - 1)

hw <- tibble(ticker = tickers, mom6 = mom6, beta = beta_d) |>
  left_join(fund |> select(ticker, fscore), by = "ticker") |>
  filter(beta < median(beta), fscore >= 4) |>
  arrange(desc(mom6)) |>
  slice_head(n = 5)

hw
stopifnot(nrow(hw) <= 5, all(hw$beta < median(beta_d)))