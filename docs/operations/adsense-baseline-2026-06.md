# AgeCalc AdSense 승인 기준선

기준일: 2026-06-19

## 공개 색인 구조

- `/sitemap.xml` URL 수: 50
- 정적 endpoint 목록: 31개
- 기본 설정에서 `/blog` 제외: 공개 블로그 색인 기능이 꺼져 있음
- 정적 가이드 상세: 20개
- 미니게임: sitemap 제외, `X-Robots-Tag: noindex, nofollow`
- 블로그 목록·상세: 공개 색인 조건을 충족하지 않으면 `noindex, nofollow`
- 블로그 초안·검토: sitemap 제외, AdSense 코드 제외

## 광고·제휴 기준선

- 공개 sitemap URL에는 AdSense account meta와 승인 스크립트가 존재한다.
- 미니게임, 블로그 초안, 블로그 검토 페이지에는 AdSense 코드를 렌더링하지 않는다.
- `COUPANG_PARTNERS_ENABLED=false`이면 홈페이지와 핵심 계산기에서 전역 쿠팡 레일을 렌더링하지 않는다.
- Task A2에서 전역 쿠팡 레일 자체를 제거하고, 이후 제휴 노출은 별도 맥락형 정책이 승인될 때까지 사용하지 않는다.

## 기준 검증 명령

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest discover -s tests -v
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/adsense_preflight.py --format text
```

기준 결과:

```text
Ran 134 tests
OK
[adsense-preflight] PASS checked_pages=50 sitemap_urls=50
```

## 보호해야 할 상태

- sitemap에는 canonical 200 응답의 index 가능 URL만 포함한다.
- `/minigames`, `/blog/drafts`, `/blog/review`는 sitemap에 포함하지 않는다.
- 공개 블로그 색인이 비활성인 동안 `/blog`를 sitemap에 포함하지 않는다.
- 전역 제휴 기능이 비활성일 때 핵심 페이지 HTML에 쿠팡 레일 iframe과 배너가 없어야 한다.

## Foundation 확장

2026-06-22에 8개 라이프 허브를 추가하면서 sitemap의 의도된 URL 수는 50개에서 58개로 증가한다. 기존 50개 URL은 유지하며 다음 canonical 허브만 추가한다.

- `/age/`
- `/family/`
- `/education/`
- `/anniversary/`
- `/retirement/`
- `/health/`
- `/pets/`
- `/generations/`
