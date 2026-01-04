from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    PROJECT_NAME: str = "SaaS Platform API"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DB_NAME: str = "saas_platform_db"
    MONGO_USER: str = ""
    MONGO_PASS: str = ""

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Org Security
    ORG_SECRET_KEY: str = "org_super_secret_key" # In prod, override with env
    ORG_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Student Security
    STUDENT_SECRET_KEY: str = "student_super_secret_key" # In prod, override with env
    STUDENT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours

    # Teacher Security
    TEACHER_SECRET_KEY: str = "teacher_super_secret_key" # In prod, override with env
    TEACHER_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Init
    FIRST_SUPER_ADMIN_EMAIL: str = "admin@example.com"
    FIRST_SUPER_ADMIN_PASSWORD: str = "changeme"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
