from datetime import datetime
from app.core.database import db

COLLECTION_NAME = "attendance_audit_logs"

class AuditLogger:
    @staticmethod
    async def log_event(
        entity: str,
        entity_id: str,
        action: str,
        old_value: any,
        new_value: any,
        performed_by: str,
        reason: str
    ):
        """
        Logs an audit event to the 'attendance_audit_logs' collection.
        This is fire-and-forget or awaited depending on usage, but here we await it to ensure consistency.
        """
        if db.client:
            database = db.get_db()
            collection = database[COLLECTION_NAME]
            
            entry = {
                "entity": entity,
                "entity_id": entity_id,
                "action": action,
                "old_value": old_value,
                "new_value": new_value,
                "performed_by": performed_by,
                "reason": reason,
                "timestamp": datetime.utcnow()
            }
            
            await collection.insert_one(entry)
