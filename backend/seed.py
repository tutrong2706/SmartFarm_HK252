"""
seed.py — Nhập dữ liệu mẫu vào database SmartFarm
Chạy: python seed.py  (từ thư mục backend/)

Dữ liệu nhập:
  - 4 DeviceType (loại thiết bị)
  - 8 Device    (theo Bảng 1 tài liệu)
  - 4 CropSetting (Táo, Nho, Đào, Dưa hấu)
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine
import models

# Tạo bảng nếu chưa có
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ─────────────────────────────────────────────────────────────────
# 1. DEVICE TYPES  (4 loại)
# ─────────────────────────────────────────────────────────────────
device_types_data = [
    {"name": "Nhiệt độ & Độ ẩm không khí",  "category": "SENSOR"},   # id=1 → DHT20
    {"name": "Độ ẩm đất",                   "category": "SENSOR"},   # id=2 → Soil Moisture
    {"name": "Cường độ ánh sáng",           "category": "SENSOR"},   # id=3 → Light Sensor
    {"name": "Màn hình hiển thị",           "category": "ACTUATOR"}, # id=4 → LCD 16×2
    {"name": "Bơm nước",                    "category": "ACTUATOR"}, # id=5 → Pump 1 & 2
    {"name": "Quạt thông gió",              "category": "ACTUATOR"}, # id=6 → Fan
    {"name": "Đèn LED RGB",                 "category": "ACTUATOR"}, # id=7 → NeoPixel LED
]

print("── Thêm DeviceType ──")
type_map = {}   # name → id
for dt_data in device_types_data:
    existing = db.query(models.DeviceType).filter_by(
        name=dt_data["name"], category=dt_data["category"]
    ).first()
    if existing:
        type_map[dt_data["name"]] = existing.id
        print(f"  ✓ Đã tồn tại: {dt_data['name']}")
    else:
        dt = models.DeviceType(**dt_data)
        db.add(dt)
        db.flush()
        type_map[dt_data["name"]] = dt.id
        print(f"  + Thêm mới:   {dt_data['name']} (id={dt.id})")

db.commit()

# ─────────────────────────────────────────────────────────────────
# 2. DEVICES  (8 thiết bị theo Bảng 1)
# ─────────────────────────────────────────────────────────────────
devices_data = [
    {
        "name":          "DHT20",
        "type_key":      "Nhiệt độ & Độ ẩm không khí",
        "pin_connector": "I2C (SDA, SCL)",
        "is_active":     True,
        "zone_id":       None,
    },
    {
        "name":          "Soil Moisture",
        "type_key":      "Độ ẩm đất",
        "pin_connector": "GPIO 2 (Analog)",
        "is_active":     True,
        "zone_id":       None,
    },
    {
        "name":          "Light Sensor",
        "type_key":      "Cường độ ánh sáng",
        "pin_connector": "GPIO 3 (Analog)",
        "is_active":     True,
        "zone_id":       None,
    },
    {
        "name":          "LCD 16x2",
        "type_key":      "Màn hình hiển thị",
        "pin_connector": "I2C (0x27)",
        "is_active":     True,
        "zone_id":       None,
    },
    {
        "name":          "Pump 1",
        "type_key":      "Bơm nước",
        "pin_connector": "GPIO 8 (Digital)",
        "is_active":     False,
        "zone_id":       None,
    },
    {
        "name":          "Pump 2",
        "type_key":      "Bơm nước",
        "pin_connector": "GPIO 9 (Digital)",
        "is_active":     False,
        "zone_id":       None,
    },
    {
        "name":          "Fan",
        "type_key":      "Quạt thông gió",
        "pin_connector": "GPIO 1 (PWM)",
        "is_active":     True,
        "zone_id":       None,
    },
    {
        "name":          "NeoPixel LED",
        "type_key":      "Đèn LED RGB",
        "pin_connector": "GPIO 6 (WS2812B)",
        "is_active":     False,
        "zone_id":       None,
    },
]

print("\n── Thêm Device ──")
for d_data in devices_data:
    existing = db.query(models.Device).filter_by(name=d_data["name"]).first()
    if existing:
        print(f"  ✓ Đã tồn tại: {d_data['name']}")
    else:
        device = models.Device(
            name          = d_data["name"],
            type_id       = type_map[d_data["type_key"]],
            pin_connector = d_data["pin_connector"],
            is_active     = d_data["is_active"],
            zone_id       = d_data["zone_id"],
        )
        db.add(device)
        print(f"  + Thêm mới:   {d_data['name']}")

db.commit()

# ─────────────────────────────────────────────────────────────────
# 3. CROP SETTINGS  (Táo, Nho, Đào, Dưa hấu)
# ─────────────────────────────────────────────────────────────────
crop_settings_data = [
    {
        "crop_name": "Táo",
        "temp_min":  18.0,
        "temp_max":  26.0,
        "humid_min": 50.0,
        "humid_max": 70.0,
        "auto_mode": True,
    },
    {
        "crop_name": "Nho",
        "temp_min":  20.0,
        "temp_max":  30.0,
        "humid_min": 55.0,
        "humid_max": 75.0,
        "auto_mode": True,
    },
    {
        "crop_name": "Đào",
        "temp_min":  15.0,
        "temp_max":  24.0,
        "humid_min": 45.0,
        "humid_max": 65.0,
        "auto_mode": False,
    },
    {
        "crop_name": "Dưa hấu",
        "temp_min":  25.0,
        "temp_max":  35.0,
        "humid_min": 60.0,
        "humid_max": 80.0,
        "auto_mode": True,
    },
]

print("\n── Thêm CropSetting ──")
for c_data in crop_settings_data:
    existing = db.query(models.CropSetting).filter_by(crop_name=c_data["crop_name"]).first()
    if existing:
        print(f"  ✓ Đã tồn tại: {c_data['crop_name']}")
    else:
        crop = models.CropSetting(**c_data)
        db.add(crop)
        print(f"  + Thêm mới:   {c_data['crop_name']}")

db.commit()
db.close()

print("\n✅ Seed hoàn tất!")
