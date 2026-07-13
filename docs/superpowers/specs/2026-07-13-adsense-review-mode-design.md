# AgeCalc AdSense 승인 모드 설계

## 목적

AdSense의 `가치가 별로 없는 콘텐츠` 거절에 대응해 디자인과 계산 기능은 유지하면서 심사 대상과 상업성 신호를 보수적으로 축소한다.

## 동작

- `ADSENSE_REVIEW_MODE`는 기본 활성화하며 쿠팡과 공개 블로그 설정보다 우선한다.
- 승인 대상은 sitemap의 46개 핵심 계산기, 표, 정적 가이드, 신뢰 페이지다.
- 8개 라이프 허브는 메뉴와 URL을 유지하되 `noindex, follow`와 AdSense 코드 제외를 적용한다.
- 블로그 목록과 공개 글은 `noindex, nofollow`로 유지하고 sitemap과 메뉴에서 제외한다.
- 승인 모드에서는 쿠팡 HTML, 제휴 링크, 제휴 고지 및 CSP 허용 도메인을 제거한다.
- 비어 있는 retirement, health, generations sitemap은 sitemap index에서 제외한다.

## 품질 게이트

- sitemap URL은 200, canonical, indexable이어야 하며 AdSense 승인 코드를 포함해야 한다.
- sitemap HTML에 쿠팡 도메인, `rel="sponsored"`, 제휴 고지가 있으면 사전점검을 실패시킨다.
- 제외 페이지는 200과 noindex를 유지하며 AdSense 코드와 tracking client가 없어야 한다.
- 콘텐츠 품질 감사는 sitemap URL만 검사하며 신뢰 페이지는 임의의 글자 수 채우기를 요구하지 않는다.

## 배포 원칙

운영 환경에서도 승인 모드와 쿠팡·블로그 개별 비활성 플래그를 함께 설정한다. Search Console에서 sitemap과 noindex 반영을 확인한 뒤 14일 동안 구조를 안정적으로 유지하고 재심사를 요청한다.
