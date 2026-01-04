from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

# --- Salary Structure (Configuration) ---
class TeacherSalaryStructure(BaseModel):
    id: str = Field(alias="_id")
    
    org_id: str
    school_id: str
    teacher_id: str
    
    salary_type: str = "monthly" # monthly | per_day
    
    basic: float
    allowances: Dict[str, float] = {} # e.g. {"hra": 5000}
    deductions: Dict[str, float] = {} # e.g. {"pf": 1800}
    
    effective_from: datetime # or date string stored as datetime
    status: str = "active" # active | inactive
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True

# --- Monthly Salary Record ---
class AttendanceSummary(BaseModel):
    working_days: int
    present: float
    absent: float
    paid_leaves: float
    source: str = "SYSTEM_DEFAULT" # SYSTEM_DEFAULT | ATTENDANCE_MODULE

class SalaryCalculation(BaseModel):
    basic: float
    allowances_total: float
    gross: float
    deductions_total: float
    net_payable: float

class PaymentInfo(BaseModel):
    status: str = "pending" # pending | paid
    paid_on: Optional[datetime] = None
    mode: Optional[str] = None # bank | cash | cheque

class TeacherSalary(BaseModel):
    id: str = Field(alias="_id")
    
    org_id: str
    school_id: str
    teacher_id: str
    
    month: str # "YYYY-MM" format
    
    attendance_summary: AttendanceSummary
    calculation: SalaryCalculation
    payment: PaymentInfo
    
    locked: bool = False
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
