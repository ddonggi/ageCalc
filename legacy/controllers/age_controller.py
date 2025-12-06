from models.age_calculator import AgeCalculator
from korean_lunar_calendar import KoreanLunarCalendar

class AgeController:
    """나이 계산 요청을 처리하는 Controller 클래스"""
    
    def __init__(self):
        self.age_calculator = AgeCalculator()
        self.lunar_calendar = KoreanLunarCalendar()
    
    def calculate_age_from_string(self, birth_date_string, calendar_type='solar'):
        """
        생년월일 문자열로부터 나이를 계산
        
        Args:
            birth_date_string (str): YYYY-MM-DD 형식의 날짜 문자열
            calendar_type (str): 'solar' (양력) 또는 'lunar' (음력)
            
        Returns:
            dict: 계산 결과를 담은 딕셔너리
        """
        if not birth_date_string:
            return {
                'success': False,
                'message': '생년월일을 입력해주세요.',
                'age': None
            }
        
        # 날짜 파싱
        birth_date = self.age_calculator.parse_birth_date(birth_date_string)
        
        if birth_date is None:
            return {
                'success': False,
                'message': '올바른 날짜 형식을 입력해주세요 (YYYY-MM-DD)',
                'age': None
            }
            
        # 음력인 경우 양력으로 변환
        original_birth_date_string = birth_date_string
        is_lunar = calendar_type == 'lunar'
        
        if is_lunar:
            try:
                self.lunar_calendar.setLunarDate(birth_date.year, birth_date.month, birth_date.day, False)
                solar_date_string = self.lunar_calendar.SolarIsoFormat()
                birth_date = self.age_calculator.parse_birth_date(solar_date_string)
                birth_date_string = solar_date_string # 계산에 사용할 양력 날짜로 업데이트
            except Exception as e:
                return {
                    'success': False,
                    'message': '음력 날짜 변환 중 오류가 발생했습니다. 올바른 날짜인지 확인해주세요.',
                    'age': None
                }
        
        # 나이 계산
        age = self.age_calculator.calculate_age(birth_date)
        
        message = f'생년월일: {original_birth_date_string}'
        if is_lunar:
            message += f' (음력) → 양력 환산: {birth_date_string}'
        
        return {
            'success': True,
            'message': message,
            'age': age
        }

