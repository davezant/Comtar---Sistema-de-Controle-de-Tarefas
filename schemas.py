from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from models import StatusTask

class UserRegisterRequest(BaseModel):
    name: str = Field(..., max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=64) # RN06
    description: Optional[str] = Field(default="", max_length=256)
    deadline_date: datetime

class TaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=64)
    description: Optional[str] = None
    deadline_date: Optional[datetime] = None
    status: Optional[StatusTask] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    creation_date: datetime
    deadline_date: datetime
    status: StatusTask