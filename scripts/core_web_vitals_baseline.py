#!/usr/bin/env python3
"""Collect a mobile Core Web Vitals baseline without changing site code."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Callable


SITE_ORIGIN = "https://agecalc.cloud"
TARGET_PATHS = (
    "/",
    "/grade-birth-year-table",
    "/birth-year-age-table",
    "/age",
    "/school-grade-calculator",
    "/grade-age-table",
    "/school-entry-year-table",
    "/100-day-calculator",
    "/college-entry-year-calculator",
)
TARGET_URLS = tuple(f"{SITE_ORIGIN}{path}" for path in TARGET_PATHS)
GOOD_THRESHOLDS = {"lcp_ms": 2500, "inp_ms": 200, "cls": 0.1}
REQUIRED_GSC_FILES = ("메타데이터.csv", "차트.csv", "테이블.csv")


class DataQualityError(ValueError):
    """Raised when source data cannot support a trustworthy baseline."""


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise DataQualityError(f"원본 파일이 없습니다: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or ())
        return fields, [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
        ]


def _require_fields(path: Path, fields: list[str], required: tuple[str, ...]) -> None:
    missing = set(required) - set(fields)
    if missing:
        raise DataQualityError(f"{path.name} 필수 열 누락: {', '.join(sorted(missing))}")


def _site_url(value: str, label: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or parsed.netloc != "agecalc.cloud":
        raise DataQualityError(f"{label} URL은 https://agecalc.cloud 이어야 합니다: {value}")
    if parsed.query or parsed.fragment:
        raise DataQualityError(f"{label} URL은 기본 canonical URL이어야 합니다: {value}")
    return value


def load_search_console_cwv(data_dir: Path) -> dict[str, object]:
    candidates = sorted(
        path
        for path in data_dir.glob("*core-web-vitals*-2026-08-16")
        if path.is_dir()
    )
    if len(candidates) != 1:
        raise DataQualityError(
            "Search Console CWV 폴더가 정확히 하나 필요합니다: "
            "*core-web-vitals*-2026-08-16"
        )
    export_dir = candidates[0]
    for filename in REQUIRED_GSC_FILES:
        if not (export_dir / filename).is_file():
            raise DataQualityError(f"Search Console CWV 파일 누락: {filename}")

    metadata_path = export_dir / "메타데이터.csv"
    metadata_fields, metadata_rows = _read_csv(metadata_path)
    _require_fields(metadata_path, metadata_fields, ("속성", "값"))
    metadata = {row["속성"]: row["값"] for row in metadata_rows}
    if metadata.get("기기") != "모바일":
        raise DataQualityError("Search Console CWV 자료는 mobile(모바일) 보고서여야 합니다")

    chart_path = export_dir / "차트.csv"
    chart_fields, chart_rows = _read_csv(chart_path)
    if chart_fields != ["날짜", "빠른 URL"]:
        raise DataQualityError("차트.csv는 날짜, 빠른 URL 열이어야 합니다")
    if not chart_rows:
        raise DataQualityError("차트.csv에 데이터가 없습니다")
    chart = []
    for row in chart_rows:
        try:
            parsed_date = date.fromisoformat(row["날짜"])
            fast_urls = int(row["빠른 URL"])
        except ValueError as exc:
            raise DataQualityError("차트.csv 날짜 또는 빠른 URL 형식 오류") from exc
        if fast_urls < 0:
            raise DataQualityError("빠른 URL 수는 음수일 수 없습니다")
        chart.append({"date": parsed_date.isoformat(), "fast_urls": fast_urls})
    if [row["date"] for row in chart] != sorted(row["date"] for row in chart):
        raise DataQualityError("차트.csv 날짜가 오름차순이 아닙니다")

    table_path = export_dir / "테이블.csv"
    table_fields, table_rows = _read_csv(table_path)
    _require_fields(table_path, table_fields, ("URL 예시", "그룹 채우기"))
    if len(table_rows) != 1:
        raise DataQualityError("Valid 보고서의 URL 그룹은 정확히 하나여야 합니다")
    example_url = _site_url(table_rows[0]["URL 예시"], "Search Console 예시")
    try:
        affected_url_count = int(table_rows[0]["그룹 채우기"])
    except ValueError as exc:
        raise DataQualityError("그룹 채우기는 정수여야 합니다") from exc
    if affected_url_count < 0:
        raise DataQualityError("그룹 URL 수는 음수일 수 없습니다")

    status_match = re.search(r"core-web-vitals-([^-]+)-2026-08-16$", export_dir.name)
    status = status_match.group(1).lower() if status_match else "unknown"
    return {
        "source": "google_search_console_core_web_vitals",
        "device": "mobile",
        "status": status,
        "report_date": "2026-08-16",
        "period": {"start": chart[0]["date"], "end": chart[-1]["date"]},
        "example_url": example_url,
        "affected_url_count": affected_url_count,
        "latest_fast_url_count": chart[-1]["fast_urls"],
        "p75_value": "not_available",
        "metric_breakdown": "not_available",
        "chart": chart,
    }


def _audit_value(audits: dict[str, object], key: str) -> float:
    audit = audits.get(key)
    if not isinstance(audit, dict) or not isinstance(audit.get("numericValue"), (int, float)):
        raise DataQualityError(f"PageSpeed 응답에 {key} 수치가 없습니다")
    return float(audit["numericValue"])


def _resource_group(item: dict[str, object]) -> str:
    url = str(item.get("url", ""))
    host = urllib.parse.urlsplit(url).netloc.lower()
    resource_type = str(item.get("resourceType", "")).lower()
    if any(token in host for token in ("googlesyndication", "doubleclick", "googleadservices")):
        return "ads"
    if host in {"fonts.googleapis.com", "fonts.gstatic.com"}:
        return "fonts"
    if resource_type == "image" or re.search(r"\.(?:avif|gif|jpe?g|png|svg|webp)(?:$|\?)", url, re.I):
        return "images"
    if host == "agecalc.cloud" and (resource_type == "script" or ".js" in url):
        return "first_party_scripts"
    return "other"


def extract_pagespeed_run(payload: dict[str, object]) -> dict[str, object]:
    lighthouse = payload.get("lighthouseResult")
    if not isinstance(lighthouse, dict):
        raise DataQualityError("PageSpeed 응답에 lighthouseResult가 없습니다")
    audits = lighthouse.get("audits")
    categories = lighthouse.get("categories")
    if not isinstance(audits, dict) or not isinstance(categories, dict):
        raise DataQualityError("PageSpeed 응답의 audits 또는 categories가 없습니다")
    performance = categories.get("performance", {})
    score = performance.get("score") if isinstance(performance, dict) else None
    if not isinstance(score, (int, float)):
        raise DataQualityError("PageSpeed 성능 점수가 없습니다")

    resource_bytes = {
        "ads": 0,
        "fonts": 0,
        "images": 0,
        "first_party_scripts": 0,
        "other": 0,
    }
    network = audits.get("network-requests", {})
    network_details = network.get("details", {}) if isinstance(network, dict) else {}
    network_items = network_details.get("items", []) if isinstance(network_details, dict) else []
    for item in network_items if isinstance(network_items, list) else []:
        if not isinstance(item, dict):
            continue
        size = item.get("transferSize", 0)
        if isinstance(size, (int, float)) and size >= 0:
            resource_bytes[_resource_group(item)] += int(size)

    third_party_rows = []
    third_party = audits.get("third-party-summary", {})
    details = third_party.get("details", {}) if isinstance(third_party, dict) else {}
    items = details.get("items", []) if isinstance(details, dict) else []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict):
            third_party_rows.append(
                {
                    "entity": str(item.get("entity", "unknown")),
                    "transfer_bytes": int(item.get("transferSize", 0) or 0),
                    "main_thread_ms": float(item.get("mainThreadTime", 0) or 0),
                }
            )

    lcp_element = "not_available"
    lcp_audit = audits.get("largest-contentful-paint-element", {})
    lcp_details = lcp_audit.get("details", {}) if isinstance(lcp_audit, dict) else {}
    lcp_items = lcp_details.get("items", []) if isinstance(lcp_details, dict) else []
    if isinstance(lcp_items, list) and lcp_items:
        node = lcp_items[0].get("node", {}) if isinstance(lcp_items[0], dict) else {}
        if isinstance(node, dict) and node.get("snippet"):
            lcp_element = str(node["snippet"])

    return {
        "measured_at": str(payload.get("analysisUTCTimestamp", "not_available")),
        "final_url": _site_url(str(lighthouse.get("finalUrl", payload.get("id", ""))), "PageSpeed final"),
        "lighthouse_version": str(lighthouse.get("lighthouseVersion", "not_available")),
        "performance_score": round(float(score) * 100),
        "lcp_ms": round(_audit_value(audits, "largest-contentful-paint"), 3),
        "cls": round(_audit_value(audits, "cumulative-layout-shift"), 6),
        "tbt_ms": round(_audit_value(audits, "total-blocking-time"), 3),
        "fcp_ms": round(_audit_value(audits, "first-contentful-paint"), 3),
        "ttfb_ms": round(_audit_value(audits, "server-response-time"), 3),
        "total_bytes": round(_audit_value(audits, "total-byte-weight")),
        "resource_bytes": resource_bytes,
        "third_parties": third_party_rows,
        "lcp_element": lcp_element,
    }


def summarize_runs(runs: list[dict[str, object]], *, required_runs: int) -> dict[str, object]:
    metric_keys = (
        "performance_score",
        "lcp_ms",
        "cls",
        "tbt_ms",
        "fcp_ms",
        "ttfb_ms",
        "total_bytes",
    )
    median = {
        key: round(float(statistics.median(float(run[key]) for run in runs)), 6)
        for key in metric_keys
    } if runs else {}
    resource_groups = ("ads", "fonts", "images", "first_party_scripts", "other")
    median_resource_bytes = {
        group: round(
            statistics.median(
                int(run.get("resource_bytes", {}).get(group, 0)) for run in runs
            )
        )
        for group in resource_groups
    } if runs else {}
    third_party_entities = sorted(
        {
            str(item["entity"])
            for run in runs
            for item in run.get("third_parties", [])
            if isinstance(item, dict) and item.get("entity")
        }
    )
    third_parties = []
    for entity in third_party_entities:
        transfer_values = []
        main_thread_values = []
        for run in runs:
            match = next(
                (
                    item
                    for item in run.get("third_parties", [])
                    if isinstance(item, dict) and item.get("entity") == entity
                ),
                {},
            )
            transfer_values.append(int(match.get("transfer_bytes", 0) or 0))
            main_thread_values.append(float(match.get("main_thread_ms", 0) or 0))
        third_parties.append(
            {
                "entity": entity,
                "median_transfer_bytes": round(statistics.median(transfer_values)),
                "median_main_thread_ms": round(statistics.median(main_thread_values), 3),
            }
        )
    return {
        "status": "complete" if len(runs) == required_runs else "incomplete",
        "required_runs": required_runs,
        "successful_runs": len(runs),
        "median": median,
        "diagnostics": {
            "median_resource_bytes": median_resource_bytes,
            "third_parties": third_parties,
            "lcp_elements": sorted(
                {
                    str(run["lcp_element"])
                    for run in runs
                    if run.get("lcp_element") != "not_available"
                }
            ),
        },
        "runs": runs,
    }


def build_baseline(
    data_dir: Path,
    pagespeed_runs: dict[str, list[dict[str, object]]],
    *,
    target_urls: tuple[str, ...] = TARGET_URLS,
    required_runs: int = 3,
    errors: dict[str, list[str]] | None = None,
) -> dict[str, object]:
    field_data = load_search_console_cwv(data_dir)
    lab_data = []
    complete = True
    for url in target_urls:
        _site_url(url, "측정 대상")
        summary = summarize_runs(pagespeed_runs.get(url, []), required_runs=required_runs)
        summary["url"] = url
        summary["errors"] = list((errors or {}).get(url, ()))
        lab_data.append(summary)
        complete = complete and summary["status"] == "complete"
    group_paths = (
        (
            "input_calculators",
            {"/age", "/school-grade-calculator", "/100-day-calculator"},
        ),
        (
            "table_pages",
            {
                "/grade-birth-year-table",
                "/birth-year-age-table",
                "/grade-age-table",
                "/school-entry-year-table",
            },
        ),
        ("college_calculator", {"/college-entry-year-calculator"}),
        ("shared_home", {"/"}),
    )
    url_groups = []
    for name, paths in group_paths:
        members = [
            item
            for item in lab_data
            if urllib.parse.urlsplit(str(item["url"])).path in paths and item["median"]
        ]
        if not members:
            continue
        url_groups.append(
            {
                "name": name,
                "url_count": len(members),
                "median": {
                    key: round(statistics.median(item["median"][key] for item in members), 6)
                    for key in ("performance_score", "lcp_ms", "cls", "tbt_ms", "ttfb_ms", "total_bytes")
                },
            }
        )
    measured = [item for item in lab_data if item["median"]]
    analysis = {
        "lab_lcp_good_count": sum(item["median"]["lcp_ms"] <= GOOD_THRESHOLDS["lcp_ms"] for item in measured),
        "lab_cls_good_count": sum(item["median"]["cls"] <= GOOD_THRESHOLDS["cls"] for item in measured),
        "lab_lcp_over_4s_urls": [item["url"] for item in measured if item["median"]["lcp_ms"] > 4000],
        "lab_tbt_over_200ms_urls": [item["url"] for item in measured if item["median"]["tbt_ms"] > 200],
        "lab_cls_over_0_1_urls": [item["url"] for item in measured if item["median"]["cls"] > 0.1],
        "largest_payload": max(
            (
                {"url": item["url"], "bytes": item["median"]["total_bytes"]}
                for item in measured
            ),
            key=lambda row: row["bytes"],
            default={"url": "not_available", "bytes": 0},
        ),
        "url_groups": url_groups,
    }
    return {
        "as_of": "2026-08-16",
        "status": "complete" if complete else "incomplete",
        "thresholds": GOOD_THRESHOLDS,
        "field_data": field_data,
        "lab_data": lab_data,
        "analysis": analysis,
        "limitations": {
            "inp_lab": "not_measurable_use_tbt_proxy_only",
            "field_p75": "not_available_in_supplied_search_console_export",
        },
    }


def render_markdown(data: dict[str, object]) -> str:
    field = data["field_data"]
    lines = [
        "# Core Web Vitals 기준선",
        "",
        f"- 상태: `{data['status']}`",
        f"- 기준일: `{data['as_of']}`",
        "- 공식 좋은 기준: 모바일 p75 LCP ≤2.5초, INP ≤200ms, CLS ≤0.1",
        "- INP는 Search Console 현장 데이터로만 판정하며 Lighthouse TBT는 보조 지표로만 사용합니다.",
        "",
        "## Search Console 모바일 현장 데이터",
        "",
        f"- 보고서 상태: `{field['status']}`",
        f"- 기간: {field['period']['start']}~{field['period']['end']}",
        f"- 예시 URL: `{field['example_url']}`",
        f"- 그룹 URL 수: {field['affected_url_count']}",
        f"- URL별 p75: `{field['p75_value']}`",
        "",
        "## PageSpeed 모바일 실험실 측정",
        "",
        "| URL | 상태 | 점수 | LCP | CLS | TBT | TTFB | 전송량 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in data["lab_data"]:
        median = item["median"]
        if median:
            lines.append(
                f"| `{item['url']}` | {item['status']} | {median['performance_score']:.0f} | "
                f"{median['lcp_ms']:.0f}ms | {median['cls']:.3f} | {median['tbt_ms']:.0f}ms | "
                f"{median['ttfb_ms']:.0f}ms | {median['total_bytes']:.0f}B |"
            )
        else:
            lines.append(f"| `{item['url']}` | incomplete | - | - | - | - | - | - |")
    lines.extend(["", "## 관측된 리소스·제3자 진단", ""])
    for item in data["lab_data"]:
        if not item["median"]:
            continue
        lines.extend(
            [
                f"### `{item['url']}`",
                "",
                "| 리소스 범주 | 중앙 전송량 |",
                "|---|---:|",
            ]
        )
        for group, byte_count in item["diagnostics"]["median_resource_bytes"].items():
            lines.append(f"| {group} | {byte_count:,}B |")
        third_parties = item["diagnostics"]["third_parties"]
        if third_parties:
            lines.extend(["", "관측된 제3자:"])
            for third_party in third_parties:
                lines.append(
                    f"- {third_party['entity']}: 전송 {third_party['median_transfer_bytes']:,}B, "
                    f"메인 스레드 {third_party['median_main_thread_ms']:.1f}ms"
                )
        lcp_elements = item["diagnostics"]["lcp_elements"]
        if lcp_elements:
            lines.extend(["", "관측된 LCP 요소:"])
            lines.extend(f"- `{element}`" for element in lcp_elements)
        lines.append("")
    analysis = data["analysis"]
    lines.extend(
        [
            "## URL군별 중앙값",
            "",
            "| URL군 | URL 수 | 점수 | LCP | CLS | TBT | 전송량 |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for group in analysis["url_groups"]:
        median = group["median"]
        lines.append(
            f"| {group['name']} | {group['url_count']} | {median['performance_score']:.0f} | "
            f"{median['lcp_ms']:.0f}ms | {median['cls']:.3f} | {median['tbt_ms']:.0f}ms | "
            f"{median['total_bytes']:.0f}B |"
        )
    lines.extend(
        [
            "",
            "## 우선 조사 후보",
            "",
            f"- 실험실 LCP 4초 초과: {len(analysis['lab_lcp_over_4s_urls'])}개 URL",
            f"- 실험실 TBT 200ms 초과: {len(analysis['lab_tbt_over_200ms_urls'])}개 URL",
            f"- 실험실 CLS 0.1 초과: {len(analysis['lab_cls_over_0_1_urls'])}개 URL",
            f"- 최대 전송량: `{analysis['largest_payload']['url']}` "
            f"{analysis['largest_payload']['bytes']:,.0f}B",
            "- 위 항목은 후속 최적화 후보이며 현장 INP 또는 개별 URL p75로 확대 해석하지 않습니다.",
            "",
        ]
    )
    lines.extend(
        [
            "",
            "## 해석 제한",
            "",
            "- Search Console 내보내기에 없는 URL별 p75와 지표별 수치는 추정하지 않습니다.",
            "- 광고·폰트·이미지·스크립트 영향은 PageSpeed 응답에 실제로 관측된 요청과 진단만 기록합니다.",
            "- 이 기준선은 성능 수정의 근거이며 이번 단계에서 공개 사이트 코드를 변경하지 않습니다.",
            "",
        ]
    )
    return "\n".join(lines)


def _fetch_pagespeed(url: str, api_key: str, *, timeout: int = 120) -> dict[str, object]:
    query = urllib.parse.urlencode(
        {
            "url": url,
            "strategy": "mobile",
            "category": "performance",
            "locale": "ko",
            "key": api_key,
        }
    )
    request = urllib.request.Request(
        f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?{query}",
        headers={"User-Agent": "AgeCalc-CWV-Baseline/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def collect_pagespeed_runs(
    urls: tuple[str, ...],
    api_key: str,
    *,
    required_runs: int = 3,
    fetcher: Callable[[str, str], dict[str, object]] = _fetch_pagespeed,
) -> tuple[dict[str, list[dict[str, object]]], dict[str, list[str]]]:
    results: dict[str, list[dict[str, object]]] = {}
    errors: dict[str, list[str]] = {}
    for url in urls:
        runs = []
        failures = []
        for _ in range(required_runs + 2):
            if len(runs) == required_runs:
                break
            try:
                runs.append(extract_pagespeed_run(fetcher(url, api_key)))
            except (DataQualityError, urllib.error.URLError, TimeoutError, ValueError) as exc:
                failures.append(type(exc).__name__)
        results[url] = runs
        errors[url] = failures
    return results, errors


def write_outputs(data: dict[str, object], output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "baseline-2026-08-16.json"
    markdown_path = output_dir / "baseline-2026-08-16.md"
    method_path = output_dir / "measurement-method.md"
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(data), encoding="utf-8")
    method_path.write_text(
        "# Core Web Vitals 재측정 방법\n\n"
        "1. Search Console 모바일 CWV 내보내기를 `_data/*core-web-vitals*-2026-08-16/`에 둡니다.\n"
        "2. `_data/.env.cwv`에 `PAGESPEED_API_KEY`를 설정합니다. 이 파일은 Git에 포함하지 않습니다.\n"
        "3. 아래 명령으로 모바일 3회 측정을 실행합니다.\n\n"
        "```bash\n"
        "set -a\nsource _data/.env.cwv\nset +a\n"
        "/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/core_web_vitals_baseline.py\n"
        "```\n\n"
        "Lighthouse는 INP를 직접 측정하지 않으므로 TBT를 보조 지표로만 사용합니다.\n",
        encoding="utf-8",
    )
    return markdown_path, json_path, method_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("_data"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("_workspace/p2-4-core-web-vitals"),
    )
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs는 1 이상이어야 합니다")
    api_key = (os.getenv("PAGESPEED_API_KEY") or "").strip()
    if not api_key:
        parser.error("PAGESPEED_API_KEY 환경변수가 필요합니다")
    try:
        runs, errors = collect_pagespeed_runs(TARGET_URLS, api_key, required_runs=args.runs)
        baseline = build_baseline(
            args.data_dir,
            runs,
            required_runs=args.runs,
            errors=errors,
        )
        paths = write_outputs(baseline, args.output_dir)
    except DataQualityError as exc:
        parser.error(str(exc))
    for path in paths:
        print(f"wrote {path}")
    return 0 if baseline["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
