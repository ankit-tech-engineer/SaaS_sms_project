from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audit")

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Log details
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else "unknown",
            "status_code": response.status_code,
            "process_time": process_time,
            "timestamp": time.time(),
            "user_id": getattr(request.state, "user_id", None) or getattr(request.state, "org_id", None) 
        }
        
        # Async insert to DB
        try:
            from app.core.database import db
            if db.client:
                database = db.get_db()
                await database["audit_logs"].insert_one(log_data)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

        logger.info(f"AUDIT LOG: {log_data}")
        
        return response
