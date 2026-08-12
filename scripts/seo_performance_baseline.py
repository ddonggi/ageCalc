#!/usr/bin/env python3
"""Normalize Google Search Console and Naver performance exports."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit


SITE_HOST = "agecalc.cloud"
AS_OF_DATE = "2026-08-12"
CHANGE_DATE = "2026-08-11"
BRAND_TERMS = ("agecalc", "age calc", "agecalc.cloud")


class DataQualityError(ValueError):
    """Raised when an export cannot safely support the baseline."""


def _read_dict_rows(path: Path, required: Iterable[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise DataQualityError(f"원본 파일이 없습니다: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or ())
        missing = set(required) - fields
        if missing:
            raise DataQualityError(f"{path.name} 필수 열 누락: {', '.join(sorted(missing))}")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def _number(value: str, label: str, *, integer: bool = False) -> int | float:
    try:
        number = int(value) if integer else float(value)
    except (TypeError, ValueError) as exc:
        raise DataQualityError(f"{label} 숫자 형식 오류: {value!r}") from exc
    if number < 0:
        raise DataQualityError(f"{label}에 음수 값이 있습니다: {value!r}")
    return number


def _percent(value: str, label: str) -> float:
    return float(_number(value.rstrip("%"), label))


def _metric_rows(
    path: Path,
    dimension: str,
    *,
    ctr_tolerance: float = 0.011,
) -> list[dict[str, object]]:
    required = (dimension, "클릭수", "노출", "CTR", "게재 순위")
    raw_rows = _read_dict_rows(path, required)
    seen: set[str] = set()
    rows: list[dict[str, object]] = []
    for line_number, raw in enumerate(raw_rows, start=2):
        key = raw[dimension]
        if not key:
            raise DataQualityError(f"{path.name}:{line_number} {dimension} 값이 비어 있습니다")
        if key in seen:
            raise DataQualityError(f"{path.name}에 중복 {dimension} 값이 있습니다: {key}")
        seen.add(key)
        clicks = int(_number(raw["클릭수"], f"{path.name} 클릭수", integer=True))
        impressions = int(_number(raw["노출"], f"{path.name} 노출", integer=True))
        position = float(_number(raw["게재 순위"], f"{path.name} 게재 순위"))
        reported_ctr = _percent(raw["CTR"], f"{path.name} CTR")
        calculated_ctr = clicks / impressions * 100 if impressions else 0.0
        if abs(reported_ctr - calculated_ctr) > ctr_tolerance:
            raise DataQualityError(
                f"{path.name}:{line_number} CTR 불일치: 보고 {reported_ctr:g}%, 계산 {calculated_ctr:.4f}%"
            )
        rows.append(
            {
                "key": key,
                "clicks": clicks,
                "impressions": impressions,
                "ctr_percent": round(calculated_ctr, 6),
                "position": position,
            }
        )
    return rows


def _total(rows: Iterable[dict[str, object]]) -> dict[str, object]:
    materialized = list(rows)
    clicks = sum(int(row["clicks"]) for row in materialized)
    impressions = sum(int(row["impressions"]) for row in materialized)
    weighted_position = (
        sum(float(row["position"]) * int(row["impressions"]) for row in materialized) / impressions
        if impressions
        else 0.0
    )
    return {
        "clicks": clicks,
        "impressions": impressions,
        "ctr_percent": round(clicks / impressions * 100, 6) if impressions else 0.0,
        "average_position": round(weighted_position, 6),
        "row_count": len(materialized),
    }


def _validate_date_series(rows: list[dict[str, object]], filename: str) -> None:
    dates: list[date] = []
    for row in rows:
        try:
            dates.append(datetime.strptime(str(row["key"]), "%Y-%m-%d").date())
        except ValueError as exc:
            raise DataQualityError(f"{filename} 날짜 형식 오류: {row['key']}") from exc
    if dates != sorted(dates):
        raise DataQualityError(f"{filename} 날짜가 오름차순이 아닙니다")
    for previous, current in zip(dates, dates[1:]):
        if (current - previous).days != 1:
            raise DataQualityError(f"{filename} 날짜가 연속적이지 않습니다: {previous} → {current}")


def _validate_site_url(url: str, filename: str, *, allow_www: bool = False) -> str:
    parsed = urlsplit(url)
    allowed_hosts = {SITE_HOST, f"www.{SITE_HOST}"} if allow_www else {SITE_HOST}
    if parsed.scheme != "https" or parsed.netloc not in allowed_hosts:
        raise DataQualityError(f"{filename} URL은 https://{SITE_HOST} 이어야 합니다: {url}")
    if not parsed.path.startswith("/"):
        raise DataQualityError(f"{filename} URL 경로가 올바르지 않습니다: {url}")
    return parsed.path


def _load_naver_daily(path: Path, as_of: date) -> tuple[list[dict[str, object]], dict[str, object]]:
    if not path.is_file():
        raise DataQualityError(f"원본 파일이 없습니다: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if len(rows) != 3 or rows[1][0] != "노출" or rows[2][0] != "클릭":
        raise DataQualityError(f"{path.name}은 날짜·노출·클릭 3행 형식이어야 합니다")
    if not (len(rows[0]) == len(rows[1]) == len(rows[2])):
        raise DataQualityError(f"{path.name} 행별 열 수가 다릅니다")
    dates: list[date] = []
    parsed_rows: list[dict[str, object]] = []
    for index, short_date in enumerate(rows[0][1:], start=1):
        try:
            month, day = map(int, short_date.split("."))
            candidate = date(as_of.year, month, day)
        except (ValueError, TypeError) as exc:
            raise DataQualityError(f"{path.name} 날짜 형식 오류: {short_date}") from exc
        if candidate > as_of:
            candidate = date(as_of.year - 1, month, day)
        if candidate in dates:
            raise DataQualityError(f"{path.name}에 중복 날짜가 있습니다: {candidate}")
        dates.append(candidate)
        impressions = int(_number(rows[1][index], f"{path.name} 노출", integer=True))
        clicks = int(_number(rows[2][index], f"{path.name} 클릭", integer=True))
        parsed_rows.append(
            {
                "date": candidate.isoformat(),
                "clicks": clicks,
                "impressions": impressions,
                "ctr_percent": round(clicks / impressions * 100, 6) if impressions else 0.0,
            }
        )
    if dates != sorted(dates):
        raise DataQualityError(f"{path.name} 날짜가 오름차순이 아닙니다")
    for previous, current in zip(dates, dates[1:]):
        if (current - previous).days != 1:
            raise DataQualityError(f"{path.name} 날짜가 연속적이지 않습니다: {previous} → {current}")
    clicks = sum(int(row["clicks"]) for row in parsed_rows)
    impressions = sum(int(row["impressions"]) for row in parsed_rows)
    total = {
        "clicks": clicks,
        "impressions": impressions,
        "ctr_percent": round(clicks / impressions * 100, 6) if impressions else 0.0,
        "row_count": len(parsed_rows),
        "start_date": dates[0].isoformat(),
        "end_date": dates[-1].isoformat(),
    }
    return parsed_rows, total


def _load_naver_table(path: Path, dimension: str) -> list[dict[str, object]]:
    required = ("순위", dimension, "클릭", "노출", "CTR(%)")
    raw_rows = _read_dict_rows(path, required)
    seen_ranks: set[int] = set()
    rows: list[dict[str, object]] = []
    for line_number, raw in enumerate(raw_rows, start=2):
        rank = int(_number(raw["순위"], f"{path.name} 순위", integer=True))
        if rank in seen_ranks:
            raise DataQualityError(f"{path.name}에 중복 순위가 있습니다: {rank}")
        seen_ranks.add(rank)
        clicks = int(_number(raw["클릭"], f"{path.name} 클릭", integer=True))
        impressions = int(_number(raw["노출"], f"{path.name} 노출", integer=True))
        reported_ctr = _percent(raw["CTR(%)"], f"{path.name} CTR")
        calculated_ctr = clicks / impressions * 100 if impressions else 0.0
        if abs(reported_ctr - calculated_ctr) > 0.11:
            raise DataQualityError(
                f"{path.name}:{line_number} CTR 불일치: 보고 {reported_ctr:g}%, 계산 {calculated_ctr:.4f}%"
            )
        rows.append(
            {
                "rank": rank,
                dimension.lower(): raw[dimension],
                "clicks": clicks,
                "impressions": impressions,
                "ctr_percent": round(calculated_ctr, 6),
            }
        )
    if [int(row["rank"]) for row in rows] != sorted(seen_ranks):
        raise DataQualityError(f"{path.name} 순위가 오름차순이 아닙니다")
    return rows


def _simple_total(rows: list[dict[str, object]]) -> dict[str, object]:
    clicks = sum(int(row["clicks"]) for row in rows)
    impressions = sum(int(row["impressions"]) for row in rows)
    return {
        "clicks": clicks,
        "impressions": impressions,
        "ctr_percent": round(clicks / impressions * 100, 6) if impressions else 0.0,
        "row_count": len(rows),
    }


def _brand_segments(query_rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    brand: list[dict[str, object]] = []
    nonbrand: list[dict[str, object]] = []
    for row in query_rows:
        normalized = " ".join(str(row["key"]).lower().split())
        target = brand if any(term in normalized for term in BRAND_TERMS) else nonbrand
        target.append(row)
    segments = {
        "known_brand": _total(brand),
        "known_nonbrand": _total(nonbrand),
        "unclassified_or_unreported": {
            "status": "not_quantifiable_from_export",
            "reason": "익명 검색어와 상위 1,000행 밖 검색어는 원본 표에 없습니다.",
        },
    }
    return segments


def _naver_path_groups(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"clicks": 0, "impressions": 0, "url_count": 0})
    for row in rows:
        url = str(row["url"])
        path = _validate_site_url(url, "네이버 웹문서")
        grouped[path]["clicks"] += int(row["clicks"])
        grouped[path]["impressions"] += int(row["impressions"])
        grouped[path]["url_count"] += 1
    result = []
    for path, metric in grouped.items():
        impressions = metric["impressions"]
        result.append(
            {
                "path": path,
                **metric,
                "ctr_percent": round(metric["clicks"] / impressions * 100, 6) if impressions else 0.0,
            }
        )
    return sorted(result, key=lambda row: (-int(row["impressions"]), str(row["path"])))


def build_baseline(data_dir: Path) -> dict[str, object]:
    data_dir = Path(data_dir)
    candidates = sorted(data_dir.glob("google_*-Performance-on-Search-2026-08-12"))
    if len(candidates) != 1:
        raise DataQualityError(f"GSC 성과 폴더는 정확히 하나여야 합니다: {len(candidates)}개 발견")
    gsc = candidates[0]
    chart_rows = _metric_rows(gsc / "차트.csv", "날짜")
    _validate_date_series(chart_rows, "차트.csv")
    page_rows = _metric_rows(gsc / "페이지.csv", "인기 페이지")
    for row in page_rows:
        _validate_site_url(str(row["key"]), "페이지.csv", allow_www=True)
    www_page_rows = [row for row in page_rows if urlsplit(str(row["key"])).netloc == f"www.{SITE_HOST}"]
    query_rows = _metric_rows(gsc / "검색어 수.csv", "인기 검색어")
    device_rows = _metric_rows(gsc / "기기.csv", "기기")
    country_rows = _metric_rows(gsc / "국가.csv", "국가")

    property_total = _total(chart_rows)
    property_total.update({"start_date": chart_rows[0]["key"], "end_date": chart_rows[-1]["key"], "grain": "property/day"})
    device_total = _total(device_rows)
    country_total = _total(country_rows)
    for label, total in (("기기", device_total), ("국가", country_total)):
        if (total["clicks"], total["impressions"]) != (property_total["clicks"], property_total["impressions"]):
            raise DataQualityError(f"GSC {label} 합계가 property 일별 합계와 일치하지 않습니다")

    naver_daily_rows, naver_total = _load_naver_daily(data_dir / "naver_export_chart.csv", date.fromisoformat(AS_OF_DATE))
    naver_queries = _load_naver_table(data_dir / "naver_top30_2026-08-12.csv", "검색 키워드")
    naver_web = _load_naver_table(data_dir / "naver_web_documents_top30_2026-08-12.csv", "URL")
    for row in naver_web:
        row["url"] = row.pop("url")
        _validate_site_url(str(row["url"]), "naver_web_documents_top30_2026-08-12.csv")

    page_total = _total(page_rows)
    query_total = _total(query_rows)
    result = {
        "schema_version": 1,
        "generated_for": AS_OF_DATE,
        "change_date": CHANGE_DATE,
        "source_files": {
            "google": str(gsc),
            "naver_daily": str(data_dir / "naver_export_chart.csv"),
            "naver_queries": str(data_dir / "naver_top30_2026-08-12.csv"),
            "naver_web_documents": str(data_dir / "naver_web_documents_top30_2026-08-12.csv"),
        },
        "google": {
            "property_total": property_total,
            "page_table": {
                "grain": "canonical_page",
                "total": page_total,
                "comparison_to_property": "expected_aggregation_difference",
                "purpose": "URL 우선순위와 페이지별 CTR 비교",
                "rows": page_rows,
            },
            "query_table": {
                "grain": "reported_query",
                "total": query_total,
                "coverage": "partial_top_rows",
                "purpose": "검색 의도 탐색용이며 전체 KPI 합계로 사용하지 않음",
                "segments": _brand_segments(query_rows),
            },
            "devices": {"total": device_total, "rows": device_rows, "query_device_cross_dimension": "not_available"},
            "countries": {"total": country_total, "rows": country_rows},
        },
        "naver": {
            "property_total": naver_total,
            "daily_rows": naver_daily_rows,
            "query_top30": {"coverage": "top_30_partial", "total": _simple_total(naver_queries), "rows": naver_queries},
            "web_documents": {
                "coverage": "top_30_partial",
                "total": _simple_total(naver_web),
                "rows": naver_web,
                "path_groups": _naver_path_groups(naver_web),
            },
        },
        "historical_summary": {
            "source": "user_provided_summary_without_date_range_or_raw_export",
            "clicks": 139,
            "impressions": 12608,
            "ctr_percent": 1.1,
            "average_position": 8.1,
            "allowed_use": "context_only",
        },
        "observation_schedule": {
            "change_date_excluded": CHANGE_DATE,
            "day_14": {"before": "2026-07-28~2026-08-10", "after": "2026-08-12~2026-08-25", "collect_on_or_after": "2026-08-28"},
            "day_28": {"before": "2026-07-14~2026-08-10", "after": "2026-08-12~2026-09-08", "collect_on_or_after": "2026-09-11"},
            "filters": {"search_type": "웹", "property": SITE_HOST, "country_and_device": "비교 양쪽에 동일 적용"},
        },
        "quality": {
            "status": "fit_for_baseline_with_documented_partial_tables",
            "google_device_matches_property": True,
            "google_country_matches_property": True,
            "google_page_difference_severity": "low_expected",
            "google_noncanonical_www_page_rows": len(www_page_rows),
            "google_noncanonical_www_page_severity": "medium_for_url_normalization" if www_page_rows else "none",
            "google_query_coverage_severity": "medium_for_query_share_analysis",
            "naver_top30_coverage_severity": "medium_partial",
        },
    }
    return result


def _metric_text(metric: dict[str, object], *, position: bool = False) -> str:
    text = f"클릭 {int(metric['clicks']):,}, 노출 {int(metric['impressions']):,}, CTR {float(metric['ctr_percent']):.3f}%"
    if position:
        text += f", 평균순위 {float(metric['average_position']):.2f}"
    return text


def render_markdown(data: dict[str, object]) -> str:
    google = data["google"]
    naver = data["naver"]
    property_total = google["property_total"]
    lines = [
        "# P0-5 검색 성과 기준선 (2026-08-12)",
        "",
        "## 데이터와 grain 요약",
        "",
        f"- Google 전체(property/day): {property_total['start_date']}~{property_total['end_date']}, {_metric_text(property_total, position=True)}",
        f"- Google 페이지(canonical page): {_metric_text(google['page_table']['total'], position=True)}. URL 우선순위에만 사용합니다.",
        f"- Google 검색어(보고된 상위 행): {_metric_text(google['query_table']['total'], position=True)}. 익명 검색어와 1,000행 밖 검색어가 없어 전체 KPI로 사용하지 않습니다.",
        f"- 네이버 전체(property/day): {naver['property_total']['start_date']}~{naver['property_total']['end_date']}, {_metric_text(naver['property_total'])}",
        f"- 네이버 검색어 TOP 30: {_metric_text(naver['query_top30']['total'])}",
        f"- 네이버 웹문서 TOP 30: {_metric_text(naver['web_documents']['total'])}",
        "",
        "## 품질 판정",
        "",
        "| 발견 | 증거 | 영향 | 심각도·신뢰도 | 처리 |",
        "|---|---|---|---|---|",
        f"| Google property와 페이지 합계 차이 | property 노출 {property_total['impressions']:,}, 페이지 노출 {google['page_table']['total']['impressions']:,} | 전체 KPI와 URL 합계를 직접 비교하면 오해 가능 | 낮음·높음 | 전체는 일별 차트, URL은 페이지 표 사용 |",
        f"| Google 검색어 부분집합 | {google['query_table']['total']['row_count']:,}행, 노출 {google['query_table']['total']['impressions']:,} | 브랜드 비중과 전체 검색어 점유율 산출 불가 | 중간·높음 | 알려진 행만 분류하고 미보고분은 미분류 |",
        f"| 네이버 TOP 30 부분집합 | 웹문서 노출 {naver['web_documents']['total']['impressions']:,} / 전체 {naver['property_total']['impressions']:,} | 전체와 TOP 30을 동일 grain으로 오인 가능 | 중간·높음 | 원 URL과 경로 그룹을 함께 보존 |",
        f"| Google 비정규 `www` 호스트 | 페이지 표 {data['quality']['google_noncanonical_www_page_rows']}행 | 대표 호스트 신호 점검 필요 | 중간·높음 | P0-1 URL 정규화 감사로 이관 |",
        "",
        "Google의 공식 설명에 따라 property 차트와 page 표는 집계 방식이 다르며, 검색어 표에는 익명 검색어 및 행 제한이 적용됩니다:",
        "[집계 방식](https://support.google.com/webmasters/answer/17011364?hl=en), [데이터 차이](https://support.google.com/webmasters/answer/17010575?hl=en).",
        "",
        "## Google 기기 기준선",
        "",
        "| 기기 | 클릭 | 노출 | CTR | 평균순위 |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in google["devices"]["rows"]:
        lines.append(f"| {row['key']} | {row['clicks']:,} | {row['impressions']:,} | {row['ctr_percent']:.3f}% | {row['position']:.2f} |")
    lines.extend(["", "검색어×기기 교차 원본은 없으므로 해당 분해는 `not_available`입니다.", "", "## Google 페이지 우선순위", "", "| URL | 클릭 | 노출 | CTR | 평균순위 |", "|---|---:|---:|---:|---:|"])
    for row in google["page_table"]["rows"][:20]:
        lines.append(f"| {row['key']} | {row['clicks']:,} | {row['impressions']:,} | {row['ctr_percent']:.3f}% | {row['position']:.2f} |")
    lines.extend(["", "## 네이버 웹문서 canonical 경로 그룹", "", "쿼리 URL 원본은 JSON에 그대로 보존하고 아래 표만 경로 단위로 합산합니다.", "", "| 경로 | URL 수 | 클릭 | 노출 | CTR |", "|---|---:|---:|---:|---:|"])
    for row in naver["web_documents"]["path_groups"]:
        lines.append(f"| `{row['path']}` | {row['url_count']} | {row['clicks']:,} | {row['impressions']:,} | {row['ctr_percent']:.3f}% |")
    schedule = data["observation_schedule"]
    lines.extend(
        [
            "",
            "## 변경 전후 관찰 일정",
            "",
            f"- 변경일 `{schedule['change_date_excluded']}`은 양쪽 기간에서 제외합니다.",
            f"- 14일: 변경 전 {schedule['day_14']['before']}, 변경 후 {schedule['day_14']['after']}, {schedule['day_14']['collect_on_or_after']} 이후 수집",
            f"- 28일: 변경 전 {schedule['day_28']['before']}, 변경 후 {schedule['day_28']['after']}, {schedule['day_28']['collect_on_or_after']} 이후 수집",
            "- 검색 유형은 `웹`으로 고정하고 국가·기기 필터는 비교 양쪽에 동일하게 적용합니다.",
            "- 관찰 일정은 P0-5 완료를 막지 않으며, 실제 수집 시 별도 기록으로 추가합니다.",
            "",
            "## 가정과 사용 제한",
            "",
            "- 직전 3개월 요약값(클릭 139, 노출 12,608, CTR 1.1%, 평균순위 8.1)은 날짜와 원본이 없어 맥락 설명에만 사용합니다.",
            "- Google 페이지 표는 대부분 canonical URL로 집계되지만 URL Inspection 판정 자체를 대신하지 않습니다.",
            "- 이 기준선은 검색 성과 비교용이며 Search Console·네이버 서치어드바이저 설정을 변경하지 않습니다.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(data: dict[str, object], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "baseline-2026-08-12.json"
    markdown_path = output_dir / "baseline-2026-08-12.md"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(data), encoding="utf-8")
    return markdown_path, json_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("_data"))
    parser.add_argument("--output-dir", type=Path, default=Path("_workspace/p0-5-performance-baseline"))
    args = parser.parse_args()
    try:
        data = build_baseline(args.data_dir)
        markdown_path, json_path = write_outputs(data, args.output_dir)
    except DataQualityError as exc:
        parser.error(str(exc))
    print(f"wrote {markdown_path}")
    print(f"wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
