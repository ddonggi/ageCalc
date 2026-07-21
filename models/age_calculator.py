from datetime import datetime

from models.date_rules import calculate_man_age

class AgeCalculator:
    """만 나이 계산을 담당하는 Model 클래스"""
    
    @staticmethod
    def calculate_age(birth_date):
        """
        생년월일을 받아서 만 나이를 계산
        
        Args:
            birth_date (datetime): 생년월일
            
        Returns:
            int: 만 나이
        """
        today = datetime.now().date()
        return calculate_man_age(birth_date.date(), today)
    
    @staticmethod
    def parse_birth_date(date_string):
        """
        날짜 문자열을 datetime 객체로 변환
        
        Args:
            date_string (str): YYYY-MM-DD 형식의 날짜 문자열
            
        Returns:
            datetime: 파싱된 날짜 객체 또는 None
        """
        try:
            return datetime.strptime(date_string, '%Y-%m-%d')
        except ValueError:
            return None
