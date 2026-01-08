from datetime import datetime, date, timedelta
from typing import List, Optional
from app.core.database import db
from app.modules.attendance.model import COLLECTION_NAME as ATTENDANCE_COLLECTION
from app.core.academic_year import get_current_academic_year
from app.modules.reports.attendance_reports.schema import (
    DailySummaryResponse,
    StudentMonthlySummary,
    SectionMonthlySummary,
    DefaulterStudent,
    AttendanceTrendResponse,
    TrendDataPoint,
    StudentRangeSummary,
    StudentAttendanceLog
)

class AttendanceReportService:
    
    @staticmethod
    def _base_match_stage(school_id: str, academic_year: str, extra_filters: dict = None):
        match = {
            "school_id": school_id,
            "academic_year": academic_year,
            "status": "APPROVED",
            "locked": True
        }
        if extra_filters:
            match.update(extra_filters)
        return {"$match": match}

    @staticmethod
    async def get_daily_summary(
        school_id: str, 
        report_date: date, 
        class_id: Optional[str] = None, 
        section_id: Optional[str] = None
    ) -> DailySummaryResponse:
        database = db.get_db()
        academic_year = get_current_academic_year() # Or determine from date? Usually current.
        
        # Determine Academic Year from date if needed, but for simplicity assuming current context or passed context.
        # Actually, best to fetch academic year config or just use the one stored in record.
        # But we query by date, so academic_year is redundant match but good for index usage.
        
        match_filter = {"date": str(report_date)}
        if class_id: match_filter["class_id"] = class_id
        if section_id: match_filter["section_id"] = section_id
        
        pipeline = [
            AttendanceReportService._base_match_stage(school_id, academic_year, match_filter),
            # Unwind records to count individual statuses
            {"$unwind": "$records"},
            {"$group": {
                "_id": None,
                "total_students": {"$sum": 1},
                "present": {"$sum": {"$cond": [{"$eq": ["$records.status", "present"]}, 1, 0]}},
                "absent": {"$sum": {"$cond": [{"$eq": ["$records.status", "absent"]}, 1, 0]}},
                "late": {"$sum": {"$cond": [{"$eq": ["$records.status", "late"]}, 1, 0]}},
                "half_day": {"$sum": {"$cond": [{"$eq": ["$records.status", "half_day"]}, 1, 0]}},
                "on_leave": {"$sum": {"$cond": [{"$eq": ["$records.status", "on_leave"]}, 1, 0]}}
            }}
        ]
        
        result = await database[ATTENDANCE_COLLECTION].aggregate(pipeline).to_list(1)
        
        if not result:
            return DailySummaryResponse(
                date=report_date,
                total_students=0,
                present=0,
                absent=0,
                late=0,
                half_day=0,
                on_leave=0,
                attendance_percentage=0.0
            )
            
        data = result[0]
        # Calculate Percentage (Present + Late + Half Day?) usually just Present.
        # Let's count Present + Late as Present-ish?
        # Standard: Present / Total * 100
        total = data["total_students"]
        # Policy dependent logic? Assuming simple Present count for now.
        effective_present = data["present"] + data["late"] # Late usually counts as present
        
        percentage = round((effective_present / total * 100), 2) if total > 0 else 0.0
        
        return DailySummaryResponse(
            date=report_date,
            total_students=total,
            present=data["present"],
            absent=data["absent"],
            late=data["late"],
            half_day=data["half_day"],
            on_leave=data["on_leave"],
            attendance_percentage=percentage
        )

    @staticmethod
    async def get_student_monthly(
        school_id: str,
        student_id: str,
        month: str # YYYY-MM
    ) -> StudentMonthlySummary:
        database = db.get_db()
        academic_year = get_current_academic_year()
        
        # Filter by regex date or start/end
        # "date": {"$regex": f"^{month}"} logic
        
        pipeline = [
            AttendanceReportService._base_match_stage(school_id, academic_year, {
                "date": {"$regex": f"^{month}"}
            }),
            {"$unwind": "$records"},
            {"$match": {"records.student_id": student_id}},
            {"$group": {
                "_id": "$records.student_id",
                "total_days": {"$sum": 1},
                "present": {"$sum": {"$cond": [{"$in": ["$records.status", ["present", "late"]]}, 1, 0]}},
                "absent": {"$sum": {"$cond": [{"$eq": ["$records.status", "absent"]}, 1, 0]}},
                # On Leave treated as? Absent usually or separate. "Leave treated as absent unless policy says otherwise" -> user instruction.
                # Assuming absent for percentage calculation denominator if working day.
            }}
        ]
        
        result = await database[ATTENDANCE_COLLECTION].aggregate(pipeline).to_list(1)
        
        if not result:
             return StudentMonthlySummary(
                student_id=student_id,
                month=month,
                total_working_days=0,
                present_days=0,
                absent_days=0,
                percentage=0.0
             )
             
        data = result[0]
        total = data["total_days"]
        present = data["present"]
        
        pct = round((present / total * 100), 2) if total > 0 else 0.0
        
        return StudentMonthlySummary(
            student_id=student_id,
            month=month,
            total_working_days=total,
            present_days=present,
            absent_days=data["absent"],
            percentage=pct
        )
    @staticmethod
    async def get_section_monthly(
        school_id: str,
        class_id: str,
        section_id: str,
        month: str
    ) -> SectionMonthlySummary:
        database = db.get_db()
        academic_year = get_current_academic_year()
        
        pipeline = [
            AttendanceReportService._base_match_stage(school_id, academic_year, {
                "class_id": class_id,
                "section_id": section_id,
                "date": {"$regex": f"^{month}"}
            }),
            {"$unwind": "$records"},
            {"$group": {
                "_id": None,
                "total_student_days": {"$sum": 1},
                "total_present": {"$sum": {"$cond": [{"$in": ["$records.status", ["present", "late"]]}, 1, 0]}},
                "unique_students": {"$addToSet": "$records.student_id"}
            }},
            {"$project": {
                "total_students": {"$size": "$unique_students"},
                "avg_percentage": {
                    "$cond": [
                        {"$eq": ["$total_student_days", 0]},
                        0,
                        {"$multiply": [{"$divide": ["$total_present", "$total_student_days"]}, 100]}
                    ]
                }
            }}
        ]
        
        result = await database[ATTENDANCE_COLLECTION].aggregate(pipeline).to_list(1)
        
        if not result:
            return SectionMonthlySummary(
                class_id=class_id,
                section_id=section_id,
                month=month,
                total_students=0,
                avg_percentage=0.0
            )
            
        data = result[0]
        return SectionMonthlySummary(
            class_id=class_id,
            section_id=section_id,
            month=month,
            total_students=data["total_students"],
            avg_percentage=round(data["avg_percentage"], 2)
        )

    @staticmethod
    async def get_defaulters(
        school_id: str,
        month: str,
        threshold: float,
        class_id: Optional[str] = None,
        section_id: Optional[str] = None
    ) -> List[DefaulterStudent]:
        database = db.get_db()
        academic_year = get_current_academic_year()
        
        match_filter = {"date": {"$regex": f"^{month}"}}
        if class_id: match_filter["class_id"] = class_id
        if section_id: match_filter["section_id"] = section_id
        
        pipeline = [
            AttendanceReportService._base_match_stage(school_id, academic_year, match_filter),
            {"$unwind": "$records"},
            {"$group": {
                "_id": "$records.student_id",
                "total_days": {"$sum": 1},
                "present": {"$sum": {"$cond": [{"$in": ["$records.status", ["present", "late"]]}, 1, 0]}},
                "absent": {"$sum": {"$cond": [{"$eq": ["$records.status", "absent"]}, 1, 0]}}
            }},
            # Calculate Percentage
            {"$addFields": {
                "percentage": {
                    "$cond": [
                        {"$eq": ["$total_days", 0]},
                        0,
                        {"$multiply": [{"$divide": ["$present", "$total_days"]}, 100]}
                    ]
                }
            }},
            # Filter Defaulters
            {"$match": {"percentage": {"$lt": threshold}}},
            {"$project": {
                "student_id": "$_id",
                "attendance_percentage": {"$round": ["$percentage", 2]},
                "days_absent": "$absent"
            }}
        ]
        
        results = await database[ATTENDANCE_COLLECTION].aggregate(pipeline).to_list(length=1000)
        
        # Optional: Enrich with student names if needed (not strict requirement but nice)
        return [DefaulterStudent(**r) for r in results]

    @staticmethod
    async def get_attendance_trend(
        school_id: str,
        class_id: str,
        section_id: str,
        months_back: int = 6
    ) -> AttendanceTrendResponse:
        database = db.get_db()
        academic_year = get_current_academic_year()
        
        # Calculate date range? Or just group by substring of month
        # Trend over last 6 months.
        # We can just match all dates in academic year and group by month.
        
        pipeline = [
            AttendanceReportService._base_match_stage(school_id, academic_year, {
                "class_id": class_id,
                "section_id": section_id
            }),
            {"$addFields": {
                "month_str": {"$substr": ["$date", 0, 7]} # YYYY-MM
            }},
            {"$unwind": "$records"},
            {"$group": {
                "_id": "$month_str",
                "total_records": {"$sum": 1},
                "present": {"$sum": {"$cond": [{"$in": ["$records.status", ["present", "late"]]}, 1, 0]}}
            }},
            {"$addFields": {
                "avg_percentage": {
                     "$cond": [
                        {"$eq": ["$total_records", 0]},
                        0,
                        {"$multiply": [{"$divide": ["$present", "$total_records"]}, 100]}
                    ]
                }
            }},
            {"$sort": {"_id": 1}},
            {"$project": {
                "month": "$_id",
                "average_percentage": {"$round": ["$avg_percentage", 2]}
            }}
        ]
        
        results = await database[ATTENDANCE_COLLECTION].aggregate(pipeline).to_list(None)
        
        return AttendanceTrendResponse(
            class_id=class_id,
            section_id=section_id,
            trend=[TrendDataPoint(**r) for r in results]
        )

    @staticmethod
    async def get_student_range_summary(
        school_id: str,
        student_id: str,
        start_date: date,
        end_date: date
    ) -> StudentRangeSummary:
        database = db.get_db()
        academic_year = get_current_academic_year()
        
        pipeline = [
            AttendanceReportService._base_match_stage(school_id, academic_year, {
                "date": {"$gte": str(start_date), "$lte": str(end_date)}
            }),
            {"$unwind": "$records"},
            {"$match": {"records.student_id": student_id}},
            {"$group": {
                "_id": "$records.student_id",
                "total_days": {"$sum": 1},
                "present": {"$sum": {"$cond": [{"$in": ["$records.status", ["present", "late"]]}, 1, 0]}},
                "absent": {"$sum": {"$cond": [{"$eq": ["$records.status", "absent"]}, 1, 0]}}
            }}
        ]
        
        result = await database[ATTENDANCE_COLLECTION].aggregate(pipeline).to_list(1)
        
        if not result:
            return StudentRangeSummary(
                student_id=student_id,
                start_date=str(start_date),
                end_date=str(end_date),
                total_working_days=0,
                present_days=0,
                absent_days=0,
                percentage=0.0
            )
            
        data = result[0]
        total = data["total_days"]
        present = data["present"]
        pct = round((present / total * 100), 2) if total > 0 else 0.0
        
        return StudentRangeSummary(
            student_id=student_id,
            start_date=str(start_date),
            end_date=str(end_date),
            total_working_days=total,
            present_days=present,
            absent_days=data["absent"],
            percentage=pct
        )

    @staticmethod
    async def get_student_history(
        school_id: str,
        student_id: str,
        start_date: date,
        end_date: date
    ) -> List[StudentAttendanceLog]:
        database = db.get_db()
        academic_year = get_current_academic_year()
        
        pipeline = [
            AttendanceReportService._base_match_stage(school_id, academic_year, {
                "date": {"$gte": str(start_date), "$lte": str(end_date)}
            }),
            {"$unwind": "$records"},
            {"$match": {"records.student_id": student_id}},
            {"$sort": {"date": -1}}, # Latest first
            {"$project": {
                "date": "$date",
                "status": "$records.status"
            }}
        ]
        
        results = await database[ATTENDANCE_COLLECTION].aggregate(pipeline).to_list(None)
        
        return [StudentAttendanceLog(**r) for r in results]
