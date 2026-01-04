from typing import Dict, Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field

# --- Structure Request/Response ---
class SalaryStructureRequest(BaseModel):
    salary_type: str = "monthly"
    basic: float
    allowances: Dict[str, float] = {}
    deductions: Dict[str, float] = {}
    effective_from: date

class SalaryStructureResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None 

# --- Generate Request ---
class GenerateSalaryRequest(BaseModel):
    month: str # "YYYY-MM"

# --- List Response ---
class SalaryListItem(BaseModel):
    salary_id: str
    teacher_id: str
    teacher_name: str
    month: str
    net_payable: float
    status: str
    locked: bool

class SalaryListResponse(BaseModel):
    success: bool
    data: List[SalaryListItem]

# --- Payment Request ---
class MarkPaidRequest(BaseModel):
    mode: str
    paid_on: date

class GenericResponse(BaseModel):
    success: bool
    message: str
