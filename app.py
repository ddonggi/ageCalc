from flask import Flask, render_template, request, jsonify
from controllers.age_controller import AgeController

app = Flask(__name__)

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


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
