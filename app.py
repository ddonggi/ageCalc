from flask import Flask, render_template, request, jsonify, g
import json
import os
import threading
from datetime import datetime
import secrets
from controllers.age_controller import AgeController

app = Flask(__name__)
_score_lock = threading.Lock()
_score_file = os.path.join(app.root_path, "data", "snake_scores.json")

@app.before_request
def set_csp_nonce():
    g.csp_nonce = secrets.token_urlsafe(16)

@app.context_processor
def inject_csp_nonce():
    return {"csp_nonce": getattr(g, "csp_nonce", "")}

@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    nonce = getattr(g, "csp_nonce", "")
    csp = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        f"script-src 'self' 'nonce-{nonce}' https://www.googletagmanager.com https://www.clarity.ms; "
        "connect-src 'self' https://www.google-analytics.com https://www.clarity.ms; "
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

@app.route('/parent-child')
def parent_child():
    """부모·자녀 나이 관계 계산 페이지"""
    return render_template('parent-child.html')

@app.route('/minigames')
def minigames():
    """미니게임 모음 페이지"""
    return render_template('minigames.html')

@app.route('/minigames/snake')
def snake_game():
    """스네이크 게임 페이지"""
    return render_template('snake.html')



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
