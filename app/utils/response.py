from typing import Any, Optional
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.encoders import jsonable_encoder

class APIResponse:
    @staticmethod
    def success(
        data: Any = None, 
        message: str = "Success", 
        status_code: int = status.HTTP_200_OK,
        meta: Optional[dict] = None
    ):
        response_content = {
            "success": True,
            "message": message,
            "data": jsonable_encoder(data)
        }
        if meta:
            response_content["meta"] = meta
            
        return JSONResponse(
            status_code=status_code,
            content=response_content
        )

    @staticmethod
    def error(
        message: str = "Error", 
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[Any] = None
    ):
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": message,
                "data": jsonable_encoder(data),
                "error": True
            }
        )
