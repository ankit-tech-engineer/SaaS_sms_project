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
            "process_time": f"{process_time:.4f}s"
        }
        
        # In a real system, you might save this to DB
        logger.info(f"AUDIT LOG: {log_data}")
        
        return response
