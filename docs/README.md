# AgeCalc 문서 목차

[메인 README](../readme.md)

개발·운영 안내와 과거 전략·실행 기록을 구분해 찾는 문서입니다. 날짜가 있는 기록은 당시 판단이며 최신 코드·서버 설정을 대신하지 않습니다. 계획의 체크박스나 작성일만으로 구현·배포 완료를 판단하지 않습니다.

## 개발·운영 안내

- [DEVELOPMENT](DEVELOPMENT.md)
- [ARCHITECTURE](ARCHITECTURE.md)
- [ROUTES](ROUTES.md)
- [TEAM_RULES](TEAM_RULES.md)
- [TEAM_OPERATIONS](TEAM_OPERATIONS.md)
- [DEPLOYMENT_GUIDE](../DEPLOYMENT_GUIDE.md)
- [BLOG_WORKFLOW](BLOG_WORKFLOW.md)
- [BLOG_POSTS_SCHEMA](../BLOG_POSTS_SCHEMA.md)
- [runtime-policy](operations/runtime-policy.md)
- [tls-certificates](operations/tls-certificates.md)
- [i18n](operations/i18n.md)
- [seo-query-index-policy](operations/seo-query-index-policy.md)

## 운영 이력·기준선

- [adsense-baseline-2026-06](operations/adsense-baseline-2026-06.md)
- [days-between-dates](operations/days-between-dates.md)
- [life-timeline-release-2026-08-23](operations/life-timeline-release-2026-08-23.md)
- [seo-change-log](operations/seo-change-log.md)

## 전략·로드맵

- [AGECALC_SEO_ADSENSE_LIFE_PLATFORM_STRATEGY](AGECALC_SEO_ADSENSE_LIFE_PLATFORM_STRATEGY.md)
- [agecalc-revenue-1500-roadmap](roadmaps/agecalc-revenue-1500-roadmap.md)
- [css-layout-checklist](roadmaps/css-layout-checklist.md)

## 설계 기록

- [2026-06-26-agecalc-blog-template-design](superpowers/specs/2026-06-26-agecalc-blog-template-design.md)
- [2026-07-13-adsense-review-mode-design](superpowers/specs/2026-07-13-adsense-review-mode-design.md)
- [2026-08-10-css-content-hash-cache-busting-design](superpowers/specs/2026-08-10-css-content-hash-cache-busting-design.md)
- [2026-08-10-mobile-footer-qr-size-design](superpowers/specs/2026-08-10-mobile-footer-qr-size-design.md)
- [2026-08-28-editorial-luxury-redesign-design](superpowers/specs/2026-08-28-editorial-luxury-redesign-design.md)
- [2026-09-15-regional-calculators-design](superpowers/specs/2026-09-15-regional-calculators-design.md)

## 구현 계획 기록

- [2026-06-19-agecalc-life-platform-implementation](superpowers/plans/2026-06-19-agecalc-life-platform-implementation.md)
- [2026-06-26-agecalc-blog-template-implementation](superpowers/plans/2026-06-26-agecalc-blog-template-implementation.md)
- [2026-07-31-hub-content-enrichment](superpowers/plans/2026-07-31-hub-content-enrichment.md)
- [2026-08-10-css-content-hash-cache-busting](superpowers/plans/2026-08-10-css-content-hash-cache-busting.md)
- [2026-08-10-mobile-footer-qr-size](superpowers/plans/2026-08-10-mobile-footer-qr-size.md)
- [2026-08-23-agecalc-expansion-checklist](superpowers/plans/2026-08-23-agecalc-expansion-checklist.md)
- [2026-08-28-editorial-luxury-redesign](superpowers/plans/2026-08-28-editorial-luxury-redesign.md)
- [2026-09-10-release-gate-cleanup](superpowers/plans/2026-09-10-release-gate-cleanup.md)
- [2026-09-15-regional-calculators](superpowers/plans/2026-09-15-regional-calculators.md)

## 추적 중인 조사·측정 기록

- [improvement-checklist](../_workspace/improvement-checklist.md)
- [classification-2026-08-23](../_workspace/p0-4-index-coverage/classification-2026-08-23.md)
- [baseline-2026-08-12](../_workspace/p0-5-performance-baseline/baseline-2026-08-12.md)
- [publication-policy](../_workspace/p2-3-owned-data/publication-policy.md)
- [baseline-2026-08-16](../_workspace/p2-4-core-web-vitals/baseline-2026-08-16.md)
- [measurement-method](../_workspace/p2-4-core-web-vitals/measurement-method.md)
- [baseline-2026-08-23](../_workspace/p2-7-geo-citation/baseline-2026-08-23.md)
- [measurement-protocol](../_workspace/p2-7-geo-citation/measurement-protocol.md)

## 문서 관리 원칙

- 메인 README에는 소개·주요 기능·읽는 순서·링크를 둡니다. 실행 명령과 세부 정책은 해당 주제 문서에서 관리합니다.
- 개발 환경은 DEVELOPMENT, 구조는 ARCHITECTURE, URL 안내는 ROUTES, 팀 규칙은 TEAM_RULES, 전달용 예시는 TEAM_OPERATIONS에 둡니다.
- 배포·서비스 관리는 루트 DEPLOYMENT_GUIDE, 블로그 명령·품질 기준은 BLOG_WORKFLOW에서 관리합니다. 같은 절차를 여러 문서에 복사하지 않고 상대 링크로 연결합니다.
- 운영 정책은 operations에, 전략은 roadmaps에, 과거 설계·구현 계획은 superpowers에 둡니다. 실제 결과는 작업별 outputs에 남깁니다.
- 날짜·대상 커밋·검증 환경을 기록하고 사실/가정/확인 필요를 구분합니다. 수익 목표·과거 테스트 수·과거 URL 수를 현재 성과로 인용하지 않습니다.
- 기존 문서의 경로·제목 앵커를 옮길 때는 참조를 함께 점검합니다. 기존 readme.md와 팀 운영 규칙 앵커는 호환성을 위해 유지합니다.
- AGENTS.md·agents/·docs/research/·outputs/·_workspace/의 비추적 자료는 작업 트리마다 다를 수 있습니다. 사용자 자료를 자동 이동·삭제·커밋하지 않습니다.
- 이 목차는 추적 문서와 이번에 추가한 안내 문서를 대상으로 합니다. 비추적 산출물 전체나 다른 worktree의 복사본을 현재 지침으로 나열하지 않습니다.
