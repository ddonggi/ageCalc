# Core Web Vitals 재측정 방법

1. Search Console 모바일 CWV 내보내기를 `_data/*core-web-vitals*-2026-08-16/`에 둡니다.
2. `_data/.env.cwv`에 `PAGESPEED_API_KEY`를 설정합니다. 이 파일은 Git에 포함하지 않습니다.
3. 아래 명령으로 모바일 3회 측정을 실행합니다.

```bash
set -a
source _data/.env.cwv
set +a
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/core_web_vitals_baseline.py
```

Lighthouse는 INP를 직접 측정하지 않으므로 TBT를 보조 지표로만 사용합니다.
