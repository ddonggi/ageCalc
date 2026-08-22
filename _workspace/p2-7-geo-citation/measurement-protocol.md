# AgeCalc GEO 인용 측정 방법

질문 세트 버전: `2026-v1`
측정 대상: Google 검색 AI Overview, ChatGPT 웹 검색, Perplexity Web

이 측정은 AgeCalc가 AI 답변에 자연스럽게 언급되거나 출처로 연결되는지를 월별로 비교하기 위한 것입니다. 질문에는 AgeCalc 이름을 넣지 않습니다. 한 회차의 36개 관측은 가능하면 같은 날, 같은 기기와 지역에서 진행합니다.

## 측정 전 준비

1. `_workspace/p2-7-geo-citation/observation-template.csv`를 복사해 `_data/geo-citation-YYYY-MM-DD/observations.csv`로 저장합니다.
2. 해당 폴더 아래 `evidence/`를 만들고 화면 캡처를 보관합니다. `_data`의 원본은 Git에 포함하지 않습니다.
3. 대한민국에서 데스크톱 브라우저를 사용하고 화면 언어를 한국어로 맞춥니다.
4. 개인화 영향을 줄이기 위해 Google과 Perplexity는 로그아웃한 비공개 창, ChatGPT는 메모리가 꺼진 임시 대화를 사용합니다.
5. 질문 문구를 고치거나 부연 질문을 붙이지 않습니다. 결과가 마음에 들지 않아도 같은 질문을 다시 실행하지 않습니다.

## 플랫폼별 조건

### Google 검색 AI Overview

- 로그아웃한 비공개 창에서 `google.com`을 엽니다.
- 검색어는 `query_text`를 그대로 붙여 넣습니다.
- AI Overview가 나타나지 않으면 `observation_status=surface_not_present`로 기록합니다. 일반 검색 결과의 AgeCalc 노출은 이 측정에 넣지 않습니다.
- AI Overview가 나타나면 `observation_status=observed`, `platform_model=not_displayed`로 기록합니다.

### ChatGPT 웹 검색

- 메모리가 적용되지 않는 새 임시 대화를 시작합니다.
- 웹 검색 기능이 켜졌는지 확인한 뒤 `query_text`만 입력합니다.
- 화면에 표시된 모델 이름을 `platform_model`에 적습니다. 모델 이름을 확인할 수 없으면 `default_not_displayed`라고 적습니다.
- 검색을 사용하지 않은 답변이 나오면 사실대로 기록하되 `notes`에 `web search not used by response`를 남깁니다.

### Perplexity Web

- 로그아웃한 비공개 창에서 새 검색을 시작하고 검색 범위를 Web으로 둡니다.
- `query_text`만 입력합니다.
- 표시된 모델 이름을 적고, 표시되지 않으면 `default_not_displayed`라고 적습니다.

## 관측값 입력 규칙

- `observation_status`: 답변 화면을 확인했으면 `observed`, Google AI Overview가 없으면 `surface_not_present`, 플랫폼 오류로 확인하지 못했으면 `technical_failure`입니다.
- `brand_mentioned`: 답변 본문에 `AgeCalc`, `에이지칼크`, `agecalc.cloud`가 보이면 `true`입니다.
- `agecalc_url_cited`: 답변의 출처나 링크가 `https://agecalc.cloud/` 또는 그 하위 URL을 가리킬 때만 `true`입니다.
- `agecalc_cited_urls`: AgeCalc URL을 화면 순서대로 세미콜론(`;`)으로 구분합니다.
- `citation_positions`: 전체 출처 중 AgeCalc 출처의 1부터 시작하는 순번을 세미콜론으로 구분합니다.
- `citation_context`: `direct_answer`, `supporting_source`, `related_link`, `mixed` 중 하나를 사용합니다. 인용이 없으면 `not_applicable`입니다.
- `sentiment`: 브랜드를 언급한 문장의 태도를 `positive`, `neutral`, `negative`로 기록합니다. 브랜드 언급이 없으면 `not_applicable`입니다.
- `all_cited_domains`: 화면에 인용된 모든 출처 도메인을 순서대로 세미콜론으로 구분합니다. 같은 도메인이 두 번 인용되면 두 번 적습니다.
- `citation_link_available`: 사용자가 실제로 누를 수 있는 AgeCalc 링크가 있으면 `true`입니다.
- `downstream_clicks`: 별도 GA4 유입 자료를 연결하기 전에는 항상 `not_available`입니다.

`surface_not_present` 행의 브랜드·인용·문맥·감성·링크 값은 모두 `not_applicable`로 기록합니다. `technical_failure`는 기준선 완료로 인정하지 않으므로 같은 회차 안에서 오류 원인을 해결한 뒤 다시 측정합니다.

## 증거 파일과 체크섬

캡처 파일명은 `google_ai_overview-q01_man_age.png`처럼 플랫폼과 질문 ID를 함께 적습니다. 계정명, 이메일, 프로필 사진이 보이면 로컬에서 가린 뒤 `_data`에 넣습니다.

Ubuntu에서 SHA-256을 확인합니다.

```bash
sha256sum _data/geo-citation-YYYY-MM-DD/evidence/*.png
```

macOS에서 확인할 때는 다음 명령을 사용합니다.

```bash
shasum -a 256 evidence-file.png
```

해시 64자를 `evidence_sha256`에 넣고 파일의 상대 경로를 `evidence_file`에 적습니다. 한 답변이 여러 장이면 화면 순서대로 파일명과 해시를 각각 세미콜론(`;`)으로 구분하며, 두 필드의 항목 수와 순서를 일치시킵니다. 원본 답변을 저장소에 커밋하지 않고도 같은 증거 파일인지 확인하기 위한 값입니다.

## 검증 명령

관측 파일을 모두 입력한 뒤 다음 명령을 실행합니다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python \
  scripts/validate_geo_citation_baseline.py \
  --observations _data/geo-citation-YYYY-MM-DD/observations.csv \
  --require-complete
```

`valid: ... (36 rows)`가 출력되어야 첫 기준선 보고서를 만들 수 있습니다. 월별 재측정에서도 `prompt-catalog.json`의 질문과 조건을 그대로 사용합니다. 질문 세트가 바뀌면 이전 회차와 직접 비교하지 않고 새 버전 기준선을 만듭니다.
