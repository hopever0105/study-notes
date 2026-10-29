# =====================================================================
#  성과와 위험 평가
# 목적: 수익률 시계열 하나(+벤치마크)로 성과/위험/벤치마크 대비 지표를 계산
# 가상 데이터 사용 (실제 데이터는 1번 섹션의 strat, bench, smb, wml, dates만 교체)
# 약속: strat, bench, smb, wml = 같은 길이의 일간 수익률 벡터, dates = 날짜 벡터
# =====================================================================

library(dplyr)
library(tidyr)
library(ggplot2)
FONT <- switch(Sys.info()[["sysname"]], Windows = "Malgun Gothic", Darwin = "AppleGothic", "NanumGothic")
theme_set(theme_minimal(base_family = FONT, base_size = 12))
set.seed(202)


# 1. 연습용 가상 데이터 ------------------------------------------------
dates <- seq(as.Date("2022-01-03"), as.Date("2026-10-28"), by = "day")
dates <- dates[!format(dates, "%u") %in% c("6", "7")]
N <- length(dates)

bench <- rnorm(N, 0.0003, 0.009)
smb   <- rnorm(N, 0.0000, 0.004)        # 가상의 소형주 요인 수익률
wml   <- rnorm(N, 0.0001, 0.005)        # 가상의 모멘텀 요인 수익률
strat <- 0.00015 + 0.85 * bench + 0.30 * smb + 0.20 * wml + rnorm(N, 0, 0.004)

rf_annual <- 0.03                      # 무위험수익률(연). 실제로는 CD금리/국채금리 등 사용
rf_d      <- (1 + rf_annual)^(1 / 252) - 1
ANN       <- 252                       # 연율화 거래일 수


# 2. 지표 함수 모음 ----------------------------------------------------
# 2-1. 수익률 지표
cagr    <- function(r) prod(1 + r)^(ANN / length(r)) - 1       # 연복리수익률
ann_vol <- function(r) sd(r) * sqrt(ANN)

# 2-2. 위험조정 수익률
sharpe  <- function(r, rf = rf_d) mean(r - rf) / sd(r - rf) * sqrt(ANN)

sortino <- function(r, mar = rf_d) {
  dd <- sqrt(mean(pmin(r - mar, 0)^2))                          # 하방편차
  mean(r - mar) / dd * sqrt(ANN)
}

# 2-3. 낙폭(drawdown)
drawdown_series <- function(r) {
  wealth <- cumprod(1 + r)
  wealth / cummax(wealth) - 1
}
max_dd <- function(r) min(drawdown_series(r))

# 가장 오래 수면 아래(직전 고점 미회복)에 있었던 기간(거래일)
longest_underwater <- function(r) {
  under <- drawdown_series(r) < 0
  if (!any(under)) return(0L)
  max(rle(under)$lengths[rle(under)$values])
}

calmar <- function(r) cagr(r) / abs(max_dd(r))

# 2-4. 꼬리 위험: 과거 시뮬레이션 방식과 정규분포 가정 방식
var_hist  <- function(r, p = 0.05) unname(quantile(r, p))
cvar_hist <- function(r, p = 0.05) mean(r[r <= quantile(r, p)])
var_norm  <- function(r, p = 0.05) mean(r) + qnorm(p) * sd(r)

skew <- function(r) mean((r - mean(r))^3) / sd(r)^3
kurt <- function(r) mean((r - mean(r))^4) / sd(r)^4 - 3        # 초과첨도

# 2-5. 벤치마크 대비 지표
capm <- function(r, b, rf = rf_d) {
  fit <- lm(I(r - rf) ~ I(b - rf))
  c(alpha_ann = unname(coef(fit)[1]) * ANN,
    beta      = unname(coef(fit)[2]),
    r2        = summary(fit)$r.squared)
}
tracking_error <- function(r, b) sd(r - b) * sqrt(ANN)
info_ratio     <- function(r, b) mean(r - b) / sd(r - b) * sqrt(ANN)

capture <- function(r, b) {
  c(up   = mean(r[b > 0]) / mean(b[b > 0]),
    down = mean(r[b < 0]) / mean(b[b < 0]))
}


# 3. 한 번에 보는 성과표 ----------------------------------------------
perf_table <- function(r, b = NULL) {
  out <- tibble(
    CAGR        = cagr(r),
    변동성      = ann_vol(r),
    샤프        = sharpe(r),
    소르티노    = sortino(r),
    MDD         = max_dd(r),
    칼마        = calmar(r),
    최장낙폭일  = longest_underwater(r),
    VaR95_일    = var_hist(r),
    CVaR95_일   = cvar_hist(r),
    왜도        = skew(r),
    초과첨도    = kurt(r),
    승률        = mean(r > 0)
  )
  if (!is.null(b)) {
    cp <- capm(r, b)
    out <- bind_cols(out, tibble(
      알파_연 = cp["alpha_ann"], 베타 = cp["beta"],
      추적오차 = tracking_error(r, b), 정보비율 = info_ratio(r, b),
      상승포착 = capture(r, b)["up"], 하락포착 = capture(r, b)["down"]
    ))
  }
  out
}

tab <- bind_rows(
  perf_table(strat, bench) |> mutate(portfolio = "전략"),
  perf_table(bench)        |> mutate(portfolio = "벤치마크")
) |> relocate(portfolio)

print(tab |> mutate(across(where(is.numeric), ~ round(.x, 4))), width = Inf)


# 4. 낙폭 시각화 ------------------------------------------------------
dd_df <- bind_rows(
  tibble(date = dates, dd = drawdown_series(strat), who = "전략"),
  tibble(date = dates, dd = drawdown_series(bench), who = "벤치마크")
)
ggplot(dd_df, aes(date, dd, color = who)) +
  geom_line() +
  scale_y_continuous(labels = scales::percent) +
  labs(title = "낙폭(Drawdown)", x = NULL, y = NULL, color = NULL)


# 5. 월별 수익률 표(히트맵) -------------------------------------------
monthly <- tibble(date = dates, r = strat) |>
  mutate(year = as.integer(format(date, "%Y")),
         month = as.integer(format(date, "%m"))) |>
  group_by(year, month) |>
  summarise(ret = prod(1 + r) - 1, .groups = "drop")

ggplot(monthly, aes(factor(month), factor(year), fill = ret)) +
  geom_tile(color = "white") +
  geom_text(aes(label = sprintf("%.1f", ret * 100)), size = 3) +
  scale_fill_gradient2(low = "steelblue", mid = "white", high = "firebrick",
                       midpoint = 0, labels = scales::percent) +
  labs(title = "월별 수익률(%)", x = "월", y = NULL, fill = NULL)


# 6. 롤링 지표: 성과가 시기별로 안정적인가 -----------------------------
roll_apply <- function(x, width, f) {
  out <- rep(NA_real_, length(x))
  for (i in width:length(x)) out[i] <- f(x[(i - width + 1):i])
  out
}
roll <- tibble(
  date    = dates,
  vol_1y  = roll_apply(strat, 252, ann_vol),
  sharpe_1y = roll_apply(strat, 252, sharpe)
) |>
  pivot_longer(-date, names_to = "metric", values_to = "value")

ggplot(roll, aes(date, value)) +
  geom_line(na.rm = TRUE) +
  facet_wrap(~ metric, scales = "free_y", ncol = 1) +
  labs(title = "1년 롤링 지표", x = NULL, y = NULL)


# 7. 샤프지수의 불확실성: 부트스트랩 ----------------------------------
# 표본이 짧으면 샤프지수는 크게 흔들린다. 재표집으로 신뢰구간을 본다.
boot_sharpe <- replicate(2000, sharpe(sample(strat, replace = TRUE)))
quantile(boot_sharpe, c(0.025, 0.5, 0.975))
# 구간이 0을 포함하면 '우연일 가능성'을 배제하기 어렵다는 뜻
# (주의: 단순 재표집은 시계열의 자기상관을 무시함)


# 8. 위험 지표 비교: 정규분포 가정이 꼬리 위험을 얼마나 놓치나 ---------
c(VaR_과거시뮬 = var_hist(strat), VaR_정규가정 = var_norm(strat),
  CVaR_과거시뮬 = cvar_hist(strat))


# 9. 롤링 베타: 시장 민감도가 시간에 따라 변하는가 -------------------
roll_beta <- function(r, b, width = 252) {
  out <- rep(NA_real_, length(r))
  for (i in width:length(r)) {
    idx <- (i - width + 1):i
    out[i] <- cov(r[idx], b[idx]) / var(b[idx])
  }
  out
}
rb <- tibble(date = dates, beta_1y = roll_beta(strat, bench))
ggplot(rb, aes(date, beta_1y)) +
  geom_line(na.rm = TRUE) +
  geom_hline(yintercept = 1, linetype = "dashed") +
  labs(title = "1년 롤링 베타", x = NULL, y = "베타")


# 10. 다중요인 회귀: 알파가 정말 '알파'인가 ----------------------------
# 시장만으로 설명되지 않던 수익이 다른 요인(소형주, 모멘텀) 노출 때문일 수 있다.
rf <- rf_d
fit1 <- lm(I(strat - rf) ~ I(bench - rf))                         # 시장만
fit3 <- lm(I(strat - rf) ~ I(bench - rf) + smb + wml)             # 시장 + 소형주 + 모멘텀

pick <- function(fit, label) {
  s <- summary(fit)$coefficients
  tibble(model = label, term = rownames(s),
         estimate = s[, 1], t_value = s[, 3]) |>
    mutate(estimate = ifelse(term == "(Intercept)", estimate * ANN, estimate),   # 알파는 연율화
           term = ifelse(term == "(Intercept)", "alpha_ann", term))
}
bind_rows(pick(fit1, "시장 1요인"), pick(fit3, "3요인"))
# 해석: 3요인에서 알파의 t값이 작아지면, 초과수익의 일부는 요인 노출로 설명된다는 뜻
# (|t| < 2 정도면 통계적으로 0과 구분하기 어렵다고 본다)


# 11. 큰 낙폭 구간 표: 언제, 얼마나, 얼마나 오래 ---------------------
drawdown_episodes <- function(r, dates, top = 3) {
  dd    <- drawdown_series(r)
  under <- dd < 0
  grp   <- cumsum(c(TRUE, diff(under) != 0))          # 구간 번호 (수면 위/아래 번갈아)
  ep <- tibble(date = dates, dd = dd, under = under, grp = grp) |>
    filter(under) |>
    group_by(grp) |>
    summarise(start  = min(date),
              trough = date[which.min(dd)],
              depth  = min(dd),
              days   = n(),
              end    = max(date), .groups = "drop") |>
    arrange(depth) |>
    slice_head(n = top)
  ep |> mutate(recovered = end < max(dates)) |> select(-grp)
}
drawdown_episodes(strat, dates, top = 3)
# recovered = FALSE 이면 아직 직전 고점을 회복하지 못한 진행 중인 낙폭


# 12. 저장 -------------------------------------------------------------
dir.create("output", showWarnings = FALSE)
write.csv(tab, "output/performance_table.csv", row.names = FALSE, fileEncoding = "UTF-8")


# =====================================================================
# 연도별로 CAGR(해당 연도 수익률), 변동성, 샤프, MDD를 계산한 표를 만들고
# 샤프가 가장 낮은 해와 그 해의 MDD를 출력하기
# =====================================================================

by_year <- tibble(date = dates, r = strat) |>
  mutate(year = as.integer(format(date, "%Y"))) |>
  group_by(year) |>
  summarise(
    ret    = prod(1 + r) - 1,          # 해당 연도 실제 수익률 (연율화 아님)
    vol    = ann_vol(r),
    sharpe = sharpe(r),
    mdd    = max_dd(r),
    days   = n(),
    .groups = "drop"
  )
by_year

worst <- by_year |> slice_min(sharpe, n = 1)
cat(sprintf("샤프가 가장 낮은 해: %d (샤프 %.2f, MDD %.1f%%)\n",
            worst$year, worst$sharpe, worst$mdd * 100))
stopifnot(nrow(worst) == 1, all(by_year$mdd <= 0))