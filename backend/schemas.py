from pydantic import BaseModel
from typing import Optional

# Base schema chứa các trường chung
class ZoneBase(BaseModel):
    name: str
    description: Optional[str] = None
    crop_setting_id: Optional[int] = None

# Schema dùng khi tạo mới (nhận từ Client)
class ZoneCreate(ZoneBase):
    pass

# Schema dùng khi trả dữ liệu về (Response)
class ZoneResponse(ZoneBase):
    id: int

    class Config:
        from_attributes = True  # Cho phép Pydantic đọc dữ liệu từ SQLAlchemy Model
#Đăng kí/Đăng nhập
# Dữ liệu khách gửi lên khi Đăng ký
class UserCreate(BaseModel):
    username: str
    password: str
    name: str

# Dữ liệu trả về (ẩn mật khẩu đi)
class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str

    class Config:
        from_attributes = True

# Dữ liệu Token trả về khi Đăng nhập thành công
class Token(BaseModel):
    access_token: str
    token_type: str        