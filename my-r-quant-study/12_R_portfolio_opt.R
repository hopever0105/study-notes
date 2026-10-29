# =====================================================================
# 포트폴리오 구성: 최소분산, 최대분산효과, 제약조건
# 가상 데이터 사용 (실제 데이터는 1번 섹션의 rets만 교체: 일자 x 자산 일간수익률)
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
set.seed(5)


# 1. 연습용 가상 데이터 ------------------------------------------------
n_asset <- 10
N       <- 756                                   # 약 3년치 거래일
asset   <- sprintf("A%02d", 1:n_asset)
sector  <- c(rep("IT", 3), rep("금융", 2), rep("소재", 2), rep("헬스케어", 3))
names(sector) <- asset

mkt_f  <- rnorm(N, 0.0003, 0.009)                # 시장 공통 요인
sec_f  <- sapply(unique(sector), function(s) rnorm(N, 0, 0.006))   # 섹터 요인
beta   <- runif(n_asset, 0.5, 1.4)
idio   <- runif(n_asset, 0.008, 0.02)

rets <- sapply(seq_len(n_asset), function(i)
  beta[i] * mkt_f + sec_f[, sector[i]] + rnorm(N, 0.0002, idio[i]))
colnames(rets) <- asset

S  <- cov(rets) * 252                            # 연율화 공분산
mu <- colMeans(rets) * 252                       # 연율화 기대수익(표본평균)


# 2. 공통 도구 ---------------------------------------------------------
# 2-1. 공분산 축소(shrinkage): 표본 공분산은 자산이 많고 기간이 짧을수록 불안정
#      대각 성분만 남긴 행렬 쪽으로 lambda 비율만큼 당겨 안정화
shrink_cov <- function(S, lambda = 0.2) (1 - lambda) * S + lambda * diag(diag(S))

# 2-2. 포트폴리오 지표
port_stats <- function(w, Sigma, mu = NULL) {
  vol <- sqrt(drop(t(w) %*% Sigma %*% w))
  c(vol = vol,
    ret = if (is.null(mu)) NA_real_ else sum(w * mu),
    DR  = sum(w * sqrt(diag(Sigma))) / vol)        # 분산효과비율(DR)
}

# 2-3. 위험 기여도: 각 자산이 포트폴리오 변동성에 기여하는 비율 (합 = 1)
risk_contrib <- function(w, Sigma) {
  m <- drop(Sigma %*% w)
  w * m / drop(t(w) %*% Sigma %*% w)
}


# 3. 최소분산 포트폴리오 ----------------------------------------------
# solve.QP는 다음 형태를 푼다:  min  1/2 w'Dw - d'w   s.t.  A'w >= b  (앞 meq개는 등식)
# 최소분산: D = 2*Sigma, d = 0
# 제약: (1) 합 = 1  (2) w >= lower  (3) w <= upper  (4) 섹터 합 <= cap (선택) (5) 목표수익 (선택)
min_var <- function(Sigma, lower = 0, upper = 1,
                    groups = NULL, group_cap = NULL,
                    mu = NULL, target = NULL) {
  n     <- ncol(Sigma)
  lower <- rep_len(lower, n)
  upper <- rep_len(upper, n)
  
  A <- cbind(rep(1, n), diag(n), -diag(n))        # 열 하나가 제약 하나
  b <- c(1, lower, -upper)
  
  if (!is.null(groups) && !is.null(group_cap)) {
    for (g in names(group_cap)) {
      ind <- as.numeric(groups == g)
      A <- cbind(A, -ind)                          # -sum(w_g) >= -cap
      b <- c(b, -group_cap[[g]])
    }
  }
  if (!is.null(target)) {
    A <- cbind(A, mu)                              # mu'w >= target
    b <- c(b, target)
  }
  
  D   <- 2 * Sigma + diag(1e-8, n)                 # 양의 정부호 보장용 미세 보정
  sol <- solve.QP(Dmat = D, dvec = rep(0, n), Amat = A, bvec = b, meq = 1)
  w   <- sol$solution
  names(w) <- colnames(Sigma)
  w
}

w_eq <- setNames(rep(1 / n_asset, n_asset), asset)           # 비교 기준: 동일가중
w_mv <- min_var(S)                                           # 롱온리 최소분산
round(w_mv, 3)
stopifnot(abs(sum(w_mv) - 1) < 1e-8, all(w_mv > -1e-8))


# 4. 제약조건 추가 -----------------------------------------------------
# 4-1. 자산별 비중 5% ~ 20%
w_mv_box <- min_var(S, lower = 0.05, upper = 0.20)

# 4-2. 자산별로 다른 상하한 (예: A01은 최대 5%, A10은 최소 10%)
lo <- rep(0, n_asset); up <- rep(0.25, n_asset)
up[1]  <- 0.05
lo[10] <- 0.10
w_mv_ind <- min_var(S, lower = lo, upper = up)

# 4-3. 섹터 한도: IT 30% 이하, 금융 25% 이하
w_mv_sec <- min_var(S, lower = 0, upper = 0.30,
                    groups = sector,
                    group_cap = list(IT = 0.30, 금융 = 0.25))
tapply(w_mv_sec, sector, sum)


# 5. 최대분산효과 포트폴리오 ------------------------------------------
# 분산효과비율 DR(w) = (w'σ) / sqrt(w'Σw), σ = 자산별 변동성
# y_i = w_i*σ_i / (w'σ) 로 바꾸면 DR = 1 / sqrt(y' C y)  (C = 상관행렬)
# => DR 최대화 = 상관행렬 기준 최소분산(합 = 1, y >= 0), 이후 w ∝ y / σ
max_div <- function(Sigma) {
  n   <- ncol(Sigma)
  sig <- sqrt(diag(Sigma))
  C   <- cov2cor(Sigma)
  
  A <- cbind(rep(1, n), diag(n))
  b <- c(1, rep(0, n))
  y <- solve.QP(2 * C + diag(1e-8, n), rep(0, n), A, b, meq = 1)$solution
  
  w <- y / sig
  w <- w / sum(w)
  names(w) <- colnames(Sigma)
  w
}
w_md <- max_div(S)
round(w_md, 3)

# 검산: 무작위 롱온리 포트폴리오 2,000개보다 DR이 높아야 함
rand_w  <- replicate(2000, { x <- rexp(n_asset); x / sum(x) })
rand_dr <- apply(rand_w, 2, function(w) port_stats(w, S)["DR"])
stopifnot(port_stats(w_md, S)["DR"] >= max(rand_dr) - 1e-6)


# 6. 방식별 비교 -------------------------------------------------------
cands <- list(
  동일가중       = w_eq,
  최소분산       = w_mv,
  최소분산_박스  = w_mv_box,
  최소분산_섹터  = w_mv_sec,
  최대분산효과   = w_md
)

cmp <- bind_rows(lapply(names(cands), function(nm) {
  s <- port_stats(cands[[nm]], S, mu)
  tibble(portfolio = nm, vol = s["vol"], ret = s["ret"], DR = s["DR"],
         max_w = max(cands[[nm]]),
         n_active = sum(cands[[nm]] > 0.01))
}))
cmp

# 비중 막대 비교
bind_rows(lapply(names(cands), function(nm)
  tibble(portfolio = nm, asset = names(cands[[nm]]), w = cands[[nm]]))) |>
  ggplot(aes(asset, w, fill = portfolio)) +
  geom_col(position = "dodge") +
  scale_y_continuous(labels = scales::percent) +
  labs(title = "방식별 투자비중", x = NULL, y = NULL, fill = NULL)

# 위험 기여도: 동일가중 vs 최소분산
tibble(asset = asset,
       동일가중 = risk_contrib(w_eq, S),
       최소분산 = risk_contrib(w_mv, S)) |>
  pivot_longer(-asset, names_to = "portfolio", values_to = "rc") |>
  ggplot(aes(asset, rc, fill = portfolio)) +
  geom_col(position = "dodge") +
  scale_y_continuous(labels = scales::percent) +
  labs(title = "위험 기여도", x = NULL, y = NULL, fill = NULL)


# 7. 효율적 투자선 (롱온리) --------------------------------------------
r_lo <- sum(w_mv * mu)
targets <- seq(r_lo, max(mu) * 0.98, length.out = 15)

frontier <- bind_rows(lapply(targets, function(tg) {
  w <- tryCatch(min_var(S, mu = mu, target = tg), error = function(e) NULL)
  if (is.null(w)) return(NULL)
  tibble(target = tg, vol = port_stats(w, S)["vol"], ret = sum(w * mu))
}))

ggplot(frontier, aes(vol, ret)) +
  geom_line() + geom_point() +
  geom_point(data = cmp, aes(vol, ret, color = portfolio), size = 3) +
  scale_x_continuous(labels = scales::percent) +
  scale_y_continuous(labels = scales::percent) +
  labs(title = "효율적 투자선과 각 포트폴리오", x = "변동성(연)", y = "기대수익(연)", color = NULL)

# 주의: 기대수익(mu)을 표본평균으로 쓰면 매우 불안정함.
#       최소분산/최대분산효과가 수익률 추정이 필요 없다는 점이 실무에서 선호되는 이유


dir.create("data", showWarnings = FALSE)
saveRDS(cands, "data/optimized_weights.rds")


# =====================================================================

# 롤링 백테스트로 동일가중과 최소분산(자산별 최대 30%)의 '표본 외' 변동성 비교
#  - 252일 데이터로 공분산 추정(shrinkage 0.2)
#  - 21거래일마다 리밸런싱, 다음 21일 동안 그 비중으로 보유(일일 고정비중 근사)
#  - 거래비용은 무시
# =====================================================================

est_win <- 252
step    <- 21
rebal   <- seq(est_win, N - step, by = step)

r_eq <- c(); r_mv <- c()
for (i in rebal) {
  est  <- rets[(i - est_win + 1):i, ]
  S_i  <- shrink_cov(cov(est) * 252, lambda = 0.2)
  w_i  <- min_var(S_i, lower = 0, upper = 0.30)
  
  idx  <- (i + 1):(i + step)
  r_eq <- c(r_eq, rets[idx, ] %*% rep(1 / n_asset, n_asset))
  r_mv <- c(r_mv, rets[idx, ] %*% w_i)
}
stopifnot(length(r_eq) == length(r_mv))

bt <- tibble(
  portfolio = c("동일가중", "최소분산(30%캡)"),
  ann_vol   = c(sd(r_eq), sd(r_mv)) * sqrt(252),
  ann_ret   = c(mean(r_eq), mean(r_mv)) * 252
) |>
  mutate(ret_per_vol = ann_ret / ann_vol)
bt
# 최소분산이 동일가중보다 표본 외 변동성이 낮은지(보통은 낮음) 확인

# 8. 위험균형(리스크 패리티)과 위험예산 ---------------------------------
# 8-1. 60/40 직관: 자금은 60/40이어도 위험은 거의 주식이 차지
S_6040 <- matrix(c(0.18^2,           0.1 * 0.18 * 0.06,
                   0.1 * 0.18 * 0.06, 0.06^2), 2, 2,
                 dimnames = list(c("주식", "채권"), c("주식", "채권")))
w_6040 <- c(주식 = 0.6, 채권 = 0.4)
round(risk_contrib(w_6040, S_6040), 3)             # 주식 0.935, 채권 0.065

# 8-2. 목표 위험예산(budget)에 맞는 비중 찾기
#      budget = 각 자산이 맡을 위험 비중 (기본: 모두 동일 = 위험균형)
#      softmax로 비중을 만들어 롱온리, 합 = 1을 자동으로 만족시킨다
risk_budget <- function(Sigma, budget = NULL) {
  n <- ncol(Sigma)
  if (is.null(budget)) budget <- rep(1 / n, n)
  stopifnot(abs(sum(budget) - 1) < 1e-9)
  
  to_w <- function(x) { w <- exp(x - max(x)); w / sum(w) }
  obj  <- function(x) sum((risk_contrib(to_w(x), Sigma) - budget)^2) * 1e4
  
  x0  <- -log(sqrt(diag(Sigma)))                    # 역변동성에서 출발
  fit <- optim(x0, obj, method = "BFGS", control = list(reltol = 1e-14, maxit = 5000))
  w <- to_w(fit$par); names(w) <- colnames(Sigma)
  w
}

w_rp <- risk_budget(S)
round(w_rp, 3)
round(risk_contrib(w_rp, S), 3)                     # 모두 약 0.1이어야 함
stopifnot(max(abs(risk_contrib(w_rp, S) - 1 / n_asset)) < 5e-3)

# 8-3. 위험예산을 다르게: A01은 위험의 20%, 나머지는 균등
budget <- rep(0.8 / (n_asset - 1), n_asset); budget[1] <- 0.20
w_rb <- risk_budget(S, budget)
round(risk_contrib(w_rb, S), 3)

# 8-4. 비교표에 추가
for (nm in c("위험균형", "위험예산")) cands[[nm]] <- if (nm == "위험균형") w_rp else w_rb
bind_rows(lapply(names(cands), function(nm) {
  s <- port_stats(cands[[nm]], S, mu)
  tibble(portfolio = nm, vol = s["vol"], DR = s["DR"], max_w = max(cands[[nm]]),
         max_risk_share = max(risk_contrib(cands[[nm]], S)))
}))


# 9. 인덱스 추종 포트폴리오 --------------------------------------------
# 목표: 벤치마크(시총가중)를 적은 종목으로 최대한 비슷하게 따라가기
#       min (w - w_b)' Σ (w - w_b)   s.t.  sum(w) = 1, w >= 0, (선택) 종목 수 k개로 제한
caps <- exp(rnorm(n_asset, 0, 0.8))
w_b  <- setNames(caps / sum(caps), asset)           # 가상의 시총가중 벤치마크

tracking_portfolio <- function(Sigma, w_b, k = NULL) {
  n    <- length(w_b)
  keep <- if (is.null(k)) seq_len(n) else order(w_b, decreasing = TRUE)[1:k]
  m    <- length(keep)
  
  A <- cbind(rep(1, m), diag(m)); b <- c(1, rep(0, m))
  D <- 2 * Sigma[keep, keep] + diag(1e-10, m)
  d <- 2 * drop(Sigma[keep, ] %*% w_b)              # 1/2 w'Dw - d'w 형태로 맞춤
  
  sol <- solve.QP(D, d, A, b, meq = 1)$solution
  w <- setNames(rep(0, n), names(w_b)); w[keep] <- sol
  w
}

te_fn        <- function(w, w_b, Sigma) sqrt(drop(t(w - w_b) %*% Sigma %*% (w - w_b)))
active_share <- function(w, w_b) 0.5 * sum(abs(w - w_b))

w_t_all <- tracking_portfolio(S, w_b)               # 제한 없음 -> 벤치마크와 같아야 함
stopifnot(max(abs(w_t_all - w_b)) < 1e-4)

track_tbl <- bind_rows(lapply(c(10, 7, 5, 3), function(k) {
  w <- tracking_portfolio(S, w_b, k)
  tibble(n_hold = k, tracking_error = te_fn(w, w_b, S), active_share = active_share(w, w_b))
}))
track_tbl            # 종목 수를 줄일수록 추적오차가 커지는 정도를 확인