import re

from models.age_calculator import AgeCalculator
from korean_lunar_calendar import KoreanLunarCalendar

class AgeController:
    """나이 계산 요청을 처리하는 Controller 클래스"""
    
    def __init__(self):
        self.age_calculator = AgeCalculator()
        self.lunar_calendar = KoreanLunarCalendar()
    
    def calculate_age_from_string(self, birth_date_string, calendar_type='solar', *, reference_date=None):
        """
        생년월일 문자열로부터 나이를 계산
        
        Args:
            birth_date_string (str): YYYY-MM-DD 형식의 날짜 문자열
            calendar_type (str): 'solar' (양력) 또는 'lunar' (음력)
            reference_date (date): 요청에 표시된 만나이 계산 기준일
            
        Returns:
            dict: 계산 결과를 담은 딕셔너리
        """
        if not birth_date_string:
            return {
                'success': False,
                'message': '생년월일을 입력해주세요.',
                'age': None
            }
        
        original_birth_date_string = birth_date_string
        is_lunar = calendar_type == 'lunar'
        if is_lunar:
            match = re.fullmatch(r'([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})', birth_date_string)
            if not match or not self.lunar_calendar.setLunarDate(*map(int, match.groups()), False):
                return {
                    'success': False,
                    'message': '지원하지 않거나 존재하지 않는 음력 날짜입니다. 평달 생년월일을 확인해주세요.',
                    'age': None,
                }
            birth_date_string = self.lunar_calendar.SolarIsoFormat()

        birth_date = self.age_calculator.parse_birth_date(birth_date_string)
        if birth_date is None:
            return {
                'success': False,
                'message': '올바른 날짜 형식을 입력해주세요 (YYYY-MM-DD)',
                'age': None,
            }

        # 나이 계산
        try:
            age = self.age_calculator.calculate_age(birth_date, reference_date=reference_date)
        except ValueError:
            return {
                'success': False,
                'message': '미래의 생년월일은 계산할 수 없습니다.',
                'age': None,
            }
        
        message = f'생년월일: {original_birth_date_string}'
        if is_lunar:
            message += f' (음력) → 양력 환산: {birth_date_string}'
        
        return {
            'success': True,
            'message': message,
            'age': age,
            'solar_birth_year': birth_date.year,
        }
