from __future__ import annotations

from copy import deepcopy

from content.blog.age_articles import AGE_ARTICLES
from content.blog.birth_year_articles import BIRTH_YEAR_ARTICLES
from content.blog.education_family_articles import EDUCATION_FAMILY_ARTICLES
from content.blog.health_articles import HEALTH_ARTICLES
from content.blog.legacy_articles import BLOG_ARTICLE_BLUEPRINTS as LEGACY_ARTICLES
from content.blog.pet_articles import PET_ARTICLES
from content.blog.policy_benefit_articles import POLICY_BENEFIT_ARTICLES
from content.blog.schema import (
    BLOG_CATEGORIES,
    article_metadata,
    complete_article,
    merge_article_registries,
    validate_article_registry,
)


PRIORITY_ARTICLE_SLUGS = (
    "2026-man-age-guide",
    "man-age-vs-korean-age",
    "2000-birth-year-age",
    "2026-school-entry-birth-year",
    "age-65-benefits-2026",
    "dog-age-calculation-guide",
    "national-pension-receiving-age",
    "2026-national-health-checkup-eligibility",
)


def _source(organization: str, title: str, url: str) -> dict[str, str]:
    return {
        "organization": organization,
        "title": title,
        "url": url,
        "checked_at": "2026-07-21",
    }


LEGACY_ARTICLE_METADATA = {
    "2026-man-age-guide": article_metadata(
        slug="2026-man-age-guide",
        category="age",
        tags=("2026년 만나이", "생일 전후", "민법 제158조"),
        reviewed_at="2026-07-21",
        effective_date="2026-01-01",
        expires_at="2027-01-31",
        sources=[_source("국가법령정보센터", "민법 제158조 나이의 계산과 표시", "https://www.law.go.kr/법령/민법")],
        meta_title="2026년 만나이 계산법과 생일 전후 기준 | AgeCalc",
        meta_description="2026년 현재 만나이를 생일 전후로 계산하는 방법과 출생연도만 알 때의 해석, 공식 기준을 설명합니다.",
        thumbnail_alt="2026년 만나이 계산 기준을 안내하는 AgeCalc 이미지",
    ),
    "birth-year-age-interpretation": article_metadata(
        slug="birth-year-age-interpretation",
        category="birth-year",
        tags=("출생연도", "만나이 범위", "기준일"),
        reviewed_at="2026-07-21",
        effective_date="2026-01-01",
        expires_at="2027-01-31",
        sources=[_source("국가법령정보센터", "민법 제158조 나이의 계산과 표시", "https://www.law.go.kr/법령/민법")],
        meta_title="출생연도만 알 때 만나이 범위를 해석하는 법 | AgeCalc",
        meta_description="생일을 모를 때 출생연도만으로 현재 만나이를 한 값으로 단정하지 않고 범위와 기준일로 확인하는 방법을 설명합니다.",
        thumbnail_alt="출생연도별 만나이 범위를 설명하는 AgeCalc 이미지",
    ),
    "early-birth-school-grade-guide": article_metadata(
        slug="early-birth-school-grade-guide",
        category="education-family",
        tags=("빠른년생", "학년", "입학연도"),
        reviewed_at="2026-07-21",
        effective_date="2026-03-01",
        expires_at="2027-03-01",
        sources=[
            _source("국가법령정보센터", "초·중등교육법 제13조 취학 의무", "https://www.law.go.kr/법령/초·중등교육법"),
            _source("교육부", "초·중등 교육 정책 안내", "https://www.moe.go.kr/"),
        ],
        meta_title="빠른년생의 현재 나이와 학년·입학연도 기준 | AgeCalc",
        meta_description="빠른년생을 공식 만나이와 학교 학년, 입학연도 기준으로 나눠 확인하는 방법을 설명합니다.",
        thumbnail_alt="빠른년생 나이와 학년 기준을 설명하는 AgeCalc 이미지",
    ),
    "baby-months-calculation-guide": article_metadata(
        slug="baby-months-calculation-guide",
        category="education-family",
        tags=("아이 개월 수", "월령", "백일"),
        reviewed_at="2026-07-21",
        effective_date="2026-07-21",
        expires_at="2027-07-21",
        sources=[_source("국민건강보험공단", "영유아 건강검진 안내", "https://www.nhis.or.kr/")],
        meta_title="아이 개월 수 계산과 월령 해석 기준 | AgeCalc",
        meta_description="출생일 기준 아이 개월 수와 생후 일수, 백일·첫돌 같은 기념 시점을 구분해 확인하는 방법을 설명합니다.",
        thumbnail_alt="아이 개월 수와 월령 계산을 설명하는 AgeCalc 이미지",
    ),
    "parent-child-age-gap-guide": article_metadata(
        slug="parent-child-age-gap-guide",
        category="education-family",
        tags=("부모 자녀", "나이 차이", "가족 일정"),
        reviewed_at="2026-07-21",
        effective_date="2026-07-21",
        expires_at="2027-07-21",
        sources=[_source("국가법령정보센터", "민법 제158조 나이의 계산과 표시", "https://www.law.go.kr/법령/민법")],
        meta_title="부모·자녀 나이 차이와 생일 전후 해석 | AgeCalc",
        meta_description="부모와 자녀의 출생연도 차이와 현재 만나이 차이가 생일 전후에 따라 달라지는 이유를 설명합니다.",
        thumbnail_alt="부모와 자녀의 나이 차이를 설명하는 AgeCalc 이미지",
    ),
}


def _completed_legacy_articles() -> dict[str, dict[str, object]]:
    completed: dict[str, dict[str, object]] = {}
    for slug, article in LEGACY_ARTICLES.items():
        completed[slug] = complete_article(article, LEGACY_ARTICLE_METADATA[slug])
    completed["2026-man-age-guide"]["content_sections"] = [
        {
            "heading": "생년월일과 기준일을 먼저 나란히 둡니다",
            "paragraphs": [
                "만나이 계산에는 태어난 날짜와 나이를 알고 싶은 기준일이 모두 필요합니다. 현재 나이를 묻는 경우에도 서비스가 사용하는 오늘 날짜를 확인해야 해외 체류나 자정 전후처럼 날짜가 달라지는 상황을 설명할 수 있습니다.",
                "기준연도에서 출생연도를 빼는 계산은 시작일 뿐입니다. 기준일의 월일이 출생 월일보다 앞서면 생일 전이므로 한 살을 빼고, 같거나 뒤라면 뺀 값을 그대로 사용합니다.",
            ],
        },
        {
            "heading": "생일 당일부터 새 만나이로 봅니다",
            "paragraphs": [
                "민법 제158조는 출생일을 산입해 만 나이로 계산하도록 규정합니다. 일상 계산에서는 생일 당일이 되면 한 살이 증가한다고 이해할 수 있으며 생일 전날까지는 이전 만나이를 유지합니다.",
                "‘2026년 기준 몇 살’처럼 연도만 제시된 질문에는 생일 전후 두 값을 함께 답하는 것이 정확합니다. 특정 날짜의 단일 값이 필요하면 생년월일과 기준일을 모두 확인합니다.",
            ],
        },
        {
            "heading": "2월 29일과 월말은 실제 달력으로 계산합니다",
            "paragraphs": [
                "윤년 2월 29일 출생자는 평년의 생일 경계를 어떻게 볼지 법률·서비스 문맥에서 추가 설명이 필요할 수 있습니다. 단순히 365일을 곱하거나 월 수를 고정해 계산하면 윤년과 월 길이 차이를 놓칩니다.",
                "AgeCalc는 달력 날짜를 기준으로 결과를 계산하지만, 계약이나 행정 신청의 마감일은 해당 기관 규정이 우선입니다. 날짜 경계가 중요한 사안은 담당 기관의 기준일 안내를 함께 보관합니다.",
            ],
        },
        {
            "heading": "연나이와 출생연도 표는 목적이 다릅니다",
            "paragraphs": [
                "연나이는 현재 연도에서 출생연도를 빼므로 같은 해 출생자는 생일과 관계없이 같은 값입니다. 빠른 비교에는 편리하지만 원칙적인 만나이와 동일한 계산이 아닙니다.",
                "출생연도 표 역시 생일을 모를 때 가능한 만나이 범위를 보여 주는 도구입니다. 표의 한 줄을 개인의 정확한 나이로 복사하지 말고, 필요한 경우 만나이 계산기로 생일 전후를 다시 확인합니다.",
            ],
        },
        {
            "heading": "계산 결과 뒤에 제도별 공식 확인을 연결합니다",
            "paragraphs": [
                "학교 입학, 국민연금, 건강검진, 복지 혜택은 나이 숫자 외에 학년도, 가입기간, 소득, 거주지, 대상 조회 같은 조건을 사용합니다. 만나이를 정확히 계산해도 제도 자격이 자동으로 확정되는 것은 아닙니다.",
                "따라서 결과 화면에서 관련 계산기와 공식 출처로 이동해 확인 순서를 이어 갑니다. 이 글의 검수일과 만료일도 함께 보고, 이후 변경된 법령이나 기관 공고가 있으면 최신 공식 안내를 우선합니다.",
            ],
        },
    ]
    completed["birth-year-age-interpretation"]["content_sections"] = [
        {
            "heading": "출생연도만으로는 두 개의 만나이가 가능합니다",
            "paragraphs": [
                "같은 출생연도라도 올해 생일이 지난 사람과 아직 오지 않은 사람은 현재 만나이가 한 살 다릅니다. 따라서 ‘1992년생은 몇 살’처럼 월일이 없는 질문에는 하나의 숫자 대신 생일 전후 두 값을 범위로 답해야 합니다.",
                "범위의 큰 값은 기준연도에서 출생연도를 뺀 값이고, 작은 값은 거기서 한 살을 뺀 값입니다. 정확한 신청일이나 계약 기준이 필요할 때만 생년월일과 기준일을 나란히 두고 만나이 계산기로 다시 확인합니다.",
            ],
        },
        {
            "heading": "연나이와 과거 한국식 나이를 섞지 않습니다",
            "paragraphs": [
                "연나이는 현재 연도에서 출생연도를 빼므로 같은 해에 태어난 사람을 빠르게 묶어 볼 때 편리합니다. 반면 만나이는 생일 경계를 반영하므로 공적 나이 확인이나 개인 일정에는 연나이와 다른 결과가 나올 수 있습니다.",
                "과거 일상에서 쓰던 세는나이는 태어난 해를 한 살로 보고 새해마다 한 살을 더했습니다. 검색 결과에 서로 다른 숫자가 보이면 계산 오류로 단정하지 말고 어떤 나이 체계를 사용했는지부터 구분합니다.",
            ],
        },
        {
            "heading": "학교와 세대 정보는 별도의 기준표로 확인합니다",
            "paragraphs": [
                "출생연도는 학년이나 입학연도를 추정하는 출발점이지만 조기입학, 입학유예, 해외 학제, 학적 변동까지 확정하지는 않습니다. 학교 정보가 목적이면 나이표의 결과를 그대로 쓰지 않고 학년 계산기와 입학연도 표로 이동합니다.",
                "띠와 세대 구분도 출생연도를 활용하지만 음력 설 경계나 조사기관의 세대 정의처럼 별도 기준이 있습니다. 한 화면의 나이 숫자로 모든 프로필을 확정하지 않는 것이 안전합니다.",
            ],
        },
        {
            "heading": "기준일을 기록하면 해가 바뀌어도 설명할 수 있습니다",
            "paragraphs": [
                "출생연도 나이는 매년 달라지므로 표를 저장하거나 다른 사람에게 전달할 때는 ‘2026년 7월 기준’처럼 기준일을 함께 적습니다. 기준일이 없으면 같은 문장이 다음 해에 틀린 정보처럼 보일 수 있습니다.",
                "AgeCalc의 연도 표는 현재 시점의 빠른 탐색을 돕고, 개인의 정확한 값은 만나이 계산기가 담당합니다. 결과를 행정 서류에 옮기기 전에는 해당 기관이 요구하는 나이 정의와 접수 기준일을 다시 확인합니다.",
            ],
        },
        {
            "heading": "개인정보가 필요 없는 단계부터 확인합니다",
            "paragraphs": [
                "대략적인 나이 범위만 필요하다면 출생연도 표만으로 충분하므로 전체 생년월일을 입력하거나 공유할 필요가 없습니다. 개인 결과가 필요할 때도 계산은 브라우저 안에서 하고 공유 주소에는 입력값을 포함하지 않습니다.",
                "가족이나 지인의 나이를 확인할 때는 필요한 목적과 범위를 먼저 정합니다. 생년월일 전체를 메시지나 검색 주소에 남기기보다 범위 결과와 공식 확인 경로만 전달하는 편이 개인정보 노출을 줄입니다.",
            ],
        },
    ]
    completed["early-birth-school-grade-guide"]["content_sections"] = [
        {
            "heading": "빠른년생이라는 표현은 과거 취학 경험을 설명합니다",
            "paragraphs": [
                "빠른년생은 과거 1~2월생 일부가 전년도 출생자와 같은 학년에 입학했던 경험을 가리키는 일상 표현입니다. 현재의 공식 나이 계산 방식이나 모든 학생에게 적용되는 별도 법적 나이 체계를 뜻하지 않습니다.",
                "따라서 처음 만난 사람의 호칭이나 현재 나이를 판단할 때 빠른년생 여부만으로 한 살을 더하거나 빼지 않습니다. 공식 나이는 생년월일 기준 만나이로, 학교 경험은 실제 입학연도와 학적으로 나누어 설명합니다.",
            ],
        },
        {
            "heading": "현재 학생은 일반 입학 기준과 실제 학적을 구분합니다",
            "paragraphs": [
                "출생연도 기반 학년 계산기는 일반적인 국내 학제에서 입학유예나 조기입학이 없다는 가정으로 빠른 참고값을 제공합니다. 전학, 유급, 월반, 해외 학교 재학처럼 개인 이력이 있으면 계산 결과와 실제 학년이 달라질 수 있습니다.",
                "취학통지서나 학교 생활기록처럼 행정 결과가 이미 있다면 계산표보다 그 문서를 우선합니다. 입학 전이라면 주민센터, 교육지원청 또는 정부24의 해당 연도 취학 안내에서 신청 기간과 예외 절차를 확인합니다.",
            ],
        },
        {
            "heading": "나이 질문과 학번 질문에 다른 도구를 사용합니다",
            "paragraphs": [
                "‘지금 몇 살인가’는 생일 전후를 반영하는 만나이 계산 문제입니다. ‘몇 학번인가’나 ‘어느 학년인가’는 학년도와 입학 시점의 문제이므로 출생연도만 보고 동일한 답을 만들면 예외를 놓치기 쉽습니다.",
                "먼저 만나이 계산기로 현재 나이를 확인하고, 다음으로 학년 계산기에서 일반 학제 결과를 본 뒤 실제 학적과 비교합니다. 두 결과를 한 문장에 적을 때도 각각의 기준일과 가정을 명시합니다.",
            ],
        },
        {
            "heading": "조기입학과 입학유예는 자동 판정하지 않습니다",
            "paragraphs": [
                "조기입학이나 입학유예는 보호자의 선택만으로 언제든 적용되는 단순 계산 옵션이 아니라 법령과 해당 연도 행정 절차에 따라 처리됩니다. 지역과 시기에 따라 제출 서류나 상담 기관이 달라질 수 있습니다.",
                "AgeCalc는 일반 입학연도를 보여 주고 가능한 예외가 있음을 설명하지만 개인의 입학 가능 여부를 승인하지 않습니다. 실제 결정을 준비할 때는 관할 기관의 최신 공고와 학교 안내를 확인합니다.",
            ],
        },
        {
            "heading": "성인이 된 뒤의 호칭은 합의와 맥락이 우선입니다",
            "paragraphs": [
                "과거 같은 학년이었던 관계에서는 출생연도가 달라도 친구 호칭을 유지할 수 있습니다. 이는 사회적 관계의 관습이며 법적 나이나 행정상 연령을 바꾸지 않습니다.",
                "직장, 가족 모임, 동문 관계처럼 맥락이 바뀌면 상대가 편한 호칭을 묻는 것이 가장 분명합니다. 계산 결과는 사실 확인에 쓰고 인간관계의 호칭을 자동으로 결정하는 규칙으로 사용하지 않습니다.",
            ],
        },
    ]
    completed["baby-months-calculation-guide"]["content_sections"] = [
        {
            "heading": "완료 월령은 지난 달 수를 기준으로 계산합니다",
            "paragraphs": [
                "아이 개월 수는 출생일에서 기준일까지 완전히 지난 달의 수로 계산합니다. 기준일의 일자가 출생일보다 앞이면 마지막 한 달이 아직 완료되지 않았으므로 달 수에서 하나를 빼는 방식이 기본입니다.",
                "1월 31일처럼 월말에 태어난 경우에는 달마다 일수가 달라 단순히 30일을 한 달로 나누면 오차가 생깁니다. AgeCalc는 실제 달력의 연·월·일을 비교하고 생후 일수는 날짜 차이로 별도 표시합니다.",
            ],
        },
        {
            "heading": "개월 수와 생후 일수는 쓰임이 다릅니다",
            "paragraphs": [
                "월령은 영유아 시기의 큰 구간을 설명할 때 편리하고, 생후 일수는 백일이나 특정 날짜 간격을 확인할 때 유용합니다. 같은 아이도 ‘3개월’과 ‘생후 100일’이 정확히 같은 날을 뜻하지는 않습니다.",
                "행사 날짜를 잡을 때는 100일 계산기를, 현재 완료 월령을 볼 때는 아이 개월 수 계산기를 사용합니다. 예방접종이나 검진 일정은 계산 결과만으로 결정하지 않고 의료기관과 공식 안내의 대상 기간을 확인합니다.",
            ],
        },
        {
            "heading": "첫돌 전후에는 날짜와 월령을 함께 적습니다",
            "paragraphs": [
                "첫돌은 출생일의 다음 해 같은 월일이라는 기념일 개념이고, 12개월 완료 시점과 밀접하지만 설명 문맥은 다를 수 있습니다. 초대장이나 가족 기록에는 실제 날짜를 적고 발달 기록에는 당시 월령을 함께 남기면 혼동이 줄어듭니다.",
                "윤년 2월 29일 출생처럼 다음 해에 같은 날짜가 없는 경우에는 행사 기준과 행정 기준이 달라질 수 있습니다. 가족이 정한 기념일과 기관이 사용하는 기준일을 구분해 확인합니다.",
            ],
        },
        {
            "heading": "월령은 발달 진단 결과가 아닙니다",
            "paragraphs": [
                "같은 월령의 아이도 성장 속도와 건강 상태는 서로 다릅니다. 계산기가 보여 주는 숫자는 검진표나 안내문에서 연령 구간을 찾는 도구일 뿐 발달 지연이나 질환을 판정하지 않습니다.",
                "수유, 수면, 운동, 언어처럼 걱정되는 변화가 있으면 온라인 평균표와 비교해 결론내리지 말고 소아청소년과나 영유아 검진 기관에 상담합니다. 응급 증상은 월령 계산보다 즉시 의료 안내를 우선합니다.",
            ],
        },
        {
            "heading": "아이의 생년월일은 주소에 남기지 않습니다",
            "paragraphs": [
                "아이 생년월일은 가족을 식별할 수 있는 개인 정보이므로 계산 결과를 공유할 때 입력값이 포함된 긴 주소를 만들지 않습니다. AgeCalc의 아이 개월 수 계산은 브라우저 안에서 실행되며 결과 화면을 그대로 참고할 수 있습니다.",
                "보호자끼리 일정을 조율할 때는 필요한 행사 날짜나 월령만 전달하고 전체 생년월일을 공개 채팅방에 반복해 적지 않습니다. 공식 신청에는 해당 기관이 제공하는 안전한 인증·제출 경로를 이용합니다.",
            ],
        },
        {
            "heading": "기준일이 바뀌면 월령도 다시 계산합니다",
            "paragraphs": [
                "월령은 출생일에 고정된 값이 아니라 확인하는 날짜에 따라 계속 달라집니다. 병원 예약일, 검진 예정일, 어린이집 서류 작성일처럼 목적에 맞는 기준일이 있다면 오늘 계산한 숫자를 그대로 옮기지 말고 해당 날짜에 다시 확인해야 합니다.",
                "특히 자정 무렵이나 해외 체류 중에는 기기 시간대에 따라 오늘 날짜가 다르게 보일 수 있습니다. 공식 서류에는 기관이 지정한 기준일과 현지 날짜를 따르고, AgeCalc 결과 옆에도 확인한 날짜를 함께 적어 나중에 숫자의 근거를 알 수 있게 합니다.",
                "조산아의 교정 월령은 출생일만으로 산출하는 일반 월령과 다른 의료적 기준을 사용합니다. 계산기는 교정 월령을 자동 판정하지 않으며, 필요한 경우 담당 의료진이 안내한 예정일과 교정 기준을 우선합니다.",
            ],
        },
    ]
    completed["parent-child-age-gap-guide"]["content_sections"] = [
        {
            "heading": "출생연도 차이와 현재 만나이 차이는 다를 수 있습니다",
            "paragraphs": [
                "부모와 자녀의 출생연도를 빼면 달력 연도 차이를 알 수 있지만, 현재 만나이 차이는 두 사람의 생일이 각각 지났는지에 따라 한 살 다르게 보일 수 있습니다. 정확한 현재 값을 설명하려면 같은 기준일을 사용해야 합니다.",
                "예를 들어 연도 차이가 30년이어도 기준일 시점에 부모의 생일만 지났거나 자녀의 생일만 지났다면 표시되는 만나이 차이가 달라집니다. 계산 결과에는 각자의 만나이와 연도 차이를 나누어 적습니다.",
            ],
        },
        {
            "heading": "환갑과 입학처럼 서로 다른 일정 기준을 분리합니다",
            "paragraphs": [
                "부모의 환갑·칠순 같은 전통 기념 나이는 세는 방식과 행사 관습이 섞일 수 있고, 자녀의 입학은 학년도와 실제 학적을 따릅니다. 가족 나이 차이 하나만으로 두 일정을 동시에 확정할 수 없습니다.",
                "부모 일정은 기념 나이 가이드와 생일 날짜를, 자녀 일정은 학년 계산기와 취학 안내를 각각 확인합니다. 이후 가족 달력에서 날짜를 합치면 어떤 기준으로 잡은 행사인지 설명하기 쉽습니다.",
            ],
        },
        {
            "heading": "형제자매와 조부모 관계에도 같은 원칙을 적용합니다",
            "paragraphs": [
                "두 사람의 현재 나이 차이를 비교하는 수학은 관계가 달라도 같지만, 결과 해설에 필요한 생활 맥락은 달라집니다. 형제자매는 학년과 생일 순서가 중요할 수 있고 조부모는 건강검진이나 복지 기준을 함께 살필 수 있습니다.",
                "관계 이름으로 나이를 자동 추정하지 말고 각자의 출생일을 개별 계산한 뒤 필요한 일정만 연결합니다. 가족관계나 법적 보호자 여부는 나이 차이 계산 결과로 판정할 수 없습니다.",
            ],
        },
        {
            "heading": "정책 대상 여부는 개인별 조건을 다시 확인합니다",
            "paragraphs": [
                "만 65세 혜택, 국민연금, 국가건강검진처럼 연령이 들어가는 제도도 가입기간, 소득, 거주지, 가입자 유형 같은 추가 조건을 사용합니다. 부모가 기준 나이에 도달했다고 모든 혜택이 자동 적용되는 것은 아닙니다.",
                "AgeCalc에서 도달 시점을 확인한 뒤 복지로, 국민연금공단, 국민건강보험공단과 지자체의 개인 조회로 이어 갑니다. 정책 글의 검수 기한이 지났다면 연결된 공식 기관의 최신 안내를 우선합니다.",
            ],
        },
        {
            "heading": "가족 생년월일을 공유 주소에 넣지 않습니다",
            "paragraphs": [
                "여러 가족 구성원의 생년월일을 한 주소에 담으면 링크를 받은 사람, 브라우저 기록, 분석 도구와 서버 로그에 개인 정보가 노출될 수 있습니다. 계산기 링크는 입력값 없는 기본 주소만 공유합니다.",
                "결과를 보관해야 한다면 필요한 숫자와 일정만 가족이 관리하는 안전한 공간에 기록합니다. 공개 게시물이나 단체 대화에서는 전체 생년월일 대신 연령 범위나 행사 날짜처럼 목적에 필요한 최소 정보만 사용합니다.",
            ],
        },
    ]
    return completed


BLOG_ARTICLE_BLUEPRINTS = merge_article_registries(
    _completed_legacy_articles(),
    AGE_ARTICLES,
    BIRTH_YEAR_ARTICLES,
    EDUCATION_FAMILY_ARTICLES,
    POLICY_BENEFIT_ARTICLES,
    HEALTH_ARTICLES,
    PET_ARTICLES,
)

validate_article_registry(BLOG_ARTICLE_BLUEPRINTS)


def structured_blog_article_for_slug(slug: str) -> dict[str, object] | None:
    blueprint = BLOG_ARTICLE_BLUEPRINTS.get(slug)
    if blueprint is None:
        return None
    return deepcopy(blueprint)


def structured_blog_articles_for_category(category_slug: str) -> list[dict[str, object]]:
    if category_slug not in BLOG_CATEGORIES:
        return []
    return [
        deepcopy(article)
        for article in BLOG_ARTICLE_BLUEPRINTS.values()
        if article["category"] == category_slug
    ]
