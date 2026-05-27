import time
import requests
import os
from dotenv import load_dotenv

# Load cấu hình
load_dotenv()
AIO_USERNAME = os.getenv('OWNER_USERNAME', 'YOUR_USERNAME')
AIO_KEY = os.getenv('ADAFRUIT_IO_KEY', 'YOUR_KEY')
BASE_URL = "http://localhost:8000"

# Cấu hình thiết bị cần test (ID của Quạt là 37 như bạn nói)
TEST_DEVICE_ID  =41
FEED_KEY = "dadn-fan"

def print_step(msg):
    print(f"\n{'-'*50}\n▶ {msg}\n{'-'*50}")

def test_web_to_adafruit():
    """TEST LUỒNG 1: Web gọi API -> Backend gửi lên Adafruit"""
    print_step("TEST LUỒNG 1: WEB -> BACKEND -> ADAFRUIT")
    
    # 1. Gọi API Backend (Giả lập người dùng bấm nút ON trên Web)
    print("1. Giả lập bấm Web: Bật Quạt (is_active=True)")
    api_url = f"{BASE_URL}/api/devices/{TEST_DEVICE_ID}/toggle"
    try:
        res = requests.patch(api_url, json={"is_active": True}, timeout=5)
        if res.status_code == 200:
            print("   ✅ Gọi API Backend thành công.")
        else:
            print(f"   ❌ Lỗi API Backend: {res.text}")
            return False
    except Exception as e:
        print(f"   ❌ Không thể kết nối Backend: {e}")
        return False

    # 2. Kiểm tra trực tiếp trên Adafruit REST API xem dữ liệu đã lên chưa
    print(f"2. Chờ 3 giây để Backend gửi tín hiệu lên Adafruit...")
    time.sleep(3)
    
    aio_url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{FEED_KEY}/data/last"
    headers = {"X-AIO-Key": AIO_KEY}
    try:
        res_aio = requests.get(aio_url, headers=headers, timeout=5)
        if res_aio.status_code == 200:
            last_value = res_aio.json().get("value")
            if last_value == "1":
                print("   ✅ THÀNH CÔNG: Tín hiệu đã lên tới Adafruit IO (value=1)!")
            else:
                print(f"   ❌ THẤT BẠI: Adafruit nhận được value={last_value} thay vì 1.")
        else:
            print(f"   ❌ Lỗi truy cập Adafruit: {res_aio.text}")
    except Exception as e:
        print(f"   ❌ Lỗi kết nối Adafruit: {e}")

def test_adafruit_to_web():
    """TEST LUỒNG 2: Adafruit thay đổi -> Gateway -> Backend cập nhật DB"""
    print_step("TEST LUỒNG 2: ADAFRUIT -> GATEWAY -> BACKEND (CẬP NHẬT DB)")
    
    # 1. Giả lập tín hiệu tắt từ Gateway (như thể Gateway vừa bắt được tín hiệu OFF từ MQTT)
    print("1. Giả lập Gateway nhận tín hiệu tắt từ Adafruit và báo cho Backend...")
    sync_url = f"{BASE_URL}/api/devices/sync-feed"
    payload = {
        "feed_key": FEED_KEY,
        "is_active": False
    }
    try:
        res = requests.post(sync_url, json=payload, timeout=5)
        if res.status_code == 200:
            print("   ✅ Gateway đã gọi API sync-feed thành công.")
        else:
            print(f"   ❌ Lỗi API sync-feed: {res.text}")
            return False
    except Exception as e:
        print(f"   ❌ Không thể kết nối Backend: {e}")
        return False

    # 2. Kiểm tra xem Database có thực sự tắt cái Quạt chưa (Giả lập Web load lại)
    print("2. Kiểm tra lại Database xem trạng thái thiết bị...")
    check_url = f"{BASE_URL}/api/devices/" # Có thể viết API get theo ID, đây lấy list
    try:
        res_check = requests.get(check_url, timeout=5)
        devices = res_check.json()
        target_device = next((d for d in devices if d["id"] == TEST_DEVICE_ID), None)
        
        if target_device:
            if target_device["is_active"] == False:
                print(f"   ✅ THÀNH CÔNG: Thiết bị ID {TEST_DEVICE_ID} đã được cập nhật thành OFF trong Database!")
            else:
                print("   ❌ THẤT BẠI: Thiết bị vẫn đang ON trong Database.")
        else:
            print("   ❌ Không tìm thấy thiết bị trong Database.")
    except Exception as e:
        print(f"   ❌ Lỗi gọi API Backend: {e}")

if __name__ == "__main__":
    print("🚀 BẮT ĐẦU CHẠY KIỂM THỬ TỰ ĐỘNG (AUTOMATED TEST)")
    test_web_to_adafruit()
    test_adafruit_to_web()
    print("\n🎉 HOÀN TẤT BÀI KIỂM THỬ!")