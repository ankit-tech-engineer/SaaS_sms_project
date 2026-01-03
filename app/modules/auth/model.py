from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.core.permissions import Role, Permission
from datetime import datetime
import uuid

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, (str, uuid.UUID)):
            raise ValueError("Invalid UUID")
        return str(v)

class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    name: str
    email: EmailStr
    hashed_password: str
    role: Role = Role.ADMIN
    permissions: List[Permission] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
