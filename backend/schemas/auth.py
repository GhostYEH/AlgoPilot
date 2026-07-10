from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=6, max_length=128)
    email: EmailStr | None = None


class UserLogin(BaseModel):
    username: str
    password: str
    role: str = Field(default="student", pattern=r"^(student|teacher)$")


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None = None
    role: str = "student"

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
