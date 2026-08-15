#!/usr/bin/env python3
"""Validate the owned-data metric catalog without external dependencies."""

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_SOURCES = {"ga4", "page_feedback_db"}
EXPECTED_EXCLUDED_SOURCES = {"server_logs", "clarity", "blog_rss_db"}
EXPECTED_GATE = {
    "minimum_denominator": 100,
    "minimum_coverage_days": 28,
    "minimum_cell_count": 20,
}
EXPECTED_RETENTION = {
    "monthly_aggregates": 14,
    "page_feedback_raw": 12,
}


def validate_catalog(catalog: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    approved_sources = set(catalog.get("approved_sources", []))
    excluded_sources = set(catalog.get("excluded_sources", {}))

    if approved_sources != EXPECTED_SOURCES:
        errors.append(f"approved_sources must be {sorted(EXPECTED_SOURCES)}")
    if excluded_sources != EXPECTED_EXCLUDED_SOURCES:
        errors.append(
            f"excluded_sources must be {sorted(EXPECTED_EXCLUDED_SOURCES)}"
        )

    for field, expected in EXPECTED_GATE.items():
        actual = catalog.get("publication_gate", {}).get(field)
        if actual != expected:
            errors.append(f"publication_gate.{field} must be {expected}")

    for field, expected in EXPECTED_RETENTION.items():
        actual = catalog.get("retention_months", {}).get(field)
        if actual != expected:
            errors.append(f"retention_months.{field} must be {expected}")

    forbidden_fields = set(catalog.get("forbidden_fields", []))
    events = catalog.get("events", [])
    event_names = {event.get("name") for event in events}
    for event in events:
        name = event.get("name", "<unnamed>")
        source = event.get("source")
        if source not in approved_sources:
            errors.append(f"event {name} uses unapproved source {source}")
        if source in excluded_sources:
            errors.append(f"event {name} uses excluded source {source}")
        if event.get("status") == "planned" and (
            source != "ga4" or event.get("consent_required") is not True
        ):
            errors.append(f"planned event {name} must be consented GA4 data")

        exposed_fields = set(event.get("allowed_dimensions", [])) | set(
            event.get("aggregate_fields", [])
        )
        for forbidden in sorted(exposed_fields & forbidden_fields):
            errors.append(f"event {name} exposes forbidden field {forbidden}")

    for metric in catalog.get("public_metrics", []):
        name = metric.get("name", "<unnamed>")
        for key in ("numerator_event", "denominator_event"):
            event_name = metric.get(key)
            if not event_name:
                errors.append(f"public metric {name} requires {key}")
            elif event_name not in event_names:
                errors.append(
                    f"public metric {name} references unknown event {event_name}"
                )
        if not metric.get("formula"):
            errors.append(f"public metric {name} requires formula")
        if not metric.get("unit"):
            errors.append(f"public metric {name} requires unit")
        if not metric.get("bias_disclosure"):
            errors.append(f"public metric {name} requires bias_disclosure")
        if metric.get("publication_gate") != "catalog_default":
            errors.append(f"public metric {name} must use catalog_default gate")

    return tuple(errors)


def main() -> int:
    default_path = (
        Path(__file__).resolve().parents[1]
        / "_workspace"
        / "p2-3-owned-data"
        / "metric-catalog.json"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", nargs="?", type=Path, default=default_path)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    errors = validate_catalog(catalog)
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print(f"valid: {args.catalog}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
