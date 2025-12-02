from korean_lunar_calendar import KoreanLunarCalendar

def inspect_library():
    calendar = KoreanLunarCalendar()
    calendar.setLunarDate(1990, 1, 1, False)
    
    print(f"SolarIsoFormat: {getattr(calendar, 'SolarIsoFormat', 'Not Found')}")
    print(f"solarYear: {calendar.solarYear}")
    print(f"solarMonth: {calendar.solarMonth}")
    print(f"solarDay: {calendar.solarDay}")

if __name__ == "__main__":
    inspect_library()
