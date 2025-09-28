from flask import Flask, render_template, request, jsonify
from controllers.age_controller import AgeController

app = Flask(__name__)

@app.get("/health") 
def health(): 
    return {"ok": True}, 200


@app.route('/', methods=['GET', 'POST'])
def index():
    """메인 페이지 - 나이 계산 폼과 결과를 표시"""
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
            
            if birth_date:
                controller = AgeController()
                result = controller.calculate_age_from_string(birth_date)
                return jsonify(result)
            else:
                return jsonify({'success': False, 'message': '생년월일을 입력해주세요.'})
        
        # 일반 폼 제출 처리 (기존 코드 유지)
        result = None
        birth_date = None
        year = None
        month = None
        day = None
        
        if 'birth_date' in request.form and request.form['birth_date']:
            birth_date = request.form['birth_date']
        elif all(key in request.form for key in ['year', 'month', 'day']):
            year = request.form['year']
            month = request.form['month'].zfill(2)
            day = request.form['day'].zfill(2)
            birth_date = f"{year}-{month}-{day}"
        
        if birth_date:
            controller = AgeController()
            result = controller.calculate_age_from_string(birth_date)
    
    # GET 요청 또는 일반 폼 제출 시
    return render_template('index.html', result=result if 'result' in locals() else None, 
                         birth_date=birth_date if 'birth_date' in locals() else None, 
                         year=year if 'year' in locals() else None, 
                         month=month if 'month' in locals() else None, 
                         day=day if 'day' in locals() else None)

@app.route('/privacy')
def privacy():
    """개인정보 처리 방침 페이지"""
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    """이용 약관 페이지"""
    return render_template('terms.html')

if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
