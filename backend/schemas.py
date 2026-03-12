from pydantic import BaseModel
from typing import Optional

# Base schema chứa các trường chung
class ZoneBase(BaseModel):
    name: str
    description: Optional[str] = None
    crop_setting_id: Optional[int] = None

# Schema dùng khi tạo mới (nhận từ Client)
class ZoneCreate(BaseModel):
    name: str
    description: Optional[str] = None       # Cho phép bỏ trống
    crop_setting_id: Optional[int] = None   # Mặc định sẽ là null thay vì 0

# Schema dùng khi cập nhật một phần zone (PATCH)
class ZonePatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    crop_setting_id: Optional[int] = None

# Schema dùng khi trả dữ liệu về (Response)
class ZoneResponse(ZoneBase):
    id: int

    class Config:
        from_attributes = True  # Cho phép Pydantic đọc dữ liệu từ SQLAlchemy Model

# ── Crop Settings ──────────────────────────────────────
class CropSettingCreate(BaseModel):
    crop_name: str
    temp_min: float
    temp_max: float
    humid_min: float
    humid_max: float
    auto_mode: bool = False

class CropSettingResponse(BaseModel):
    id: int
    crop_name: str
    temp_min: float
    temp_max: float
    humid_min: float
    humid_max: float
    auto_mode: bool

    class Config:
        from_attributes = True

# ── Devices ────────────────────────────────────────────
class DeviceResponse(BaseModel):
    id: int
    device_name: str        # mapped from Device.name
    device_type: str        # mapped from DeviceType.category (SENSOR / ACTUATOR)
    pin: Optional[str] = None           # mapped from Device.pin_connector
    func: Optional[str] = None          # mapped from DeviceType.name (chức năng)
    zone_id: Optional[int] = None
    status: str = "ONLINE"  # derived: ONLINE if is_active else OFFLINE
    is_active: bool

    class Config:
        from_attributes = False  # we build this manually in the endpoint

class DeviceToggle(BaseModel):
    is_active: bool
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