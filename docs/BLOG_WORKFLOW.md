# Blog Automation Workflow

블로그 자동화의 목표는 RSS 원문을 그대로 복제하지 않고, AgeCalc 독자에게 맞는 한국어 설명형 글로 재창작한 뒤 수동 검수로 공개하는 것입니다.

## Pipeline
```mermaid
flowchart TD
    Timer[systemd timer<br/>09:00 / 12:00 / 19:00 KST] --> Run[rss_blog_scheduler.py run]
    Run --> Fetch[RSS/Atom 수집]
    Fetch --> Item{새 FeedItem?}
    Item -- no --> Stop[종료]
    Item -- yes --> Resolve[Google News URL이면 실제 원문 URL 해석]
    Resolve --> Generate[OpenAI 한국어 재창작]
    Generate --> Quality{품질 기준 통과?}
    Quality -- no --> NeedsReview[needs_review 저장]
    Quality -- yes --> Image[OpenAI 커버 이미지 생성]
    Image --> Draft[draft 저장]
    Draft --> Review[/blog/drafts에서 확인]
    Review --> Publish{공개 버튼}
    Publish --> Audit[AdSense audit]
    Audit -->|통과| Published[published]
    Audit -->|실패| DraftError[오류 표시 후 draft 유지]
```

원본 Mermaid 파일: [docs/diagrams/blog-workflow.mmd](diagrams/blog-workflow.mmd)

## Status
| Status | Meaning | Public Access |
| --- | --- | --- |
| `needs_review` | 원문 해석 실패, 자동 생성 실패, 2,500자 미만, 출처/내부 링크/구조 부족 등으로 공개 부적합 | 비공개 |
| `draft` | 자동 검수 기준을 통과한 공개 후보 | `/blog/drafts`에서 비밀번호 필요 |
| `published` | 수동 공개 또는 토큰 승인까지 통과한 글 | `/blog/<slug>` |

## Current Quality Gates
- HTML 태그 제외 본문 최소 `2,500자`
- 생성 목표 한글 기준 `2,700자 이상`
- `h2`/`h3` 소제목 5개 이상
- 실제 원문 URL 필요
- Google News RSS redirect URL만 출처로 남으면 실패
- AgeCalc 내부 계산기 링크 1개 이상 필요
- 대표 이미지 필요
- 내부 표식인 `Generated from RSS`가 남으면 실패
- 영어 원문은 한국어 설명형 글로 재창작되어야 하며 원문 제목을 그대로 쓰면 실패

## Manual Commands
초안 1개 생성:
```bash
sudo -iu agecalc
cd /srv/apps/agecalc
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/rss_blog_scheduler.py run --limit 1 --status draft --provider openai --model gpt-4.1-mini
```

기존 글 일부를 보강해 `draft`로 전환:
```bash
sudo -iu agecalc
cd /srv/apps/agecalc
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/rewrite_blog_posts.py --limit 5 --apply --model gpt-4.1-mini
```

전체 상태를 보강하고 통과 글을 자동 공개:
```bash
sudo -iu agecalc
cd /srv/apps/agecalc
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/rewrite_blog_posts.py --status all --all --attempts 2 --apply --publish-on-pass --demote-failed-published --model gpt-4.1-mini
```

커버 이미지 누락 보정:
```bash
sudo -iu agecalc
cd /srv/apps/agecalc
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/rss_blog_scheduler.py backfill-covers --status draft --limit 2
```

감사 리포트:
```bash
sudo -iu agecalc
cd /srv/apps/agecalc
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/adsense_blog_review.py --format json
```

## Publishing Rules
1. `/blog/drafts`에 `BLOG_DRAFT_PASSWORD`로 로그인합니다.
2. `draft` 글 상세에서 `이 글 공개하기`를 누릅니다.
3. 서버가 `audit_post(..., require_cover_image=True)`로 다시 검사합니다.
4. 통과하면 `published`로 바꾸고 public 상세로 redirect합니다.
5. 실패하면 오류 메시지를 표시하고 공개하지 않습니다.

`needs_review` 글에는 공개 버튼이 없습니다. 먼저 재작성하거나 수동 보정해 `draft`로 전환해야 합니다. 대량 보강 스크립트에서 `--publish-on-pass`를 쓰면 검수 통과 글은 바로 `published`로 전환되고, 실패 글은 `needs_review`로 남습니다.
