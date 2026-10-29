# =====================================================================
# 데이터 분석과 시각화 (dplyr 동사 + ggplot2)
# 가상 데이터 사용: 종목정보 60개, 주가 3종목 (실제 데이터는 1번 섹션만 교체)
# =====================================================================

# [한글 그래프 설정] 처음 한 번만:
#   RStudio > Tools > Global Options > General > Graphics > Backend 를 AGG 로 변경
#   (아래 pkgs 에 ragg 가 포함되어 자동 설치됨)
pkgs <- c("dplyr", "tidyr", "ggplot2", "plotly", "htmlwidgets", "ragg")
to_install <- pkgs[!pkgs %in% rownames(installed.packages())]
if (length(to_install) > 0) install.packages(to_install)

library(dplyr)
library(tidyr)
library(ggplot2)

# 운영체제별 한글 폰트 (그래프 한글 깨짐 방지). 안 되면 직접 폰트명을 지정
FONT <- switch(Sys.info()[["sysname"]],
               Windows = "Malgun Gothic",
               Darwin  = "AppleGothic",
               "NanumGothic")
theme_set(theme_minimal(base_family = FONT, base_size = 12))

dir.create("output", showWarnings = FALSE)


# 1. 연습용 가상 데이터 ------------------------------------------------
set.seed(11)
n <- 60

stocks <- tibble(
  ticker  = sprintf("S%02d", 1:n),
  sector  = sample(c("IT", "금융", "소재", "헬스케어", "소비재"), n, replace = TRUE),
  market  = sample(c("KOSPI", "KOSDAQ"), n, replace = TRUE, prob = c(0.6, 0.4)),
  cap_eok = round(exp(rnorm(n, 8, 1.2))),             # 시가총액(억원)
  pbr     = round(exp(rnorm(n, 0, 0.6)), 2),
  per     = round(exp(rnorm(n, 2.4, 0.6)), 1),
  roe     = round(rnorm(n, 0.08, 0.06), 3)
)

dates <- seq(as.Date("2023-01-02"), as.Date("2026-10-28"), by = "day")
dates <- dates[!format(dates, "%u") %in% c("6", "7")]
m <- length(dates)
path <- function(start, drift) start * cumprod(1 + rnorm(m, drift, 0.014))

prices <- tibble(
  date   = rep(dates, times = 3),
  ticker = rep(c("S01", "S02", "S03"), each = m),
  close  = c(path(100, 0.0004), path(60, 0.0002), path(30, 0.0006))
)


# 2. dplyr 동사 정리 ---------------------------------------------------
glimpse(stocks)                                   # 구조 한눈에

# 2-1. 열 다루기
stocks |> select(ticker, sector, pbr)             # 이름으로 선택
stocks |> select(ticker, where(is.numeric))       # 숫자 열만
stocks |> select(-market)                         # 제외
stocks |> rename(시총 = cap_eok) |> head(3)

stocks |>
  mutate(
    cap_trillion = cap_eok / 10000,               # 억원 -> 조원
    value_flag   = pbr < 1 & roe > 0.08           # 조건식으로 논리 열
  ) |> head(3)

stocks |> mutate(across(c(per, pbr), ~ round(.x, 1))) |> head(3)   # 여러 열 한 번에

# 2-2. 행 다루기
stocks |> filter(market == "KOSPI", pbr < 1)
stocks |> filter(sector %in% c("IT", "금융"), between(roe, 0.05, 0.15))
stocks |> filter(!is.na(per), per < 10)
stocks |> distinct(sector)
stocks |> arrange(desc(cap_eok)) |> slice_head(n = 5)
stocks |> slice_max(roe, n = 3)                   # roe 상위 3개

# 2-3. 요약
stocks |> summarise(n = n(), 평균PBR = mean(pbr), PER중앙값 = median(per))

stocks |>
  group_by(sector) |>
  summarise(n = n(), 중앙PBR = median(pbr), 평균ROE = mean(roe), .groups = "drop") |>
  arrange(desc(평균ROE))

stocks |> count(sector, market)                   # 빈도표

# 2-4. 순위와 분위수
stocks |>
  mutate(
    pbr_rank  = row_number(pbr),                  # 1 = 가장 낮은 PBR
    pbr_tile  = ntile(pbr, 5),                    # 5분위
    rank_in_sector = row_number(desc(roe))        # (전체 기준) 아래에서 그룹별로 다시
  ) |> head(3)

stocks |>
  group_by(sector) |>
  mutate(roe_rank_in_sector = min_rank(desc(roe))) |>   # 섹터 안에서의 순위
  ungroup() |>
  filter(roe_rank_in_sector == 1)                       # 섹터별 ROE 1위

# 2-5. 결합
sector_info <- tibble(sector = c("IT", "금융", "소재", "헬스케어", "소비재"),
                      cyc = c("성장", "경기민감", "경기민감", "방어", "방어"))
stocks <- stocks |> left_join(sector_info, by = "sector")


# 3. ggplot2 구조 ------------------------------------------------------
# 그래프 = 데이터 + 매핑(aes) + 도형(geom) + 필요하면 통계/축/테마를 + 로 쌓기
g_base <- ggplot(stocks, aes(x = pbr, y = roe))   # 아직 아무것도 안 그림
g_base + geom_point()                             # 도형을 얹어야 그려짐

# 색, 크기, 모양에 변수를 매핑
ggplot(stocks, aes(pbr, roe, color = sector, size = cap_eok)) +
  geom_point(alpha = 0.7)


# 4. 분할(facet) -------------------------------------------------------
ggplot(stocks, aes(pbr, roe)) +
  geom_point() +
  facet_wrap(~ market)                            # 시장별로 패널 나누기

ggplot(stocks, aes(pbr, roe)) +
  geom_point() +
  facet_grid(cyc ~ market)                        # 행/열 두 변수로 분할


# 5. 통계 레이어 -------------------------------------------------------
ggplot(stocks, aes(pbr, roe)) +
  geom_point(alpha = 0.6) +
  geom_smooth(method = "lm", se = TRUE)           # 추세선 + 신뢰구간


# 6. 좌표와 축 ---------------------------------------------------------
ggplot(stocks, aes(cap_eok, pbr)) +
  geom_point() +
  scale_x_log10(labels = scales::comma)           # 로그 축 (분포가 한쪽으로 치우칠 때)

ggplot(stocks, aes(pbr, roe)) +
  geom_point() +
  coord_cartesian(xlim = c(0, 3), ylim = c(-0.1, 0.25))   # 데이터는 두고 보이는 구간만


# 7. 테마와 라벨 -------------------------------------------------------
ggplot(stocks, aes(pbr, roe, color = market)) +
  geom_point() +
  labs(title = "PBR과 ROE", subtitle = "가상 데이터 60종목",
       x = "PBR(배)", y = "ROE", color = "시장") +
  theme(legend.position = "bottom")


# 8. 종목정보 시각화 ---------------------------------------------------
# 8-1. 산점도: 저PBR + 고ROE 구간 강조
p_scatter <- ggplot(stocks, aes(pbr, roe)) +
  geom_point(aes(color = pbr < 1 & roe > 0.08), alpha = 0.8) +
  geom_vline(xintercept = 1, linetype = "dashed") +
  geom_hline(yintercept = 0.08, linetype = "dashed") +
  scale_color_manual(values = c(`TRUE` = "firebrick", `FALSE` = "grey60"),
                     labels = c(`TRUE` = "후보", `FALSE` = "그 외")) +
  labs(title = "저PBR·고ROE 후보", x = "PBR", y = "ROE", color = NULL)
p_scatter

# 8-2. 히스토그램
ggplot(stocks, aes(per)) +
  geom_histogram(binwidth = 2, boundary = 0, fill = "steelblue", color = "white") +
  labs(title = "PER 분포", x = "PER(배)", y = "종목 수")

# 8-3. 박스플롯: 섹터별 분포를 비교
ggplot(stocks, aes(reorder(sector, roe, FUN = median), roe)) +
  geom_boxplot(fill = "grey90") +
  coord_flip() +
  labs(title = "섹터별 ROE 분포", x = NULL, y = "ROE")

# 8-4. dplyr로 가공한 결과를 바로 ggplot으로
stocks |>
  group_by(sector) |>
  summarise(중앙PBR = median(pbr), n = n(), .groups = "drop") |>
  ggplot(aes(reorder(sector, 중앙PBR), 중앙PBR)) +
  geom_col(fill = "steelblue") +
  geom_text(aes(label = paste0("n=", n)), hjust = -0.2) +
  coord_flip() +
  expand_limits(y = 2) +
  labs(title = "섹터별 PBR 중앙값", x = NULL, y = "PBR")

# 8-5. 막대 그래프 (빈도): 값 계산 없이 개수를 센다
ggplot(stocks, aes(sector, fill = market)) +
  geom_bar(position = "dodge") +
  labs(title = "섹터별 종목 수", x = NULL, y = "종목 수", fill = "시장")


# 9. 주가와 수익률 시각화 ----------------------------------------------
# 9-1. 선 그래프: 시작점을 100으로 맞춰 비교
rebased <- prices |>
  group_by(ticker) |>
  mutate(index100 = close / first(close) * 100) |>
  ungroup()

p_line <- ggplot(rebased, aes(date, index100, color = ticker)) +
  geom_line() +
  scale_x_date(date_breaks = "6 months", date_labels = "%y/%m") +
  labs(title = "기준일=100 가격 추이", x = NULL, y = "지수", color = "종목")
p_line

# 9-2. 인터랙티브 그래프 (마우스를 올리면 값 표시)
p_inter <- plotly::ggplotly(p_line)
p_inter
# htmlwidgets::saveWidget(p_inter, "output/price_interactive.html", selfcontained = TRUE)

# 9-3. 연도별 수익률
yearly <- prices |>
  arrange(ticker, date) |>
  group_by(ticker) |>
  mutate(ret = close / lag(close) - 1) |>
  ungroup() |>
  mutate(year = as.integer(format(date, "%Y"))) |>
  group_by(ticker, year) |>
  summarise(ret = prod(1 + ret, na.rm = TRUE) - 1, .groups = "drop")

p_year <- ggplot(yearly, aes(factor(year), ret, fill = ret > 0)) +
  geom_col(show.legend = FALSE) +
  geom_text(aes(label = scales::percent(ret, accuracy = 0.1),
                vjust = ifelse(ret >= 0, -0.3, 1.2)), size = 3) +
  scale_fill_manual(values = c(`TRUE` = "red", `FALSE` = "blue")) +
  scale_y_continuous(labels = scales::percent) +
  facet_wrap(~ ticker) +
  labs(title = "연도별 수익률 (마지막 해는 진행 중)", x = NULL, y = NULL)
p_year

# 9-4. 파일로 저장
ggsave("output/pbr_roe_scatter.png", p_scatter, width = 7, height = 5, dpi = 150)
ggsave("output/yearly_return.png",   p_year,    width = 9, height = 4, dpi = 150)


# =====================================================================
# 섹터별 PBR 중앙값을 막대그래프로 그리되
#  (1) 시장(KOSPI/KOSDAQ)별로 패널을 나누고
#  (2) 막대는 중앙값이 낮은 순서로 정렬하고
#  (3) 막대 끝에 종목 수를 표시한 뒤 PNG로 저장하기
# =====================================================================

hw <- stocks |>
  group_by(market, sector) |>
  summarise(중앙PBR = median(pbr), n = n(), .groups = "drop")

p_hw <- ggplot(hw, aes(reorder(sector, 중앙PBR), 중앙PBR)) +
  geom_col(fill = "steelblue") +
  geom_text(aes(label = paste0("n=", n)), hjust = -0.15, size = 3) +
  coord_flip() +
  expand_limits(y = max(hw$중앙PBR) * 1.2) +
  facet_wrap(~ market) +
  labs(title = "시장·섹터별 PBR 중앙값", x = NULL, y = "PBR")

p_hw
ggsave("output/hw10_sector_pbr.png", p_hw, width = 9, height = 4, dpi = 150)

# 참고: reorder()는 패널 전체 기준으로 순서를 정함.
# 패널마다 순서를 따로 정하려면 tidytext::reorder_within 이 필요하지만
# 여기서는 추가 패키지 없이 전체 기준 정렬로 단순화함