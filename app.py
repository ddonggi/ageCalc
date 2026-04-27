import math
from flask import Flask, Response, render_template, request, jsonify, g, send_from_directory, abort, redirect, session, url_for
import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
from zoneinfo import ZoneInfo
from controllers.age_controller import AgeController
from db import SessionLocal, close_db_session, init_db
from models.blog_models import GeneratedPost

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env.rss"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        if not key or key in os.environ:
            continue

        os.environ[key] = value.strip().strip('"').strip("'")


_load_env_file(ENV_FILE)


def _load_blog_timezone():
    tz_name = (os.getenv("BLOG_TIMEZONE", "Asia/Seoul") or "Asia/Seoul").strip()
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return timezone(timedelta(hours=9), name="KST")


BLOG_TIMEZONE = _load_blog_timezone()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.getenv("BLOG_REVIEW_TOKEN") or "agecalc-drafts-v1"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
_score_lock = threading.Lock()
_score_file = os.path.join(app.root_path, "data", "snake_scores.json")
os.makedirs(os.path.dirname(_score_file), exist_ok=True)
init_db()

BLOG_DRAFT_ACCESS_SESSION_KEY = "blog_draft_access"
SITE_BASE_URL = (os.getenv("BLOG_BASE_URL", "https://agecalc.cloud") or "https://agecalc.cloud").rstrip("/")
SITE_AUTHOR_NAME = os.getenv("SITE_AUTHOR_NAME", "AgeCalc 편집팀").strip() or "AgeCalc 편집팀"
SITE_CONTACT_EMAIL = os.getenv("SITE_CONTACT_EMAIL", "ldg6153@gmail.com").strip() or "ldg6153@gmail.com"
ADSENSE_CLIENT_ID = os.getenv("ADSENSE_CLIENT_ID", "ca-pub-7818333740838556").strip()
GOOGLE_SITE_VERIFICATION = os.getenv(
    "GOOGLE_SITE_VERIFICATION",
    "q0nvIaon9IVWNZZEQzTRCycYka7jIHuzYu-PwxxoKu8",
).strip()
KOREAN_ZODIAC = ["원숭이", "닭", "개", "돼지", "쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양"]
GENERATION_LABELS = [
    ((1946, 1964), "베이비붐 세대"),
    ((1965, 1980), "X세대"),
    ((1981, 1996), "밀레니얼 세대"),
    ((1997, 2012), "Z세대"),
    ((2013, 2030), "알파 세대"),
]
DOG_HUMAN_AGE_TABLE = {
    "small": [15, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80],
    "medium": [15, 24, 28, 32, 36, 42, 47, 51, 56, 60, 65, 69, 74, 78, 83, 87],
    "large": [15, 24, 28, 32, 36, 45, 50, 55, 61, 66, 72, 77, 82, 88, 93, 99],
    "giant": [12, 22, 31, 38, 45, 49, 56, 64, 71, 79, 86, 93, 100, 107, 114, 121],
}
SITE_NAVIGATION = [
    {
        "key": "calculators",
        "label": "계산기",
        "eyebrow": "직접 계산",
        "description": "입력값을 넣고 바로 결과를 확인하는 핵심 계산기입니다.",
        "links": [
            {"endpoint": "age", "label": "만나이", "summary": "생년월일로 만 나이를 바로 계산합니다."},
            {"endpoint": "dog", "label": "강아지 나이", "summary": "반려견 나이를 사람 기준으로 환산합니다."},
            {"endpoint": "cat", "label": "고양이 나이", "summary": "반려묘 나이를 사람 기준으로 환산합니다."},
            {"endpoint": "baby_months", "label": "아이 개월 수", "summary": "출생일 기준 현재 개월 수를 계산합니다."},
            {"endpoint": "d_day", "label": "기념일 계산", "summary": "다가오는 날짜까지 남은 일수를 계산합니다."},
            {"endpoint": "parent_child", "label": "부모·자녀", "summary": "부모와 자녀의 나이 차이와 주요 시점을 살펴봅니다."},
        ],
    },
    {
        "key": "reference",
        "label": "표·비교",
        "eyebrow": "빠른 확인",
        "description": "연도, 학년, 월령처럼 자주 찾는 기준을 표와 비교형 페이지로 정리했습니다.",
        "links": [
            {"endpoint": "birth_year_age_table", "label": "출생년도별 나이표", "summary": "출생연도별 연나이와 만나이 범위를 확인합니다."},
            {"endpoint": "school_grade_calculator", "label": "학년 계산기", "summary": "출생년도 기준 현재 학년과 입학 시점을 계산합니다."},
            {"endpoint": "school_entry_year_table", "label": "입학년도 계산표", "summary": "초·중·고 입학 학년도를 한 번에 확인합니다."},
            {"endpoint": "grade_age_table", "label": "학년 기준 나이표", "summary": "초1부터 고3까지 보통 나이를 표로 봅니다."},
            {"endpoint": "grade_birth_year_table", "label": "학년별 출생연도표", "summary": "학년별 보통 출생연도를 빠르게 찾습니다."},
            {"endpoint": "college_entry_year_calculator", "label": "대학 학번 나이", "summary": "25학번, 26학번의 보통 나이를 확인합니다."},
            {"endpoint": "annual_age_calculator", "label": "연나이 계산기", "summary": "생일과 관계없이 올해 기준 연나이를 계산합니다."},
            {"endpoint": "age_comparison_table", "label": "만나이·연나이 비교표", "summary": "만나이와 연나이 차이를 비교해 설명합니다."},
            {"endpoint": "age_gap_calculator", "label": "나이 차이 계산기", "summary": "두 출생년도의 차이를 만나이 범위까지 비교합니다."},
            {"endpoint": "hundred_day_calculator", "label": "100일 계산기", "summary": "시작일 기준 100일째 날짜와 현재 상태를 계산합니다."},
            {"endpoint": "birthday_dday_calculator", "label": "생일 D-day", "summary": "다음 생일까지 남은 일수를 계산합니다."},
            {"endpoint": "baby_months_table", "label": "개월수 계산표", "summary": "월령별 빠른 안내와 연 단위 환산을 함께 봅니다."},
            {"endpoint": "pet_age_table", "label": "반려동물 나이표", "summary": "강아지·고양이 나이를 사람 기준으로 비교합니다."},
            {"endpoint": "pet_months_table", "label": "반려동물 월령표", "summary": "강아지·고양이 월령 기준을 표로 정리합니다."},
            {"endpoint": "birth_year_zodiac_table", "label": "출생연도별 띠표", "summary": "출생연도별 띠와 나이 범위를 함께 확인합니다."},
        ],
    },
    {
        "key": "guides",
        "label": "안내",
        "eyebrow": "기준 정리",
        "description": "계산 기준, 참고 자료, 운영 정보와 정책 문서를 한곳에서 확인할 수 있습니다.",
        "links": [
            {"endpoint": "guide", "label": "나이 계산 가이드", "summary": "만나이, 연나이, 한국식 나이 차이를 설명합니다."},
            {"endpoint": "faq", "label": "자주 묻는 질문", "summary": "자주 헷갈리는 계산 기준과 예외를 모았습니다."},
            {"endpoint": "korean_age_guide", "label": "한국나이 기준 정리", "summary": "만 나이 통일 이후 기준과 예외를 정리했습니다."},
            {"endpoint": "references", "label": "계산 기준", "summary": "각 계산기의 참고 자료와 기준을 한 번에 확인합니다."},
            {"endpoint": "about", "label": "운영 원칙", "summary": "콘텐츠 작성 기준과 운영 원칙을 공개합니다."},
            {"endpoint": "contact", "label": "문의", "summary": "운영자 안내와 수정 요청 경로를 확인합니다."},
            {"endpoint": "privacy", "label": "개인정보처리방침", "summary": "데이터 처리와 쿠키 이용 방침을 안내합니다."},
            {"endpoint": "terms", "label": "이용약관", "summary": "서비스 이용 시 알아둘 기준과 책임 범위를 안내합니다."},
        ],
    },
]
HOME_SECTION_CONFIG = {
    "calculators": {
        "section_label": "대표 계산기",
        "title": "직접 입력해서 바로 계산하는 핵심 도구",
        "intro": "가장 자주 찾는 입력형 계산기를 먼저 배치했습니다.",
        "featured_limit": 6,
    },
    "reference": {
        "section_label": "표·비교 모음",
        "title": "표와 비교형 페이지로 기준을 빠르게 확인하세요",
        "intro": "출생연도, 학년, 월령처럼 자주 찾는 기준을 표 중심으로 정리했습니다.",
        "featured_limit": 6,
    },
    "guides": {
        "section_label": "기준과 안내",
        "title": "계산 기준과 운영 원칙을 함께 확인하세요",
        "intro": "헷갈리기 쉬운 나이 기준, 참고 자료, 운영 정보를 한곳에 모았습니다.",
        "featured_limit": 4,
    },
}
FOOTER_POLICY_LINKS = [
    {"endpoint": "about", "label": "운영 원칙"},
    {"endpoint": "references", "label": "계산 기준"},
    {"endpoint": "contact", "label": "문의"},
    {"endpoint": "privacy", "label": "개인정보처리방침"},
    {"endpoint": "terms", "label": "이용약관"},
]
PUBLIC_SITEMAP_ENDPOINTS = [
    "index",
    "age",
    "about",
    "contact",
    "references",
    "birth_year_age_table",
    "school_grade_calculator",
    "school_entry_year_table",
    "age_gap_calculator",
    "hundred_day_calculator",
    "baby_months_table",
    "annual_age_calculator",
    "age_comparison_table",
    "grade_age_table",
    "pet_age_table",
    "korean_age_guide",
    "pet_months_table",
    "grade_birth_year_table",
    "birth_year_zodiac_table",
    "college_entry_year_calculator",
    "birthday_dday_calculator",
    "privacy",
    "terms",
    "guide",
    "faq",
    "dog",
    "cat",
    "baby_months",
    "d_day",
    "parent_child",
    "blog_list",
]

@app.before_request
def set_csp_nonce():
    g.csp_nonce = secrets.token_urlsafe(16)

@app.context_processor
def inject_csp_nonce():
    editorial_policy_url = "#"
    try:
        editorial_policy_url = url_for("about")
    except RuntimeError:
        pass

    site_navigation = []
    home_navigation_sections = []
    navigation_counts = {}

    for group in SITE_NAVIGATION:
        links = [dict(link) for link in group["links"]]
        group_payload = dict(group)
        group_payload["links"] = links
        group_payload["endpoints"] = [link["endpoint"] for link in links]
        site_navigation.append(group_payload)
        navigation_counts[group["key"]] = len(links)

        section_config = HOME_SECTION_CONFIG.get(group["key"])
        if section_config:
            section_payload = dict(section_config)
            section_payload["key"] = group["key"]
            section_payload["links"] = links[: section_config["featured_limit"]]
            section_payload["more_links"] = links[section_config["featured_limit"] :]
            home_navigation_sections.append(section_payload)

    return {
        "csp_nonce": getattr(g, "csp_nonce", ""),
        "author_name": SITE_AUTHOR_NAME,
        "contact_email": SITE_CONTACT_EMAIL,
        "editorial_policy_url": editorial_policy_url,
        "adsense_enabled": _adsense_is_enabled_for_path(request.path),
        "adsense_client_id": ADSENSE_CLIENT_ID,
        "google_site_verification": GOOGLE_SITE_VERIFICATION,
        "site_navigation": site_navigation,
        "home_navigation_sections": home_navigation_sections,
        "footer_policy_links": FOOTER_POLICY_LINKS,
        "navigation_counts": navigation_counts,
    }


@app.teardown_appcontext
def cleanup_session(exception=None):
    close_db_session(exception)

@app.after_request
def add_security_headers(response):
    if request.path == "/minigames" or request.path.startswith("/minigames/"):
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    nonce = getattr(g, "csp_nonce", "")
    csp = (
        "default-src 'self'; "
        "img-src 'self' data: https://c.clarity.ms https://pagead2.googlesyndication.com https://googleads.g.doubleclick.net; "
        "font-src 'self' https://fonts.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        f"script-src 'self' 'nonce-{nonce}' https://www.googletagmanager.com https://www.clarity.ms https://scripts.clarity.ms https://pagead2.googlesyndication.com https://ep2.adtrafficquality.google; "
        "connect-src 'self' https://www.google-analytics.com https://www.clarity.ms https://c.clarity.ms https://i.clarity.ms https://ep1.adtrafficquality.google https://pagead2.googlesyndication.com https://googleads.g.doubleclick.net; "
        "frame-src https://googleads.g.doubleclick.net https://pagead2.googlesyndication.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    return response


def _ensure_score_file():
    os.makedirs(os.path.dirname(_score_file), exist_ok=True)
    if not os.path.exists(_score_file):
        with open(_score_file, "w", encoding="utf-8") as f:
            json.dump({"scores": []}, f)


def _load_scores():
    _ensure_score_file()
    with open(_score_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {"scores": []}
    return data.get("scores", [])


def _save_scores(scores):
    _ensure_score_file()
    with open(_score_file, "w", encoding="utf-8") as f:
        json.dump({"scores": scores}, f, ensure_ascii=False)


def _date_key(ts):
    return ts.strftime("%Y-%m-%d")


def _month_key(ts):
    return ts.strftime("%Y-%m")



@app.get("/health") 
def health(): 
    return {"ok": True}, 200


@app.get("/favicon.ico")
def favicon():
    return send_from_directory(app.root_path, "favicon.ico")


def _review_token_is_valid(token: str) -> bool:
    expected = (os.getenv("BLOG_REVIEW_TOKEN", "") or "").strip()
    provided = (token or "").strip()
    return bool(expected) and secrets.compare_digest(expected, provided)


def _draft_password_is_valid(password: str) -> bool:
    expected = (os.getenv("BLOG_DRAFT_PASSWORD", "") or "").strip()
    provided = (password or "").strip()
    return bool(expected) and secrets.compare_digest(expected, provided)


def _draft_access_granted() -> bool:
    return bool(session.get(BLOG_DRAFT_ACCESS_SESSION_KEY))


def _as_blog_localtime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(BLOG_TIMEZONE)


@app.template_filter("blog_datetime")
def blog_datetime(value: datetime | None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    local_dt = _as_blog_localtime(value)
    if local_dt is None:
        return ""
    return local_dt.strftime(fmt)


def _format_sitemap_lastmod(value: datetime | None) -> str | None:
    if value is None:
        return None
    local_dt = _as_blog_localtime(value)
    if local_dt is None:
        return None
    return local_dt.date().isoformat()


def _absolute_url_for(endpoint: str, **values) -> str:
    return f"{SITE_BASE_URL}{url_for(endpoint, **values)}"


def _adsense_is_enabled_for_path(path: str) -> bool:
    excluded_prefixes = ("/minigames", "/blog/drafts", "/blog/review")
    return not any(path == prefix or path.startswith(f"{prefix}/") for prefix in excluded_prefixes)


def _build_sitemap_entry(loc: str, lastmod: str | None = None) -> str:
    if lastmod:
        return f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>"
    return f"  <url><loc>{loc}</loc></url>"


def _current_local_date():
    return datetime.now(BLOG_TIMEZONE).date()


def _generation_label(year: int) -> str:
    for (start, end), label in GENERATION_LABELS:
        if start <= year <= end:
            return label
    return "넓은 세대 구분 없음"


def _birth_year_range_label(year: int, current_year: int) -> str:
    annual_age = current_year - year
    if annual_age <= 0:
        return "만 0세"
    return f"만 {annual_age - 1}~{annual_age}세"


def _build_birth_year_snapshot(year: int, current_year: int) -> dict[str, object]:
    annual_age = current_year - year
    if annual_age <= 0:
        detail = "올해 출생자는 현재 기준으로 만 0세입니다. 실제 출생일이 미래라면 아직 계산 대상이 아닐 수 있습니다."
    else:
        detail = f"생일이 지났다면 만 {annual_age}세, 아직 지나지 않았다면 만 {annual_age - 1}세입니다."

    return {
        "year": year,
        "label": f"{year}년생",
        "annual_age": f"{annual_age}세",
        "man_age_range": _birth_year_range_label(year, current_year),
        "detail": detail,
        "zodiac": KOREAN_ZODIAC[year % 12],
        "generation": _generation_label(year),
    }


def _current_school_year(today=None) -> int:
    if today is None:
        today = _current_local_date()
    return today.year if today.month >= 3 else today.year - 1


def _school_grade_label(birth_year: int, school_year: int) -> tuple[str, str]:
    elementary_entry = birth_year + 7
    diff = school_year - elementary_entry

    if diff < 0:
        if diff == -1:
            return ("취학 전", f"{elementary_entry}학년도 초등학교 입학 예정")
        return ("취학 전", f"{elementary_entry}학년도에 초등학교 입학 예정")
    if diff <= 5:
        return (f"초등학교 {diff + 1}학년", "현재 초등학생 단계")
    if diff <= 8:
        return (f"중학교 {diff - 5}학년", "현재 중학생 단계")
    if diff <= 11:
        return (f"고등학교 {diff - 8}학년", "현재 고등학생 단계")
    if diff == 12:
        return ("고등학교 졸업 이후", "대학 진학 또는 진로 선택 시기")
    return ("고등학교 졸업 이후", "학교급 계산 범위 이후 단계")


def _build_school_grade_snapshot(birth_year: int, school_year: int) -> dict[str, object]:
    current_grade, note = _school_grade_label(birth_year, school_year)
    elementary_entry = birth_year + 7
    middle_entry = birth_year + 13
    high_entry = birth_year + 16

    return {
        "year": birth_year,
        "label": f"{birth_year}년생",
        "current_grade": current_grade,
        "note": note,
        "elementary_entry": f"{elementary_entry}학년도",
        "middle_entry": f"{middle_entry}학년도",
        "high_entry": f"{high_entry}학년도",
    }


def _build_school_entry_snapshot(birth_year: int, school_year: int) -> dict[str, object]:
    grade_snapshot = _build_school_grade_snapshot(birth_year, school_year)
    current_grade = grade_snapshot["current_grade"]

    if "취학 전" in current_grade:
        status_note = f"현재는 {current_grade} 단계이며, 가장 가까운 입학 시점은 {grade_snapshot['elementary_entry']} 초등학교 입학입니다."
    elif "초등학교" in current_grade:
        status_note = f"현재는 {current_grade} 단계이며, 중학교 입학은 {grade_snapshot['middle_entry']}, 고등학교 입학은 {grade_snapshot['high_entry']}입니다."
    elif "중학교" in current_grade:
        status_note = f"현재는 {current_grade} 단계이며, 고등학교 입학은 {grade_snapshot['high_entry']}입니다."
    else:
        status_note = f"초등학교 입학은 {grade_snapshot['elementary_entry']}, 중학교 입학은 {grade_snapshot['middle_entry']}, 고등학교 입학은 {grade_snapshot['high_entry']}였습니다."

    return {
        "year": birth_year,
        "label": grade_snapshot["label"],
        "current_grade": current_grade,
        "status_note": status_note,
        "elementary_entry": grade_snapshot["elementary_entry"],
        "middle_entry": grade_snapshot["middle_entry"],
        "high_entry": grade_snapshot["high_entry"],
    }


def _build_grade_age_snapshot(stage: str, grade: int, school_year: int, current_year: int) -> dict[str, object]:
    stage_map = {
        "elementary": ("초등학교", 7),
        "middle": ("중학교", 13),
        "high": ("고등학교", 16),
    }
    school_label, offset = stage_map[stage]
    birth_year = school_year - offset - (grade - 1)
    annual_age = current_year - birth_year
    man_age_range = _birth_year_range_label(birth_year, current_year)

    note = f"{school_year}학년도 {school_label} {grade}학년은 보통 {birth_year}년생이 해당하며, 올해 기준 연나이는 {annual_age}세입니다."

    return {
        "stage": stage,
        "grade": grade,
        "label": f"{school_label} {grade}학년",
        "birth_year_label": f"{birth_year}년생",
        "annual_age": f"{annual_age}세",
        "man_age_range": man_age_range,
        "note": note,
    }


def _build_age_gap_snapshot(year_a: int, year_b: int) -> dict[str, object]:
    older_year = min(year_a, year_b)
    younger_year = max(year_a, year_b)
    gap = younger_year - older_year

    if gap == 0:
        annual_gap = "0년 차이"
        man_gap_range = "만 0세 차이"
        detail = "같은 출생년도라서 연나이와 만나이 모두 같은 흐름으로 계산됩니다."
    else:
        annual_gap = f"{gap}년 차이"
        lower = max(gap - 1, 0)
        man_gap_range = f"만 {lower}~{gap}세 차이"
        detail = f"연나이는 항상 {gap}세 차이이고, 만나이는 두 사람의 생일이 지났는지에 따라 {lower}~{gap}세 차이로 보일 수 있습니다."

    return {
        "year_a": year_a,
        "year_b": year_b,
        "older_year": older_year,
        "younger_year": younger_year,
        "pair_label": f"{older_year}년생과 {younger_year}년생",
        "annual_gap": annual_gap,
        "man_gap_range": man_gap_range,
        "detail": detail,
    }


def _parse_calendar_date(year: int | None, month: int | None, day: int | None):
    if year is None or month is None or day is None:
        return None
    try:
        return datetime(year, month, day).date()
    except ValueError:
        return None


def _format_calendar_date(value) -> str:
    return value.strftime("%Y.%m.%d")


def _build_hundred_day_snapshot(start_date, today=None) -> dict[str, object]:
    if today is None:
        today = _current_local_date()

    hundredth_date = start_date + timedelta(days=99)
    diff = (hundredth_date - today).days

    if diff > 0:
        status_label = f"D-{diff}"
        status_note = f"100일째까지 {diff}일 남았습니다."
    elif diff < 0:
        status_label = f"D+{abs(diff)}"
        status_note = f"100일째가 지난 지 {abs(diff)}일 되었습니다."
    else:
        status_label = "D-Day"
        status_note = "바로 오늘이 100일째입니다."

    elapsed = (today - start_date).days + 1
    if elapsed < 1:
        elapsed_label = "시작일 전"
    else:
        elapsed_label = f"{elapsed}일째"

    return {
        "start_date": _format_calendar_date(start_date),
        "hundredth_date": _format_calendar_date(hundredth_date),
        "status_label": status_label,
        "status_note": status_note,
        "elapsed_label": elapsed_label,
        "detail": "시작일을 1일째로 계산해 99일을 더한 날짜를 100일째로 안내합니다.",
    }


def _parse_month_day(month: int | None, day: int | None):
    if month is None or day is None:
        return None
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None

    validation_year = 2000 if month == 2 and day == 29 else 2001
    try:
        datetime(validation_year, month, day).date()
    except ValueError:
        return None
    return month, day


def _next_birthday_date(month: int, day: int, today):
    year = today.year
    while True:
        try:
            candidate = datetime(year, month, day).date()
        except ValueError:
            year += 1
            continue

        if candidate < today:
            year += 1
            continue
        return candidate


def _build_birthday_dday_snapshot(month: int, day: int, today=None) -> dict[str, object]:
    if today is None:
        today = _current_local_date()

    next_birthday = _next_birthday_date(month, day, today)
    days_until = (next_birthday - today).days

    if days_until == 0:
        status_label = "D-Day"
        status_note = "바로 오늘이 생일입니다."
    else:
        status_label = f"D-{days_until}"
        status_note = f"다음 생일까지 {days_until}일 남았습니다."

    return {
        "birthday_label": f"{month}월 {day}일",
        "next_birthday_date": _format_calendar_date(next_birthday),
        "status_label": status_label,
        "status_note": status_note,
        "days_until_label": f"{days_until}일",
        "detail": "월과 일만 입력하면 오늘 기준으로 가장 가까운 다음 생일 날짜를 계산합니다.",
    }


def _build_annual_age_snapshot(birth_date, current_year: int) -> dict[str, object]:
    birth_year = birth_date.year
    annual_age = current_year - birth_year
    man_age_range = _birth_year_range_label(birth_year, current_year)

    return {
        "birth_date": _format_calendar_date(birth_date),
        "birth_year": birth_year,
        "annual_age": f"{annual_age}세",
        "man_age_range": man_age_range,
        "detail": f"연나이는 생일과 관계없이 {current_year}년 - {birth_year}년으로 계산하므로 올해 기준 {annual_age}세입니다.",
    }


def _build_age_comparison_snapshot(birth_year: int, current_year: int) -> dict[str, object]:
    annual_age = current_year - birth_year
    man_age_range = _birth_year_range_label(birth_year, current_year)

    if annual_age <= 0:
        diff_note = "올해 출생자는 연나이와 만나이 모두 0세 기준으로 안내합니다."
        gap_label = "차이 없음"
    else:
        diff_note = "연나이는 생일과 관계없이 고정되지만, 만나이는 생일 전후에 따라 1살 차이까지 생길 수 있습니다."
        gap_label = "0~1살 차이"

    return {
        "birth_year": birth_year,
        "label": f"{birth_year}년생",
        "annual_age": f"{annual_age}세",
        "man_age_range": man_age_range,
        "gap_label": gap_label,
        "diff_note": diff_note,
    }


def _dog_size_label(size: str) -> str:
    return {
        "small": "소형견",
        "medium": "중형견",
        "large": "대형견",
        "giant": "초대형견",
    }.get(size, "소형견")


def _calc_dog_human_age(years: int, size: str) -> int:
    table = DOG_HUMAN_AGE_TABLE.get(size, DOG_HUMAN_AGE_TABLE["small"])
    if years <= 0:
        return 0
    if years <= len(table):
        return table[years - 1]

    last = table[-1]
    prev = table[-2]
    step = last - prev
    return last + step * (years - len(table))


def _calc_cat_human_age(years: int) -> int:
    if years <= 0:
        return 0
    if years == 1:
        return 15
    if years == 2:
        return 24
    return 24 + 4 * (years - 2)


def _build_pet_age_snapshot(pet: str, years: int, size: str = "small") -> dict[str, object]:
    if pet == "cat":
        human_age = _calc_cat_human_age(years)
        label = f"고양이 {years}살"
        detail = "고양이는 첫 해 15세, 둘째 해 24세, 이후에는 해마다 4세씩 더하는 기준으로 많이 안내합니다."
        size_label = ""
    else:
        human_age = _calc_dog_human_age(years, size)
        label = f"강아지 {years}살"
        detail = f"강아지는 { _dog_size_label(size) } 기준 연령표를 적용해 사람 나이로 환산합니다."
        size_label = _dog_size_label(size)

    return {
        "pet": pet,
        "years": years,
        "label": label,
        "size": size,
        "size_label": size_label,
        "human_age": f"{human_age}세",
        "detail": detail,
    }


def _calc_dog_human_age_precise(age_years: float, size: str) -> float:
    table = DOG_HUMAN_AGE_TABLE.get(size, DOG_HUMAN_AGE_TABLE["small"])
    if age_years <= 0:
        return 0.0
    if age_years <= 1:
        return 15 * age_years
    if age_years <= 2:
        return 15 + (24 - 15) * (age_years - 1)

    whole = math.floor(age_years)
    frac = age_years - whole
    last_index = len(table)

    if whole >= last_index:
        last = table[-1]
        prev = table[-2] if len(table) > 1 else last
        step = last - prev or 4
        return last + step * (age_years - last_index)

    base = table[max(whole - 1, 0)]
    next_value = table[whole] if whole < len(table) else base
    return base + (next_value - base) * frac


def _calc_cat_human_age_precise(age_years: float) -> float:
    if age_years <= 0:
        return 0.0
    if age_years <= 1:
        return 15 * age_years
    if age_years <= 2:
        return 15 + 9 * (age_years - 1)
    return 24 + 4 * (age_years - 2)


def _build_pet_month_snapshot(pet: str, months: int, size: str = "small") -> dict[str, object]:
    age_years = months / 12
    age_text = _format_years_months(months)

    if pet == "cat":
        human_age_value = _calc_cat_human_age_precise(age_years)
        label = f"고양이 {months}개월"
        size_label = ""
        detail = "고양이는 첫 2년의 성장 속도가 빨라 같은 6개월이라도 사람 나이로 보면 빠르게 커지는 편입니다."
    else:
        human_age_value = _calc_dog_human_age_precise(age_years, size)
        label = f"강아지 {months}개월"
        size_label = _dog_size_label(size)
        detail = f"강아지는 {size_label} 기준으로 월령이 빠르게 올라가며, 생후 1년 안에서도 환산 차이가 크게 보일 수 있습니다."

    rounded_human_age = max(0, round(human_age_value))
    return {
        "pet": pet,
        "months": months,
        "age_text": age_text,
        "label": label,
        "size": size,
        "size_label": size_label,
        "human_age": f"약 {rounded_human_age}세",
        "detail": detail,
    }


def _short_school_label(stage: str, grade: int) -> str:
    return {
        "elementary": f"초{grade}",
        "middle": f"중{grade}",
        "high": f"고{grade}",
    }[stage]


def _build_grade_birth_year_snapshot(stage: str, grade: int, school_year: int, current_year: int) -> dict[str, object]:
    snapshot = _build_grade_age_snapshot(stage, grade, school_year, current_year)
    short_label = _short_school_label(stage, grade)
    snapshot["short_label"] = short_label
    snapshot["query_label"] = f"{short_label}은 몇 년생"
    snapshot["school_year_label"] = f"{school_year}학년도"
    snapshot["detail"] = f"{school_year}학년도 {snapshot['label']}은 보통 {snapshot['birth_year_label']}이 해당합니다."
    return snapshot


def _build_birth_year_zodiac_snapshot(year: int, current_year: int) -> dict[str, object]:
    snapshot = _build_birth_year_snapshot(year, current_year)
    zodiac_label = f"{snapshot['zodiac']}띠"
    snapshot["zodiac_label"] = zodiac_label
    snapshot["detail"] = f"{snapshot['label']}은 {zodiac_label}이며, {snapshot['detail']}"
    return snapshot


def _format_college_cohort_label(entry_year: int) -> str:
    return f"{entry_year % 100:02d}학번"


def _build_college_entry_snapshot(entry_year: int, current_year: int) -> dict[str, object]:
    birth_year = entry_year - 19
    annual_age = current_year - birth_year
    man_age_range = _birth_year_range_label(birth_year, current_year)
    cohort_label = _format_college_cohort_label(entry_year)

    if entry_year > current_year:
        status_note = f"{cohort_label}은 아직 입학 전이거나 입학 준비 중인 시기로, 보통 {birth_year}년생 기준으로 안내합니다."
    elif entry_year == current_year:
        status_note = f"{cohort_label}은 올해 입학하는 신입생 기준이며, 보통 {birth_year}년생이 해당합니다."
    else:
        elapsed = current_year - entry_year
        status_note = f"{cohort_label}은 입학 후 {elapsed}년차 기준으로 보통 {birth_year}년생이 해당합니다."

    return {
        "entry_year": entry_year,
        "cohort_label": cohort_label,
        "birth_year": birth_year,
        "birth_year_label": f"{birth_year}년생",
        "annual_age": f"{annual_age}세",
        "man_age_range": man_age_range,
        "detail": status_note,
        "query_label": f"{cohort_label}은 보통 몇 년생",
    }


def _format_years_months(months: int) -> str:
    years, remaining_months = divmod(months, 12)
    if years == 0:
        return f"{remaining_months}개월"
    return f"{years}년 {remaining_months}개월"


def _baby_stage_label(months: int) -> str:
    if months <= 1:
        return "신생아 시기"
    if months <= 5:
        return "초기 영아기"
    if months <= 11:
        return "활동이 늘어나는 시기"
    if months <= 23:
        return "돌 이후 영아기"
    if months <= 35:
        return "두돌 이후 유아기 초반"
    return "세돌 전후 시기"


def _build_baby_month_snapshot(months: int) -> dict[str, object]:
    age_text = _format_years_months(months)
    stage = _baby_stage_label(months)

    if months == 0:
        note = "출생 직후부터 한 달 전까지는 수유, 수면, 체중 변화처럼 기본 생활 리듬을 살피는 시기입니다."
    elif months < 12:
        note = "예방접종, 수면 변화, 이유식 시작·확장처럼 월령 기준으로 자주 확인하는 정보가 많은 구간입니다."
    elif months < 24:
        note = "돌 이후에는 걷기, 말문, 식사 리듬처럼 생활 변화가 커져 월령별 흐름을 함께 보는 데 도움이 됩니다."
    else:
        note = "두돌 이후에는 개월 수와 함께 연령대 표현도 같이 쓰는 경우가 많아, 1년 단위와 월 단위를 함께 확인하는 편이 좋습니다."

    return {
        "months": months,
        "label": f"{months}개월",
        "age_text": age_text,
        "stage": stage,
        "note": note,
    }


@app.get("/sitemap.xml")
def sitemap():
    db_session = SessionLocal()
    try:
        posts = (
            db_session.query(GeneratedPost)
            .filter(GeneratedPost.status == "published")
            .order_by(GeneratedPost.published_at.desc(), GeneratedPost.id.desc())
            .all()
        )

        newest_post_dt = next(
            (
                post.published_at or post.updated_at or post.created_at
                for post in posts
                if post.published_at or post.updated_at or post.created_at
            ),
            None,
        )
        entries = []
        for endpoint in PUBLIC_SITEMAP_ENDPOINTS:
            lastmod = _format_sitemap_lastmod(newest_post_dt) if endpoint == "blog_list" else None
            entries.append(_build_sitemap_entry(_absolute_url_for(endpoint), lastmod))

        for post in posts:
            lastmod = _format_sitemap_lastmod(post.updated_at or post.published_at or post.created_at)
            entries.append(_build_sitemap_entry(_absolute_url_for("blog_detail", slug=post.slug), lastmod))
    finally:
        db_session.close()

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{chr(10).join(entries)}\n"
        "</urlset>\n"
    )
    return Response(xml, mimetype="application/xml")


@app.get('/')
def index():
    """메인 페이지 - 나이 계산 도구 안내"""
    return render_template('index.html')


@app.route('/age', methods=['GET', 'POST'])
def age():
    """만나이 계산 페이지 - 나이 계산 폼과 결과를 표시"""
    if request.method == 'POST':
        # AJAX 요청인지 확인
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX 요청 처리
            result = None
            birth_date = None
            
            # 개별 년/월/일 값 또는 전체 날짜 값 처리
            if 'birth_date' in request.form and request.form['birth_date']:
                birth_date = request.form['birth_date']
            elif all(key in request.form for key in ['year', 'month', 'day']):
                year = request.form['year']
                month = request.form['month'].zfill(2)
                day = request.form['day'].zfill(2)
                birth_date = f"{year}-{month}-{day}"
            
            calendar_type = request.form.get('calendar_type', 'solar')
            
            if birth_date:
                controller = AgeController()
                result = controller.calculate_age_from_string(birth_date, calendar_type)
                return jsonify(result)
            else:
                return jsonify({'success': False, 'message': '생년월일을 입력해주세요.'})
        
        # 일반 폼 제출 처리 (기존 코드 유지)
        result = None
        birth_date = None
        year = None
        month = None
        day = None
        calendar_type = 'solar'
        
        if 'birth_date' in request.form and request.form['birth_date']:
            birth_date = request.form['birth_date']
        elif all(key in request.form for key in ['year', 'month', 'day']):
            year = request.form['year']
            month = request.form['month'].zfill(2)
            day = request.form['day'].zfill(2)
            birth_date = f"{year}-{month}-{day}"
            
        calendar_type = request.form.get('calendar_type', 'solar')
        
        if birth_date:
            controller = AgeController()
            result = controller.calculate_age_from_string(birth_date, calendar_type)
    
    # GET 요청 또는 일반 폼 제출 시
    return render_template('age.html', result=result if 'result' in locals() else None, 
                         birth_date=birth_date if 'birth_date' in locals() else None, 
                         year=year if 'year' in locals() else None, 
                         month=month if 'month' in locals() else None, 
                         day=day if 'day' in locals() else None,
                         calendar_type=calendar_type if 'calendar_type' in locals() else 'solar')

@app.route('/privacy')
def privacy():
    """개인정보 처리 방침 페이지"""
    return render_template('privacy.html')

@app.route('/about')
def about():
    """운영 및 편집 원칙 페이지"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """문의 및 운영자 안내 페이지"""
    return render_template('contact.html')

@app.route('/references')
def references():
    """계산 기준과 참고 자료 안내 페이지"""
    return render_template('references.html')

@app.route('/birth-year-age-table')
def birth_year_age_table():
    """출생년도별 나이표 안내 페이지"""
    today = _current_local_date()
    current_year = today.year
    min_year = max(1900, current_year - 100)
    max_year = current_year

    selected_year = request.args.get('year', type=int)
    if selected_year is not None and not (min_year <= selected_year <= max_year):
        selected_year = None

    rows = []
    selected_row = None
    for year in range(max_year, min_year - 1, -1):
        row = _build_birth_year_snapshot(year, current_year)
        row["is_selected"] = year == selected_year
        rows.append(row)
        if row["is_selected"]:
            selected_row = row

    example_years = [year for year in (1990, 2000, 2010) if min_year <= year <= max_year]
    examples = [_build_birth_year_snapshot(year, current_year) for year in example_years]

    return render_template(
        'birth-year-age-table.html',
        current_year=current_year,
        selected_year=selected_year,
        selected_row=selected_row,
        birth_year_rows=rows,
        year_options=range(max_year, min_year - 1, -1),
        examples=examples,
    )

@app.route('/school-grade-calculator')
def school_grade_calculator():
    """출생년도 기준 학년 안내 페이지"""
    today = _current_local_date()
    school_year = _current_school_year(today)
    current_year = today.year
    min_year = max(1990, school_year - 19)
    max_year = current_year

    selected_year = request.args.get('year', type=int)
    if selected_year is not None and not (1900 <= selected_year <= current_year):
        selected_year = None

    rows = []
    selected_row = _build_school_grade_snapshot(selected_year, school_year) if selected_year else None
    for year in range(max_year, min_year - 1, -1):
        row = _build_school_grade_snapshot(year, school_year)
        row["is_selected"] = year == selected_year
        rows.append(row)

    example_years = [year for year in (school_year - 7, school_year - 10, school_year - 13, school_year - 16) if 1900 <= year <= current_year]
    examples = [_build_school_grade_snapshot(year, school_year) for year in example_years]

    return render_template(
        'school-grade-calculator.html',
        school_year=school_year,
        selected_year=selected_year,
        selected_row=selected_row,
        school_grade_rows=rows,
        year_options=range(max_year, min_year - 1, -1),
        examples=examples,
    )


@app.route('/school-entry-year-table')
def school_entry_year_table():
    """출생년도 기준 입학 학년도 안내 페이지"""
    today = _current_local_date()
    school_year = _current_school_year(today)
    current_year = today.year
    min_year = max(1990, school_year - 19)
    max_year = current_year

    selected_year = request.args.get('year', type=int)
    if selected_year is not None and not (1900 <= selected_year <= current_year):
        selected_year = None

    rows = []
    selected_row = _build_school_entry_snapshot(selected_year, school_year) if selected_year is not None else None
    for year in range(max_year, min_year - 1, -1):
        row = _build_school_entry_snapshot(year, school_year)
        row["is_selected"] = year == selected_year
        rows.append(row)

    example_years = [year for year in (2017, 2018, 2019, 2020) if 1900 <= year <= current_year]
    examples = [_build_school_entry_snapshot(year, school_year) for year in example_years]

    return render_template(
        'school-entry-year-table.html',
        school_year=school_year,
        selected_year=selected_year,
        selected_row=selected_row,
        school_entry_rows=rows,
        year_options=range(max_year, min_year - 1, -1),
        examples=examples,
    )

@app.route('/age-gap-calculator')
def age_gap_calculator():
    """출생년도 기준 나이 차이 안내 페이지"""
    current_year = _current_local_date().year
    min_year = max(1900, current_year - 100)
    max_year = current_year

    year_a = request.args.get('year_a', type=int)
    year_b = request.args.get('year_b', type=int)

    if year_a is not None and not (min_year <= year_a <= max_year):
        year_a = None
    if year_b is not None and not (min_year <= year_b <= max_year):
        year_b = None

    selected_gap = None
    if year_a is not None and year_b is not None:
        selected_gap = _build_age_gap_snapshot(year_a, year_b)

    example_pairs = [(1990, 1995), (2000, 2002), (2010, 2015)]
    examples = [
        _build_age_gap_snapshot(a, b)
        for a, b in example_pairs
        if min_year <= a <= max_year and min_year <= b <= max_year
    ]

    gap_rows = []
    for gap in range(0, 13):
        if gap == 0:
            note = "같은 출생년도라서 동갑인 경우입니다."
            man_gap = "만 0세 차이"
        else:
            note = f"연나이는 {gap}세 차이이고, 만나이는 생일 전후에 따라 {gap - 1}~{gap}세 차이로 보일 수 있습니다."
            man_gap = f"만 {gap - 1}~{gap}세 차이"
        gap_rows.append({
            "gap": f"{gap}년 차이",
            "man_gap": man_gap,
            "note": note,
        })

    return render_template(
        'age-gap-calculator.html',
        current_year=current_year,
        year_options=range(max_year, min_year - 1, -1),
        selected_year_a=year_a,
        selected_year_b=year_b,
        selected_gap=selected_gap,
        examples=examples,
        gap_rows=gap_rows,
    )

@app.route('/100-day-calculator')
def hundred_day_calculator():
    """시작일 기준 100일째 날짜 안내 페이지"""
    today = _current_local_date()
    current_year = today.year
    min_year = 1900
    max_year = current_year + 5

    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    day = request.args.get('day', type=int)

    selected_start_date = None
    if year is not None and month is not None and day is not None and min_year <= year <= max_year:
        selected_start_date = _parse_calendar_date(year, month, day)

    selected_snapshot = _build_hundred_day_snapshot(selected_start_date, today) if selected_start_date else None
    invalid_date = year is not None and month is not None and day is not None and selected_snapshot is None

    example_inputs = [
        ("커플 100일 예시", today - timedelta(days=30)),
        ("아기 백일 예시", today - timedelta(days=99)),
        ("프로젝트 회고 예시", today - timedelta(days=140)),
    ]
    examples = []
    for title, start_date in example_inputs:
        example = _build_hundred_day_snapshot(start_date, today)
        example["title"] = title
        examples.append(example)

    return render_template(
        '100-day-calculator.html',
        today=today,
        current_year=current_year,
        selected_snapshot=selected_snapshot,
        invalid_date=invalid_date,
        year=year,
        month=month,
        day=day,
        examples=examples,
    )


@app.route('/baby-months-table')
def baby_months_table():
    """생후 개월 수 기준 안내 페이지"""
    selected_months = request.args.get('months', type=int)
    if selected_months is not None and not (0 <= selected_months <= 36):
        selected_months = None

    month_rows = [_build_baby_month_snapshot(months) for months in range(0, 37)]
    selected_row = _build_baby_month_snapshot(selected_months) if selected_months is not None else None
    examples = [_build_baby_month_snapshot(months) for months in (6, 12, 18, 24, 36)]

    return render_template(
        'baby-months-table.html',
        selected_months=selected_months,
        selected_row=selected_row,
        month_rows=month_rows,
        month_options=range(0, 37),
        examples=examples,
    )


@app.route('/annual-age-calculator')
def annual_age_calculator():
    """출생연도 기준 연나이 안내 페이지"""
    today = _current_local_date()
    current_year = today.year
    min_year = 1900
    max_year = current_year

    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    day = request.args.get('day', type=int)

    selected_birth_date = None
    if year is not None and month is not None and day is not None and min_year <= year <= max_year:
        selected_birth_date = _parse_calendar_date(year, month, day)

    selected_snapshot = _build_annual_age_snapshot(selected_birth_date, current_year) if selected_birth_date else None
    invalid_date = year is not None and month is not None and day is not None and selected_snapshot is None

    example_dates = [
        datetime(1990, 1, 1).date(),
        datetime(2000, 6, 15).date(),
        datetime(2010, 12, 31).date(),
    ]
    examples = [_build_annual_age_snapshot(example_date, current_year) for example_date in example_dates]

    return render_template(
        'annual-age-calculator.html',
        current_year=current_year,
        today=today,
        selected_snapshot=selected_snapshot,
        invalid_date=invalid_date,
        year=year,
        month=month,
        day=day,
        examples=examples,
    )


@app.route('/age-comparison-table')
def age_comparison_table():
    """만나이와 연나이 비교 안내 페이지"""
    current_year = _current_local_date().year
    min_year = max(1900, current_year - 100)
    max_year = current_year

    selected_year = request.args.get('year', type=int)
    if selected_year is not None and not (min_year <= selected_year <= max_year):
        selected_year = None

    rows = []
    selected_row = None
    for year in range(max_year, min_year - 1, -1):
        row = _build_age_comparison_snapshot(year, current_year)
        row["is_selected"] = year == selected_year
        rows.append(row)
        if row["is_selected"]:
            selected_row = row

    example_years = [year for year in (1990, 1992, 2000, 2010) if min_year <= year <= max_year]
    examples = [_build_age_comparison_snapshot(year, current_year) for year in example_years]

    return render_template(
        'age-comparison-table.html',
        current_year=current_year,
        selected_year=selected_year,
        selected_row=selected_row,
        comparison_rows=rows,
        year_options=range(max_year, min_year - 1, -1),
        examples=examples,
    )


@app.route('/grade-age-table')
def grade_age_table():
    """학년 기준 나이표 페이지"""
    today = _current_local_date()
    school_year = _current_school_year(today)
    current_year = today.year

    stage = request.args.get('stage', default='elementary', type=str)
    grade = request.args.get('grade', type=int)

    valid_stage_grades = {"elementary": 6, "middle": 3, "high": 3}
    if stage not in valid_stage_grades:
        stage = "elementary"
    if grade is not None and not (1 <= grade <= valid_stage_grades[stage]):
        grade = None

    rows = []
    for stage_key, max_grade in valid_stage_grades.items():
        for grade_number in range(1, max_grade + 1):
            row = _build_grade_age_snapshot(stage_key, grade_number, school_year, current_year)
            row["is_selected"] = stage_key == stage and grade_number == grade
            rows.append(row)

    selected_row = _build_grade_age_snapshot(stage, grade, school_year, current_year) if grade is not None else None
    examples = [
        _build_grade_age_snapshot("elementary", 1, school_year, current_year),
        _build_grade_age_snapshot("middle", 1, school_year, current_year),
        _build_grade_age_snapshot("high", 1, school_year, current_year),
    ]

    return render_template(
        'grade-age-table.html',
        school_year=school_year,
        selected_stage=stage,
        selected_grade=grade,
        selected_row=selected_row,
        grade_rows=rows,
        examples=examples,
    )


@app.route('/pet-age-table')
def pet_age_table():
    """반려동물 나이표 페이지"""
    pet = request.args.get('pet', default='dog', type=str)
    years = request.args.get('years', type=int)
    size = request.args.get('size', default='small', type=str)

    if pet not in {"dog", "cat"}:
        pet = "dog"
    if size not in DOG_HUMAN_AGE_TABLE:
        size = "small"
    if years is not None and not (1 <= years <= 20):
        years = None

    selected_row = _build_pet_age_snapshot(pet, years, size) if years is not None else None

    dog_rows = []
    for age in range(1, 17):
        dog_rows.append({
            "years_label": f"{age}살",
            "small": f"{_calc_dog_human_age(age, 'small')}세",
            "medium": f"{_calc_dog_human_age(age, 'medium')}세",
            "large": f"{_calc_dog_human_age(age, 'large')}세",
            "giant": f"{_calc_dog_human_age(age, 'giant')}세",
        })

    cat_rows = []
    for age in range(1, 17):
        cat_rows.append({
            "years_label": f"{age}살",
            "human_age": f"{_calc_cat_human_age(age)}세",
        })

    examples = [
        _build_pet_age_snapshot("dog", 1, "small"),
        _build_pet_age_snapshot("dog", 7, "large"),
        _build_pet_age_snapshot("cat", 2),
    ]

    return render_template(
        'pet-age-table.html',
        pet=pet,
        years=years,
        size=size,
        selected_row=selected_row,
        dog_rows=dog_rows,
        cat_rows=cat_rows,
        examples=examples,
    )


@app.route('/korean-age-guide')
def korean_age_guide():
    """한국나이 폐지 이후 기준 정리 페이지"""
    return render_template('korean-age-guide.html')


@app.route('/pet-months-table')
def pet_months_table():
    """반려동물 월령표 페이지"""
    pet = request.args.get('pet', default='dog', type=str)
    months = request.args.get('months', type=int)
    size = request.args.get('size', default='small', type=str)

    if pet not in {"dog", "cat"}:
        pet = "dog"
    if size not in DOG_HUMAN_AGE_TABLE:
        size = "small"
    if months is not None and not (1 <= months <= 24):
        months = None

    selected_row = _build_pet_month_snapshot(pet, months, size) if months is not None else None

    dog_rows = []
    for month_value in range(1, 25):
        dog_rows.append({
            "months_label": f"{month_value}개월",
            "age_text": _format_years_months(month_value),
            "small": f"약 {round(_calc_dog_human_age_precise(month_value / 12, 'small'))}세",
            "medium": f"약 {round(_calc_dog_human_age_precise(month_value / 12, 'medium'))}세",
            "large": f"약 {round(_calc_dog_human_age_precise(month_value / 12, 'large'))}세",
            "giant": f"약 {round(_calc_dog_human_age_precise(month_value / 12, 'giant'))}세",
        })

    cat_rows = []
    for month_value in range(1, 25):
        cat_rows.append({
            "months_label": f"{month_value}개월",
            "age_text": _format_years_months(month_value),
            "human_age": f"약 {round(_calc_cat_human_age_precise(month_value / 12))}세",
        })

    examples = [
        _build_pet_month_snapshot("dog", 3, "small"),
        _build_pet_month_snapshot("dog", 12, "large"),
        _build_pet_month_snapshot("cat", 6),
    ]

    return render_template(
        'pet-months-table.html',
        pet=pet,
        months=months,
        size=size,
        selected_row=selected_row,
        dog_rows=dog_rows,
        cat_rows=cat_rows,
        examples=examples,
    )


@app.route('/grade-birth-year-table')
def grade_birth_year_table():
    """학년별 출생연도표 페이지"""
    today = _current_local_date()
    school_year = _current_school_year(today)
    current_year = today.year

    stage = request.args.get('stage', default='elementary', type=str)
    grade = request.args.get('grade', type=int)

    valid_stage_grades = {"elementary": 6, "middle": 3, "high": 3}
    if stage not in valid_stage_grades:
        stage = "elementary"
    if grade is not None and not (1 <= grade <= valid_stage_grades[stage]):
        grade = None

    rows = []
    for stage_key, max_grade in valid_stage_grades.items():
        for grade_number in range(1, max_grade + 1):
            row = _build_grade_birth_year_snapshot(stage_key, grade_number, school_year, current_year)
            row["is_selected"] = stage_key == stage and grade_number == grade
            rows.append(row)

    selected_row = _build_grade_birth_year_snapshot(stage, grade, school_year, current_year) if grade is not None else None
    examples = [
        _build_grade_birth_year_snapshot("elementary", 1, school_year, current_year),
        _build_grade_birth_year_snapshot("middle", 1, school_year, current_year),
        _build_grade_birth_year_snapshot("high", 1, school_year, current_year),
    ]

    return render_template(
        'grade-birth-year-table.html',
        school_year=school_year,
        selected_stage=stage,
        selected_grade=grade,
        selected_row=selected_row,
        grade_rows=rows,
        examples=examples,
    )


@app.route('/birth-year-zodiac-table')
def birth_year_zodiac_table():
    """출생연도별 띠표 페이지"""
    current_year = _current_local_date().year
    min_year = max(1900, current_year - 100)
    max_year = current_year

    selected_year = request.args.get('year', type=int)
    if selected_year is not None and not (min_year <= selected_year <= max_year):
        selected_year = None

    rows = []
    selected_row = None
    for year in range(max_year, min_year - 1, -1):
        row = _build_birth_year_zodiac_snapshot(year, current_year)
        row["is_selected"] = year == selected_year
        rows.append(row)
        if row["is_selected"]:
            selected_row = row

    example_years = [year for year in (1990, 2000, 2012, 2024) if min_year <= year <= max_year]
    examples = [_build_birth_year_zodiac_snapshot(year, current_year) for year in example_years]

    return render_template(
        'birth-year-zodiac-table.html',
        current_year=current_year,
        selected_year=selected_year,
        selected_row=selected_row,
        zodiac_rows=rows,
        year_options=range(max_year, min_year - 1, -1),
        examples=examples,
    )


@app.route('/college-entry-year-calculator')
def college_entry_year_calculator():
    """대학 학번 나이 계산기 페이지"""
    current_year = _current_local_date().year
    min_entry_year = max(1990, current_year - 20)
    max_entry_year = current_year + 1

    selected_year = request.args.get('year', type=int)
    if selected_year is not None and not (min_entry_year <= selected_year <= max_entry_year):
        selected_year = None

    rows = []
    selected_row = None
    for entry_year in range(max_entry_year, min_entry_year - 1, -1):
        row = _build_college_entry_snapshot(entry_year, current_year)
        row["is_selected"] = entry_year == selected_year
        rows.append(row)
        if row["is_selected"]:
            selected_row = row

    example_years = [year for year in (2024, 2025, 2026) if min_entry_year <= year <= max_entry_year]
    examples = [_build_college_entry_snapshot(year, current_year) for year in example_years]

    return render_template(
        'college-entry-year-calculator.html',
        current_year=current_year,
        selected_year=selected_year,
        selected_row=selected_row,
        college_rows=rows,
        year_options=range(max_entry_year, min_entry_year - 1, -1),
        examples=examples,
    )


@app.route('/birthday-dday-calculator')
def birthday_dday_calculator():
    """생일 D-day 계산기 페이지"""
    today = _current_local_date()
    month = request.args.get('month', type=int)
    day = request.args.get('day', type=int)

    selected_month_day = _parse_month_day(month, day)
    selected_snapshot = None
    invalid_date = month is not None and day is not None and selected_month_day is None

    if selected_month_day is not None:
        selected_snapshot = _build_birthday_dday_snapshot(selected_month_day[0], selected_month_day[1], today)

    example_inputs = [(1, 1), (5, 10), (12, 25)]
    examples = [
        _build_birthday_dday_snapshot(example_month, example_day, today)
        for example_month, example_day in example_inputs
    ]

    return render_template(
        'birthday-dday-calculator.html',
        today=today,
        month=month,
        day=day,
        selected_snapshot=selected_snapshot,
        invalid_date=invalid_date,
        examples=examples,
    )

@app.route('/terms')
def terms():
    """이용 약관 페이지"""
    return render_template('terms.html')

@app.route('/guide')
def guide():
    """가이드 페이지"""
    return render_template('guide.html')

@app.route('/faq')
def faq():
    """자주 묻는 질문 페이지"""
    return render_template('faq.html')

@app.route('/dog')
def dog():
    """강아지 나이 계산 페이지"""
    return render_template('dog.html')

@app.route('/cat')
def cat():
    """고양이 나이 계산 페이지"""
    return render_template('cat.html')

@app.route('/baby-months')
def baby_months():
    """아기 개월 수 계산 페이지"""
    return render_template('baby-months.html')

@app.route('/d-day')
def d_day():
    """기념일/D-Day 계산 페이지"""
    return render_template('d-day.html')

@app.route('/parent-child')
def parent_child():
    """부모·자녀 나이 관계 계산 페이지"""
    return render_template('parent-child.html')


@app.route('/blog')
def blog_list():
    page = request.args.get('page', default=1, type=int)
    page = max(page, 1)
    per_page = 8
    session = SessionLocal()

    base_query = (
        session.query(GeneratedPost)
        .filter(GeneratedPost.status == "published")
        .order_by(GeneratedPost.published_at.desc(), GeneratedPost.id.desc())
    )
    total = base_query.count()
    total_pages = max(1, math.ceil(total / per_page)) if total else 1
    if page > total_pages:
        page = total_pages

    posts = base_query.offset((page - 1) * per_page).limit(per_page).all()
    return render_template(
        'blog-list.html',
        posts=posts,
        page=page,
        total_pages=total_pages,
        total=total
    )


@app.route('/blog/<slug>')
def blog_detail(slug):
    session = SessionLocal()
    post = (
        session.query(GeneratedPost)
        .filter(GeneratedPost.slug == slug, GeneratedPost.status == "published")
        .first()
    )
    if post is None:
        abort(404)
    return render_template('blog-detail.html', post=post, draft_mode=False, review_mode=False)


@app.route('/blog/drafts', methods=['GET', 'POST'])
def blog_drafts():
    error = None

    if request.method == 'POST':
        if _draft_password_is_valid(request.form.get('password', '')):
            session.permanent = True
            session[BLOG_DRAFT_ACCESS_SESSION_KEY] = True
            return redirect(url_for('blog_drafts'))
        error = '비밀번호가 올바르지 않습니다.'

    if not _draft_access_granted():
        return render_template(
            'blog-drafts.html',
            access_granted=False,
            error=error,
            posts=[],
        )

    db_session = SessionLocal()
    posts = (
        db_session.query(GeneratedPost)
        .filter(GeneratedPost.status.in_(["draft", "needs_review"]))
        .order_by(GeneratedPost.created_at.desc(), GeneratedPost.id.desc())
        .all()
    )
    return render_template(
        'blog-drafts.html',
        access_granted=True,
        error=None,
        posts=posts,
    )


@app.post('/blog/drafts/logout')
def blog_drafts_logout():
    session.pop(BLOG_DRAFT_ACCESS_SESSION_KEY, None)
    return redirect(url_for('blog_drafts'))


@app.route('/blog/drafts/<slug>')
def blog_draft_detail(slug):
    if not _draft_access_granted():
        return redirect(url_for('blog_drafts'))

    db_session = SessionLocal()
    post = (
        db_session.query(GeneratedPost)
        .filter(GeneratedPost.slug == slug, GeneratedPost.status.in_(["draft", "needs_review"]))
        .first()
    )
    if post is None:
        abort(404)
    return render_template('blog-detail.html', post=post, draft_mode=True, review_mode=False)


@app.route('/blog/review/<int:post_id>')
def blog_review(post_id):
    token = request.args.get("token", "")
    if not _review_token_is_valid(token):
        abort(403)

    db_session = SessionLocal()
    post = db_session.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
    if post is None:
        abort(404)
    return render_template(
        'blog-detail.html',
        post=post,
        draft_mode=False,
        review_mode=True,
        review_token=token,
    )


@app.post('/blog/review/<int:post_id>/approve')
def blog_review_approve(post_id):
    token = request.args.get("token", "")
    if not _review_token_is_valid(token):
        abort(403)

    db_session = SessionLocal()
    post = db_session.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
    if post is None:
        abort(404)
    if post.status != "published":
        post.status = "published"
        post.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db_session.commit()
    return redirect(url_for('blog_detail', slug=post.slug))

@app.route('/minigames')
def minigames():
    """미니게임 모음 페이지"""
    return render_template('minigames.html')

@app.route('/minigames/guess')
def guess_game():
    """숫자 맞추기 게임 페이지"""
    return render_template('guess.html')

@app.route('/minigames/snake')
def snake_game():
    """스네이크 게임 페이지"""
    return render_template('snake.html')

@app.route('/minigames/tictactoe')
def tictactoe_game():
    """틱택토 게임 페이지"""
    return render_template('tictactoe.html')

@app.route('/minigames/rps')
def rps_game():
    """가위바위보 게임 페이지"""
    return render_template('rps.html')

@app.route('/minigames/nim')
def nim_game():
    """님 게임 페이지"""
    return render_template('nim.html')

@app.route('/minigames/pong')
def pong_game():
    """퐁 게임 페이지"""
    return render_template('pong.html')

@app.route('/minigames/hangman')
def hangman_game():
    """행맨 게임 페이지"""
    return render_template('hangman.html')

@app.route('/minigames/memory')
def memory_game():
    """메모리 매치 게임 페이지"""
    return render_template('memory.html')

@app.route('/minigames/connect4')
def connect4_game():
    """커넥트4 게임 페이지"""
    return render_template('connect4.html')

@app.route('/minigames/lightsout')
def lightsout_game():
    """라이츠아웃 게임 페이지"""
    return render_template('lightsout.html')

@app.route('/minigames/minesweeper')
def minesweeper_game():
    """지뢰찾기 게임 페이지"""
    return render_template('minesweeper.html')

@app.route('/minigames/simon')
def simon_game():
    """사이먼 게임 페이지"""
    return render_template('simon.html')

@app.route('/minigames/2048')
def game_2048():
    """2048 게임 페이지"""
    return render_template('2048.html')

@app.route('/minigames/blackjack')
def blackjack_game():
    """블랙잭 게임 페이지"""
    return render_template('blackjack.html')

@app.route('/minigames/breakout')
def breakout_game():
    """브레이크아웃 게임 페이지"""
    return render_template('breakout.html')

@app.route('/minigames/hanoi')
def hanoi_game():
    """하노이 게임 페이지"""
    return render_template('hanoi.html')

@app.route('/minigames/pig')
def pig_game():
    """피그 다이스 게임 페이지"""
    return render_template('pig.html')

@app.route('/minigames/gomoku')
def gomoku_game():
    """오목 게임 페이지"""
    return render_template('gomoku.html')

@app.route('/minigames/reversi')
def reversi_game():
    """리버시 게임 페이지"""
    return render_template('reversi.html')

@app.route('/minigames/dotsandboxes')
def dotsandboxes_game():
    """점 잇기 게임 페이지"""
    return render_template('dotsandboxes.html')

@app.route('/minigames/mancala')
def mancala_game():
    """만칼라 게임 페이지"""
    return render_template('mancala.html')

@app.route('/minigames/mastermind')
def mastermind_game():
    """마스터마인드 게임 페이지"""
    return render_template('mastermind.html')

@app.route('/minigames/war')
def war_game():
    """카드 전쟁 게임 페이지"""
    return render_template('war.html')

@app.route('/minigames/battleship')
def battleship_game():
    """해전 게임 페이지"""
    return render_template('battleship.html')

@app.route('/minigames/checkers')
def checkers_game():
    """체커 게임 페이지"""
    return render_template('checkers.html')

@app.route('/minigames/fifteen')
def fifteen_game():
    """15 퍼즐 게임 페이지"""
    return render_template('fifteen.html')

@app.route('/minigames/pegsolitaire')
def pegsolitaire_game():
    """페그 솔리테어 게임 페이지"""
    return render_template('pegsolitaire.html')

@app.route('/minigames/yahtzee')
def yahtzee_game():
    """야추 게임 페이지"""
    return render_template('yahtzee.html')



@app.post("/snake-score")
def snake_score():
    data = request.get_json(silent=True) or {}
    try:
        score = int(data.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    if score < 0:
        score = 0

    now = datetime.now()
    today = _date_key(now)
    month = _month_key(now)

    with _score_lock:
        scores = _load_scores()
        today_scores = [s for s in scores if s.get("date") == today]
        prev_daily_best = max([s.get("score", 0) for s in today_scores], default=0)
        scores.append({
            "score": score,
            "ts": now.isoformat(),
            "date": today,
            "month": month
        })
        # Keep recent 5000 scores
        if len(scores) > 5000:
            scores = scores[-5000:]
        _save_scores(scores)

    today_scores = [s for s in scores if s.get("date") == today]
    month_scores = [s for s in scores if s.get("month") == month]
    daily_best = max([s.get("score", 0) for s in today_scores], default=0)
    monthly_best = max([s.get("score", 0) for s in month_scores], default=0)
    higher = sum(1 for s in today_scores if s.get("score", 0) > score)
    rank = higher + 1
    total = len(today_scores)
    is_new_daily_best = score > prev_daily_best and score > 0
    return jsonify({
        "ok": True,
        "rank": rank,
        "total": total
    })


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
