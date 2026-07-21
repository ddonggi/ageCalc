from __future__ import annotations

from content.blog.schema import build_article


PET_ARTICLES = {
    "dog-age-calculation-guide": build_article(
        slug="dog-age-calculation-guide",
        title="강아지 나이 계산법 | 사람 나이 7배 공식의 한계",
        h1="강아지 나이는 사람 나이로 어떻게 환산할까",
        summary="강아지 나이를 단순히 7배로 계산하기 어려운 이유와 크기·품종·생애 단계를 함께 보는 방법을 설명합니다.",
        category="pets",
        tags=("강아지 나이", "반려견 생애 단계", "사람 나이 환산"),
        primary_cta={"label": "강아지 나이 계산기", "path": "/dog"},
        secondary_cta={"label": "반려동물 나이표", "path": "/pet-age-table"},
        direct_answer_title="강아지 나이는 매년 일정하게 7살씩 늘어난다고 보기 어렵습니다",
        direct_answer_paragraphs=[
            "강아지는 생후 첫 1~2년에 사람보다 빠르게 성장하고 이후 노화 속도는 체격, 품종, 생활환경과 건강 상태에 따라 달라집니다. 그래서 전 생애를 단순히 7배로 환산하는 공식은 생애 단계를 설명하기에 부족합니다.",
            "AAHA 가이드는 강아지의 생애를 퍼피, 젊은 성견, 성숙한 성견, 시니어 등 단계로 보고 품종과 예상 수명을 함께 고려하도록 설명합니다. 나이 환산표는 이해를 돕는 비유이지 임상 진단값이 아닙니다.",
            "AgeCalc 결과는 생활 단계와 대략적인 사람 나이 대응을 보여 줍니다. 예방접종, 검진 주기, 통증이나 행동 변화는 나이표가 아니라 담당 수의사의 개별 평가를 따릅니다.",
        ],
        audience_items=[
            "반려견의 현재 생애 단계를 이해하려는 보호자",
            "‘강아지 나이×7’ 공식이 실제 성장과 어떻게 다른지 궁금한 사람",
            "건강 판단과 재미있는 환산 결과를 명확히 분리하고 싶은 사람",
        ],
        example_cards=[
            {"label": "첫해", "title": "빠른 성장기", "description": "생후 1년은 사람의 일곱 살과 같은 속도로만 설명하기 어려울 만큼 큰 변화가 일어납니다."},
            {"label": "성견", "title": "체격별 차이", "description": "같은 실제 나이라도 소형견과 대형견의 기대수명과 생애 단계가 다를 수 있습니다."},
            {"label": "시니어", "title": "개별 평가", "description": "시니어 시작 시점은 품종·크기·건강 상태를 수의사와 함께 판단합니다."},
        ],
        comparison_rows=[
            {"label": "단순 7배", "standard": "빠른 암산용 비유", "exception": "첫 성장기·체격 차이를 반영하지 못함"},
            {"label": "AgeCalc 환산표", "standard": "크기별 대략적 대응", "exception": "진단·수명 예측으로 사용하지 않음"},
            {"label": "수의학적 생애 단계", "standard": "품종·크기·생활·건강 종합", "exception": "담당 수의사의 개별 평가 필요"},
        ],
        content_sections=[
            {
                "heading": "첫 1~2년의 성장 속도가 특히 빠릅니다",
                "paragraphs": [
                    "강아지는 어린 시기에 신체와 행동이 빠르게 발달합니다. 첫해를 사람의 일곱 살로만 대응하면 성적 성숙과 사회적 발달, 체격 변화가 충분히 설명되지 않습니다.",
                    "그래서 많은 환산표는 첫 1~2년에 큰 사람 나이 값을 배정하고 이후 증가 폭을 낮춥니다. 표마다 숫자가 다른 것은 하나의 절대 공식이 아니라 설명 모델이기 때문입니다.",
                ],
            },
            {
                "heading": "대형견과 소형견은 같은 속도로 늙지 않습니다",
                "paragraphs": [
                    "대형견은 성숙 과정과 평균 수명이 소형견과 달라 같은 실제 나이에 더 이른 생애 단계로 분류될 수 있습니다. 품종 내부에서도 유전적 특성과 체중, 생활환경이 차이를 만듭니다.",
                    "AgeCalc에서 체격을 선택할 수 있다면 정확한 미래 수명을 예측하는 기능이 아니라 대략적인 환산 곡선을 조정하는 장치로 이해합니다. 체중 하나만으로 건강 나이를 진단할 수는 없습니다.",
                ],
            },
            {
                "heading": "생애 단계는 건강 대화를 돕는 틀입니다",
                "paragraphs": [
                    "AAHA는 생애 단계별로 예방관리에서 확인할 주제가 달라질 수 있다고 설명합니다. 퍼피의 예방접종과 행동 사회화, 성견의 체중·치아 관리, 시니어의 만성질환 모니터링처럼 관심점이 이동합니다.",
                    "그러나 가이드라인도 모든 반려견에게 하나의 배타적 진료 절차를 지시하지 않습니다. 보호자가 생활 변화를 기록하고 수의사와 맞춤 계획을 세우기 위한 공통 언어로 활용합니다.",
                ],
            },
            {
                "heading": "환산 결과와 증상 판단을 분리합니다",
                "paragraphs": [
                    "걷기 어려움, 식욕 변화, 호흡 이상, 통증, 갑작스러운 행동 변화가 있다면 ‘사람 나이로 아직 젊다’는 계산 결과로 진료를 미루지 않습니다. 증상의 긴급성과 원인은 실제 검진이 필요합니다.",
                    "반대로 높은 환산 나이가 나왔다고 질병이 있다고 단정할 수도 없습니다. 정기 검진 기록, 예방접종 이력, 체중 변화와 생활 습관을 함께 관리하는 것이 더 실용적입니다.",
                ],
            },
            {
                "heading": "생년월일을 모르면 추정 나이를 별도로 기록합니다",
                "paragraphs": [
                    "입양견처럼 정확한 출생일을 모르면 보호소나 동물병원의 치아·신체 평가로 추정한 나이를 사용할 수 있습니다. 이때 계산 결과에도 ‘추정’임을 남겨 정밀한 생년월일처럼 공유하지 않습니다.",
                    "나이표는 가족에게 생애 단계를 설명하는 데 유용하지만 반려동물 등록정보나 병원 기록을 대체하지 않습니다. 다음 검진에서 수의사에게 추정 기준과 변화 여부를 함께 확인합니다.",
                ],
            },
        ],
        faq_items=[
            {"question": "강아지 나이는 사람 나이의 7배인가요?", "answer": "전 생애에 일정하게 적용하기 어렵습니다. 첫 성장 속도와 체격·품종별 노화 차이를 반영하지 못하는 단순 비유입니다."},
            {"question": "강아지는 몇 살부터 시니어인가요?", "answer": "품종, 크기와 예상 수명에 따라 달라 하나의 나이로 단정하기 어렵습니다. 담당 수의사와 생애 단계 및 검진 계획을 확인하세요."},
            {"question": "환산 나이로 건강 상태를 알 수 있나요?", "answer": "아닙니다. 환산은 설명용이며 증상과 건강 상태는 수의학적 검진이 필요합니다."},
        ],
        related_tools=[
            {"label": "강아지 나이 계산기", "path": "/dog", "summary": "실제 나이와 크기별 환산"},
            {"label": "반려동물 나이표", "path": "/pet-age-table", "summary": "강아지·고양이 환산표"},
            {"label": "반려동물 월령표", "path": "/pet-months-table", "summary": "어린 반려동물 월령 확인"},
        ],
        related_articles=[
            {"title": "아이 개월 수 계산", "path": "/blog/baby-months-calculation-guide", "summary": "월령을 해석하는 다른 사례"},
            {"title": "부모·자녀 나이 차이", "path": "/blog/parent-child-age-gap-guide", "summary": "가족 나이 관계 해석"},
        ],
        reviewed_at="2026-07-21",
        effective_date="2026-07-21",
        expires_at="2027-07-21",
        sources=[
            {"organization": "American Animal Hospital Association", "title": "2019 AAHA Canine Life Stage Guidelines", "url": "https://www.aaha.org/resources/life-stage-canine-2019/life-stage-canine-2019-2/", "checked_at": "2026-07-21"},
            {"organization": "American Animal Hospital Association", "title": "Canine Life Stage Calculator", "url": "https://www.aaha.org/resources/life-stage-canine-2019/canine-life-stage-calculator/", "checked_at": "2026-07-21"},
        ],
        meta_title="강아지 나이 계산법과 7배 공식의 한계 | AgeCalc",
        meta_description="강아지 나이를 사람 나이로 단순 7배 하기 어려운 이유와 크기·품종·생애 단계별 해석, 수의학적 한계를 설명합니다.",
        thumbnail_alt="강아지 실제 나이와 사람 나이 환산을 설명하는 AgeCalc 이미지",
        disclaimer="반려견 나이 환산은 설명용이며 질병 진단이나 검진 주기를 결정하지 않습니다. 건강 문제는 수의사와 상담하세요.",
    )
}
