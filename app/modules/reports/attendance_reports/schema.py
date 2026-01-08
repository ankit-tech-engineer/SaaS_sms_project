from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date

class DailySummaryResponse(BaseModel):
    date: date
    total_students: int
    present: int
    absent: int
    late: int
    half_day: int
    on_leave: int
    attendance_percentage: float
    
class StudentMonthlySummary(BaseModel):
    student_id: str
    month: str # YYYY-MM
    total_working_days: int
    present_days: int
    absent_days: int
    percentage: float
    
class SectionMonthlySummary(BaseModel):
    class_id: str
    section_id: str
    month: str
    total_students: int
    avg_percentage: float
    
class DefaulterStudent(BaseModel):
    student_id: str
    student_name: Optional[str] = None # Enriched if possible, otherwise ID
    attendance_percentage: float
    days_absent: int
    
class TrendDataPoint(BaseModel):
    month: str
    average_percentage: float

class AttendanceTrendResponse(BaseModel):
    class_id: str
    section_id: str
    trend: List[TrendDataPoint]

class StudentRangeSummary(BaseModel):
    student_id: str
    start_date: str
    end_date: str
    total_working_days: int
    present_days: int
    absent_days: int
    percentage: float

class StudentAttendanceLog(BaseModel):
    date: date
    status: str

