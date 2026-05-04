#!/usr/bin/env python3
"""Preflight checks for the AdSense re-review state.

The checks intentionally avoid live network calls. They validate the local Flask
routes, dynamic sitemap, robots.txt, and ads.txt that will be deployed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

FORBIDDEN_SITEMAP_PREFIXES = ("/minigames", "/blog/drafts", "/blog/review")


@dataclass
class PreflightIssue:
    code: str
    target: str
    message: str


@dataclass
class PreflightReport:
    checked_pages: int = 0
    sitemap_urls: int = 0
    issues: list[PreflightIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def add_issue(self, code: str, target: str, message: str) -> None:
        self.issues.append(PreflightIssue(code=code, target=target, message=message))


def _extract_sitemap_locations(sitemap_xml: str) -> list[str]:
    return [unescape(match.strip()) for match in re.findall(r"<loc>(.*?)</loc>", sitemap_xml, re.S)]


def _sitemap_location_to_path(location: str, site_base_url: str, report: PreflightReport) -> str | None:
    expected = urlparse(site_base_url)
    parsed = urlparse(location)
    if parsed.scheme != expected.scheme or parsed.netloc != expected.netloc:
        report.add_issue("external_sitemap_url", location, "사이트맵 URL이 운영 도메인과 일치하지 않습니다.")
        return None
    if parsed.query or parsed.fragment:
        report.add_issue("noncanonical_sitemap_url", location, "사이트맵 URL에는 쿼리나 fragment를 넣지 않습니다.")
        return None
    return parsed.path or "/"


def validate_sitemap_paths(paths: list[str], report: PreflightReport) -> None:
    for path in paths:
        for prefix in FORBIDDEN_SITEMAP_PREFIXES:
            if path == prefix or path.startswith(f"{prefix}/"):
                report.add_issue("forbidden_sitemap_path", path, "승인 전 사이트맵에 노출하지 않을 경로입니다.")


def _has_noindex(response, html: str) -> bool:
    robots_header = (response.headers.get("X-Robots-Tag") or "").lower()
    html_lower = html.lower()
    return "noindex" in robots_header or 'name="robots" content="noindex' in html_lower


def _validate_public_page(path: str, response, html: str, adsense_client_id: str, report: PreflightReport) -> None:
    if response.status_code != 200:
        report.add_issue("page_not_200", path, f"공개 사이트맵 URL 응답이 {response.status_code}입니다.")
        return

    if _has_noindex(response, html):
        report.add_issue("public_page_noindex", path, "사이트맵에 포함된 공개 페이지가 noindex 상태입니다.")

    adsense_account = f'<meta name="google-adsense-account" content="{adsense_client_id}">'
    adsense_script = f"pagead/js/adsbygoogle.js?client={adsense_client_id}"
    if adsense_account not in html or adsense_script not in html:
        report.add_issue("adsense_code_missing", path, "공개 페이지에 애드센스 승인 코드가 없습니다.")

    if not re.search(r"<title>.+?</title>", html, re.S):
        report.add_issue("title_missing", path, "공개 페이지에 title이 없습니다.")
    if not re.search(r'<meta name="description" content="[^"]{30,}"', html):
        report.add_issue("description_missing", path, "공개 페이지의 meta description이 없거나 너무 짧습니다.")
    if not re.search(r"<h1[^>]*>.+?</h1>", html, re.S):
        report.add_issue("h1_missing", path, "공개 페이지에 h1이 없습니다.")


def _validate_robots_txt(robots_path: Path, site_base_url: str, report: PreflightReport) -> None:
    if not robots_path.exists():
        report.add_issue("robots_missing", str(robots_path), "robots.txt 파일이 없습니다.")
        return

    body = robots_path.read_text(encoding="utf-8")
    required_snippets = [
        "User-agent: Mediapartners-Google",
        "User-agent: Google-Display-Ads-Bot",
        "Allow: /ads.txt",
        f"Sitemap: {site_base_url}/sitemap.xml",
    ]
    for snippet in required_snippets:
        if snippet not in body:
            report.add_issue("robots_rule_missing", str(robots_path), f"robots.txt에 필요한 항목이 없습니다: {snippet}")


def _validate_ads_txt(ads_path: Path, adsense_client_id: str, report: PreflightReport) -> None:
    if not ads_path.exists():
        report.add_issue("ads_txt_missing", str(ads_path), "ads.txt 파일이 없습니다.")
        return

    publisher_id = adsense_client_id.removeprefix("ca-")
    body = ads_path.read_text(encoding="utf-8")
    if f"google.com, {publisher_id}, DIRECT" not in body:
        report.add_issue("ads_txt_publisher_missing", str(ads_path), "ads.txt에 현재 애드센스 publisher ID가 없습니다.")


def run_local_preflight() -> PreflightReport:
    from app import ADSENSE_CLIENT_ID, SITE_BASE_URL, app

    report = PreflightReport()
    client = app.test_client()

    sitemap_response = client.get("/sitemap.xml")
    if sitemap_response.status_code != 200:
        report.add_issue("sitemap_not_200", "/sitemap.xml", f"사이트맵 응답이 {sitemap_response.status_code}입니다.")
        return report

    sitemap_body = sitemap_response.get_data(as_text=True)
    locations = _extract_sitemap_locations(sitemap_body)
    report.sitemap_urls = len(locations)
    if not locations:
        report.add_issue("sitemap_empty", "/sitemap.xml", "사이트맵에 공개 URL이 없습니다.")

    paths = [
        path
        for location in locations
        if (path := _sitemap_location_to_path(location, SITE_BASE_URL, report)) is not None
    ]
    validate_sitemap_paths(paths, report)

    for path in paths:
        response = client.get(path)
        html = response.get_data(as_text=True)
        _validate_public_page(path, response, html, ADSENSE_CLIENT_ID, report)
        report.checked_pages += 1

    _validate_robots_txt(PROJECT_ROOT / "static" / "robots.txt", SITE_BASE_URL, report)
    _validate_ads_txt(PROJECT_ROOT / "static" / "ads.txt", ADSENSE_CLIENT_ID, report)
    return report


def format_report(report: PreflightReport) -> str:
    status = "PASS" if report.ok else "FAIL"
    lines = [
        f"[adsense-preflight] {status} checked_pages={report.checked_pages} sitemap_urls={report.sitemap_urls}",
    ]
    for issue in report.issues:
        lines.append(f"- {issue.code}: {issue.target} - {issue.message}")
    return "\n".join(lines)


def _report_to_json(report: PreflightReport) -> str:
    payload = {
        "ok": report.ok,
        "checked_pages": report.checked_pages,
        "sitemap_urls": report.sitemap_urls,
        "issues": [issue.__dict__ for issue in report.issues],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run AdSense approval preflight checks against the local Flask app.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    args = parser.parse_args(argv)

    report = run_local_preflight()
    print(_report_to_json(report) if args.format == "json" else format_report(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
