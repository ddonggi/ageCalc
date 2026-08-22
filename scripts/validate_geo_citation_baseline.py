#!/usr/bin/env python3
"""Build and validate AgeCalc GEO citation observation sheets."""

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


FIELDNAMES = (
    "measurement_date",
    "query_set_version",
    "query_id",
    "query_text",
    "platform",
    "surface",
    "country",
    "language",
    "device",
    "session_state",
    "platform_model",
    "web_search_enabled",
    "observation_status",
    "brand_mentioned",
    "agecalc_url_cited",
    "agecalc_cited_urls",
    "citation_positions",
    "citation_context",
    "sentiment",
    "all_cited_domains",
    "citation_link_available",
    "downstream_clicks",
    "evidence_file",
    "evidence_sha256",
    "notes",
)

OBSERVATION_STATUSES = {
    "pending",
    "observed",
    "surface_not_present",
    "technical_failure",
}
BOOLEAN_VALUES = {"pending", "true", "false", "not_applicable"}
CITATION_CONTEXTS = {
    "pending",
    "direct_answer",
    "supporting_source",
    "related_link",
    "mixed",
    "not_applicable",
}
SENTIMENTS = {"pending", "positive", "neutral", "negative", "not_applicable"}


def build_observation_rows(catalog: dict[str, Any]) -> list[dict[str, str]]:
    defaults = catalog["measurement_defaults"]
    rows: list[dict[str, str]] = []
    for query in catalog["queries"]:
        for platform in catalog["platforms"]:
            rows.append(
                {
                    "measurement_date": "",
                    "query_set_version": catalog["version"],
                    "query_id": query["id"],
                    "query_text": query["text"],
                    "platform": platform["id"],
                    "surface": platform["surface"],
                    "country": defaults["country"],
                    "language": defaults["language"],
                    "device": defaults["device"],
                    "session_state": platform["session_state"],
                    "platform_model": "",
                    "web_search_enabled": platform["web_search_enabled"],
                    "observation_status": "pending",
                    "brand_mentioned": "pending",
                    "agecalc_url_cited": "pending",
                    "agecalc_cited_urls": "",
                    "citation_positions": "",
                    "citation_context": "pending",
                    "sentiment": "pending",
                    "all_cited_domains": "",
                    "citation_link_available": "pending",
                    "downstream_clicks": "not_available",
                    "evidence_file": "",
                    "evidence_sha256": "",
                    "notes": "",
                }
            )
    return rows


def validate_observations(
    catalog: dict[str, Any],
    rows: Iterable[dict[str, str]],
    *,
    require_complete: bool = False,
) -> tuple[str, ...]:
    rows = list(rows)
    errors: list[str] = []
    platforms = {item["id"]: item for item in catalog["platforms"]}
    queries = {item["id"]: item for item in catalog["queries"]}
    defaults = catalog["measurement_defaults"]
    expected = {(query_id, platform_id) for query_id in queries for platform_id in platforms}
    actual_pairs: list[tuple[str, str]] = []

    for number, row in enumerate(rows, start=2):
        prefix = f"row {number}"
        missing_fields = set(FIELDNAMES) - set(row)
        if missing_fields:
            errors.append(f"{prefix}: missing fields {sorted(missing_fields)}")
            continue

        query_id = row["query_id"]
        platform_id = row["platform"]
        actual_pairs.append((query_id, platform_id))
        if query_id not in queries:
            errors.append(f"{prefix}: unknown query {query_id}")
        if platform_id not in platforms:
            errors.append(f"{prefix}: unknown platform {platform_id}")
        if query_id in queries and row["query_text"] != queries[query_id]["text"]:
            errors.append(f"{prefix}: query text differs from catalog")
        if row["query_set_version"] != catalog["version"]:
            errors.append(f"{prefix}: query set version differs from catalog")
        for field in ("country", "language", "device"):
            if row[field] != defaults[field]:
                errors.append(f"{prefix}: {field} differs from catalog")
        if platform_id in platforms:
            for field in ("surface", "session_state", "web_search_enabled"):
                if row[field] != platforms[platform_id][field]:
                    errors.append(f"{prefix}: {field} differs from catalog")

        status = row["observation_status"]
        if status not in OBSERVATION_STATUSES:
            errors.append(f"{prefix}: invalid observation_status {status}")
            continue
        for field in ("brand_mentioned", "agecalc_url_cited", "citation_link_available"):
            if row[field] not in BOOLEAN_VALUES:
                errors.append(f"{prefix}: invalid {field} {row[field]}")
        if row["citation_context"] not in CITATION_CONTEXTS:
            errors.append(f"{prefix}: invalid citation_context {row['citation_context']}")
        if row["sentiment"] not in SENTIMENTS:
            errors.append(f"{prefix}: invalid sentiment {row['sentiment']}")

        if status == "observed":
            _validate_observed_row(row, prefix, errors)
        elif status == "surface_not_present":
            _validate_unavailable_row(row, prefix, errors)

    duplicate_pairs = sorted(pair for pair, count in Counter(actual_pairs).items() if count > 1)
    if duplicate_pairs:
        errors.append(f"duplicate combination: {duplicate_pairs}")
    missing_pairs = sorted(expected - set(actual_pairs))
    if missing_pairs:
        errors.append(f"missing combinations: {missing_pairs}")
    unexpected_pairs = sorted(set(actual_pairs) - expected)
    if unexpected_pairs:
        errors.append(f"unexpected combinations: {unexpected_pairs}")

    if require_complete:
        incomplete_count = sum(
            row.get("observation_status") in {"pending", "technical_failure"} for row in rows
        )
        if incomplete_count:
            errors.append(f"pending observations: {incomplete_count}")
        measurement_dates = {
            row.get("measurement_date")
            for row in rows
            if row.get("observation_status") in {"observed", "surface_not_present"}
        }
        if len(measurement_dates) != 1:
            errors.append("complete run requires one measurement_date")

    return tuple(errors)


def _validate_observed_row(row: dict[str, str], prefix: str, errors: list[str]) -> None:
    if not row["measurement_date"]:
        errors.append(f"{prefix}: observed row requires measurement_date")
    elif not _is_iso_date(row["measurement_date"]):
        errors.append(f"{prefix}: measurement_date must use YYYY-MM-DD")
    if not row["platform_model"]:
        errors.append(f"{prefix}: observed row requires platform_model")
    for field in ("brand_mentioned", "agecalc_url_cited", "citation_link_available"):
        if row[field] not in {"true", "false"}:
            errors.append(f"{prefix}: observed row requires boolean {field}")

    if row["brand_mentioned"] == "false" and row["sentiment"] != "not_applicable":
        errors.append(f"{prefix}: sentiment must be not_applicable without brand mention")
    if row["brand_mentioned"] == "true" and row["sentiment"] not in {
        "positive",
        "neutral",
        "negative",
    }:
        errors.append(f"{prefix}: brand mention requires sentiment")

    cited = row["agecalc_url_cited"] == "true"
    urls = _split_values(row["agecalc_cited_urls"])
    has_agecalc_url = bool(urls) and all(_is_agecalc_url(url) for url in urls)
    if cited and not has_agecalc_url:
        errors.append(f"{prefix}: citation requires an https agecalc.cloud URL")
    if not cited and urls:
        errors.append(f"{prefix}: uncited row must not contain AgeCalc URLs")
    if cited and row["citation_context"] not in {
        "direct_answer",
        "supporting_source",
        "related_link",
        "mixed",
    }:
        errors.append(f"{prefix}: citation requires citation_context")
    if not cited and row["citation_context"] != "not_applicable":
        errors.append(f"{prefix}: citation_context must be not_applicable without citation")
    if cited and not row["citation_positions"]:
        errors.append(f"{prefix}: citation requires citation_positions")
    positions = _split_values(row["citation_positions"])
    if positions and (
        len(positions) != len(urls)
        or any(not position.isdigit() or int(position) < 1 for position in positions)
    ):
        errors.append(f"{prefix}: citation_positions must match URLs and use positive integers")

    cited_domains = {
        domain.lower().removeprefix("www.")
        for domain in _split_values(row["all_cited_domains"])
    }
    if cited and "agecalc.cloud" not in cited_domains:
        errors.append(f"{prefix}: all_cited_domains must include agecalc.cloud")
    if not cited and row["citation_link_available"] == "true":
        errors.append(f"{prefix}: link cannot exist without citation")

    _validate_evidence(row, prefix, errors, "observed row")
    if row["downstream_clicks"] != "not_available":
        errors.append(f"{prefix}: downstream_clicks must remain not_available without GA4 data")


def _validate_unavailable_row(row: dict[str, str], prefix: str, errors: list[str]) -> None:
    if not _is_iso_date(row["measurement_date"]):
        errors.append(f"{prefix}: unavailable surface requires YYYY-MM-DD measurement_date")
    for field in ("brand_mentioned", "agecalc_url_cited", "citation_link_available"):
        if row[field] != "not_applicable":
            errors.append(f"{prefix}: unavailable surface requires not_applicable {field}")
    for field in ("citation_context", "sentiment"):
        if row[field] != "not_applicable":
            errors.append(f"{prefix}: unavailable surface requires not_applicable {field}")
    _validate_evidence(row, prefix, errors, "unavailable surface")


def _validate_evidence(
    row: dict[str, str], prefix: str, errors: list[str], subject: str
) -> None:
    files = _split_values(row["evidence_file"])
    checksums = _split_values(row["evidence_sha256"])
    if not files:
        errors.append(f"{prefix}: {subject} requires evidence_file")
    if not checksums or any(not _is_sha256(checksum) for checksum in checksums):
        errors.append(f"{prefix}: {subject} requires SHA-256 evidence checksums")
    if files and checksums and len(files) != len(checksums):
        errors.append(f"{prefix}: evidence files and checksums must have matching counts")


def summarize_observations(rows: Iterable[dict[str, str]]) -> dict[str, Any]:
    rows = list(rows)
    observed = [row for row in rows if row["observation_status"] == "observed"]
    citations = sum(row["agecalc_url_cited"] == "true" for row in observed)
    mentions = sum(row["brand_mentioned"] == "true" for row in observed)
    all_domains = [
        domain.lower().removeprefix("www.")
        for row in observed
        for domain in _split_values(row["all_cited_domains"])
    ]
    agecalc_citations = sum(domain == "agecalc.cloud" for domain in all_domains)
    sentiment = {key: 0 for key in ("positive", "neutral", "negative")}
    for row in observed:
        if row["brand_mentioned"] == "true" and row["sentiment"] in sentiment:
            sentiment[row["sentiment"]] += 1

    denominator = len(observed)
    return {
        "total_rows": len(rows),
        "valid_observations": denominator,
        "surface_not_present": sum(
            row["observation_status"] == "surface_not_present" for row in rows
        ),
        "technical_failures": sum(
            row["observation_status"] == "technical_failure" for row in rows
        ),
        "citation_rate": citations / denominator if denominator else None,
        "brand_mention_rate": mentions / denominator if denominator else None,
        "citation_share": agecalc_citations / len(all_domains) if all_domains else None,
        "sentiment": sentiment,
        "downstream_clicks": "not_available",
    }


def _split_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def _is_agecalc_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname in {"agecalc.cloud", "www.agecalc.cloud"}


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return len(value) == 10


def write_template(catalog: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(build_observation_rows(catalog))


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    default_dir = root / "_workspace" / "p2-7-geo-citation"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=default_dir / "prompt-catalog.json")
    parser.add_argument("--observations", type=Path, default=default_dir / "observation-template.csv")
    parser.add_argument("--write-template", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    if args.write_template:
        write_template(catalog, args.observations)
        print(f"wrote: {args.observations}")
        return 0

    rows = _load_rows(args.observations)
    errors = validate_observations(catalog, rows, require_complete=args.require_complete)
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print(f"valid: {args.observations} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
