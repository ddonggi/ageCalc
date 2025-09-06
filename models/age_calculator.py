from datetime import datetime

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
        today = datetime.now()
        age = today.year - birth_date.year
        
        # 생일이 지나지 않았으면 1살 빼기
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        return age
    
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

