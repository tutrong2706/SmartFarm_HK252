"""
seed.py — Nhập và Cập nhật dữ liệu mẫu vào database SmartFarm
Chạy: python seed.py  (từ thư mục backend/)
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine
import models
from datetime import datetime, timedelta

# Tạo bảng nếu chưa có (không làm thay đổi bảng đã có)
models.Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ─────────────────────────────────────────────────────────────────
# 0. ZONES
# ─────────────────────────────────────────────────────────────────
zones_data = [
    {"name": "Vườn Táo",    "description": "Khu vực trồng táo",   "crop_setting_id": None},
    {"name": "Vườn Nho",    "description": "Khu vực trồng nho",   "crop_setting_id": None},
    {"name": "Vườn Đào",    "description": "Khu vực trồng đào",   "crop_setting_id": None},
    {"name": "Vườn Dưa Hấu","description": "Khu vực trồng dưa hấu","crop_setting_id": None},
]

print("── Thêm / Cập nhật Zone ──")
zone_id_map = {}
for i, z_data in enumerate(zones_data, start=1):
    existing = db.query(models.Zone).filter_by(name=z_data["name"]).first()
    if existing:
        for k, v in z_data.items(): setattr(existing, k, v)
        zone_id_map[i] = existing.id
        print(f"  🔄 Đã cập nhật: {z_data['name']} (id={existing.id})")
    else:
        zone = models.Zone(**z_data)
        db.add(zone)
        db.flush()
        zone_id_map[i] = zone.id
        print(f"  + Thêm mới:   {z_data['name']} (id={zone.id})")
db.commit()

# ─────────────────────────────────────────────────────────────────
# 1. DEVICE TYPES
# ─────────────────────────────────────────────────────────────────
device_types_data = [
    {"name": "Nhiệt độ & Độ ẩm không khí",  "category": "SENSOR"},
    {"name": "Độ ẩm đất",                   "category": "SENSOR"},
    {"name": "Cường độ ánh sáng",           "category": "SENSOR"},
    {"name": "CO2 / Chất lượng không khí",  "category": "SENSOR"},
    {"name": "Cảm biến mưa",               "category": "SENSOR"},
    {"name": "Màn hình hiển thị",           "category": "ACTUATOR"},
    {"name": "Bơm nước",                    "category": "ACTUATOR"},
    {"name": "Quạt thông gió",              "category": "ACTUATOR"},
    {"name": "Đèn LED RGB",                 "category": "ACTUATOR"},
    {"name": "Relay / Van điện từ",         "category": "ACTUATOR"},
]

print("\n── Thêm / Cập nhật DeviceType ──")
type_map = {}
for dt_data in device_types_data:
    existing = db.query(models.DeviceType).filter_by(name=dt_data["name"]).first()
    if existing:
        existing.category = dt_data["category"]
        type_map[dt_data["name"]] = existing.id
        print(f"  🔄 Đã cập nhật: {dt_data['name']}")
    else:
        dt = models.DeviceType(**dt_data)
        db.add(dt)
        db.flush()
        type_map[dt_data["name"]] = dt.id
        print(f"  + Thêm mới:   {dt_data['name']} (id={dt.id})")
db.commit()

# ─────────────────────────────────────────────────────────────────
# 2. DEVICES
# ─────────────────────────────────────────────────────────────────
ZONE_MAP = {
    1: {"short": "TAO",  "label": "Vườn Táo"},
    2: {"short": "NHO",  "label": "Vườn Nho"},
    3: {"short": "DAO",  "label": "Vườn Đào"},
    4: {"short": "DUA",  "label": "Vườn Dưa Hấu"},
}

DEVICE_TEMPLATES = [
    {"suffix": "S01 — DHT20", "type_key": "Nhiệt độ & Độ ẩm không khí", "pin": "I2C (SDA/SCL)", "is_active": True},
    {"suffix": "S02 — Soil Moisture", "type_key": "Độ ẩm đất", "pin": "GPIO 2 (Analog)", "is_active": True},
    {"suffix": "S03 — Light Sensor", "type_key": "Cường độ ánh sáng", "pin": "GPIO 3 (Analog)", "is_active": True},
    {"suffix": "S04 — CO2 Sensor", "type_key": "CO2 / Chất lượng không khí", "pin": "UART (TX/RX)", "is_active": True},
    {"suffix": "A01 — Pump", "type_key": "Bơm nước", "pin": "GPIO 8 (Digital)", "is_active": False},
    {"suffix": "A02 — Fan", "type_key": "Quạt thông gió", "pin": "GPIO 1 (PWM)", "is_active": False},
]

SHARED_DEVICES = [
    {"name": "LCD-01 — Màn hình trung tâm", "type_key": "Màn hình hiển thị", "pin": "I2C (0x27)", "is_active": True, "zone_id": None},
    {"name": "LED-01 — NeoPixel tổng", "type_key": "Đèn LED RGB", "pin": "GPIO 6 (WS2812B)", "is_active": False, "zone_id": None},
    {"name": "RAIN-01 — Cảm biến mưa sân vườn", "type_key": "Cảm biến mưa", "pin": "GPIO 4 (Digital)", "is_active": True, "zone_id": None},
    {"name": "RLY-01 — Relay van tưới tổng", "type_key": "Relay / Van điện từ", "pin": "GPIO 5 (Digital)", "is_active": False, "zone_id": None},
]

print("\n── Thêm / Cập nhật Device ──")
# Xóa các thiết bị cũ không đúng chuẩn nếu có
OLD_NAMES = ["DHT20","Soil Moisture","Light Sensor","LCD 16x2","Pump 1","Pump 2","Fan","NeoPixel LED"]
for old_name in OLD_NAMES:
    old = db.query(models.Device).filter_by(name=old_name).first()
    if old:
        db.delete(old)

for zone_id, zone_info in ZONE_MAP.items():
    short = zone_info["short"]
    for tpl in DEVICE_TEMPLATES:
        dev_name = f"{short}-{tpl['suffix']}"
        existing = db.query(models.Device).filter_by(name=dev_name).first()
        if existing:
            existing.type_id = type_map[tpl["type_key"]]
            existing.pin_connector = tpl["pin"]
            existing.is_active = tpl["is_active"]
            existing.zone_id = zone_id
            print(f"  🔄 Đã cập nhật: {dev_name}")
        else:
            device = models.Device(name=dev_name, type_id=type_map[tpl["type_key"]], pin_connector=tpl["pin"], is_active=tpl["is_active"], zone_id=zone_id)
            db.add(device)
            print(f"  + Thêm mới:   {dev_name}")

for sd in SHARED_DEVICES:
    existing = db.query(models.Device).filter_by(name=sd["name"]).first()
    if existing:
        existing.type_id = type_map[sd["type_key"]]
        existing.pin_connector = sd["pin"]
        existing.is_active = sd["is_active"]
        existing.zone_id = sd["zone_id"]
        print(f"  🔄 Đã cập nhật: {sd['name']}")
    else:
        device = models.Device(name=sd["name"], type_id=type_map[sd["type_key"]], pin_connector=sd["pin"], is_active=sd["is_active"], zone_id=sd["zone_id"])
        db.add(device)
        print(f"  + Thêm mới:   {sd['name']}")
db.commit()

# ─────────────────────────────────────────────────────────────────
# 3. CROP SETTINGS 
# ─────────────────────────────────────────────────────────────────
crop_settings_data = [
    {"crop_name": "Táo", "temp_min": 18.0, "temp_max": 26.0, "humid_min": 50.0, "humid_max": 70.0, "light_min": 15000.0, "light_max": 35000.0, "light_type": "SUN", "auto_mode": True},
    {"crop_name": "Nho", "temp_min": 20.0, "temp_max": 30.0, "humid_min": 55.0, "humid_max": 75.0, "light_min": 15000.0, "light_max": 35000.0, "light_type": "SUN", "auto_mode": True},
    {"crop_name": "Đào", "temp_min": 15.0, "temp_max": 24.0, "humid_min": 45.0, "humid_max": 65.0, "light_min": 5000.0, "light_max": 12000.0, "light_type": "SHADE", "auto_mode": False},
    {"crop_name": "Dưa hấu", "temp_min": 25.0, "temp_max": 35.0, "humid_min": 60.0, "humid_max": 80.0, "light_min": 15000.0, "light_max": 35000.0, "light_type": "SUN", "auto_mode": True},
]

print("\n── Thêm / Cập nhật CropSetting ──")
for c_data in crop_settings_data:
    existing = db.query(models.CropSetting).filter_by(crop_name=c_data["crop_name"]).first()
    if existing:
        for key, value in c_data.items():
            setattr(existing, key, value)
        print(f"  🔄 Đã cập nhật: {c_data['crop_name']}")
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
        "zone_id":          1,
        "metric_key":       "temperature",
        "metric_value":     36.4,
        "threshold":        26.0,
        "action_label":     "Bật quạt giải nhiệt",
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
        "zone_id":          4,
        "action_label":     "Kiểm tra Vườn Dưa Hấu",
        "action_type":      "navigate_zone",
        "is_read":          False,
        "created_at":       datetime.utcnow() - timedelta(minutes=11),
    },
    {
        "log_type":         "critical",
        "severity":         "critical",
        "title":            "Độ ẩm đất vượt ngưỡng tối đa",
        "message":          "💧 Độ ẩm đất Vườn Nho đạt 82% (Ngưỡng tối đa: 75%). Nguy cơ úng rễ! Cần thoát nước ngay.",
        "actor":            "SYSTEM",
        "zone_id":          2,
        "metric_key":       "humidity",
        "metric_value":     82.0,
        "threshold":        75.0,
        "action_label":     "Bật van thoát nước",
        "action_type":      "navigate_zone",
        "is_read":          False,
        "created_at":       datetime.utcnow() - timedelta(minutes=7),
    },
    {
        "log_type":         "critical",
        "severity":         "critical",
        "title":            "CO2 vượt ngưỡng nguy hiểm",
        "message":          "🌫️ Nồng độ CO2 tại Vườn Nho đạt 1.200ppm (Ngưỡng tối đa: 800ppm). Cần thông gió gấp!",
        "actor":            "SYSTEM",
        "zone_id":          2,
        "metric_key":       "light",
        "metric_value":     1200.0,
        "threshold":        800.0,
        "action_label":     "Bật quạt thông gió",
        "action_type":      "navigate_zone",
        "is_read":          False,
        "created_at":       datetime.utcnow() - timedelta(minutes=15),
    },
    {
        "log_type":         "critical",
        "severity":         "critical",
        "title":            "Gateway mất kết nối",
        "message":          "📡 Cổng IoT Gateway không phản hồi từ 5 phút trước. Toàn bộ cảm biến ngừng gửi dữ liệu!",
        "actor":            "SYSTEM",
        "action_label":     "Kiểm tra Gateway",
        "action_type":      "navigate_zone",
        "is_read":          False,
        "created_at":       datetime.utcnow() - timedelta(minutes=5),
    },
    # ── warning ───────────────────────────────────────────────────
    {
        "log_type":         "warning",
        "severity":         "warning",
        "title":            "Độ ẩm đất tiệm cận ngưỡng tối thiểu",
        "message":          "Độ ẩm đất Vườn Dưa hấu đang giảm nhanh, hiện ở mức 52% (Ngưỡng tối thiểu: 60%). Cần tưới sớm.",
        "actor":            "SYSTEM",
        "zone_id":          4,
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
        "title":            "Ánh sáng vượt ngưỡng cho phép",
        "message":          "☀️ Cường độ ánh sáng Vườn Đào đạt 45.000 Lux (Ngưỡng tối đa: 12.000 Lux - Cây ưa bóng). Nguy cơ cháy lá!",
        "actor":            "SYSTEM",
        "zone_id":          3,
        "metric_key":       "light",
        "metric_value":     45000.0,
        "threshold":        12000.0,
        "action_label":     "Bật lưới che nắng",
        "action_type":      "navigate_zone",
        "is_read":          False,
        "created_at":       datetime.utcnow() - timedelta(minutes=5),
    },
    {
        "log_type":         "warning",
        "severity":         "warning",
        "title":            "Máy bơm hoạt động liên tục quá lâu",
        "message":          "Pump 1 tại Vườn Táo đã hoạt động liên tục hơn 2 giờ. Cần kiểm tra để tránh quá tải động cơ.",
        "actor":            "SYSTEM",
        "zone_id":          1,
        "action_label":     "Xem Vườn Táo",
        "action_type":      "navigate_zone",
        "is_read":          True,
        "created_at":       datetime.utcnow() - timedelta(hours=2, minutes=5),
    },
    {
        "log_type":         "warning",
        "severity":         "warning",
        "title":            "Nhiệt độ tiệm cận ngưỡng tối đa",
        "message":          "🌡️ Nhiệt độ Vườn Nho đang ở 28°C (Ngưỡng tối đa: 30°C). Cần theo dõi sát.",
        "actor":            "SYSTEM",
        "zone_id":          2,
        "metric_key":       "temperature",
        "metric_value":     28.0,
        "threshold":        30.0,
        "action_label":     "Theo dõi nhiệt độ",
        "action_type":      "navigate_zone",
        "is_read":          False,
        "created_at":       datetime.utcnow() - timedelta(minutes=20),
    },
    {
        "log_type":         "warning",
        "severity":         "warning",
        "title":            "Pin cảm biến yếu",
        "message":          "🔋 Cảm biến Soil Moisture tại Vườn Táo có pin chỉ còn 15%. Cần thay pin sớm.",
        "actor":            "SYSTEM",
        "zone_id":          1,
        "action_label":     "Thay pin",
        "action_type":      "navigate_zone",
        "is_read":          False,
        "created_at":       datetime.utcnow() - timedelta(hours=1),
    },
    {
        "log_type":         "warning",
        "severity":         "warning",
        "title":            "Bể nước sắp cạn",
        "message":          "💧 Mực nước bể chứa dưới 20%. Cần bơm bổ sung để đảm bảo tưới tiêu cho các khu vực.",
        "actor":            "SYSTEM",
        "action_label":     "Kiểm tra bể nước",
        "action_type":      "navigate_zone",
        "is_read":          False,
        "created_at":       datetime.utcnow() - timedelta(minutes=45),
    },
    # ── automation ────────────────────────────────────────────────
    {
        "log_type":         "automation",
        "severity":         "success",
        "title":            "Máy bơm tự động bật",
        "message":          "💧 Hệ thống đã tự động bật Pump tại Vườn Táo do độ ẩm đất thấp hơn ngưỡng (48%).",
        "actor":            "SYSTEM",
        "zone_id":          1,
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
        "message":          "🕒 Đèn LED tổng đã được tắt tự động theo lịch trình (18:00).",
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
        "message":          "Người dùng 'Nông dân A' vừa bật máy bơm tại Vườn Nho bằng tay từ trang quản lý.",
        "actor":            "Nông dân A",
        "zone_id":          2,
        "action_label":     "Xem Vườn Nho",
        "action_type":      "navigate_zone",
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
            zone_id          = log_data.get("zone_id"),
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
