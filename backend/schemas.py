from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

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


# ── Alert Logs ────────────────────────────────────────────────────────────────

LogType      = Literal["critical", "warning", "automation", "system"]
SeverityType = Literal["critical", "warning", "info", "success"]
ActionType   = Literal["toggle_device", "navigate_zone", "navigate_device"]


class AlertLogCreate(BaseModel):
    """Dùng khi tạo log thủ công (từ frontend hoặc nội bộ backend)."""
    log_type:         LogType
    severity:         SeverityType
    title:            str
    message:          str
    zone_id:          Optional[int]   = None
    device_id:        Optional[int]   = None
    action_label:     Optional[str]   = None
    action_type:      Optional[ActionType] = None
    action_target_id: Optional[int]   = None
    actor:            Optional[str]   = None
    metric_key:       Optional[str]   = None    # "temperature" | "humidity" | "light"
    metric_value:     Optional[float] = None
    threshold:        Optional[float] = None


class AlertLogResponse(BaseModel):
    id:               int
    log_type:         str
    severity:         str
    title:            str
    message:          str
    zone_id:          Optional[int]   = None
    device_id:        Optional[int]   = None
    action_label:     Optional[str]   = None
    action_type:      Optional[str]   = None
    action_target_id: Optional[int]   = None
    actor:            Optional[str]   = None
    is_read:          bool
    metric_key:       Optional[str]   = None
    metric_value:     Optional[float] = None
    threshold:        Optional[float] = None
    created_at:       datetime

    # Resolved at query time
    zone_name:        Optional[str]   = None
    device_name:      Optional[str]   = None

    class Config:
        from_attributes = False   # built manually in endpoints
