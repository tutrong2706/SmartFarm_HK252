from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# 1. Bảng Cấu hình cây trồng (Crop Settings)
class CropSetting(Base):
    __tablename__ = "crop_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    crop_name = Column(String, index=True) # Ví dụ: Dưa lưới, Nấm
    temp_min = Column(Float)
    temp_max = Column(Float)
    humid_min = Column(Float)
    humid_max = Column(Float)
    auto_mode = Column(Boolean, default=False) # Cho phép hệ thống tự động chạy
    
    # Mối quan hệ 1-N với Zone (1 Cấu hình có thể dùng cho nhiều Khu vực)
    zones = relationship("Zone", back_populates="crop_setting")

# 2. Bảng Khu vực / Mảnh vườn (Zones)
class Zone(Base):
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # Ví dụ: Vườn A, Khu nhà kính 1
    description = Column(String, nullable=True)
    crop_setting_id = Column(Integer, ForeignKey("crop_settings.id"), nullable=True)
    
    # Khai báo mối quan hệ
    crop_setting = relationship("CropSetting", back_populates="zones")
    devices = relationship("Device", back_populates="zone")

# 3. Bảng Loại thiết bị (Device Types) - Phục vụ cho Factory Pattern
class DeviceType(Base):
    __tablename__ = "device_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String) # Ví dụ: Cảm biến nhiệt độ, Máy bơm
    category = Column(String) # Phân loại: SENSOR hoặc ACTUATOR
    
    devices = relationship("Device", back_populates="device_type")

# 4. Bảng Thiết bị vật lý (Devices)
class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # Ví dụ: Máy bơm số 1
    zone_id = Column(Integer, ForeignKey("zones.id"))
    type_id = Column(Integer, ForeignKey("device_types.id"))
    is_active = Column(Boolean, default=False) # Trạng thái Bật/Tắt hiện tại
    pin_connector = Column(String, nullable=True) # Chân cắm trên Microbit (vd: P0, P1)
    
    # Khai báo mối quan hệ
    zone = relationship("Zone", back_populates="devices")
    device_type = relationship("DeviceType", back_populates="devices")

# 5. Bảng Nhật ký & Cảnh báo hệ thống (Alert Logs)
class AlertLog(Base):
    """
    Ghi lại 4 loại sự kiện:
      critical   — vượt ngưỡng sinh thái, mất kết nối sensor/gateway
      warning    — tiệm cận ngưỡng, thiết bị chạy lâu, bể nước cạn
      automation — hành động tự động (kích hoạt bơm, tắt đèn, khôi phục)
      system     — audit log: thay đổi cấu hình, thao tác thủ công
    """
    __tablename__ = "alert_logs"

    id           = Column(Integer, primary_key=True, index=True)

    # ── Phân loại ───────────────────────────────────────────────
    log_type     = Column(String, nullable=False, index=True)
    # Giá trị: "critical" | "warning" | "automation" | "system"

    severity     = Column(String, nullable=False, default="info")
    # Giá trị: "critical" | "warning" | "info" | "success"
    # (dùng để tô màu ở frontend, tách riêng với log_type cho linh hoạt)

    # ── Nguồn / đối tượng liên quan ─────────────────────────────
    zone_id      = Column(Integer, ForeignKey("zones.id"), nullable=True)
    device_id    = Column(Integer, ForeignKey("devices.id"), nullable=True)

    # ── Nội dung ─────────────────────────────────────────────────
    title        = Column(String, nullable=False)          # Tiêu đề ngắn
    message      = Column(Text, nullable=False)            # Nội dung chi tiết

    # ── Hành động đi kèm (nút bấm phía frontend) ────────────────
    action_label = Column(String, nullable=True)           # vd: "Bật bơm giải nhiệt ngay"
    action_type  = Column(String, nullable=True)
    # Giá trị: "toggle_device" | "navigate_zone" | "navigate_device" | None

    action_target_id = Column(Integer, nullable=True)
    # ID thiết bị cần bật/tắt, hoặc ID zone cần điều hướng

    # ── Người/Hệ thống tạo log ───────────────────────────────────
    actor        = Column(String, nullable=True)           # vd: "Admin Nguyễn Lê", "SYSTEM"

    # ── Trạng thái đã đọc ────────────────────────────────────────
    is_read      = Column(Boolean, default=False, index=True)

    # ── Giá trị đo (để cảnh báo threshold) ──────────────────────
    metric_key   = Column(String, nullable=True)           # "temperature" | "humidity" | "light"
    metric_value = Column(Float, nullable=True)            # giá trị thực đo
    threshold    = Column(Float, nullable=True)            # ngưỡng bị vượt

    # ── Thời gian ────────────────────────────────────────────────
    created_at   = Column(DateTime, default=datetime.utcnow, index=True)

    # ── Relationships ────────────────────────────────────────────
    zone   = relationship("Zone")
    device = relationship("Device")
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String) # Tuyệt đối không lưu mật khẩu gốc
    name = Column(String)
    role = Column(String, default="FARMER") # Có thể là ADMIN hoặc FARMER    