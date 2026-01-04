from datetime import date

def get_current_academic_year() -> str:
    """
    Determines the academic year based on the current date.
    Assumes academic year starts in April.
    
    If Month >= April (4):
        Year = Current Year - (Current Year + 1)
        Example: May 2025 -> 2025-26
        
    If Month < April (4):
        Year = (Current Year - 1) - Current Year
        Example: March 2025 -> 2024-25
    """
    today = date.today()
    month = today.month
    year = today.year
    
    if month >= 4:
        start_year = year
        end_year = year + 1
    else:
        start_year = year - 1
        end_year = year
        
    # Format: YYYY-YY (e.g., 2025-26)
    short_end_year = str(end_year)[-2:]
    return f"{start_year}-{short_end_year}"
