import json
import unittest

from scripts.content_quality_audit import (
    ContentQualityReport,
    audit_html,
    audit_local_pages,
    format_json,
    format_text,
)


RICH_HTML = """
<!doctype html>
<html lang="ko">
<head>
  <title>고유한 나이 계산 안내</title>
  <meta name="description" content="생년월일을 기준으로 나이를 계산하고 예외와 다음 행동을 자세히 설명합니다.">
  <link rel="canonical" href="https://agecalc.cloud/example">
</head>
<body>
  <h1>고유한 나이 계산 안내</h1>
  <p class="direct-answer">생일이 지났으면 기준연도에서 출생연도를 뺀 값이 현재 만나이입니다.</p>
  <h2>계산 공식</h2><p>기준연도와 출생연도, 생일 전후를 순서대로 비교합니다.</p>
  <h2>실제 사례</h2><p>서로 다른 날짜 사례를 통해 결과가 달라지는 이유를 확인합니다.</p>
  <h2>예외와 다음 행동</h2><p>윤년과 공식 제출 상황에서는 기관 기준일도 함께 확인합니다.</p>
  <aside class="related-paths"><a href="/age">관련 도구</a></aside>
  <aside class="editorial-meta">
    <li data-official-source="true"><a href="https://example.go.kr">공식 출처</a></li>
    <p class="editorial-disclaimer">공식 판단이나 진단을 대신하지 않습니다.</p>
  </aside>
</body>
</html>
"""


class ContentQualityAuditTests(unittest.TestCase):
    def test_audit_html_requires_core_editorial_elements(self):
        html = """
        <html><head><title>짧은 페이지</title></head>
        <body><h1>짧은 페이지</h1><h2>한 개 섹션</h2><p>설명</p></body></html>
        """

        result = audit_html("/thin", html, ymyl=False)
        codes = {issue.code for issue in result.issues}

        self.assertIn("canonical_missing", codes)
        self.assertIn("description_missing", codes)
        self.assertIn("direct_answer_missing", codes)
        self.assertIn("insufficient_h2", codes)
        self.assertIn("editorial_meta_missing", codes)
        self.assertIn("related_paths_missing", codes)
        self.assertIn("thin_content_warning", codes)
        self.assertFalse(result.passed)

    def test_audit_html_requires_official_source_and_disclaimer_for_ymyl(self):
        html = RICH_HTML.replace('data-official-source="true"', 'data-official-source="false"').replace(
            '<p class="editorial-disclaimer">공식 판단이나 진단을 대신하지 않습니다.</p>',
            "",
        )

        result = audit_html("/ymyl", html, ymyl=True)
        codes = {issue.code for issue in result.issues}

        self.assertIn("official_source_missing", codes)
        self.assertIn("ymyl_disclaimer_missing", codes)
        self.assertFalse(result.passed)

    def test_thin_content_is_warning_only(self):
        result = audit_html("/rich-structure", RICH_HTML, ymyl=True)

        self.assertTrue(result.passed)
        self.assertIn(
            "thin_content_warning",
            {issue.code for issue in result.warnings},
        )

    def test_report_detects_duplicate_metadata_and_repeated_sentences(self):
        report = ContentQualityReport()
        report.add(audit_html("/one", RICH_HTML, ymyl=True))
        report.add(audit_html("/two", RICH_HTML, ymyl=True))
        report.detect_duplicates()

        warning_codes = {
            issue.code
            for result in report.results
            for issue in result.warnings
        }
        self.assertIn("duplicate_title_warning", warning_codes)
        self.assertIn("duplicate_description_warning", warning_codes)
        self.assertIn("duplicate_h1_warning", warning_codes)
        self.assertIn("repeated_sentence_warning", warning_codes)

    def test_text_and_json_formats_include_summary_and_issues(self):
        report = ContentQualityReport()
        report.add(audit_html("/thin", "<h1>얇은 페이지</h1>", ymyl=False))

        text = format_text(report)
        payload = json.loads(format_json(report))

        self.assertIn("[content-quality]", text)
        self.assertIn("direct_answer_missing", text)
        self.assertEqual(1, payload["checked_pages"])
        self.assertFalse(payload["ok"])

    def test_local_audit_can_filter_paths_and_hubs(self):
        path_report = audit_local_pages(paths=("/age",))
        hub_report = audit_local_pages(hub="age")

        self.assertEqual(["/age"], [result.path for result in path_report.results])
        self.assertGreaterEqual(len(hub_report.results), 5)
        self.assertTrue(all(result.hub == "age" for result in hub_report.results))


if __name__ == "__main__":
    unittest.main()
