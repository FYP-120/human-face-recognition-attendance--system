from pydantic import BaseModel, EmailStr

class UserModel(BaseModel):
    email: EmailStr
    password: str
    is_super_admin: bool = False

