# Life Timeline MVP Release Record

- 기록일: 2026-08-23
- 대상 URL: `/life-timeline`
- MVP 운영 반영 커밋: `1150473`
- 출시 게이트 계측·표본 검증 커밋: `558eb98`
- 운영 상태: MVP 운영 반영 완료, 계측 커밋은 다음 운영 배포 대상

## 검증 결과

- 사용자가 360x800, 768x1024, 데스크톱 화면에서 입력·오류·결과 흐름과 가로 스크롤 여부를 수동 확인했다.
- Python 도메인 계산과 브라우저 계산을 정확히 10개 리터럴 표본으로 비교했다.
- 표본에는 생일 전·당일·후, 윤년 생일, 연말 경계, 띠 연도 변경, 별자리 경계를 포함했다.
- `python -m unittest discover -s tests -v`: 408건 통과.
- 독립 변경 리뷰: 명세 준수 통과, Critical·Important·Minor 지적 없음.

## 개인정보 없는 측정 계약

계산 완료 이벤트:

```text
life_timeline_complete
{ calculator: "life_timeline" }
```

관련 도구 클릭 이벤트:

```text
life_timeline_related_tool_click
{ calculator: "life_timeline", destination: <fixed slug> }
```

허용된 `destination`은 `age`, `birthday_dday`, `birth_year_zodiac`뿐이다. 생년월일, 출생연도, 나이, 살아온 일수, 띠, 별자리, 입력 원문은 이벤트·URL·서버 요청·로그에 포함하지 않는다. 이벤트 전송은 사용자가 분석에 동의하고 `AgeCalcTracking`이 준비된 경우에만 수행한다.

## 관찰 항목

- 계산 완료율: `life_timeline_complete` ÷ `/life-timeline` 계산 시작 기준 모수
- 관련 도구 이동률: `life_timeline_related_tool_click` ÷ `life_timeline_complete`
- 관찰 기간: 계측 커밋 운영 반영일부터 14일
- 상태: 관찰 시작 전

14일 데이터가 쌓이기 전에는 배치 1의 관찰 게이트를 완료 처리하거나 배치 2 진입 근거로 사용하지 않는다.
