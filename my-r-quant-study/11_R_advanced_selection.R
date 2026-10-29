# =====================================================================
#  종목 선정 심화: 이상치, 섹터 중립, 마법공식, 멀티팩터
# 가상 데이터 사용 (실제 데이터는 1번 섹션의 d만 교체)
# =====================================================================

library(dplyr)
library(ggplot2)
FONT <- switch(Sys.info()[["sysname"]], Windows = "Malgun Gothic", Darwin = "AppleGothic", "NanumGothic")
theme_set(theme_minimal(base_family = FONT, base_size = 12))
set.seed(33)


# 1. 연습용 가상 데이터 ------------------------------------------------
n <- 120

d <- tibble(
  ticker  = sprintf("S%03d", 1:n),
  sector  = sample(c("IT", "금융", "소재", "헬스케어", "소비재", "산업재"),
                   n, replace = TRUE, prob = c(.25, .10, .15, .15, .15, .20)),
  mktcap  = exp(rnorm(n, 9, 1)),
  ebit    = mktcap * rnorm(n, 0.08, 0.06),
  netdebt = mktcap * rnorm(n, 0.10, 0.30),
  nwc     = mktcap * runif(n, 0.10, 0.50),   # 순운전자본
  nfa     = mktcap * runif(n, 0.20, 0.90),   # 순고정자산
  equity  = mktcap * exp(rnorm(n, 0.1, 0.5)),
  ni      = ebit * runif(n, 0.5, 0.9),
  gp      = mktcap * runif(n, 0.10, 0.50),
  assets  = equity * runif(n, 1.4, 3),
  mom     = rnorm(n, 0.08, 0.30),
  vol     = exp(rnorm(n, log(0.3), 0.3))
)

# 배수(PER, PBR) 대신 '수익률 형태'(수익/가격)를 쓰는 이유:
# 적자일 때 배수는 음수/무한대가 되어 순위가 뒤틀리지만, 수익률 형태는 연속적으로 비교 가능
d <- d |>
  mutate(
    ev     = mktcap + netdebt,
    ey     = ebit / ev,                 # 이익수익률 (EBIT / EV)
    roc    = ebit / (nwc + nfa),        # 투하자본수익률
    bp     = equity / mktcap,           # 장부가치/시가 (= 1 / PBR)
    ep     = ni / mktcap,               # 이익/시가 (= 1 / PER)
    roe    = ni / equity,
    gpa    = gp / assets                # 매출총이익 / 자산
  )

# 현실에서 흔한 이상치를 일부러 주입
d$roe[c(4, 50)] <- c(6.0, -5.0)
d$ep[9]         <- 3.0


# 2. 공통 도구 ---------------------------------------------------------
# 2-1. 트림: 양끝 백분위 밖의 값을 NA로 (표본에서 제외하는 효과)
trim_vec <- function(x, p = c(0.01, 0.99)) {
  q <- quantile(x, p, na.rm = TRUE)
  x[!is.na(x) & (x < q[1] | x > q[2])] <- NA
  x
}

# 2-2. 윈저라이징: 양끝 값을 경계값으로 대체 (표본은 유지)
winsor <- function(x, p = c(0.01, 0.99)) {
  q <- quantile(x, p, na.rm = TRUE)
  pmin(pmax(x, q[1]), q[2])
}

# 2-3. z-점수, 그리고 그룹(섹터) 안에서의 z-점수
zscore    <- function(x) (x - mean(x, na.rm = TRUE)) / sd(x, na.rm = TRUE)
zscore_by <- function(x, g) ave(x, g, FUN = zscore)

# 2-4. 두 종목 집합의 겹침 비율
overlap <- function(a, b) length(intersect(a, b)) / length(a)


# 3. 이상치 처리 효과 보기 ---------------------------------------------
roe_cmp <- tibble(
  raw      = d$roe,
  trimmed  = trim_vec(d$roe),
  winsored = winsor(d$roe)
)
sapply(roe_cmp, function(x) c(mean = mean(x, na.rm = TRUE),
                              sd   = sd(x, na.rm = TRUE),
                              n    = sum(!is.na(x))))

roe_cmp |>
  tidyr::pivot_longer(everything(), names_to = "method", values_to = "roe") |>
  ggplot(aes(method, roe)) +
  geom_boxplot(fill = "grey90") +
  labs(title = "ROE 이상치 처리 비교", x = NULL, y = "ROE")

# 선택 기준
# - 트림: 이상치를 '오류'로 판단할 때 (표본이 줄어듦, 해당 종목은 점수에서 제외)
# - 윈저: 이상치도 '극단적이지만 진짜'일 때 (순위는 유지, 영향만 제한)


# 4. 섹터 중립 -----------------------------------------------------------
# 4-1. 전체에서 상위 20%만 뽑으면 특정 섹터에 쏠릴 수 있음
global_top <- d |> filter(percent_rank(desc(ey)) <= 0.2) |> mutate(method = "전체 기준")

# 4-2. 섹터 안에서 상위 20%씩 뽑으면 섹터 비중이 유니버스와 비슷해짐
neutral_top <- d |>
  group_by(sector) |>
  filter(percent_rank(desc(ey)) <= 0.2) |>
  ungroup() |>
  mutate(method = "섹터 중립")

bind_rows(global_top, neutral_top) |>
  count(method, sector) |>
  ggplot(aes(sector, n, fill = method)) +
  geom_col(position = "dodge") +
  labs(title = "선정 종목의 섹터 분포", x = NULL, y = "종목 수", fill = NULL)

# 4-3. 점수 자체를 섹터 안에서 표준화하는 방법 (아래 멀티팩터에서 사용)
d |> mutate(ey_z_sector = zscore_by(ey, sector)) |>
  group_by(sector) |>
  summarise(mean_z = mean(ey_z_sector), .groups = "drop")      # 섹터마다 평균 0


# 5. 마법공식 (이익수익률 순위 + 자본수익률 순위) ---------------------
# 아이디어: 싸게(ey 높음) + 장사를 잘하는(roc 높음) 회사를 순위 합으로 선택
# 금융업은 EBIT, EV 개념이 맞지 않아 제외하는 것이 일반적
mf_universe <- d |> filter(sector != "금융", ebit > 0, !is.na(ey), !is.na(roc))

mf <- mf_universe |>
  mutate(
    r_ey    = min_rank(desc(ey)),
    r_roc   = min_rank(desc(roc)),
    mf_rank = r_ey + r_roc
  ) |>
  arrange(mf_rank) |>
  slice_head(n = 20)

mf |> select(ticker, sector, ey, roc, r_ey, r_roc, mf_rank) |> head(8)

# 두 순위가 서로 독립적인 정보를 주는지 확인
cor(mf_universe$ey, mf_universe$roc, method = "spearman")


# 6. 멀티팩터 포트폴리오 ------------------------------------------------
# 6-1. 팩터 점수: 이상치 윈저 -> 섹터 안 z-점수 -> 팩터별 평균
make_factor_scores <- function(df) {
  df |>
    mutate(across(c(ey, bp, ep, roe, gpa, mom), winsor),
           neg_vol = -vol) |>
    mutate(
      z_value   = (zscore_by(bp, sector) + zscore_by(ep, sector) + zscore_by(ey, sector)) / 3,
      z_quality = (zscore_by(roe, sector) + zscore_by(gpa, sector)) / 2,
      z_mom     = zscore_by(mom, sector),
      z_lowvol  = zscore_by(neg_vol, sector)
    )
}

# 6-2. 가중치로 합산해 상위 n개를 동일가중으로 구성
build_portfolio <- function(fac, w, n_pick = 20) {
  stopifnot(abs(sum(w) - 1) < 1e-9,
            all(c("value", "quality", "mom", "lowvol") %in% names(w)))
  fac |>
    mutate(score = w["value"]   * z_value +
             w["quality"] * z_quality +
             w["mom"]     * z_mom +
             w["lowvol"]  * z_lowvol) |>
    arrange(desc(score)) |>
    slice_head(n = n_pick) |>
    mutate(weight = 1 / n_pick)
}

fac <- make_factor_scores(d)

w_base <- c(value = 0.30, quality = 0.30, mom = 0.20, lowvol = 0.20)
port   <- build_portfolio(fac, w_base, n_pick = 20)

port |> select(ticker, sector, score, weight) |> head(8)

# 6-3. 포트폴리오 점검: 섹터 구성이 유니버스와 크게 다르지 않은지
sector_check <- bind_rows(
  d    |> count(sector) |> mutate(share = n / sum(n), group = "유니버스"),
  port |> count(sector) |> mutate(share = n / sum(n), group = "포트폴리오")
)
ggplot(sector_check, aes(sector, share, fill = group)) +
  geom_col(position = "dodge") +
  scale_y_continuous(labels = scales::percent) +
  labs(title = "섹터 비중 비교", x = NULL, y = NULL, fill = NULL)

# 6-4. 결합 방식에 따라 결과가 얼마나 달라지나: 점수합 vs 순위합
rank_port <- fac |>
  mutate(rscore = percent_rank(z_value) + percent_rank(z_quality) +
           percent_rank(z_mom) + percent_rank(z_lowvol)) |>
  arrange(desc(rscore)) |>
  slice_head(n = 20)

overlap(port$ticker, rank_port$ticker)      # 두 방식이 고른 종목의 겹침 비율

dir.create("data", showWarnings = FALSE)
saveRDS(port, "data/multifactor_portfolio.rds")


# =====================================================================
# 밸류 비중을 키운 가중치(value 0.6, quality 0.2, mom 0.1, lowvol 0.1)로 포트폴리오를
# 다시 만들고, 기본 포트폴리오와의 (1) 종목 겹침 비율 (2) 섹터별 종목 수 차이를
# 한 표로 비교하기
# =====================================================================

w_value <- c(value = 0.60, quality = 0.20, mom = 0.10, lowvol = 0.10)
port_v  <- build_portfolio(fac, w_value, n_pick = 20)

cat("겹침 비율:", overlap(port$ticker, port_v$ticker), "\n")

sector_diff <- full_join(
  port   |> count(sector, name = "base"),
  port_v |> count(sector, name = "value_heavy"),
  by = "sector"
) |>
  mutate(across(c(base, value_heavy), ~ tidyr::replace_na(.x, 0L)),
         diff = value_heavy - base) |>
  arrange(desc(abs(diff)))

sector_diff
stopifnot(nrow(port_v) == 20, abs(sum(port_v$weight) - 1) < 1e-9)