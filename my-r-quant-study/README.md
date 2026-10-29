# my-r-quant-study

R로 퀀트 투자 과정을 처음부터 끝까지 따라가며 정리한 실습 코드입니다.
**R 기초 → 데이터 수집(크롤링·API) → 정리·시각화 → 팩터 → 종목 선정 → 포트폴리오 최적화 → 백테스트 → 성과·위험 평가** 순서로 14개 파일에 쌓았습니다.

## 구성

### 1부. R 기초와 데이터 수집

| # | 파일 | 내용 |
|---|---|---|
| 01 | [01_R_Basic.R](01_R_Basic.R) | 자료형·벡터·리스트·데이터프레임, 조건문·반복문·함수·파이프, 날짜·문자열·결측치, tidyr·dplyr로 종목별 수익률 표 만들기 → 엑셀 저장 |
| 02 | [02_R_HTML_plarsing.R](02_R_HTML_plarsing.R) | HTTP GET·POST와 헤더, HTML 파싱과 CSS 선택자, 문자열→숫자 정리, 인코딩, 크롤링 매너 |
| 03 | [03_R_scraping.R](03_R_scraping.R) | 한 페이지 성공 → 함수화 → 여러 페이지 수집, 표 한 번에 읽기, 후처리·저장, 자주 나는 문제 |
| 04 | [04_R_Basic_API_Datacollection_.R](04_R_Basic_API_Datacollection_.R) | REST API 호출과 중첩 JSON 변환, API 키 관리(`.Renviron`), 재시도 함수, 반복 수집·페이지네이션 |
| 05 | [05_R_prices_returns.R](05_R_prices_returns.R) | 수정주가 받기(quantmod), xts 기본, 수익률·누적수익률·변동성, 여러 종목 합치기와 성과 요약 |
| 06 | [06_R_kr_market_data.R](06_R_kr_market_data.R) | 국내 시가총액 순 종목 목록과 업종 목록 수집 (robots.txt 점검, 구조 점검 함수, 종목코드 앞자리 0 보존) |
| 07 | [07_R_prices_financials.R](07_R_prices_financials.R) | 종목별 수정종가 캐시 → 한 표(xts)로, OpenDART 고유번호·공시 검색·재무제표 수집, 가치지표 계산 |

### 2부. 정리·분석·전략

| # | 파일 | 내용 |
|---|---|---|
| 08 | [08_R_cleaning.R](08_R_cleaning.R) | 가격·재무제표·가치지표 정리 후 하나의 마스터 표로 결합 |
| 09 | [09_R_analysis_viz.R](09_R_analysis_viz.R) | dplyr 동사, ggplot2 구조·facet·통계 레이어·축·테마, 종목정보와 주가·수익률 시각화 |
| 10 | [10_R_factors.R](10_R_factors.R) | 베타·저변동성·모멘텀·밸류·퀄리티(F-Score) 팩터, 순위 점수로 합치기 |
| 11 | [11_R_advanced_selection.R](11_R_advanced_selection.R) | 이상치 처리, 섹터 중립, 마법공식(이익수익률+자본수익률), 멀티팩터 포트폴리오 |
| 12 | [12_R_portfolio_opt.R](12_R_portfolio_opt.R) | 공분산 축소추정, 최소분산·최대분산효과, 제약조건, 효율적 투자선, 위험균형(리스크 패리티)·위험예산, 인덱스 추종 |
| 13 | [13_R_backtes.R](13_R_backtes.R) | 리밸런싱 날짜 → 신호 → 백테스트 엔진, 거래비용 민감도, 미래 정보·과최적화 함정, 표본 내/외 분리 |
| 14 | [14_R_performance_risk.R](14_R_performance_risk.R) | 성과표, 낙폭·월별 히트맵, 롤링 지표·롤링 베타, 샤프지수 부트스트랩, 정규분포 가정과 꼬리 위험 비교, 다중요인 회귀로 알파 검증, 큰 낙폭 구간 표 |

## 실행 방법

1. R 4.6 이상, RStudio 설치
2. `my-r-quant-study.Rproj` 열기 (작업 폴더가 자동으로 잡힘)
3. 07장을 돌릴 때만 `.Renviron.example`을 `.Renviron`으로 복사해 `DART_API_KEY` 입력 → RStudio 재시작
4. 파일을 열고 `Ctrl + Shift + Enter` (전체) 또는 `Ctrl + Enter` (한 줄)

08장 이후는 연습용 가상 데이터를 만들어 쓰므로 인터넷 연결 없이 바로 실행됩니다.

## 데이터 출처

| 장 | 출처 |
|---|---|
| 02 · 03 · 04 | 연습용 공개 사이트 (httpbin, books.toscrape, jsonplaceholder) |
| 05 · 07 | Yahoo Finance (quantmod) |
| 06 | 네이버 금융 |
| 07 | 금융감독원 OpenDART API |

## 폴더 구조

```
my-r-quant-study/
├── my-r-quant-study.Rproj   RStudio 프로젝트
├── 01_R_Basic.R ~ 14_R_performance_risk.R
├── .Renviron.example        API 키 예시 (.Renviron 은 올리지 않음)
├── data/                    내려받은 원본 데이터 (올리지 않음)
└── output/                  그래프·결과표 (올리지 않음)
```

## 사용 패키지

`dplyr` · `tidyr` · `lubridate` · `zoo` · `readxl` · `writexl` · `httr` · `rvest` · `xml2` · `jsonlite` · `quantmod` · `xts` · `PerformanceAnalytics` · `ggplot2` · `plotly` · `htmlwidgets` · `ragg` · `quadprog`
