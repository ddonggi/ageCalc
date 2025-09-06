from models.age_calculator import AgeCalculator

class AgeController:
    """나이 계산 요청을 처리하는 Controller 클래스"""
    
    def __init__(self):
        self.age_calculator = AgeCalculator()
    
    def calculate_age_from_string(self, birth_date_string):
        """
        생년월일 문자열로부터 나이를 계산
        
        Args:
            birth_date_string (str): YYYY-MM-DD 형식의 날짜 문자열
            
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
        
        # 나이 계산
        age = self.age_calculator.calculate_age(birth_date)
        
        return {
            'success': True,
            'message': f'생년월일: {birth_date_string}',
            'age': age
        }

