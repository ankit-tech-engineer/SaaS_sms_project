from datetime import datetime
from uuid import uuid4
from fastapi import HTTPException
from app.core.database import get_database
from app.core.academic_year import get_current_academic_year
from app.core.roll_number import generate_next_roll_number
from app.core.security_student import get_password_hash
from app.modules.students.schema import StudentAdmissionRequest
from app.modules.students.model import Student, AcademicInfo, PersonalInfo, ParentInfo
from app.modules.students.student_users.model import StudentUser, StudentSecurity

class StudentService:
    @staticmethod
    async def admit_student(
        request: StudentAdmissionRequest,
        org_id: str,
        school_id: str,
        created_by: str
    ):
        db = await get_database()
        
        # 1. Validate Class & Section
        # Verify strict context: class_id and section_id must belong to school_id
        section = await db["sections"].find_one({"_id": request.academic.section_id, "school_id": school_id})
        if not section:
            raise HTTPException(status_code=400, detail="Invalid section or does not belong to school")
            
        if section.get("class_id") != request.academic.class_id:
            raise HTTPException(status_code=400, detail="Section does not belong to the specified class")
            
        # 2. Check Duplicate Admission No
        existing_student = await db["students"].find_one({
            "school_id": school_id, 
            "academic.admission_no": request.academic.admission_no
        })
        if existing_student:
            raise HTTPException(status_code=400, detail="Admission number already exists")

        # 3. Auto-detect Academic Year
        academic_year = get_current_academic_year()
        
        # 4. Auto-assign Roll No
        roll_no = await generate_next_roll_number(
            school_id=school_id,
            class_id=request.academic.class_id,
            section_id=request.academic.section_id,
            academic_year=academic_year
        )
        
        student_id = f"stu_{uuid4().hex[:12]}"
        
        # 5. Prepare Student Document (Business Data)
        student_doc = Student(
            _id=student_id,
            org_id=org_id,
            school_id=school_id,
            academic=AcademicInfo(
                class_id=request.academic.class_id,
                section_id=request.academic.section_id,
                roll_no=roll_no,
                admission_no=request.academic.admission_no,
                academic_year=academic_year
            ),
            personal=PersonalInfo(
                first_name=request.personal.first_name,
                last_name=request.personal.last_name,
                gender=request.personal.gender,
                dob=datetime.combine(request.personal.dob, datetime.min.time())
            ),
            parent=ParentInfo(
                father_name=request.parent.father_name,
                mother_name=request.parent.mother_name,
                mobile=request.parent.mobile,
                email=request.parent.email
            ),
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 6. Auto-create Student User (Auth Data)
        # Generate Temporary Password
        import random
        import string
        temp_password_raw = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$", k=8))
        hashed_password = get_password_hash(temp_password_raw)
        
        student_user_id = f"stu_user_{uuid4().hex[:12]}"
        
        student_user_doc = StudentUser(
            _id=student_user_id,
            org_id=org_id,
            school_id=school_id,
            student_id=student_id,
            username=request.academic.admission_no, # Using Admission No as Username per prompt example
            password=hashed_password,
            security=StudentSecurity(force_password_change=True),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 7. Atomic Write
        await db["students"].insert_one(student_doc.model_dump(by_alias=True))
        await db["student_users"].insert_one(student_user_doc.model_dump(by_alias=True))
        
        return {
            "student_id": student_id,
            "academic": {
                "roll_no": roll_no,
                "academic_year": academic_year
            },
            "student_login": {
                "username": request.academic.admission_no,
                "temporary_password": temp_password_raw
            }
        }
