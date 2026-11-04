# 문서 정리 결과

- 확인일: 2026-11-04. 기준 커밋 f11630e, 작업 트리 `/srv/apps/agecalc/.worktrees/pre-release`, 브랜치 develop/pre-release. 사용자가 문서 분리·README 정리를 직접 요청한 범위에서 수행했다.
- 사실: 기존 readme.md를 209행에서 48행으로 축소하고 주요 기능·문서 링크·읽는 순서·기존 팀 규칙 앵커를 남겼다. 파일명 대소문자 변경으로 기존 참조가 깨지지 않도록 readme.md를 유지했다.
- 사실: docs/DEVELOPMENT.md, ROUTES.md, TEAM_RULES.md, operations/runtime-policy.md, operations/tls-certificates.md로 개발·라우트·팀 규칙·공개 정책·TLS 절차를 분리했다. 기존 ARCHITECTURE에 프로젝트 구조를 옮기고 BLOG_WORKFLOW를 RSS 명령·품질 기준의 참조 위치로 사용했다.
- 사실: docs/README.md에 현재 안내, 운영 이력, 전략, 설계, 구현 계획, 추적 조사 기록을 구분한 전체 목차를 추가했다. 기존 기록은 삭제하거나 현재 계획으로 재작성하지 않았다.
- 사실: 배포 가이드의 운영 폴더 직접 개발 안내, 현재 서버 상태 단정, 블로그 색인 조건 누락, 로컬 preflight와 실제 서버 검사의 혼동을 수정했다. 스키마 문서에는 블로그 4개 외 PageFeedback 모델이 있음을 명시했다. 과거 설계 문서의 worktree 절대 링크 2개를 상대 링크로 교체했다.
- 검증: 추적 Markdown과 새 docs 문서 44개에서 상대 경로·헤딩 링크 115개를 정적 검사했고 오류 0건. git diff --check 통과. 코드·앱 import·DB·외부 URL·테스트·서비스 실행 없음. 신규 파일은 모두 Markdown이다.
- 점검 한계: 전체 문서의 목록·링크와 현행 안내의 중복·모순을 점검했다. 수백 개 비추적 산출물과 다른 worktree 복사본의 내용 전체를 검증한 것은 아니다. 외부 링크의 HTTP 접근성과 과거 설계의 모든 사실은 미검증이다.
- 보존: 운영 작업 트리의 untracked AGENTS.md, agents/, docs/research/, outputs/ 및 개발 작업 트리의 기존 untracked 자료는 수정하지 않았다. 운영 작업 트리에는 이번 변경이 아직 반영되지 않았다.
- 다음 단계: 문서 변경 검토 후 승인된 범위에서 커밋·통합. 이번 작업에서 커밋·push·병합·배포는 수행하지 않았다.
