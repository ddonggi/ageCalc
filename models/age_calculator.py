from datetime import datetime
import re

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
            date_string (str): YYYY-MM-DD 또는 YYMMDD 형식의 날짜 문자열
            
        Returns:
            datetime: 파싱된 날짜 객체 또는 None
        """
        if not date_string:
            return None

        normalized = date_string.strip()

        # 6자리(YYMMDD) 입력 처리
        if re.fullmatch(r"\d{6}", normalized):
            normalized = AgeCalculator.expand_compact_date(normalized)
            if not normalized:
                return None

        try:
            return datetime.strptime(normalized, '%Y-%m-%d')
        except ValueError:
            return None

    @staticmethod
    def expand_compact_date(compact_date: str):
        """YYMMDD → YYYY-MM-DD 변환"""
        if not re.fullmatch(r"\d{6}", compact_date):
            return None

        year_part = int(compact_date[:2])
        month = int(compact_date[2:4])
        day = int(compact_date[4:])

        current_two_digit = int(str(datetime.now().year)[-2:])
        century = 2000 if year_part <= current_two_digit else 1900
        full_year = century + year_part

        try:
            datetime(full_year, month, day)
        except ValueError:
            return None

        return f"{full_year:04d}-{month:02d}-{day:02d}"

