from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
from fastapi import Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from app.utils.response import APIResponse

from app.core.config import settings
from app.core.database import db
from app.middlewares.audit import AuditMiddleware
from app.middlewares.auth import AuthMiddleware
from app.middlewares.org_context import OrgContextMiddleware
from app.middlewares.school_context import SchoolContextMiddleware
from app.middlewares.school_user_context import SchoolUserContextMiddleware # New
from app.modules.auth.service import AuthService

# Routers

# Routers
from app.modules.auth.router import router as auth_router
from app.modules.platform_admin.router import router as platform_admin_router
from app.modules.plans.router import router as plans_router
from app.modules.organizations.router import router as org_router
from app.modules.subscriptions.router import router as sub_router
from app.modules.payments.router import router as payment_router
from app.modules.organizations.org_auth.router import router as org_auth_router
from app.modules.audit.router import router as audit_router
from app.modules.schools.router import router as school_router
from app.modules.schools.school_auth.router import router as school_auth_router
from app.modules.academics.classes.router import router as classes_router
from app.modules.academics.sections.router import router as sections_router
from app.modules.academics.subjects.router import router as subjects_router
from app.modules.students.router import router as students_router
from app.modules.students.student_auth.router import router as student_auth_router
from app.modules.teachers.router import router as teachers_router # New
from app.modules.teachers.teacher_auth.router import router as teacher_auth_router # New
from app.modules.teachers.section_coordinators.router import router as section_coordinators_router # New
from app.modules.salaries.router import router as salaries_router # New
from app.modules.teachers.teacher_assignments.router import router as teacher_assignments_router # New
from app.modules.holidays.router import router as holidays_router # New
from app.modules.attendance.router import router as attendance_router # New
from app.modules.attendance.attendance_corrections.router import teacher_router as attendance_corrections_teacher_router, admin_router as attendance_corrections_admin_router # New
from app.modules.reports.attendance_reports.router import (
    router as attendance_reports_router, 
    coordinator_router as attendance_reports_coordinator_router,
    student_router as attendance_reports_student_router # New
)
from app.modules.holidays.model import ensure_holiday_indexes
from app.modules.attendance.model import ensure_attendance_indexes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db.connect()
    # Init Super Admin
    await AuthService.init_super_admin()
    await ensure_holiday_indexes()
    await ensure_attendance_indexes()
    
    yield
    
    # Shutdown
    db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return APIResponse.error(
        message=exc.detail,
        status_code=exc.status_code
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Get the first error message for simplicity
    errors = exc.errors()
    error_msg = f"Validation Error: {errors[0]['msg']} in {errors[0]['loc']}" if errors else "Validation Error"
    return APIResponse.error(
        message=error_msg,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        data=jsonable_encoder(errors)
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # In production, log the error here
    return APIResponse.error(
        message="Internal Server Error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        data=str(exc) if settings.PROJECT_NAME else None # Show error in dev
    )

from app.middlewares.status_guard import StatusGuardMiddleware

# Middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS] or ["*"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(StatusGuardMiddleware) # Master Status Guard (Runs internal to Auth/Contexts)
app.add_middleware(AuditMiddleware)
app.add_middleware(AuthMiddleware) # Platform Auth
app.add_middleware(OrgContextMiddleware) # Org Context Auth
app.add_middleware(SchoolContextMiddleware) # School Context Auth
app.add_middleware(SchoolUserContextMiddleware) # School User Context (New)

# --- Platform Routes Group ---
platform_router = APIRouter()

platform_router.include_router(auth_router, prefix="/auth", tags=["Platform: Auth"])
platform_router.include_router(platform_admin_router, prefix="/admin", tags=["Platform: Admin"])
platform_router.include_router(plans_router, prefix="/plans", tags=["Platform: Plans"])
platform_router.include_router(sub_router, prefix="/subscriptions", tags=["Platform: Subscriptions"])
platform_router.include_router(payment_router, prefix="/payments", tags=["Platform: Payments"])
platform_router.include_router(audit_router, prefix="/audit", tags=["Platform: Audit"])

# Mount Platform Routes
app.include_router(platform_router, prefix="/platform")

# --- Public Routes Group ---
public_router = APIRouter()
public_router.include_router(org_router, prefix="/org", tags=["Public: Organizations"])

# Mount Public Routes
app.include_router(public_router, prefix="/public")

# --- Org Routes Group ---
org_app_router = APIRouter()
org_app_router.include_router(org_auth_router, prefix="/auth", tags=["Org: Auth"])
org_app_router.include_router(school_router, prefix="/schools", tags=["Org: Schools"])

# Mount Org Routes
app.include_router(org_app_router, prefix="/org")

# --- School Routes Group ---
school_app_router = APIRouter()
school_app_router.include_router(school_auth_router, prefix="/auth", tags=["School: Auth"])
school_app_router.include_router(sections_router, prefix="/classes", tags=["School: Academics (Sections)"])
school_app_router.include_router(subjects_router, prefix="/classes", tags=["School: Academics (Subjects)"])
school_app_router.include_router(classes_router, prefix="/classes", tags=["School: Academics (Classes)"])
school_app_router.include_router(students_router, tags=["School: Students"])
school_app_router.include_router(teachers_router, tags=["School: Teachers"]) # New
school_app_router.include_router(section_coordinators_router, tags=["School: Coordinators"]) # New
school_app_router.include_router(salaries_router, tags=["School: Salaries"]) # New
school_app_router.include_router(teacher_assignments_router, tags=["School: Class Teacher Assignments"]) # Admin Access
school_app_router.include_router(holidays_router, tags=["School: Holidays"]) # New
school_app_router.include_router(attendance_router, tags=["School: Attendance"]) # New
school_app_router.include_router(attendance_corrections_admin_router, tags=["School: Attendance Corrections"]) # New
school_app_router.include_router(attendance_reports_router, tags=["School: Attendance Reports"]) # New

# Mount School Routes
app.include_router(school_app_router, prefix="/school")

# --- Student Routes Group ---
student_app_router = APIRouter()
student_app_router.include_router(student_auth_router, tags=["Student: Auth"]) 
student_app_router.include_router(attendance_reports_student_router, tags=["Student: Attendance Reports"]) # New 

# Mount Student Routes
app.include_router(student_app_router, prefix="/student")

# --- Teacher Routes Group ---
teacher_app_router = APIRouter()
teacher_app_router.include_router(teacher_auth_router, tags=["Teacher: Auth"])
teacher_app_router.include_router(attendance_corrections_teacher_router, tags=["Teacher: Attendance Corrections"]) # New
teacher_app_router.include_router(attendance_reports_coordinator_router, tags=["Teacher: Attendance Reports"]) # New
# teacher_app_router.include_router(teacher_assignments_router, tags=["Teacher: Class Teacher Assignments"]) # Teacher Access

# Mount Teacher Routes
app.include_router(teacher_app_router, prefix="/teacher")


@app.get("/")
async def root():
    return {"message": "SaaS Platform API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
