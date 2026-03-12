from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import auth 
import models, schemas
from database import engine, get_db

# Lệnh này yêu cầu SQLAlchemy tạo toàn bộ các bảng trong CSDL
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Farm API",
    description="Backend API cho hệ thống Nông trại thông minh HK252",
    version="1.0.0"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Farm API! Database đã được kết nối và tạo bảng thành công."}

# ==========================================
# API CHO BẢNG KHU VỰC (ZONES)
# ==========================================
# 1. CREATE - Thêm khu vực mới
@app.post("/api/zones/", response_model=schemas.ZoneResponse)
def create_zone(zone: schemas.ZoneCreate, db: Session = Depends(get_db)):
    # Biến dữ liệu Pydantic thành SQLAlchemy Model
    db_zone = models.Zone(**zone.model_dump())
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone) # Lấy lại ID vừa được tự động tạo
    return db_zone

# 2. READ - Lấy danh sách toàn bộ khu vực
@app.get("/api/zones/", response_model=list[schemas.ZoneResponse])
def get_all_zones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    zones = db.query(models.Zone).offset(skip).limit(limit).all()
    return zones

# 3. READ - Lấy chi tiết 1 khu vực theo ID
@app.get("/api/zones/{zone_id}", response_model=schemas.ZoneResponse)
def get_zone_by_id(zone_id: int, db: Session = Depends(get_db)):
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực này")
    return zone

# 4. UPDATE - Cập nhật thông tin khu vực
@app.put("/api/zones/{zone_id}", response_model=schemas.ZoneResponse)
def update_zone(zone_id: int, zone_update: schemas.ZoneCreate, db: Session = Depends(get_db)):
    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực này")
    
    # Cập nhật các trường dữ liệu
    for key, value in zone_update.model_dump().items():
        setattr(db_zone, key, value)
        
    db.commit()
    db.refresh(db_zone)
    return db_zone

# 5. DELETE - Xóa khu vực
@app.delete("/api/zones/{zone_id}")
def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực này")
    db.delete(db_zone)
    db.commit()
    return {"message": "Đã xóa khu vực thành công"}

# 6. PATCH - Cập nhật một phần khu vực (gán cây trồng, đổi tên, mô tả...)
@app.patch("/api/zones/{zone_id}", response_model=schemas.ZoneResponse)
def patch_zone(zone_id: int, zone_patch: schemas.ZonePatch, db: Session = Depends(get_db)):
    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực này")
    update_data = zone_patch.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_zone, key, value)
    db.commit()
    db.refresh(db_zone)
    return db_zone

# 7. GET - Lấy danh sách thiết bị thuộc 1 khu vực
@app.get("/api/zones/{zone_id}/devices", response_model=list[schemas.DeviceResponse])
def get_devices_by_zone(zone_id: int, db: Session = Depends(get_db)):
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực này")
    result = []
    for d in zone.devices:
        dtype = db.query(models.DeviceType).filter(models.DeviceType.id == d.type_id).first()
        result.append(schemas.DeviceResponse(
            id          = d.id,
            device_name = d.name,
            device_type = dtype.category if dtype else "SENSOR",
            pin         = d.pin_connector,
            func        = dtype.name if dtype else None,
            zone_id     = d.zone_id,
            status      = "ONLINE" if d.is_active else "OFFLINE",
            is_active   = d.is_active,
        ))
    return result

# 8. POST - Gán thiết bị vào khu vực
@app.post("/api/zones/{zone_id}/devices/{device_id}", response_model=schemas.DeviceResponse)
def assign_device_to_zone(zone_id: int, device_id: int, db: Session = Depends(get_db)):
    zone   = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực")
    if not device:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")
    device.zone_id = zone_id
    db.commit()
    db.refresh(device)
    dtype = db.query(models.DeviceType).filter(models.DeviceType.id == device.type_id).first()
    return schemas.DeviceResponse(
        id          = device.id,
        device_name = device.name,
        device_type = dtype.category if dtype else "SENSOR",
        pin         = device.pin_connector,
        func        = dtype.name if dtype else None,
        zone_id     = device.zone_id,
        status      = "ONLINE" if device.is_active else "OFFLINE",
        is_active   = device.is_active,
    )

# 9. DELETE - Gỡ thiết bị khỏi khu vực
@app.delete("/api/zones/{zone_id}/devices/{device_id}", response_model=schemas.DeviceResponse)
def remove_device_from_zone(zone_id: int, device_id: int, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter(
        models.Device.id == device_id, models.Device.zone_id == zone_id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị trong khu vực này")
    device.zone_id = None
    db.commit()
    db.refresh(device)
    dtype = db.query(models.DeviceType).filter(models.DeviceType.id == device.type_id).first()
    return schemas.DeviceResponse(
        id          = device.id,
        device_name = device.name,
        device_type = dtype.category if dtype else "SENSOR",
        pin         = device.pin_connector,
        func        = dtype.name if dtype else None,
        zone_id     = device.zone_id,
        status      = "ONLINE" if device.is_active else "OFFLINE",
        is_active   = device.is_active,
    )

# ==========================================
# API QUẢN LÝ CẤU HÌNH CÂY TRỒNG (CROP SETTINGS)
# ==========================================

# 1. CREATE - Thêm cấu hình cây trồng mới
@app.post("/api/crop-settings/", response_model=schemas.CropSettingResponse)
def create_crop_setting(crop: schemas.CropSettingCreate, db: Session = Depends(get_db)):
    db_crop = models.CropSetting(**crop.model_dump())
    db.add(db_crop)
    db.commit()
    db.refresh(db_crop)
    return db_crop

# 2. READ - Lấy toàn bộ cấu hình cây trồng
@app.get("/api/crop-settings/", response_model=list[schemas.CropSettingResponse])
def get_all_crop_settings(db: Session = Depends(get_db)):
    return db.query(models.CropSetting).all()

# 3. READ - Lấy chi tiết 1 cấu hình
@app.get("/api/crop-settings/{crop_id}", response_model=schemas.CropSettingResponse)
def get_crop_setting_by_id(crop_id: int, db: Session = Depends(get_db)):
    crop = db.query(models.CropSetting).filter(models.CropSetting.id == crop_id).first()
    if crop is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình cây trồng")
    return crop

# 4. UPDATE - Cập nhật cấu hình cây trồng
@app.put("/api/crop-settings/{crop_id}", response_model=schemas.CropSettingResponse)
def update_crop_setting(crop_id: int, crop_data: schemas.CropSettingCreate, db: Session = Depends(get_db)):
    crop = db.query(models.CropSetting).filter(models.CropSetting.id == crop_id).first()
    if crop is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình cây trồng")
    for field, value in crop_data.model_dump().items():
        setattr(crop, field, value)
    db.commit()
    db.refresh(crop)
    return crop

# 5. DELETE - Xoá cấu hình cây trồng
@app.delete("/api/crop-settings/{crop_id}", status_code=204)
def delete_crop_setting(crop_id: int, db: Session = Depends(get_db)):
    crop = db.query(models.CropSetting).filter(models.CropSetting.id == crop_id).first()
    if crop is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình cây trồng")
    db.delete(crop)
    db.commit()

# ==========================================
# API QUẢN LÝ THIẾT BỊ (DEVICES)
# ==========================================

# 1. READ - Lấy toàn bộ thiết bị
@app.get("/api/devices/", response_model=list[schemas.DeviceResponse])
def get_all_devices(db: Session = Depends(get_db)):
    devices = db.query(models.Device).all()
    result = []
    for d in devices:
        dtype = db.query(models.DeviceType).filter(models.DeviceType.id == d.type_id).first()
        result.append(schemas.DeviceResponse(
            id          = d.id,
            device_name = d.name,
            device_type = dtype.category if dtype else "SENSOR",
            pin         = d.pin_connector,
            func        = dtype.name if dtype else None,
            zone_id     = d.zone_id,
            status      = "ONLINE" if d.is_active else "OFFLINE",
            is_active   = d.is_active,
        ))
    return result

# 2. PATCH - Bật/tắt thiết bị
@app.patch("/api/devices/{device_id}/toggle", response_model=schemas.DeviceResponse)
def toggle_device(device_id: int, body: schemas.DeviceToggle, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")
    device.is_active = body.is_active
    db.commit()
    db.refresh(device)
    dtype = db.query(models.DeviceType).filter(models.DeviceType.id == device.type_id).first()
    return schemas.DeviceResponse(
        id          = device.id,
        device_name = device.name,
        device_type = dtype.category if dtype else "SENSOR",
        pin         = device.pin_connector,
        func        = dtype.name if dtype else None,
        zone_id     = device.zone_id,
        status      = "ONLINE" if device.is_active else "OFFLINE",
        is_active   = device.is_active,
    )

# ==========================================
# API ĐĂNG KÝ VÀ ĐĂNG NHẬP
# ==========================================

@app.post("/api/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Kiểm tra xem username đã tồn tại chưa
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại!")
    
    # 2. Băm mật khẩu và lưu vào DB
    hashed_pw = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username, 
        hashed_password=hashed_pw, 
        name=user.name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/login", response_model=schemas.Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Tìm user trong Database
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    # 2. Kiểm tra tài khoản và mật khẩu
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu!")
    
    # 3. Đăng nhập thành công -> Tạo JWT Token
    access_token = auth.create_access_token(data={
        "sub": user.username, 
        "role": user.role,
        "name": user.name   # <--- Bổ sung dòng này để gửi tên thật cho React
    })
    
    return {"access_token": access_token, "token_type": "bearer"}
# ==========================================
# API QUẢN LÝ TÀI KHOẢN (USERS)
# ==========================================

# READ - Lấy danh sách toàn bộ tài khoản trong hệ thống
@app.get("/api/users/", response_model=list[schemas.UserResponse])
def get_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Lấy toàn bộ user từ Database, có hỗ trợ phân trang (skip, limit)
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# READ - Lấy thông tin chi tiết của 1 tài khoản theo ID
@app.get("/api/users/{user_id}", response_model=schemas.UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản này")
    return user

# --- QUẢN LÝ KẾT NỐI WEBSOCKET ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# In-memory store: zone_id → last telemetry payload
_last_telemetry: dict = {}

# --- 1. API ĐỂ IOT GATEWAY GỬI DỮ LIỆU LÊN (POST) ---
@app.post("/api/telemetry")
async def receive_telemetry(data: dict, db: Session = Depends(get_db)):
    zone_id = data.get("zone_id")
    if zone_id is None:
        raise HTTPException(status_code=400, detail="Thiếu trường zone_id")

    # Kiểm tra khu vực tồn tại
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail=f"Khu vực #{zone_id} không tồn tại")

    # Kiểm tra khu vực có ít nhất 1 SENSOR active
    sensors_in_zone = [
        d for d in zone.devices
        if d.is_active
        and db.query(models.DeviceType)
              .filter(models.DeviceType.id == d.type_id,
                      models.DeviceType.category == "SENSOR")
              .first() is not None
    ]
    if not sensors_in_zone:
        raise HTTPException(
            status_code=400,
            detail=f"Khu vực #{zone_id} không có cảm biến (SENSOR) nào đang hoạt động. "
                   "Hãy bật cảm biến và gán vào khu vực trước khi gửi dữ liệu."
        )

    # Đảm bảo measured_at có mặt trong payload
    from datetime import datetime, timezone
    if "measured_at" not in data:
        data["measured_at"] = datetime.now(timezone.utc).isoformat()

    # Lưu reading cuối cùng vào bộ nhớ
    _last_telemetry[zone_id] = data

    # Broadcast cho tất cả frontend đang mở
    await manager.broadcast(data)
    return {"status": "success", "message": f"Đã nhận và phát sóng cho zone {zone_id}"}


# --- 2. API LẤY TÓM TẮT TELEMETRY (trung bình toàn bộ zone) ---
@app.get("/api/telemetry/summary")
def get_telemetry_summary():
    """
    Trả về:
      - per_zone: list mỗi zone với reading cuối cùng
      - averages: trung bình temperature, humidity, light across all active zones
    """
    if not _last_telemetry:
        return {"per_zone": [], "averages": {}, "active_zones": 0}

    per_zone = list(_last_telemetry.values())
    temps  = [z["temperature"] for z in per_zone if "temperature" in z]
    humids = [z["humidity"]    for z in per_zone if "humidity"    in z]
    lights = [z["light"]       for z in per_zone if "light"       in z]

    averages = {}
    if temps:  averages["temperature"] = round(sum(temps)  / len(temps),  1)
    if humids: averages["humidity"]    = round(sum(humids) / len(humids), 1)
    if lights: averages["light"]       = round(sum(lights) / len(lights), 0)

    return {
        "per_zone":    per_zone,
        "averages":    averages,
        "active_zones": len(per_zone),
    }


# --- 3. WEBSOCKET ĐỂ FRONTEND LẮNG NGHE DỮ LIỆU (WS) ---
@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Giữ kết nối luôn mở
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)