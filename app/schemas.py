from pydantic import BaseModel,EmailStr
from uuid import UUID
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: EmailStr
    password: str
class User(BaseModel):
    id: UUID
    email: EmailStr

class VerifyRequest(BaseModel):
    email: EmailStr
    code: str







class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(BaseModel):
    title: str
    content: str



class ChatMessage(BaseModel):
    content: str
class Messageid(BaseModel):
    message_id: int

class ProfilePageRead(BaseModel):
    url: str
    file_type: str
    file_name: str

    class Config:
        from_attributes = True

# class UserRead(schemas.BaseUser[uuid.UUID]):
#     profile_page: Optional[ProfilePageRead] = None
#
#     class Config:
#         from_attributes = True
# class UserCreate(schemas.BaseUserCreate):
#     pass
# class UserUpdate(schemas.BaseUserUpdate):
#     pass