"""
seed.py — Nhập dữ liệu mẫu vào database SmartFarm
Chạy: python seed.py  (từ thư mục backend/)

Dữ liệu nhập:
  - 10 DeviceType (loại thiết bị)
  - 24 Device     (4 khu vực × 6 thiết bị mỗi khu, có đánh số thứ tự)
  - 4  CropSetting (Táo, Nho, Đào, Dưa hấu)
  - 8  AlertLog mẫu
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine
import models

# Tạo bảng nếu chưa có
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ─────────────────────────────────────────────────────────────────
# 1. DEVICE TYPES
# ─────────────────────────────────────────────────────────────────
device_types_data = [
    {"name": "Nhiệt độ & Độ ẩm không khí",  "category": "SENSOR"},    # T01
    {"name": "Độ ẩm đất",                   "category": "SENSOR"},    # T02
    {"name": "Cường độ ánh sáng",           "category": "SENSOR"},    # T03
    {"name": "CO2 / Chất lượng không khí",  "category": "SENSOR"},    # T04
    {"name": "Cảm biến mưa",               "category": "SENSOR"},    # T05
    {"name": "Màn hình hiển thị",           "category": "ACTUATOR"},  # T06
    {"name": "Bơm nước",                    "category": "ACTUATOR"},  # T07
    {"name": "Quạt thông gió",              "category": "ACTUATOR"},  # T08
    {"name": "Đèn LED RGB",                 "category": "ACTUATOR"},  # T09
    {"name": "Relay / Van điện từ",         "category": "ACTUATOR"},  # T10
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
# 2. DEVICES  — 4 khu vực × 6 thiết bị, có đánh số thứ tự
#
#   Mỗi khu vực có bộ:
#     S-01  DHT20           — Cảm biến nhiệt độ & độ ẩm
#     S-02  Soil Moisture   — Cảm biến độ ẩm đất
#     S-03  Light Sensor    — Cảm biến ánh sáng
#     S-04  CO2 Sensor      — Cảm biến CO2
#     A-01  Máy bơm         — Tưới nhỏ giọt
#     A-02  Quạt thông gió  — Điều tiết nhiệt
#
#   Ký hiệu tên: [Viết tắt khu vực]-[Loại]-[Số thứ tự]
#   Ví dụ: TAO-S01  TAO-A01  NHO-S01  ...
# ─────────────────────────────────────────────────────────────────

ZONE_MAP = {
    1: {"short": "TAO",  "label": "Vườn Táo"},
    2: {"short": "NHO",  "label": "Vườn Nho"},
    3: {"short": "DAO",  "label": "Vườn Đào"},
    4: {"short": "DUA",  "label": "Vườn Dưa Hấu"},
}

# Template thiết bị cho mỗi khu (zone_id sẽ gán lúc tạo)
DEVICE_TEMPLATES = [
    # ── Cảm biến ────────────────────────────────────────────────
    {
        "suffix":    "S01 — DHT20",
        "type_key":  "Nhiệt độ & Độ ẩm không khí",
        "pin":       "I2C (SDA/SCL)",
        "is_active": True,
    },
    {
        "suffix":    "S02 — Soil Moisture",
        "type_key":  "Độ ẩm đất",
        "pin":       "GPIO 2 (Analog)",
        "is_active": True,
    },
    {
        "suffix":    "S03 — Light Sensor",
        "type_key":  "Cường độ ánh sáng",
        "pin":       "GPIO 3 (Analog)",
        "is_active": True,
    },
    {
        "suffix":    "S04 — CO2 Sensor",
        "type_key":  "CO2 / Chất lượng không khí",
        "pin":       "UART (TX/RX)",
        "is_active": True,
    },
    # ── Thiết bị chấp hành ───────────────────────────────────────
    {
        "suffix":    "A01 — Pump",
        "type_key":  "Bơm nước",
        "pin":       "GPIO 8 (Digital)",
        "is_active": False,
    },
    {
        "suffix":    "A02 — Fan",
        "type_key":  "Quạt thông gió",
        "pin":       "GPIO 1 (PWM)",
        "is_active": False,
    },
]

# Thiết bị dùng chung / standalone (không gán zone)
SHARED_DEVICES = [
    {
        "name":      "LCD-01 — Màn hình trung tâm",
        "type_key":  "Màn hình hiển thị",
        "pin":       "I2C (0x27)",
        "is_active": True,
        "zone_id":   None,
    },
    {
        "name":      "LED-01 — NeoPixel tổng",
        "type_key":  "Đèn LED RGB",
        "pin":       "GPIO 6 (WS2812B)",
        "is_active": False,
        "zone_id":   None,
    },
    {
        "name":      "RAIN-01 — Cảm biến mưa sân vườn",
        "type_key":  "Cảm biến mưa",
        "pin":       "GPIO 4 (Digital)",
        "is_active": True,
        "zone_id":   None,
    },
    {
        "name":      "RLY-01 — Relay van tưới tổng",
        "type_key":  "Relay / Van điện từ",
        "pin":       "GPIO 5 (Digital)",
        "is_active": False,
        "zone_id":   None,
    },
]

print("\n── Thêm / cập nhật Device ──")

# ── Xoá thiết bị cũ chưa có số thứ tự (tên ngắn) nếu vẫn tồn tại ──
OLD_NAMES = ["DHT20","Soil Moisture","Light Sensor","LCD 16x2",
             "Pump 1","Pump 2","Fan","NeoPixel LED"]
for old_name in OLD_NAMES:
    old = db.query(models.Device).filter_by(name=old_name).first()
    if old:
        db.delete(old)
        print(f"  🗑  Đã xoá thiết bị cũ: {old_name}")
db.commit()

# ── Thêm thiết bị theo template cho từng khu vực ──
for zone_id, zone_info in ZONE_MAP.items():
    short = zone_info["short"]
    for tpl in DEVICE_TEMPLATES:
        dev_name = f"{short}-{tpl['suffix']}"
        existing = db.query(models.Device).filter_by(name=dev_name).first()
        if existing:
            print(f"  ✓ Đã tồn tại: {dev_name}")
        else:
            device = models.Device(
                name          = dev_name,
                type_id       = type_map[tpl["type_key"]],
                pin_connector = tpl["pin"],
                is_active     = tpl["is_active"],
                zone_id       = zone_id,
            )
            db.add(device)
            print(f"  + Thêm mới:   {dev_name}  (zone={zone_id})")

# ── Thêm thiết bị dùng chung ──
for sd in SHARED_DEVICES:
    existing = db.query(models.Device).filter_by(name=sd["name"]).first()
    if existing:
        print(f"  ✓ Đã tồn tại: {sd['name']}")
    else:
        device = models.Device(
            name          = sd["name"],
            type_id       = type_map[sd["type_key"]],
            pin_connector = sd["pin"],
            is_active     = sd["is_active"],
            zone_id       = sd["zone_id"],
        )
        db.add(device)
        print(f"  + Thêm mới:   {sd['name']}  (shared)")

db.commit()

# In tổng kết
total = db.query(models.Device).count()
print(f"\n  ✅ Tổng thiết bị trong DB: {total}")

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

# ─────────────────────────────────────────────────────────────────
# 4. ALERT LOGS  (8 bản ghi mẫu — 2 per type)
# ─────────────────────────────────────────────────────────────────
from datetime import datetime, timedelta

alert_logs_data = [
    # ── critical ──────────────────────────────────────────────────
    {
        "log_type":         "critical",
        "severity":         "critical",
        "title":            "Nhiệt độ vượt ngưỡng an toàn",
        "message":          "⚠️ Nhiệt độ Vườn Táo đã vượt mốc 35°C (Ngưỡng tối đa: 26°C). Nguy cơ héo lá!",
        "actor":            "SYSTEM",
        "metric_key":       "temperature",
        "metric_value":     36.4,
        "threshold":        26.0,
        "action_label":     "Bật quạt giải nhiệt ngay",
        "action_type":      "toggle_device",
        "is_read":          False,
        "created_at":       datetime.utcnow() - timedelta(minutes=3),
    },
    {
        "log_type":         "critical",
        "severity":         "critical",
        "title":            "Cảm biến độ ẩm đất mất kết nối",
        "message":          "🔴 Cảm biến Soil Moisture tại Vườn Dưa hấu offline quá 10 phút. Không thể giám sát độ ẩm đất.",
        "actor":            "SYSTEM",
        "action_label":     "Kiểm tra thiết bị",
        "action_type":      "navigate_device",
        "is_read":          False,
        "created_at":       datetime.utcnow() - timedelta(minutes=11),
    },
    # ── warning ───────────────────────────────────────────────────
    {
        "log_type":         "warning",
        "severity":         "warning",
        "title":            "Độ ẩm đất tiệm cận ngưỡng tối thiểu",
        "message":          "Độ ẩm đất Vườn Dưa hấu đang giảm nhanh, hiện ở mức 52% (Ngưỡng tối thiểu: 60%). Cần tưới sớm.",
        "actor":            "SYSTEM",
        "metric_key":       "humidity",
        "metric_value":     52.0,
        "threshold":        60.0,
        "action_label":     "Bật bơm tưới",
        "action_type":      "toggle_device",
        "is_read":          False,
        "created_at":       datetime.utcnow() - timedelta(minutes=8),
    },
    {
        "log_type":         "warning",
        "severity":         "warning",
        "title":            "Máy bơm hoạt động liên tục quá lâu",
        "message":          "Pump 1 đã hoạt động liên tục hơn 2 giờ. Cần kiểm tra để tránh quá tải động cơ.",
        "actor":            "SYSTEM",
        "action_label":     "Xem thiết bị",
        "action_type":      "navigate_device",
        "is_read":          True,
        "created_at":       datetime.utcnow() - timedelta(hours=2, minutes=5),
    },
    # ── automation ────────────────────────────────────────────────
    {
        "log_type":         "automation",
        "severity":         "success",
        "title":            "Máy bơm tự động bật",
        "message":          "💧 Hệ thống đã tự động bật Pump 1 tại Vườn Táo do độ ẩm đất thấp hơn ngưỡng (48%).",
        "actor":            "SYSTEM",
        "metric_key":       "humidity",
        "metric_value":     48.0,
        "threshold":        50.0,
        "is_read":          True,
        "created_at":       datetime.utcnow() - timedelta(minutes=30),
    },
    {
        "log_type":         "automation",
        "severity":         "info",
        "title":            "Đèn LED tắt theo lịch",
        "message":          "🕒 Đèn NeoPixel LED Khu ươm mầm đã được tắt tự động theo lịch trình (18:00).",
        "actor":            "SYSTEM",
        "is_read":          True,
        "created_at":       datetime.utcnow() - timedelta(hours=1),
    },
    # ── system ────────────────────────────────────────────────────
    {
        "log_type":         "system",
        "severity":         "info",
        "title":            "Thay đổi cấu hình cây trồng",
        "message":          "Admin vừa thay đổi ngưỡng nhiệt độ tối đa của 'Dưa hấu' từ 30°C lên 35°C.",
        "actor":            "Admin",
        "is_read":          True,
        "created_at":       datetime.utcnow() - timedelta(hours=3),
    },
    {
        "log_type":         "system",
        "severity":         "info",
        "title":            "Thao tác thủ công thiết bị",
        "message":          "Người dùng 'Nông dân A' vừa bật Pump 2 bằng tay từ trang Quản lý thiết bị.",
        "actor":            "Nông dân A",
        "action_label":     "Xem lịch sử",
        "action_type":      "navigate_device",
        "is_read":          True,
        "created_at":       datetime.utcnow() - timedelta(hours=4),
    },
]

print("\n── Thêm AlertLog ──")
# Chỉ seed nếu bảng trống
existing_count = db.query(models.AlertLog).count()
if existing_count > 0:
    print(f"  ✓ Đã có {existing_count} log entries, bỏ qua seed logs")
else:
    for log_data in alert_logs_data:
        entry = models.AlertLog(
            log_type         = log_data["log_type"],
            severity         = log_data["severity"],
            title            = log_data["title"],
            message          = log_data["message"],
            actor            = log_data.get("actor"),
            metric_key       = log_data.get("metric_key"),
            metric_value     = log_data.get("metric_value"),
            threshold        = log_data.get("threshold"),
            action_label     = log_data.get("action_label"),
            action_type      = log_data.get("action_type"),
            is_read          = log_data.get("is_read", False),
            created_at       = log_data.get("created_at", datetime.utcnow()),
        )
        db.add(entry)
        print(f"  + Thêm log:   [{log_data['log_type'].upper()}] {log_data['title']}")
    db.commit()

db.close()

print("\n✅ Seed hoàn tất!")
