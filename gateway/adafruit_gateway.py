import time
import os
import paho.mqtt.client as mqtt
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# --- Config: Adafruit IO ---
# --- Config: Adafruit IO ---
AIO_USERNAME = os.getenv('ADAFRUIT_IO_USERNAME', 'YOUR_ADAFRUIT_USERNAME')
AIO_KEY      = os.getenv('ADAFRUIT_IO_KEY', 'YOUR_ADAFRUIT_AIO_KEY')
OWNER_USERNAME = os.getenv('OWNER_USERNAME', 'YOUR_SECONDARY_ADAFRUIT_USERNAME')
AIO_BROKER   = "io.adafruit.com"
PORT         = 1883

# --- Config: Backend API ---
BASE_URL      = "http://localhost:8000"
TELEMETRY_URL = f"{BASE_URL}/api/telemetry"

# --- State ---
current_sensor_data = {
    "temperature": None,
    "humidity": None,
    "light": None,
    "soil": None
}

# (Bạn cần sửa lại tên Feed nếu khác)
FEEDS = {
    # Cảm biến (Gửi dữ liệu từ thiết bị lên)
    "temperature": f"{OWNER_USERNAME}/f/dadn-dht20-temp",
    "humidity": f"{OWNER_USERNAME}/f/dadn-dht20-hum",
    "light": f"{OWNER_USERNAME}/f/dadn-light-sensor",
    "soil": f"{OWNER_USERNAME}/f/dadn-soil-moisture",
    
    # Thiết bị điều khiển (Nhận lệnh từ Backend/Dashboard)
    "fan": f"{OWNER_USERNAME}/f/dadn-fan",
    "pump": f"{OWNER_USERNAME}/f/pump", # Tên feed pump bạn cần kiểm tra lại trên AIO
    "light_control": f"{OWNER_USERNAME}/f/light-control",
    "mode": f"{OWNER_USERNAME}/f/mode"
}

# Dùng một ID mặc định để test (Zone 1)
TARGET_ZONE_ID = 1
TARGET_ZONE_NAME = "Vườn Táo"


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Kết nối Adafruit IO thành công!")
        # Subscribe vào tất cả các feed
        for key, topic in FEEDS.items():
            client.subscribe(topic)
            print(f"📡 Subscribed to {topic}")
    else:
        print(f"❌ Lỗi kết nối Adafruit IO. Mã lỗi: {rc}")


def on_message(client, userdata, msg):
    """
    Khi có data đẩy về từ một Feed, cập nhật vào dictionary current_sensor_data
    """
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    print(f"📥 [MQTT] Nhận {payload} từ {topic}")

    # Map topic về key tương ứng (temperature, humidity, light, soil)
    # Các Feed liên quan đến Actuator (pump, fan, light_control) không cần parse giá trị.
    sensor_keys = ["temperature", "humidity", "light", "soil"]
    for key, feed_topic in FEEDS.items():
        if topic == feed_topic:
            if key in sensor_keys:
                try:
                    current_sensor_data[key] = float(payload)
                except ValueError:
                    pass
            else:
                print(f"⚙️ [Điều khiển] {key.upper()} vừa chuyển sang trạng thái: {payload}")
            break


def push_to_fastapi():
    """ 
    Gôm data và bắn POST request lên FastAPI 
    """
    # Nếu chưa nhận đủ data thì đợi tiếp 
    # (Tuỳ logic thực tế: có thể bắt buộc nhận đủ 3 cảm biến, hoặc có gì gửi nấy)
    if all(val is None for val in current_sensor_data.values()):
        return

    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Tạo payload giống định dạng Mock Gateway 
    payload = {
        "zone_id": TARGET_ZONE_ID,
        "zone_name": TARGET_ZONE_NAME,
        "measured_at": now_iso,
        "sensors": ["Bộ Cảm Biến Adafruit Mẫu"], # Fake danh sách module
    }

    if current_sensor_data["temperature"] is not None:
        payload["temperature"] = current_sensor_data["temperature"]
    if current_sensor_data["humidity"] is not None:
        payload["humidity"] = current_sensor_data["humidity"]
    if current_sensor_data["light"] is not None:
        payload["light"] = current_sensor_data["light"]

    try:
        resp = requests.post(TELEMETRY_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            print(f"✅ [API] Đã gửi lên Backend: {payload}")
        else:
            print(f"⚠️ [API] Lỗi: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ [API] Không kết nối được FASTAPI: {e}")

# --- Khởi tạo ---
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(AIO_USERNAME, AIO_KEY)
client.on_connect = on_connect
client.on_message = on_message

try:
    print(f"🔄 Đang kết nối tới {AIO_BROKER}...")
    client.connect(AIO_BROKER, PORT, 60)
    
    # Start thread chạy ngầm quản lý MQTT
    client.loop_start() 

    # Loop chính: Mỗi 10s gửi dữ liệu lên Backend từ những gì gom được
    while True:
        time.sleep(5)
        push_to_fastapi()
        
except KeyboardInterrupt:
    print("Ngắt bởi người dùng...")
    client.loop_stop()
    client.disconnect()
