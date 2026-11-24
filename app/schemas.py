from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth ----------
class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)


class RefreshRequest(BaseModel):
    refresh_token: str


class Token(BaseModel):
    token: str                     # convenience field per spec
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


# ---------- Todos ----------
class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    completed: bool = False


class TodoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    completed: bool | None = None


class TodoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    completed: bool
    created_at: datetime


class TodoList(BaseModel):
    data: list[TodoOut]
    page: int
    limit: int
    total: int