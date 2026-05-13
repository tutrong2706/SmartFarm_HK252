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
    description: Optional[str] = None
    crop_setting_id: Optional[int] = None

# Schema dùng khi cập nhật một phần zone (PATCH)
class ZonePatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    crop_setting_id: Optional[int] = None

# Schema dùng khi trả dữ liệu về (Response)
class ZoneResponse(ZoneBase):
    id: int

    class Config:
        from_attributes = True

# ── Crop Settings ──────────────────────────────────────
class CropSettingCreate(BaseModel):
    crop_name: str
    temp_min: float
    temp_max: float
    humid_min: float
    humid_max: float
    light_min: Optional[float] = None
    light_max: Optional[float] = None
    light_type: Optional[str] = None
    auto_mode: bool = False

class CropSettingResponse(BaseModel):
    id: int
    crop_name: str
    temp_min: float
    temp_max: float
    humid_min: float
    humid_max: float
    light_min: Optional[float] = None
    light_max: Optional[float] = None
    light_type: Optional[str] = None
    auto_mode: bool

    class Config:
        from_attributes = True

# ── Devices ────────────────────────────────────────────
class DeviceResponse(BaseModel):
    id: int
    device_name: str
    device_type: str
    pin: Optional[str] = None
    func: Optional[str] = None
    zone_id: Optional[int] = None
    status: str = "ONLINE"
    is_active: bool

    class Config:
        from_attributes = False

class DeviceToggle(BaseModel):
    is_active: bool

# ── Auth ───────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str
    name: str

class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str


# ── Alert Logs ────────────────────────────────────────────────────────────────

LogType      = Literal["critical", "warning", "automation", "system"]
SeverityType = Literal["critical", "warning", "info", "success"]
ActionType   = Literal["toggle_device", "navigate_zone", "navigate_device"]


class AlertLogCreate(BaseModel):
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
    metric_key:       Optional[str]   = None
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
    zone_name:        Optional[str]   = None
    device_name:      Optional[str]   = None

    class Config:
        from_attributes = False


# ── Telemetry History & Analytics ────────────────────────────────────────────────

class TelemetryHistoryQuery(BaseModel):
    zone_id: Optional[int] = None
    metric: Optional[Literal["temperature", "humidity", "light"]] = None
    date_from: datetime
    date_to: datetime
    interval: Literal["1m", "5m", "15m", "1h", "1d"] = "1m"
    limit: int = 1000


class TelemetryHistoryResponse(BaseModel):
    id: int
    zone_id: int
    zone_name: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light: Optional[float] = None
    measured_at: datetime

    class Config:
        from_attributes = True


class TelemetryAnalyticsRow(BaseModel):
    zone_id: Optional[int] = None
    zone_name: Optional[str] = None
    metric: str
    min: float
    max: float
    avg: float
    count: int


# ── Dashboard Widgets ──────────────────────────────────────────────────────────

WidgetType = Literal["stat_card", "line_chart", "bar_chart", "gauge", "live_table"]


class DashboardWidgetCreate(BaseModel):
    user_id: Optional[int] = None
    widget_type: WidgetType
    title: str
    config: dict
    position: int = 0
    is_active: bool = True


class DashboardWidgetUpdate(BaseModel):
    widget_type: Optional[WidgetType] = None
    title: Optional[str] = None
    config: Optional[dict] = None
    position: Optional[int] = None
    is_active: Optional[bool] = None


class DashboardWidgetResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    widget_type: str
    title: str
    config: dict
    position: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Reports ────────────────────────────────────────────────────────────────────

ReportFormat = Literal["csv", "xlsx", "pdf"]
ReportStatus = Literal["pending", "processing", "completed", "failed"]


class ReportCreate(BaseModel):
    name: str
    format: ReportFormat
    date_from: datetime
    date_to: datetime
    zone_ids: Optional[list[int]] = None
    metrics: Optional[list[str]] = None


class ReportResponse(BaseModel):
    id: int
    name: str
    report_type: str
    format: str
    date_from: datetime
    date_to: datetime
    zone_ids: Optional[list[int]] = None
    metrics: Optional[list[str]] = None
    status: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Scheduled Reports (Phase 4) ────────────────────────────────────────────────

class ScheduledReportCreate(BaseModel):
    name: str
    format: ReportFormat
    date_from: datetime
    date_to: datetime
    zone_ids: Optional[list[int]] = None
    metrics: Optional[list[str]] = None
    cron_year: Optional[str] = None
    cron_month: Optional[str] = None
    cron_day: Optional[str] = None
    cron_week: Optional[str] = None
    cron_day_of_week: Optional[str] = None
    cron_hour: Optional[str] = "0"
    cron_minute: Optional[str] = "0"
    cron_second: Optional[str] = "0"
