from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON, DateTime, Text, func
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# 1. Bảng Cấu hình cây trồng (Crop Settings)
class CropSetting(Base):
    __tablename__ = "crop_settings"

    id = Column(Integer, primary_key=True, index=True)
    crop_name = Column(String, index=True)
    temp_min = Column(Float)
    temp_max = Column(Float)
    humid_min = Column(Float)
    humid_max = Column(Float)
    light_min = Column(Float, nullable=True)
    light_max = Column(Float, nullable=True)
    light_type = Column(String, nullable=True)
    auto_mode = Column(Boolean, default=False)

    zones = relationship("Zone", back_populates="crop_setting")

# 2. Bảng Khu vực / Mảnh vườn (Zones)
class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    crop_setting_id = Column(Integer, ForeignKey("crop_settings.id"), nullable=True)

    crop_setting = relationship("CropSetting", back_populates="zones")
    devices = relationship("Device", back_populates="zone")

# 3. Bảng Loại thiết bị (Device Types)
class DeviceType(Base):
    __tablename__ = "device_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    category = Column(String)

    devices = relationship("Device", back_populates="device_type")

# 4. Bảng Thiết bị vật lý (Devices)
class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    type_id = Column(Integer, ForeignKey("device_types.id"))
    is_active = Column(Boolean, default=False)
    pin_connector = Column(String, nullable=True)

    zone = relationship("Zone", back_populates="devices")
    device_type = relationship("DeviceType", back_populates="devices")

# 5. Bảng Nhật ký & Cảnh báo hệ thống (Alert Logs)
class AlertLog(Base):
    __tablename__ = "alert_logs"

    id           = Column(Integer, primary_key=True, index=True)
    log_type     = Column(String, nullable=False, index=True)
    severity     = Column(String, nullable=False, default="info")
    zone_id      = Column(Integer, ForeignKey("zones.id"), nullable=True)
    device_id    = Column(Integer, ForeignKey("devices.id"), nullable=True)
    title        = Column(String, nullable=False)
    message      = Column(Text, nullable=False)
    action_label = Column(String, nullable=True)
    action_type  = Column(String, nullable=True)
    action_target_id = Column(Integer, nullable=True)
    actor        = Column(String, nullable=True)
    is_read      = Column(Boolean, default=False, index=True)
    metric_key   = Column(String, nullable=True)
    metric_value = Column(Float, nullable=True)
    threshold    = Column(Float, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow, index=True)

    zone   = relationship("Zone")
    device = relationship("Device")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    name = Column(String)
    role = Column(String, default="FARMER")


# 7. Bảng Telemetry Data — Lưu lịch sử telemetry từ các sensor
class TelemetryData(Base):
    __tablename__ = "telemetry_data"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    light = Column(Float, nullable=True)
    measured_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    zone = relationship("Zone")


# 8. Bảng Dashboard Widgets — Cấu hình Dashboard động
class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    widget_type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    config = Column(JSON, nullable=False)
    position = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")


# 9. Bảng Reports — Metadata báo cáo
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    report_type = Column(String(50), default="custom")  # 'custom' | 'scheduled'
    format = Column(String(20), nullable=False)  # 'csv' | 'xlsx' | 'pdf'
    date_from = Column(DateTime(timezone=True), nullable=False)
    date_to = Column(DateTime(timezone=True), nullable=False)
    zone_ids = Column(JSON, nullable=True)  # [1, 2, 3] hoặc null = all
    metrics = Column(JSON, nullable=True)   # ["temperature", "humidity", "light"]
    status = Column(String(20), default="pending")  # 'pending'|'processing'|'completed'|'failed'
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")