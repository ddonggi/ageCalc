import unittest

from content import editorial_metadata
from content.editorial_metadata import (
    RELATED_SEARCH_TERM_SLOTS,
    editorial_metadata_for,
    validate_editorial_metadata,
)
from content.page_registry import find_page


EXPECTED_NAVER_TOP_30 = (
    "26학번 년생",
    "학년 계산기",
    "22학번 나이",
    "26학번",
    "아이 개월수 계산기",
    "26학번 나이",
    "20학번 나이",
    "20살 몇년생",
    "만나이 폐지",
    "연도별 띠",
    "18학번 나이",
    "중1 몇년생",
    "나이차이 계산",
    "입학년도 계산",
    "19학번 나이",
    "고1 몇년생",
    "나이차이 계산기",
    "2026년 20살 몇년생",
    "09학번 몇살",
    "연나이 계산기",
    "26학번 몇년생",
    "나이차이계산",
    "고3 몇년생",
    "학번 계산기",
    "23학번 년생",
    "27학번",
    "21학번 년생",
    "23학번 나이",
    "21학번 나이",
    "만13세 몇학년",
)

NAVER_RELATED_SEARCH_TERMS = getattr(
    editorial_metadata,
    "NAVER_RELATED_SEARCH_TERMS",
    (),
)


class EditorialMetadataTests(unittest.TestCase):
    def test_editorial_metadata_identifies_internal_review_and_cadence(self):
        page = find_page("age", {})
        metadata = editorial_metadata_for(page)

        self.assertEqual("AgeCalc 편집팀", metadata["author"])
        self.assertEqual("AgeCalc 운영자", metadata["reviewer"])
        self.assertEqual("자체 검수", metadata["review_method"])
        self.assertEqual(
            "매년 1월·7월 및 공식 변경 공지 확인 시",
            metadata["policy_review_cadence"],
        )

    def test_editorial_metadata_validation_rejects_missing_review_disclosure(self):
        page = find_page("age", {})
        metadata = editorial_metadata_for(page)
        metadata.pop("review_method", None)

        self.assertIn(
            "missing review_method",
            validate_editorial_metadata(page, metadata),
        )

    def test_naver_mapping_preserves_every_supplied_top_30_query_once(self):
        self.assertEqual(tuple(range(1, 31)), tuple(row["rank"] for row in NAVER_RELATED_SEARCH_TERMS))
        self.assertEqual(EXPECTED_NAVER_TOP_30, tuple(row["term"] for row in NAVER_RELATED_SEARCH_TERMS))
        self.assertEqual(30, len({row["term"] for row in NAVER_RELATED_SEARCH_TERMS}))

    def test_naver_mapping_uses_registered_pages_and_supported_slots(self):
        for row in NAVER_RELATED_SEARCH_TERMS:
            with self.subTest(term=row["term"]):
                self.assertIn(row["slot"], {"primary", "section", "faq"})
                self.assertIsNotNone(find_page(row["page_key"], {}))
                self.assertIn(row["term"], RELATED_SEARCH_TERM_SLOTS[row["page_key"]][row["slot"]])

    def test_naver_primary_terms_have_one_canonical_owner(self):
        primary_terms = [
            term
            for slots in RELATED_SEARCH_TERM_SLOTS.values()
            for term in slots["primary"]
        ]

        self.assertEqual(len(primary_terms), len(set(primary_terms)))

    def test_editorial_metadata_exposes_the_page_keyword_slots(self):
        page = find_page("college_entry_year_calculator", {})
        metadata = editorial_metadata_for(page)

        self.assertEqual(
            ("학번 계산기",),
            metadata["related_search_term_slots"]["primary"],
        )
        self.assertIn(
            "26학번 년생",
            metadata["related_search_term_slots"]["section"],
        )
        self.assertEqual(
            ("09학번 몇살", "26학번 몇년생"),
            metadata["related_search_term_slots"]["faq"],
        )


if __name__ == "__main__":
    unittest.main()
