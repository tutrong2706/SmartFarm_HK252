from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Optional
from datetime import datetime, timezone
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

    # ── Ghi log khi gán / đổi cây trồng ──────────────────────────
    if "crop_setting_id" in update_data:
        new_crop_id = update_data["crop_setting_id"]
        if new_crop_id != db_zone.crop_setting_id:
            new_crop_name = None
            if new_crop_id:
                nc = db.query(models.CropSetting).filter(models.CropSetting.id == new_crop_id).first()
                new_crop_name = nc.crop_name if nc else f"#{new_crop_id}"
            old_crop_name = None
            if db_zone.crop_setting_id:
                oc = db.query(models.CropSetting).filter(models.CropSetting.id == db_zone.crop_setting_id).first()
                old_crop_name = oc.crop_name if oc else f"#{db_zone.crop_setting_id}"
            if new_crop_name:
                msg = (f"Khu vực '{db_zone.name}' đã được gán cây trồng '{new_crop_name}'"
                       + (f" (trước đó: '{old_crop_name}')" if old_crop_name else "") + ".")
            else:
                msg = f"Khu vực '{db_zone.name}' đã xoá cây trồng (trước đó: '{old_crop_name}')."
            log_event(db,
                log_type = "system",
                severity = "info",
                title    = f"Thay đổi cây trồng — {db_zone.name}",
                message  = msg,
                zone_id  = zone_id,
                actor    = "Admin",
            )

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

    # ── Ghi log gán thiết bị ──────────────────────────────────────
    log_event(db,
        log_type  = "system",
        severity  = "info",
        title     = f"Gán thiết bị vào khu vực — {zone.name}",
        message   = f"Thiết bị '{device.name}' đã được gán vào {zone.name}.",
        zone_id   = zone_id,
        device_id = device.id,
        actor     = "Admin",
    )

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
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    dev_name  = device.name
    zone_name = zone.name if zone else f"#{zone_id}"
    device.zone_id = None
    db.commit()
    db.refresh(device)
    dtype = db.query(models.DeviceType).filter(models.DeviceType.id == device.type_id).first()

    # ── Ghi log gỡ thiết bị ───────────────────────────────────────
    log_event(db,
        log_type  = "system",
        severity  = "info",
        title     = f"Gỡ thiết bị khỏi khu vực — {zone_name}",
        message   = f"Thiết bị '{dev_name}' đã bị gỡ khỏi {zone_name}.",
        zone_id   = zone_id,
        device_id = device.id,
        actor     = "Admin",
    )

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

    # ── Ghi log các thay đổi ngưỡng ──────────────────────────────
    changes = []
    new_vals = crop_data.model_dump()
    field_labels = {
        "temp_min":  "Nhiệt độ tối thiểu",
        "temp_max":  "Nhiệt độ tối đa",
        "humid_min": "Độ ẩm tối thiểu",
        "humid_max": "Độ ẩm tối đa",
    }
    for field, label in field_labels.items():
        old_val = getattr(crop, field)
        new_val = new_vals.get(field)
        if new_val is not None and old_val != new_val:
            unit = "°C" if "temp" in field else "%"
            changes.append(f"{label}: {old_val}{unit} → {new_val}{unit}")

    if changes:
        log_event(db,
            log_type = "system",
            severity = "info",
            title    = f"Thay đổi cấu hình cây trồng — {crop.crop_name}",
            message  = f"Admin vừa cập nhật ngưỡng '{crop.crop_name}': " + "; ".join(changes) + ".",
            actor    = "Admin",
        )

    for field, value in new_vals.items():
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
    prev_state = device.is_active
    device.is_active = body.is_active
    db.commit()
    db.refresh(device)
    dtype = db.query(models.DeviceType).filter(models.DeviceType.id == device.type_id).first()

    # ── Ghi log thao tác thủ công ──────────────────────────────────
    if prev_state != body.is_active:
        action_word = "bật" if body.is_active else "tắt"
        zone_name   = None
        if device.zone_id:
            z = db.query(models.Zone).filter(models.Zone.id == device.zone_id).first()
            zone_name = z.name if z else None
        log_event(db,
            log_type    = "system",
            severity    = "info",
            title       = f"Thao tác thủ công — {action_word.capitalize()} thiết bị",
            message     = (f"Người dùng vừa {action_word} thiết bị '{device.name}'"
                           + (f" tại {zone_name}" if zone_name else "") + " bằng tay."),
            zone_id     = device.zone_id,
            device_id   = device.id,
            action_type = "navigate_device",
            actor       = "Manual",
        )

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

# Cooldown cho threshold alert: key=(zone_id, metric, kind) → last_logged datetime
# Tránh spam: cùng 1 cảnh báo chỉ ghi lại tối đa 1 lần / ALERT_COOLDOWN_SEC giây
_alert_cooldown: dict = {}
ALERT_COOLDOWN_SEC = 300   # 5 phút

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

    # ── Tự động ghi log khi vượt ngưỡng crop setting ──────────────
    if zone.crop_setting_id:
        crop = db.query(models.CropSetting).filter(
            models.CropSetting.id == zone.crop_setting_id
        ).first()
        if crop:
            temp  = data.get("temperature")
            humid = data.get("humidity")
            now   = datetime.now(timezone.utc)

            def _can_log(metric: str, kind: str) -> bool:
                """True nếu chưa log cảnh báo này trong ALERT_COOLDOWN_SEC giây."""
                key  = (zone_id, metric, kind)
                last = _alert_cooldown.get(key)
                if last and (now - last).total_seconds() < ALERT_COOLDOWN_SEC:
                    return False
                _alert_cooldown[key] = now
                return True

            if temp is not None:
                if temp > crop.temp_max:
                    if _can_log("temperature", "critical"):
                        log_event(db,
                            log_type    = "critical",
                            severity    = "critical",
                            title       = f"Nhiệt độ vượt ngưỡng — {zone.name}",
                            message     = (f"⚠️ Nhiệt độ {zone.name} đã lên {temp}°C "
                                           f"(Ngưỡng tối đa: {crop.temp_max}°C). Nguy cơ héo lá!"),
                            zone_id     = zone_id,
                            metric_key  = "temperature",
                            metric_value= float(temp),
                            threshold   = float(crop.temp_max),
                            action_label= "Bật quạt giải nhiệt ngay",
                            action_type = "toggle_device",
                        )
                elif temp > crop.temp_max * 0.93:
                    if _can_log("temperature", "warning"):
                        log_event(db,
                            log_type    = "warning",
                            severity    = "warning",
                            title       = f"Nhiệt độ tiệm cận ngưỡng — {zone.name}",
                            message     = (f"Nhiệt độ {zone.name} đang ở {temp}°C, "
                                           f"gần ngưỡng tối đa {crop.temp_max}°C. Theo dõi chặt!"),
                            zone_id     = zone_id,
                            metric_key  = "temperature",
                            metric_value= float(temp),
                            threshold   = float(crop.temp_max),
                        )
                else:
                    # Đã trở về bình thường — xoá cooldown để lần tới log lại ngay
                    _alert_cooldown.pop((zone_id, "temperature", "critical"), None)
                    _alert_cooldown.pop((zone_id, "temperature", "warning"),  None)

            if humid is not None:
                if humid < crop.humid_min:
                    if _can_log("humidity", "critical"):
                        log_event(db,
                            log_type    = "critical",
                            severity    = "critical",
                            title       = f"Độ ẩm thấp nguy hiểm — {zone.name}",
                            message     = (f"⚠️ Độ ẩm {zone.name} chỉ còn {humid}% "
                                           f"(Ngưỡng tối thiểu: {crop.humid_min}%). Cần tưới ngay!"),
                            zone_id     = zone_id,
                            metric_key  = "humidity",
                            metric_value= float(humid),
                            threshold   = float(crop.humid_min),
                            action_label= "Bật bơm tưới ngay",
                            action_type = "toggle_device",
                        )
                elif humid < crop.humid_min * 1.05:
                    if _can_log("humidity", "warning"):
                        log_event(db,
                            log_type    = "warning",
                            severity    = "warning",
                            title       = f"Độ ẩm tiệm cận ngưỡng — {zone.name}",
                            message     = (f"Độ ẩm {zone.name} đang giảm, hiện ở {humid}% "
                                           f"(Ngưỡng tối thiểu: {crop.humid_min}%)."),
                            zone_id     = zone_id,
                            metric_key  = "humidity",
                            metric_value= float(humid),
                            threshold   = float(crop.humid_min),
                            action_label= "Bật bơm tưới",
                            action_type = "toggle_device",
                        )
                else:
                    _alert_cooldown.pop((zone_id, "humidity", "critical"), None)
                    _alert_cooldown.pop((zone_id, "humidity", "warning"),  None)

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


# ==========================================
# ALERT LOGS  —  /api/logs/
# ==========================================

def _build_log_response(log: models.AlertLog, db: Session) -> dict:
    """Chuyển đổi ORM object → dict response, resolve zone_name & device_name."""
    zone_name   = None
    device_name = None
    if log.zone_id:
        z = db.query(models.Zone).filter(models.Zone.id == log.zone_id).first()
        zone_name = z.name if z else None
    if log.device_id:
        d = db.query(models.Device).filter(models.Device.id == log.device_id).first()
        device_name = d.name if d else None
    return {
        "id":               log.id,
        "log_type":         log.log_type,
        "severity":         log.severity,
        "title":            log.title,
        "message":          log.message,
        "zone_id":          log.zone_id,
        "device_id":        log.device_id,
        "action_label":     log.action_label,
        "action_type":      log.action_type,
        "action_target_id": log.action_target_id,
        "actor":            log.actor,
        "is_read":          log.is_read,
        "metric_key":       log.metric_key,
        "metric_value":     log.metric_value,
        "threshold":        log.threshold,
        "created_at":       log.created_at,
        "zone_name":        zone_name,
        "device_name":      device_name,
    }


def log_event(
    db: Session,
    *,
    log_type: str,
    severity: str,
    title: str,
    message: str,
    zone_id:          int   = None,
    device_id:        int   = None,
    action_label:     str   = None,
    action_type:      str   = None,
    action_target_id: int   = None,
    actor:            str   = "SYSTEM",
    metric_key:       str   = None,
    metric_value:     float = None,
    threshold:        float = None,
) -> models.AlertLog:
    """
    Helper nội bộ: tạo một AlertLog entry, commit, rồi broadcast WS event
    với type='new_log' để Dashboard cập nhật tức thì.
    """
    entry = models.AlertLog(
        log_type         = log_type,
        severity         = severity,
        title            = title,
        message          = message,
        zone_id          = zone_id,
        device_id        = device_id,
        action_label     = action_label,
        action_type      = action_type,
        action_target_id = action_target_id,
        actor            = actor,
        metric_key       = metric_key,
        metric_value     = metric_value,
        threshold        = threshold,
        created_at       = datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Resolve names for the WS push
    zone_name   = None
    device_name = None
    if zone_id:
        z = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
        zone_name = z.name if z else None
    if device_id:
        dv = db.query(models.Device).filter(models.Device.id == device_id).first()
        device_name = dv.name if dv else None

    import asyncio
    ws_payload = {
        "_type":          "new_log",
        "id":             entry.id,
        "log_type":       log_type,
        "severity":       severity,
        "title":          title,
        "message":        message,
        "zone_id":        zone_id,
        "zone_name":      zone_name,
        "device_id":      device_id,
        "device_name":    device_name,
        "action_label":   action_label,
        "action_type":    action_type,
        "actor":          actor,
        "metric_key":     metric_key,
        "metric_value":   metric_value,
        "threshold":      threshold,
        "is_read":        False,
        "created_at":     entry.created_at.isoformat(),
    }
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(manager.broadcast(ws_payload))
    except Exception:
        pass   # broadcast là best-effort, không làm hỏng response

    return entry


# ── 1. GET  /api/logs/  — lấy danh sách log (có filter) ──────────────────────
@app.get("/api/logs/", response_model=list[schemas.AlertLogResponse])
def get_logs(
    log_type:  Optional[str] = Query(None, description="critical|warning|automation|system"),
    severity:  Optional[str] = Query(None),
    zone_id:   Optional[int] = Query(None),
    is_read:   Optional[bool] = Query(None),
    limit:     int = Query(50, ge=1, le=200),
    offset:    int = Query(0,  ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(models.AlertLog)
    if log_type: q = q.filter(models.AlertLog.log_type == log_type)
    if severity: q = q.filter(models.AlertLog.severity == severity)
    if zone_id:  q = q.filter(models.AlertLog.zone_id == zone_id)
    if is_read is not None:
        q = q.filter(models.AlertLog.is_read == is_read)
    logs = q.order_by(models.AlertLog.created_at.desc()).offset(offset).limit(limit).all()
    return [_build_log_response(l, db) for l in logs]


# ── 2. GET  /api/logs/unread-count  — badge số chưa đọc ─────────────────────
@app.get("/api/logs/unread-count")
def get_unread_count(db: Session = Depends(get_db)):
    count = db.query(models.AlertLog).filter(models.AlertLog.is_read == False).count()
    return {"unread": count}


# ── 3. POST /api/logs/  — tạo log thủ công ───────────────────────────────────
@app.post("/api/logs/", response_model=schemas.AlertLogResponse, status_code=201)
def create_log(payload: schemas.AlertLogCreate, db: Session = Depends(get_db)):
    entry = log_event(
        db,
        log_type         = payload.log_type,
        severity         = payload.severity,
        title            = payload.title,
        message          = payload.message,
        zone_id          = payload.zone_id,
        device_id        = payload.device_id,
        action_label     = payload.action_label,
        action_type      = payload.action_type,
        action_target_id = payload.action_target_id,
        actor            = payload.actor or "MANUAL",
        metric_key       = payload.metric_key,
        metric_value     = payload.metric_value,
        threshold        = payload.threshold,
    )
    return _build_log_response(entry, db)


# ── 4. PATCH /api/logs/{id}/read  — đánh dấu đã đọc ─────────────────────────
@app.patch("/api/logs/{log_id}/read", response_model=schemas.AlertLogResponse)
def mark_log_read(log_id: int, db: Session = Depends(get_db)):
    entry = db.query(models.AlertLog).filter(models.AlertLog.id == log_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Log không tồn tại")
    entry.is_read = True
    db.commit()
    db.refresh(entry)
    return _build_log_response(entry, db)


# ── 5. POST /api/logs/read-all  — đánh dấu tất cả đã đọc ────────────────────
@app.post("/api/logs/read-all")
def mark_all_read(db: Session = Depends(get_db)):
    updated = db.query(models.AlertLog).filter(models.AlertLog.is_read == False).all()
    for e in updated:
        e.is_read = True
    db.commit()
    return {"marked_read": len(updated)}


# ── 6. DELETE /api/logs/{id}  — xoá 1 log ────────────────────────────────────
@app.delete("/api/logs/{log_id}", status_code=204)
def delete_log(log_id: int, db: Session = Depends(get_db)):
    entry = db.query(models.AlertLog).filter(models.AlertLog.id == log_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Log không tồn tại")
    db.delete(entry)
    db.commit()
