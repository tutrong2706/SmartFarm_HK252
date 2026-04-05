import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
import models

db = SessionLocal()

print("🗑 Đang xóa toàn bộ nhật ký (AlertLogs) để tránh lỗi khoá ngoại...")
db.query(models.AlertLog).delete()

print("🗑 Đang xóa toàn bộ thiết bị cũ...")
db.query(models.Device).delete()
db.commit()

print("🔍 Đang tìm các loại thiết bị trong DB...")
types = {dt.name: dt.id for dt in db.query(models.DeviceType).all()}

# Fallback nếu thiếu type
def get_type_id(name):
    return types.get(name) or types.get(list(types.keys())[0])

adafruit_devices = [
    # CẢM BIẾN
    models.Device(
        name="Adafruit — DHT20 Temp",
        type_id=get_type_id("Nhiệt độ & Độ ẩm không khí"),
        pin_connector="AIO /dadn-dht20-temp",
        is_active=True,
        zone_id=1
    ),
    models.Device(
        name="Adafruit — DHT20 Humidity",
        type_id=get_type_id("Nhiệt độ & Độ ẩm không khí"),
        pin_connector="AIO /dadn-dht20-hum",
        is_active=True,
        zone_id=1
    ),
    models.Device(
        name="Adafruit — Light Sensor",
        type_id=get_type_id("Cường độ ánh sáng"),
        pin_connector="AIO /dadn-light-sensor",
        is_active=True,
        zone_id=1
    ),
    models.Device(
        name="Adafruit — Soil Moisture",
        type_id=get_type_id("Độ ẩm đất"),
        pin_connector="AIO /dadn-soil-moisture",
        is_active=True,
        zone_id=1
    ),
    
    # THIẾT BỊ ĐIỀU KHIỂN (ACTUATORS)
    models.Device(
        name="Adafruit — System Fan",
        type_id=get_type_id("Quạt thông gió"),
        pin_connector="AIO /dadn-fan",
        is_active=False,
        zone_id=1
    ),
    models.Device(
        name="Adafruit — Water Pump",
        type_id=get_type_id("Bơm nước"),
        pin_connector="AIO /pump",
        is_active=False,
        zone_id=1
    ),
    models.Device(
        name="Adafruit — Light Control",
        type_id=get_type_id("Đèn LED RGB"),
        pin_connector="AIO /light-control",
        is_active=False,
        zone_id=1
    ),
    models.Device(
        name="Adafruit — Mode Switch",
        type_id=get_type_id("Màn hình hiển thị"), # Tạm dùng loại này cho biến Mode
        pin_connector="AIO /mode",
        is_active=True,
        zone_id=1
    )
]

db.add_all(adafruit_devices)
db.commit()

print("✅ Đã thiết lập xong toàn bộ các Device dựa theo Feed của Adafruit vào Zone 1!\n")
for d in adafruit_devices:
    print(f"   - {d.name} (Pin: {d.pin_connector})")
