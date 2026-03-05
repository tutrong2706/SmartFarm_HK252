from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON, DateTime
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

# 5. Bảng Nhật ký hệ thống (System Logs) - Phục vụ chức năng Audit Log (JSONB)
class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, nullable=True)
    actor_type = Column(String) # 'ADMIN', 'FARMER', 'SYSTEM_AUTO'
    action_type = Column(String) # 'UPDATE_CONFIG', 'CONTROL_DEVICE'
    target_entity = Column(String) # Tên bảng bị tác động (vd: 'devices')
    target_id = Column(Integer)
    changes = Column(JSON) # LƯU Ý: Lưu đối tượng JSON (old/new) tại đây
    created_at = Column(DateTime, default=datetime.utcnow)
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String) # Tuyệt đối không lưu mật khẩu gốc
    name = Column(String)
    role = Column(String, default="FARMER") # Có thể là ADMIN hoặc FARMER    