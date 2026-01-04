from datetime import datetime
from uuid import uuid4
from fastapi import HTTPException
from app.core.database import get_database
from app.modules.salaries.model import (
    TeacherSalaryStructure, TeacherSalary, 
    AttendanceSummary, SalaryCalculation, PaymentInfo
)
from app.modules.salaries.schema import (
    SalaryStructureRequest, GenerateSalaryRequest, MarkPaidRequest
)

class SalaryService:
    @staticmethod
    async def set_salary_structure(
        teacher_id: str,
        request: SalaryStructureRequest,
        org_id: str,
        school_id: str
    ):
        db = await get_database()
        
        # 1. Validate Teacher
        teacher = await db["teachers"].find_one({"_id": teacher_id, "school_id": school_id})
        if not teacher:
             raise HTTPException(status_code=404, detail="Teacher not found")
        
        # 2. Deactivate Old Structures
        await db["teacher_salary_structures"].update_many(
            {"teacher_id": teacher_id, "status": "active"},
            {"$set": {"status": "inactive"}}
        )
        
        # 3. Create New Structure
        struct_id = f"sal_struct_{uuid4().hex[:12]}"
        
        # Handle date conversion if needed, pydantic usually handles date->datetime in model validation if hinted
        effective_date = datetime.combine(request.effective_from, datetime.min.time())
        
        new_struct = TeacherSalaryStructure(
            _id=struct_id,
            org_id=org_id,
            school_id=school_id,
            teacher_id=teacher_id,
            salary_type=request.salary_type,
            basic=request.basic,
            allowances=request.allowances,
            deductions=request.deductions,
            effective_from=effective_date,
            status="active"
        )
        
        await db["teacher_salary_structures"].insert_one(new_struct.model_dump(by_alias=True))
        
        return {
            "success": True, 
            "message": "Salary structure updated successfully",
            "data": new_struct.model_dump()
        }

    @staticmethod
    async def get_salary_structure(teacher_id: str, school_id: str):
        db = await get_database()
        struct = await db["teacher_salary_structures"].find_one({
            "teacher_id": teacher_id,
            "school_id": school_id,
            "status": "active"
        })
        return struct

    @staticmethod
    async def generate_monthly_salaries(
        request: GenerateSalaryRequest,
        org_id: str,
        school_id: str
    ):
        db = await get_database()
        
        # 1. Get All Active Teachers in School
        teachers_cursor = db["teachers"].find({"school_id": school_id, "status": "active"})
        teachers = await teachers_cursor.to_list(length=1000)
        
        generated_count = 0
        errors = []
        
        for teacher in teachers:
            t_id = teacher["_id"]
            
            # 2. Check for existing Salary for this month
            existing = await db["teacher_salaries"].find_one({
                "teacher_id": t_id,
                "month": request.month
            })
            if existing:
                # Skip if already exists (or maybe update if not locked? But user said 'Generate' usually implies creation)
                # Let's skip to avoid overwriting logic unless explicit recalculate.
                continue
                
            # 3. Get Active Structure
            struct = await db["teacher_salary_structures"].find_one({
                "teacher_id": t_id,
                "status": "active"
            })
            
            if not struct:
                errors.append(f"No active structure for teacher {t_id}")
                continue
            
            # 4. Calculation Logic (Assumption: 26 Working Days, Full Attendance)
            # Default Values
            working_days = 26
            present = 26
            absent = 0
            paid_leaves = 0
            
            # TODO: Future Attendance Integration here
            
            # Calculate Amounts
            # Simple Logic: (Basic / Working Days) * Present ??? 
            # OR Fixed Monthly if full attendance?
            # User instructions imply: "Set attendance_summary as: present = working_days... Calculate salary"
            # We will assume full salary for now as per "Attendance assumed FULL by default"
            
            basic_amt = struct["basic"]
            allowances_total = sum(struct["allowances"].values())
            gross = basic_amt + allowances_total
            deductions_total = sum(struct["deductions"].values())
            net = gross - deductions_total
            
            # 5. Create Salary Record
            sal_id = f"salary_{request.month.replace('-', '')}_{t_id}"
            
            salary_doc = TeacherSalary(
                _id=sal_id,
                org_id=org_id,
                school_id=school_id,
                teacher_id=t_id,
                month=request.month,
                attendance_summary=AttendanceSummary(
                    working_days=working_days,
                    present=present,
                    absent=absent,
                    paid_leaves=paid_leaves,
                    source="SYSTEM_DEFAULT"
                ),
                calculation=SalaryCalculation(
                    basic=basic_amt,
                    allowances_total=allowances_total,
                    gross=gross,
                    deductions_total=deductions_total,
                    net_payable=net
                ),
                payment=PaymentInfo(status="pending")
            )
            
            await db["teacher_salaries"].insert_one(salary_doc.model_dump(by_alias=True))
            generated_count += 1
            
        return {
            "success": True, 
            "message": f"Generated salaries for {generated_count} teachers",
            "errors": errors
        }

    @staticmethod
    async def mark_as_paid(
        salary_id: str,
        request: MarkPaidRequest,
        school_id: str
    ):
        db = await get_database()
        
        # 1. Fetch Salary
        salary = await db["teacher_salaries"].find_one({"_id": salary_id, "school_id": school_id})
        if not salary:
            raise HTTPException(status_code=404, detail="Salary record not found")
            
        if salary.get("locked"):
            raise HTTPException(status_code=400, detail="Salary is already paid and locked")
            
        # 2. Update & Lock
        paid_on_dt = datetime.combine(request.paid_on, datetime.min.time())
        
        await db["teacher_salaries"].update_one(
            {"_id": salary_id},
            {"$set": {
                "payment.status": "paid",
                "payment.paid_on": paid_on_dt,
                "payment.mode": request.mode,
                "locked": True
            }}
        )
        
        return {"success": True, "message": "Salary marked as paid and locked"}

    @staticmethod
    async def list_salaries(month: str, school_id: str):
        db = await get_database()
        
        pipeline = [
            {"$match": {"school_id": school_id, "month": month}},
            {"$lookup": {
                "from": "teachers",
                "localField": "teacher_id",
                "foreignField": "_id",
                "as": "teacher_info"
            }},
            {"$unwind": "$teacher_info"},
            {"$project": {
                "salary_id": "$_id",
                "teacher_id": "$teacher_id",
                "teacher_name": {
                    "$concat": ["$teacher_info.personal.first_name", " ", "$teacher_info.personal.last_name"]
                },
                "month": "$month",
                "net_payable": "$calculation.net_payable",
                "status": "$payment.status",
                "locked": "$locked"
            }}
        ]
        
        results = await db["teacher_salaries"].aggregate(pipeline).to_list(length=1000)
        return results
