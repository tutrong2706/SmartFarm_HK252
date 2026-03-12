"""
mock_gateway.py — Giả lập Gateway IoT SmartFarm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Quy tắc hoạt động:
  1. Khi khởi động, truy vấn API để lấy danh sách khu vực (zones).
  2. Với mỗi khu vực, truy vấn xem có thiết bị SENSOR nào được gán không.
  3. CHỈ gửi dữ liệu cho khu vực có ít nhất 1 SENSOR đang hoạt động (is_active=True).
  4. Mỗi SENSOR type sẽ cho ra loại dữ liệu khác nhau (nhiệt độ, độ ẩm, ánh sáng).
  5. Payload gửi lên bao gồm: zone_id, zone_name, danh sách sensors, các chỉ số,
     và measured_at (ISO 8601 timestamp) để frontend hiển thị "đo lúc X".
  6. Mỗi lần lặp cũng gọi lại API để cập nhật zone/sensor list (hot-reload).

Cách chạy:
  cd gateway
  python mock_gateway.py
"""

import time
import random
import requests
from datetime import datetime, timezone

# ─── Cấu hình ────────────────────────────────────────────────────────────────
BASE_URL      = "http://localhost:8000"
TELEMETRY_URL = f"{BASE_URL}/api/telemetry"
ZONES_URL     = f"{BASE_URL}/api/zones/"
DEVICES_URL   = f"{BASE_URL}/api/devices/"
INTERVAL_SEC  = 5      # giây giữa mỗi lần gửi
RELOAD_EVERY  = 12     # số chu kỳ trước khi reload zone/device list

# Nhiễu ngẫu nhiên nhỏ để giả lập dao động thực tế
def jitter(val, pct=0.04):
    return round(val * (1 + random.uniform(-pct, pct)), 1)

# ─── Hồ sơ môi trường mặc định cho từng khu vực ──────────────────────────────
# Mỗi khu sẽ có "baseline" khác nhau để dữ liệu có ý nghĩa
ZONE_PROFILES = {
    1: {"temp_base": 30.0, "humid_base": 70.0, "light_base": 800},
    2: {"temp_base": 26.0, "humid_base": 60.0, "light_base": 600},
    3: {"temp_base": 28.0, "humid_base": 75.0, "light_base": 500},
    4: {"temp_base": 24.0, "humid_base": 55.0, "light_base": 900},
}
DEFAULT_PROFILE = {"temp_base": 28.0, "humid_base": 65.0, "light_base": 650}


def get_profile(zone_id):
    return ZONE_PROFILES.get(zone_id, DEFAULT_PROFILE)


def build_sensor_state(sensors):
    """
    Xây dựng dict trạng thái cảm biến: loại sensor nào đang active.
    sensors: list[dict] từ API /api/devices/
    """
    active_types = {}
    for s in sensors:
        if s.get("is_active") and s.get("device_type") == "SENSOR":
            func = (s.get("func") or "").lower()
            name = (s.get("device_name") or "").lower()
            key = None
            if "nhiệt" in func or "temp" in name or "dht" in name:
                key = "temperature"
            elif "độ ẩm" in func or "humid" in func or "soil" in name:
                key = "humidity"
            elif "ánh sáng" in func or "light" in name:
                key = "light"
            if key:
                active_types[key] = s.get("device_name", "sensor")
    return active_types


def fetch_active_zones():
    """
    Trả về list[dict]:
      zone_id, zone_name, active_sensor_types (dict: key → device_name)
    Chỉ bao gồm khu vực có ít nhất 1 SENSOR active.
    """
    try:
        zones_resp = requests.get(ZONES_URL, timeout=5)
        devices_resp = requests.get(DEVICES_URL, timeout=5)
        zones_resp.raise_for_status()
        devices_resp.raise_for_status()
    except Exception as e:
        print(f"  ❌ Không lấy được dữ liệu zone/device từ API: {e}")
        return []

    zones = zones_resp.json()
    all_devices = devices_resp.json()

    # Nhóm device theo zone_id
    devices_by_zone = {}
    for d in all_devices:
        z = d.get("zone_id")
        if z is not None:
            devices_by_zone.setdefault(z, []).append(d)

    active_zones = []
    for zone in zones:
        zid = zone["id"]
        sensors_in_zone = [d for d in devices_by_zone.get(zid, [])
                           if d.get("device_type") == "SENSOR" and d.get("is_active")]
        if not sensors_in_zone:
            continue  # Khu vực không có SENSOR active → bỏ qua

        sensor_types = build_sensor_state(sensors_in_zone)
        if not sensor_types:
            continue  # Không nhận ra loại sensor nào

        active_zones.append({
            "zone_id":   zid,
            "zone_name": zone.get("name", f"Khu {zid}"),
            "sensors":   sensor_types,
            "device_list": [s["device_name"] for s in sensors_in_zone],
        })

    return active_zones


def generate_payload(zone_info):
    """
    Tạo payload cho một khu vực. CHỈ gồm các chỉ số mà khu vực đó có sensor tương ứng.
    """
    profile = get_profile(zone_info["zone_id"])
    sensor_types = zone_info["sensors"]
    now_iso = datetime.now(timezone.utc).isoformat()

    payload = {
        "zone_id":    zone_info["zone_id"],
        "zone_name":  zone_info["zone_name"],
        "measured_at": now_iso,       # ISO timestamp → frontend tính "X phút trước"
        "sensors":    zone_info["device_list"],
    }

    if "temperature" in sensor_types:
        payload["temperature"] = jitter(profile["temp_base"])
    if "humidity" in sensor_types:
        payload["humidity"] = jitter(profile["humid_base"])
    if "light" in sensor_types:
        payload["light"] = int(jitter(profile["light_base"]))

    return payload


def send_payload(payload):
    try:
        resp = requests.post(TELEMETRY_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            ts = datetime.now().strftime("%H:%M:%S")
            keys = [k for k in ("temperature", "humidity", "light") if k in payload]
            vals = "  ".join(
                f"{'🌡' if k=='temperature' else '💧' if k=='humidity' else '☀️'}"
                f"{payload[k]}{'°C' if k=='temperature' else '%' if k=='humidity' else ' lx'}"
                for k in keys
            )
            print(f"  [{ts}] Zone {payload['zone_id']} ({payload['zone_name']}) → {vals}")
        elif resp.status_code == 400:
            print(f"  ⚠  Zone {payload['zone_id']} bị từ chối: {resp.json().get('detail')}")
        else:
            print(f"  ⚠  Zone {payload['zone_id']}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ❌ Lỗi gửi zone {payload['zone_id']}: {e}")


# ─── Main loop ────────────────────────────────────────────────────────────────
print("=" * 60)
print("  🌿  SmartFarm Mock Gateway — khởi động")
print(f"  📡  Backend: {BASE_URL}")
print(f"  ⏱   Interval: {INTERVAL_SEC}s · Reload zone list mỗi {RELOAD_EVERY * INTERVAL_SEC}s")
print("=" * 60)

active_zones = []
cycle = 0

while True:
    # Reload zone/sensor list định kỳ (hoặc khi list rỗng)
    if cycle % RELOAD_EVERY == 0 or not active_zones:
        print("\n🔄 Đang kiểm tra danh sách khu vực & cảm biến từ API...")
        active_zones = fetch_active_zones()
        if active_zones:
            print(f"✅ Tìm thấy {len(active_zones)} khu vực có cảm biến active:")
            for z in active_zones:
                sensor_str = ", ".join(
                    f"{k} ({v})" for k, v in z["sensors"].items()
                )
                print(f"   • Zone {z['zone_id']} — {z['zone_name']}: {sensor_str}")
        else:
            print("⚠  Không có khu vực nào có SENSOR active. Chờ cấu hình...")
            print("   → Hãy vào Quản lý Thiết bị, bật cảm biến và gán vào khu vực.")
        print()

    if active_zones:
        print(f"📤 Gửi dữ liệu ({len(active_zones)} zone):")
        for zone_info in active_zones:
            payload = generate_payload(zone_info)
            send_payload(payload)

    cycle += 1
    time.sleep(INTERVAL_SEC)
