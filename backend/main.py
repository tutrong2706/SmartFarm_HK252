import os
from dotenv import load_dotenv  # <-- Thêm dòng này

# Nạp các biến môi trường từ file .env
load_dotenv() # <-- Gọi hàm này ngay lập tức
import csv
import io
import uuid
from pydantic import BaseModel
import json
import base64
import requests
import threading
from pathlib import Path
from functools import wraps
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Optional, Literal
from datetime import datetime, timezone, timedelta
import auth
import models, schemas
from database import engine, get_db
from chatbot import chat_with_ai, clear_history, get_history
from sql_agent import query_database
from rag_system import retrieve_documents, format_retrieved_docs
from apscheduler.schedulers.background import BackgroundScheduler

# ── Phase 4: Bổ sung ──────────────────────────────────────────────
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, PageBreak, Image as RLImage, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# Register Unicode font for Vietnamese support
def _register_unicode_font():
    """Register a Unicode font for Vietnamese character support."""
    import os
    # Try common Unicode fonts in order of preference
    # Segoe UI has the best Unicode support for Vietnamese on Windows
    font_paths = [
        # Segoe UI (best Unicode support for Vietnamese on Windows)
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/segoeui.ttf",  # Fallback duplicate
        # DejaVu Sans (commonly available on Linux/Windows)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/times.ttf",
        "/System/Library/Fonts/SFNS.ttf",  # macOS
    ]
    
    # Also try bold variants
    bold_font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",  # Segoe UI Bold
        "C:/Windows/Fonts/segoeuib.ttf",  # Fallback duplicate
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/timesbd.ttf",
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Unicode', font_path))
                # Try to register bold variant
                for bold_path in bold_font_paths:
                    if os.path.exists(bold_path):
                        try:
                            pdfmetrics.registerFont(TTFont('Unicode-Bold', bold_path))
                        except Exception:
                            pass
                        break
                return 'Unicode'
            except Exception:
                continue
    
    # If no font found, return default (will have issues with Vietnamese)
    return 'Helvetica'

# Register font at module load
UNICODE_FONT = _register_unicode_font() if HAS_REPORTLAB else 'Helvetica'
UNICODE_FONT_BOLD = 'Unicode-Bold' if UNICODE_FONT == 'Unicode' else 'Helvetica-Bold'

try:
    import redis
    REDIS_CLIENT = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    REDIS_AVAILABLE = True
except Exception:
    REDIS_CLIENT = None
    REDIS_AVAILABLE = False

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

_report_scheduler = None

# Lệnh này yêu cầu SQLAlchemy tạo toàn bộ các bảng trong CSDL
models.Base.metadata.create_all(bind=engine)

# Thư mục lưu file báo cáo
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

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


def get_current_user(token: str = Depends(auth.oauth2_scheme)):
    """Lấy thông tin user từ JWT token."""
    credentials_exception = HTTPException(
        status_code=401, detail="Không thể xác thực credentials"
    )
    try:
        payload = auth.decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return payload
    except Exception:
        raise credentials_exception


@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Farm API! Database đã được kết nối và tạo bảng thành công."}


# ==========================================
# API CHO BẢNG KHU VỰC (ZONES)
# ==========================================
@app.post("/api/zones/", response_model=schemas.ZoneResponse)
def create_zone(zone: schemas.ZoneCreate, db: Session = Depends(get_db)):
    db_zone = models.Zone(**zone.model_dump())
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone


@app.get("/api/zones/", response_model=list[schemas.ZoneResponse])
def get_all_zones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    zones = db.query(models.Zone).offset(skip).limit(limit).all()
    return zones


@app.get("/api/zones/{zone_id}", response_model=schemas.ZoneResponse)
def get_zone_by_id(zone_id: int, db: Session = Depends(get_db)):
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực này")
    return zone


@app.put("/api/zones/{zone_id}", response_model=schemas.ZoneResponse)
def update_zone(zone_id: int, zone_update: schemas.ZoneCreate, db: Session = Depends(get_db)):
    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực này")
    for key, value in zone_update.model_dump().items():
        setattr(db_zone, key, value)
    db.commit()
    db.refresh(db_zone)
    return db_zone


@app.delete("/api/zones/{zone_id}")
def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực này")
    db.delete(db_zone)
    db.commit()
    return {"message": "Đã xóa khu vực thành công"}


@app.patch("/api/zones/{zone_id}", response_model=schemas.ZoneResponse)
def patch_zone(zone_id: int, zone_patch: schemas.ZonePatch, db: Session = Depends(get_db)):
    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if db_zone is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực này")
    update_data = zone_patch.model_dump(exclude_unset=True)

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
                      log_type="system",
                      severity="info",
                      title=f"Thay đổi cây trồng — {db_zone.name}",
                      message=msg,
                      zone_id=zone_id,
                      actor="Admin",
                      )

    for key, value in update_data.items():
        setattr(db_zone, key, value)
    db.commit()
    db.refresh(db_zone)
    return db_zone


@app.get("/api/zones/{zone_id}/devices", response_model=list[schemas.DeviceResponse])
def get_devices_by_zone(zone_id: int, db: Session = Depends(get_db)):
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực này")
    result = []
    for d in zone.devices:
        dtype = db.query(models.DeviceType).filter(models.DeviceType.id == d.type_id).first()
        result.append(schemas.DeviceResponse(
            id=d.id,
            device_name=d.name,
            device_type=dtype.category if dtype else "SENSOR",
            pin=d.pin_connector,
            func=dtype.name if dtype else None,
            zone_id=d.zone_id,
            status="ONLINE" if d.is_active else "OFFLINE",
            is_active=d.is_active,
        ))
    return result


@app.post("/api/zones/{zone_id}/devices/{device_id}", response_model=schemas.DeviceResponse)
def assign_device_to_zone(zone_id: int, device_id: int, db: Session = Depends(get_db)):
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Không tìm thấy khu vực")
    if not device:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")
    device.zone_id = zone_id
    db.commit()
    db.refresh(device)
    dtype = db.query(models.DeviceType).filter(models.DeviceType.id == device.type_id).first()

    log_event(db,
              log_type="system",
              severity="info",
              title=f"Gán thiết bị vào khu vực — {zone.name}",
              message=f"Thiết bị '{device.name}' đã được gán vào {zone.name}.",
              zone_id=zone_id,
              device_id=device.id,
              actor="Admin",
              )

    return schemas.DeviceResponse(
        id=device.id,
        device_name=device.name,
        device_type=dtype.category if dtype else "SENSOR",
        pin=device.pin_connector,
        func=dtype.name if dtype else None,
        zone_id=device.zone_id,
        status="ONLINE" if device.is_active else "OFFLINE",
        is_active=device.is_active,
    )


@app.delete("/api/zones/{zone_id}/devices/{device_id}", response_model=schemas.DeviceResponse)
def remove_device_from_zone(zone_id: int, device_id: int, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter(
        models.Device.id == device_id, models.Device.zone_id == zone_id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị trong khu vực này")
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    dev_name = device.name
    zone_name = zone.name if zone else f"#{zone_id}"
    device.zone_id = None
    db.commit()
    db.refresh(device)
    dtype = db.query(models.DeviceType).filter(models.DeviceType.id == device.type_id).first()

    log_event(db,
              log_type="system",
              severity="info",
              title=f"Gỡ thiết bị khỏi khu vực — {zone_name}",
              message=f"Thiết bị '{dev_name}' đã bị gỡ khỏi {zone_name}.",
              zone_id=zone_id,
              device_id=device.id,
              actor="Admin",
              )

    return schemas.DeviceResponse(
        id=device.id,
        device_name=device.name,
        device_type=dtype.category if dtype else "SENSOR",
        pin=device.pin_connector,
        func=dtype.name if dtype else None,
        zone_id=device.zone_id,
        status="ONLINE" if device.is_active else "OFFLINE",
        is_active=device.is_active,
    )


# ==========================================
# API QUẢN LÝ CẤU HÌNH CÂY TRỒNG (CROP SETTINGS)
# ==========================================
@app.post("/api/crop-settings/", response_model=schemas.CropSettingResponse)
def create_crop_setting(crop: schemas.CropSettingCreate, db: Session = Depends(get_db)):
    db_crop = models.CropSetting(**crop.model_dump())
    db.add(db_crop)
    db.commit()
    db.refresh(db_crop)
    return db_crop


@app.get("/api/crop-settings/", response_model=list[schemas.CropSettingResponse])
def get_all_crop_settings(db: Session = Depends(get_db)):
    return db.query(models.CropSetting).all()


@app.get("/api/crop-settings/{crop_id}", response_model=schemas.CropSettingResponse)
def get_crop_setting_by_id(crop_id: int, db: Session = Depends(get_db)):
    crop = db.query(models.CropSetting).filter(models.CropSetting.id == crop_id).first()
    if crop is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình cây trồng")
    return crop


@app.put("/api/crop-settings/{crop_id}", response_model=schemas.CropSettingResponse)
def update_crop_setting(crop_id: int, crop_data: schemas.CropSettingCreate, db: Session = Depends(get_db)):
    crop = db.query(models.CropSetting).filter(models.CropSetting.id == crop_id).first()
    if crop is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình cây trồng")

    old_auto_mode = crop.auto_mode
    new_auto_mode = crop_data.auto_mode

    changes = []
    new_vals = crop_data.model_dump()
    field_labels = {
        "temp_min": "Nhiệt độ tối thiểu",
        "temp_max": "Nhiệt độ tối đa",
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
                  log_type="system",
                  severity="info",
                  title=f"Thay đổi cấu hình cây trồng — {crop.crop_name}",
                  message=f"Admin vừa cập nhật ngưỡng '{crop.crop_name}': " + "; ".join(changes) + ".",
                  actor="Admin",
                  )

    if not old_auto_mode and new_auto_mode:
        try:
            zones = db.query(models.Zone).filter(models.Zone.crop_setting_id == crop_id).all()
            for zone in zones:
                if zone.id in _last_telemetry:
                    telemetry = _last_telemetry[zone.id]
                    temp = telemetry.get("temperature")
                    humid = telemetry.get("humidity")
                    light = telemetry.get("light")

                    def _find_actuator(type_name: str):
                        for dev in zone.devices:
                            dt = db.query(models.DeviceType).filter(models.DeviceType.id == dev.type_id).first()
                            if dt and dt.category == "ACTUATOR" and type_name.lower() in dt.name.lower():
                                return dev
                        return None

                    def _auto_set(device, target_active: bool, action_desc: str, device_type: str = None, metric: str = None, value: float = None, threshold: float = None):
                        if device is None:
                            if device_type and metric and value is not None and threshold is not None:
                                _log_missing_device(db, zone.id, device_type, metric, value, threshold)
                            return
                        if device.is_active == target_active:
                            return
                        device.is_active = target_active
                        db.commit()
                        db.refresh(device)
                        log_event(db,
                                  log_type="automation",
                                  severity="success",
                                  title=f"{'Bật' if target_active else 'Tắt'} tự động — {device.name}",
                                  message=(f"🔄 Hệ thống tự động {action_desc} tại {zone.name} "
                                         f"({device.name})."),
                                  zone_id=zone.id,
                                  device_id=device.id,
                                  actor="SYSTEM",
                                  )

                if temp is not None:
                    if temp > crop.temp_max:
                        if _can_log(db, zone.id, "temperature", "critical"):
                            log_event(db,
                                      log_type="critical",
                                      severity="critical",
                                      title=f"Nhiệt độ vượt ngưỡng — {zone.name}",
                                      message=(f"⚠️ Nhiệt độ {zone.name} đã lên {temp}°C "
                                             f"(Ngưỡng tối đa: {crop.temp_max}°C). Nguy cơ héo lá!"),
                                      zone_id=zone.id,
                                      metric_key="temperature",
                                      metric_value=float(temp),
                                      threshold=float(crop.temp_max),
                                      action_label="Bật quạt giải nhiệt ngay",
                                      action_type="toggle_device",
                                      )
                        if crop.auto_mode:
                            fan = _find_actuator("quạt")
                            _auto_set(fan, True, "bật quạt thông gió để hạ nhiệt độ", "quạt", "nhiệt độ", temp, crop.temp_max)
                    elif temp > crop.temp_max * 0.93:
                        if _can_log(db, zone.id, "temperature", "warning"):
                            log_event(db,
                                      log_type="warning",
                                      severity="warning",
                                      title=f"Nhiệt độ tiệm cận ngưỡng — {zone.name}",
                                      message=(f"Nhiệt độ {zone.name} đang ở {temp}°C, "
                                             f"gần ngưỡng tối đa {crop.temp_max}°C. Theo dõi chặt!"),
                                      zone_id=zone.id,
                                      metric_key="temperature",
                                      metric_value=float(temp),
                                      threshold=float(crop.temp_max),
                                      )
                    elif temp < crop.temp_min:
                        if crop.auto_mode:
                            fan = _find_actuator("quạt")
                            _auto_set(fan, False, "tắt quạt thông gió do nhiệt độ đã hạ", "quạt", "nhiệt độ", temp, crop.temp_min)
                    else:
                        _alert_cooldown.pop((zone.id, "temperature", "critical"), None)
                        _alert_cooldown.pop((zone.id, "temperature", "warning"), None)
                        if crop.auto_mode:
                            fan = _find_actuator("quạt")
                            _auto_set(fan, False, "tắt quạt thông gió — nhiệt độ đã ổn định", "quạt", "nhiệt độ", temp, crop.temp_min)

                if humid is not None:
                    if humid < crop.humid_min:
                        if _can_log(db, zone.id, "humidity", "critical"):
                            log_event(db,
                                      log_type="critical",
                                      severity="critical",
                                      title=f"Độ ẩm thấp nguy hiểm — {zone.name}",
                                      message=(f"⚠️ Độ ẩm {zone.name} chỉ còn {humid}% "
                                             f"(Ngưỡng tối thiểu: {crop.humid_min}%). Cần tưới ngay!"),
                                      zone_id=zone.id,
                                      metric_key="humidity",
                                      metric_value=float(humid),
                                      threshold=float(crop.humid_min),
                                      action_label="Bật bơm tưới ngay",
                                      action_type="toggle_device",
                                      )
                        if crop.auto_mode:
                            pump = _find_actuator("bơm")
                            _auto_set(pump, True, "bật máy bơm tưới do độ ẩm thấp", "bơm", "độ ẩm", humid, crop.humid_min)
                    elif humid < crop.humid_min * 1.05:
                        if _can_log(db, zone.id, "humidity", "warning"):
                            log_event(db,
                                      log_type="warning",
                                      severity="warning",
                                      title=f"Độ ẩm tiệm cận ngưỡng — {zone.name}",
                                      message=(f"Độ ẩm {zone.name} đang giảm, hiện ở {humid}% "
                                             f"(Ngưỡng tối thiểu: {crop.humid_min}%)."),
                                      zone_id=zone.id,
                                      metric_key="humidity",
                                      metric_value=float(humid),
                                      threshold=float(crop.humid_min),
                                      )
                    elif humid > crop.humid_max:
                        if _can_log(db, zone.id, "humidity", "humid_high"):
                            log_event(db,
                                      log_type="warning",
                                      severity="warning",
                                      title=f"Độ ẩm vượt ngưỡng — {zone.name}",
                                      message=(f"💧 Độ ẩm {zone.name} đạt {humid}% "
                                             f"(Ngưỡng tối đa: {crop.humid_max}%). Nguy cơ úng rễ!"),
                                      zone_id=zone.id,
                                      metric_key="humidity",
                                      metric_value=float(humid),
                                      threshold=float(crop.humid_max),
                                      )
                        if crop.auto_mode:
                            pump = _find_actuator("bơm")
                            _auto_set(pump, False, "tắt máy bơm — độ ẩm đã đạt ngưỡng", "bơm", "độ ẩm", humid, crop.humid_max)
                            relay = _find_actuator("relay")
                            _auto_set(relay, True, "bật van thoát nước do độ ẩm quá cao", "relay", "độ ẩm", humid, crop.humid_max)
                    else:
                        _alert_cooldown.pop((zone.id, "humidity", "critical"), None)
                        _alert_cooldown.pop((zone.id, "humidity", "warning"), None)
                        if crop.auto_mode:
                            pump = _find_actuator("bơm")
                            _auto_set(pump, False, "tắt máy bơm — độ ẩm đã ổn định", "bơm", "độ ẩm", humid, crop.humid_max)
                            relay = _find_actuator("relay")
                            _auto_set(relay, False, "tắt van thoát nước", "relay", "độ ẩm", humid, crop.humid_max)

                if light is not None and crop.light_min is not None and crop.light_max is not None:
                    if light > crop.light_max:
                        if crop.auto_mode:
                            led = _find_actuator("led")
                            _auto_set(led, False, "tắt đèn LED do ánh sáng vượt ngưỡng", "LED", "ánh sáng", light, crop.light_max)
                            rly = _find_actuator("relay")
                            _auto_set(rly, True, "bật lưới che nắng do ánh sáng vượt ngưỡng", "relay", "ánh sáng", light, crop.light_max)
                    elif light < crop.light_min:
                        if crop.auto_mode:
                            led = _find_actuator("led")
                            _auto_set(led, True, "bật đèn LED bổ sung do ánh sáng yếu", "LED", "ánh sáng", light, crop.light_min)
                    else:
                        if crop.auto_mode:
                            rly = _find_actuator("relay")
                            _auto_set(rly, False, "tắt lưới che nắng — ánh sáng đã ổn định", "relay", "ánh sáng", light, crop.light_max)
            db.commit()
        except Exception as e:
            print(f"Error in auto_mode activation: {e}")
            db.rollback()

    for field, value in new_vals.items():
        setattr(crop, field, value)
    db.commit()
    db.refresh(crop)
    return crop


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
@app.get("/api/devices/", response_model=list[schemas.DeviceResponse])
def get_all_devices(db: Session = Depends(get_db)):
    devices = db.query(models.Device).all()
    result = []
    for d in devices:
        dtype = db.query(models.DeviceType).filter(models.DeviceType.id == d.type_id).first()
        result.append(schemas.DeviceResponse(
            id=d.id,
            device_name=d.name,
            device_type=dtype.category if dtype else "SENSOR",
            pin=d.pin_connector,
            func=dtype.name if dtype else None,
            zone_id=d.zone_id,
            status="ONLINE" if d.is_active else "OFFLINE",
            is_active=d.is_active,
        ))
    return result


AIO_USERNAME = os.getenv('ADAFRUIT_IO_USERNAME', 'YOUR_ADAFRUIT_USERNAME')
AIO_KEY = os.getenv('ADAFRUIT_IO_KEY', 'YOUR_ADAFRUIT_AIO_KEY')


def _publish_adafruit(feed_key: str, value: str):
    def run():
        # Kiểm tra ngay xem file .env có được nạp đúng không
        if not AIO_USERNAME or not AIO_KEY:
            print("❌ [LỖI] Chưa cấu hình ADAFRUIT_IO_USERNAME hoặc ADAFRUIT_IO_KEY trong file .env")
            return

        try:
            url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{feed_key}/data"
            headers = {"X-AIO-Key": AIO_KEY, "Content-Type": "application/json"}
            payload = {"datum": {"value": value}}
            
            resp = requests.post(url, json=payload, headers=headers, timeout=5)
            
            # Ép in ra kết quả thay vì dùng "pass"
            if resp.status_code == 200:
                print(f"✅ [ADAFRUIT] Đã gửi thành công giá trị {value} tới feed: {feed_key}")
            else:
                print(f"❌ [ADAFRUIT] Lỗi từ Cloud: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"❌ [ADAFRUIT] Lỗi kết nối mạng: {e}")

    threading.Thread(target=run, daemon=True).start()


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

    if prev_state != body.is_active:
        action_word = "bật" if body.is_active else "tắt"
        zone_name = None
        if device.zone_id:
            z = db.query(models.Zone).filter(models.Zone.id == device.zone_id).first()
            zone_name = z.name if z else None

        if device.pin_connector and str(device.pin_connector).startswith("AIO /"):
            feed_key = str(device.pin_connector).replace("AIO /", "").strip()
            str_val = "1" if body.is_active else "0"
            _publish_adafruit(feed_key, str_val)

        log_event(db,
                  log_type="system",
                  severity="info",
                  title=f"Thao tác thủ công — {action_word.capitalize()} thiết bị",
                  message=(f"Người dùng vừa {action_word} thiết bị '{device.name}'"
                         + (f" tại {zone_name}" if zone_name else "") + " bằng tay."),
                  zone_id=device.zone_id,
                  device_id=device.id,
                  action_type="navigate_device",
                  actor="Manual",
                  )

    return schemas.DeviceResponse(
        id=device.id,
        device_name=device.name,
        device_type=dtype.category if dtype else "SENSOR",
        pin=device.pin_connector,
        func=dtype.name if dtype else None,
        zone_id=device.zone_id,
        status="ONLINE" if device.is_active else "OFFLINE",
        is_active=device.is_active,
    )
class SyncFeedPayload(BaseModel):
    feed_key: str
    is_active: bool

@app.post("/api/devices/sync-feed")
async def sync_device_from_feed(payload: SyncFeedPayload, db: Session = Depends(get_db)):
    """API để Gateway báo cáo trạng thái thiết bị thực tế về hệ thống"""
    devices = db.query(models.Device).filter(models.Device.pin_connector.contains(payload.feed_key)).all()
    
    if not devices:
        return {"status": "ignored", "message": "Không tìm thấy thiết bị khớp với feed này"}

    for device in devices:
        if device.is_active != payload.is_active:
            device.is_active = payload.is_active
            db.commit()
            db.refresh(device)
            
            # Bắn WebSocket để Frontend tự động giật công tắc mà không cần F5
            ws_payload = {
                "_type": "device_sync",
                "device_id": device.id,
                "is_active": device.is_active
            }
            await manager.broadcast(ws_payload)

    return {"status": "success"}

# ==========================================
# API ĐĂNG KÝ VÀ ĐĂNG NHẬP
# ==========================================
@app.post("/api/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại!")
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
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu!")
    access_token = auth.create_access_token(data={
        "sub": user.username,
        "role": user.role,
        "name": user.name
    })
    return {"access_token": access_token, "token_type": "bearer"}


# ==========================================
# API QUẢN LÝ TÀI KHOẢN (USERS)
# ==========================================
@app.get("/api/users/", response_model=list[schemas.UserResponse])
def get_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


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

_last_telemetry: dict = {}
_alert_cooldown: dict = {}
ALERT_COOLDOWN_SEC = 300


# ── Cache helper ──────────────────────────────────────────────────
def _cache_set(key: str, value: str, ttl: int = 300):
    if REDIS_AVAILABLE:
        try:
            REDIS_CLIENT.setex(key, ttl, value)
        except Exception:
            pass


def _cache_get(key: str) -> Optional[str]:
    if REDIS_AVAILABLE:
        try:
            return REDIS_CLIENT.get(key)
        except Exception:
            pass
    return None


def _can_log(db: Session, zone_id: int, metric: str, kind: str) -> bool:
    key = f"alert:{zone_id}:{metric}:{kind}"
    cached = _cache_get(key)
    if cached:
        return False
    _cache_set(key, "1", ttl=ALERT_COOLDOWN_SEC)
    return True


def _log_missing_device(db: Session, zone_id: int, device_type: str, metric: str, value: float, threshold: float):
    """Ghi log khi thiếu thiết bị điều khiển"""
    log_event(db,
        log_type="warning",
        severity="warning",
        title=f"Thiếu thiết bị — {device_type}",
        message=f"Khu vực #{zone_id} cần gắn thiết bị {device_type} vì {metric} đang ở mức {value} (ngưỡng: {threshold})",
        zone_id=zone_id,
        action_label=f"Thêm thiết bị {device_type}",
        action_type="navigate_device",
    )


# --- 1. API ĐỂ IOT GATEWAY GỬI DỮ LIỆU LÊN (POST) ---
@app.post("/api/telemetry")
async def receive_telemetry(data: dict, db: Session = Depends(get_db)):
    zone_id = data.get("zone_id")
    if zone_id is None:
        raise HTTPException(status_code=400, detail="Thiếu trường zone_id")

    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail=f"Khu vực #{zone_id} không tồn tại")

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

    if "measured_at" not in data:
        data["measured_at"] = datetime.now(timezone.utc).isoformat()

    _last_telemetry[zone_id] = data

    # ── LƯU VÀO BẢNG telemetry_data ─────────────────────────────
    measured_at_parsed = datetime.fromisoformat(data["measured_at"])
    if measured_at_parsed.tzinfo is None:
        measured_at_parsed = measured_at_parsed.replace(tzinfo=timezone.utc)

    telemetry_row = models.TelemetryData(
        zone_id=zone_id,
        temperature=data.get("temperature"),
        humidity=data.get("humidity"),
        light=data.get("light"),
        measured_at=measured_at_parsed,
    )
    db.add(telemetry_row)
    db.commit()

    # ── Tự động ghi log khi vượt ngưỡng crop setting ──────────────
    if zone.crop_setting_id:
        crop = db.query(models.CropSetting).filter(
            models.CropSetting.id == zone.crop_setting_id
        ).first()
        if crop:
            temp = data.get("temperature")
            humid = data.get("humidity")
            light = data.get("light")
            now = datetime.now(timezone.utc)

            def _find_actuator(type_name: str):
                for dev in zone.devices:
                    dt = db.query(models.DeviceType).filter(models.DeviceType.id == dev.type_id).first()
                    if dt and dt.category == "ACTUATOR" and type_name.lower() in dt.name.lower():
                        return dev
                return None

            def _auto_set(device, target_active: bool, action_desc: str, device_type: str = None, metric: str = None, value: float = None, threshold: float = None):
                if device is None:
                    if device_type and metric and value is not None and threshold is not None:
                        _log_missing_device(db, zone_id, device_type, metric, value, threshold)
                    return
                if device.is_active == target_active:
                    return
                device.is_active = target_active
                db.commit()
                db.refresh(device)
                log_event(db,
                          log_type="automation",
                          severity="success",
                          title=f"{'Bật' if target_active else 'Tắt'} tự động — {device.name}",
                          message=(f"🔄 Hệ thống tự động {action_desc} tại {zone.name} "
                                 f"({device.name})."),
                          zone_id=zone_id,
                          device_id=device.id,
                          actor="SYSTEM",
                          )

            if temp is not None:
                if temp > crop.temp_max:
                    if _can_log(db, zone_id, "temperature", "critical"):
                        log_event(db,
                                  log_type="critical",
                                  severity="critical",
                                  title=f"Nhiệt độ vượt ngưỡng — {zone.name}",
                                  message=(f"⚠️ Nhiệt độ {zone.name} đã lên {temp}°C "
                                         f"(Ngưỡng tối đa: {crop.temp_max}°C). Nguy cơ héo lá!"),
                                  zone_id=zone_id,
                                  metric_key="temperature",
                                  metric_value=float(temp),
                                  threshold=float(crop.temp_max),
                                  action_label="Bật quạt giải nhiệt ngay",
                                  action_type="toggle_device",
                                  )
                    if crop.auto_mode:
                        fan = _find_actuator("quạt")
                        _auto_set(fan, True, "bật quạt thông gió để hạ nhiệt độ", "quạt", "nhiệt độ", temp, crop.temp_max)
                elif temp > crop.temp_max * 0.93:
                    if _can_log(db, zone_id, "temperature", "warning"):
                        log_event(db,
                                  log_type="warning",
                                  severity="warning",
                                  title=f"Nhiệt độ tiệm cận ngưỡng — {zone.name}",
                                  message=(f"Nhiệt độ {zone.name} đang ở {temp}°C, "
                                         f"gần ngưỡng tối đa {crop.temp_max}°C. Theo dõi chặt!"),
                                  zone_id=zone_id,
                                  metric_key="temperature",
                                  metric_value=float(temp),
                                  threshold=float(crop.temp_max),
                                  )
                elif temp < crop.temp_min:
                    if crop.auto_mode:
                        fan = _find_actuator("quạt")
                        _auto_set(fan, False, "tắt quạt thông gió do nhiệt độ đã hạ", "quạt", "nhiệt độ", temp, crop.temp_min)
                else:
                    _alert_cooldown.pop((zone_id, "temperature", "critical"), None)
                    _alert_cooldown.pop((zone_id, "temperature", "warning"), None)
                    if crop.auto_mode:
                        fan = _find_actuator("quạt")
                        _auto_set(fan, False, "tắt quạt thông gió — nhiệt độ đã ổn định", "quạt", "nhiệt độ", temp, crop.temp_min)

            if humid is not None:
                if humid < crop.humid_min:
                    if _can_log(db, zone_id, "humidity", "critical"):
                        log_event(db,
                                  log_type="critical",
                                  severity="critical",
                                  title=f"Độ ẩm thấp nguy hiểm — {zone.name}",
                                  message=(f"⚠️ Độ ẩm {zone.name} chỉ còn {humid}% "
                                         f"(Ngưỡng tối thiểu: {crop.humid_min}%). Cần tưới ngay!"),
                                  zone_id=zone_id,
                                  metric_key="humidity",
                                  metric_value=float(humid),
                                  threshold=float(crop.humid_min),
                                  action_label="Bật bơm tưới ngay",
                                  action_type="toggle_device",
                                  )
                    if crop.auto_mode:
                        pump = _find_actuator("bơm")
                        _auto_set(pump, True, "bật máy bơm tưới do độ ẩm thấp", "bơm", "độ ẩm", humid, crop.humid_min)
                elif humid < crop.humid_min * 1.05:
                    if _can_log(db, zone_id, "humidity", "warning"):
                        log_event(db,
                                  log_type="warning",
                                  severity="warning",
                                  title=f"Độ ẩm tiệm cận ngưỡng — {zone.name}",
                                  message=(f"Độ ẩm {zone.name} đang giảm, hiện ở {humid}% "
                                         f"(Ngưỡng tối thiểu: {crop.humid_min}%)."),
                                  zone_id=zone_id,
                                  metric_key="humidity",
                                  metric_value=float(humid),
                                  threshold=float(crop.humid_min),
                                  )
                elif humid > crop.humid_max:
                    if _can_log(db, zone_id, "humidity", "humid_high"):
                        log_event(db,
                                  log_type="warning",
                                  severity="warning",
                                  title=f"Độ ẩm vượt ngưỡng — {zone.name}",
                                  message=(f"💧 Độ ẩm {zone.name} đạt {humid}% "
                                         f"(Ngưỡng tối đa: {crop.humid_max}%). Nguy cơ úng rễ!"),
                                  zone_id=zone_id,
                                  metric_key="humidity",
                                  metric_value=float(humid),
                                  threshold=float(crop.humid_max),
                                  )
                    if crop.auto_mode:
                        pump = _find_actuator("bơm")
                        _auto_set(pump, False, "tắt máy bơm — độ ẩm đã đạt ngưỡng", "bơm", "độ ẩm", humid, crop.humid_max)
                        relay = _find_actuator("relay")
                        _auto_set(relay, True, "bật van thoát nước do độ ẩm quá cao", "relay", "độ ẩm", humid, crop.humid_max)
                else:
                    _alert_cooldown.pop((zone_id, "humidity", "critical"), None)
                    _alert_cooldown.pop((zone_id, "humidity", "warning"), None)
                    if crop.auto_mode:
                        pump = _find_actuator("bơm")
                        _auto_set(pump, False, "tắt máy bơm — độ ẩm đã ổn định", "bơm", "độ ẩm", humid, crop.humid_max)
                        relay = _find_actuator("relay")
                        _auto_set(relay, False, "tắt van thoát nước", "relay", "độ ẩm", humid, crop.humid_max)

            if light is not None and crop.light_min is not None and crop.light_max is not None:
                if light > crop.light_max:
                    if crop.auto_mode:
                        led = _find_actuator("led")
                        _auto_set(led, False, "tắt đèn LED do ánh sáng vượt ngưỡng", "LED", "ánh sáng", light, crop.light_max)
                        rly = _find_actuator("relay")
                        _auto_set(rly, True, "bật lưới che nắng do ánh sáng vượt ngưỡng", "relay", "ánh sáng", light, crop.light_max)
                elif light < crop.light_min:
                    if crop.auto_mode:
                        led = _find_actuator("led")
                        _auto_set(led, True, "bật đèn LED bổ sung do ánh sáng yếu", "LED", "ánh sáng", light, crop.light_min)
                else:
                    if crop.auto_mode:
                        rly = _find_actuator("relay")
                        _auto_set(rly, False, "tắt lưới che nắng — ánh sáng đã ổn định", "relay", "ánh sáng", light, crop.light_max)
        db.commit()

    # Invalidate Redis summary cache
    if REDIS_AVAILABLE:
        try:
            REDIS_CLIENT.delete("telemetry:summary")
        except Exception:
            pass

    await manager.broadcast(data)
    return {"status": "success", "message": f"Đã nhận, lưu DB và phát sóng cho zone {zone_id}"}


# --- 2. API LẤY TÓM TẮT TELEMETRY (có Redis cache) ---
@app.get("/api/telemetry/summary")
def get_telemetry_summary(db: Session = Depends(get_db)):
    # Kiểm tra Redis cache trước
    cached = _cache_get("telemetry:summary")
    if cached:
        import json
        return json.loads(cached)

    if not _last_telemetry:
        result = {"per_zone": [], "averages": {}, "active_zones": 0}
        _cache_set("telemetry:summary", json.dumps(result), ttl=60)
        return result

    per_zone = list(_last_telemetry.values())
    temps = [z["temperature"] for z in per_zone if "temperature" in z]
    humids = [z["humidity"] for z in per_zone if "humidity" in z]
    lights = [z["light"] for z in per_zone if "light" in z]

    averages = {}
    if temps:
        averages["temperature"] = round(sum(temps) / len(temps), 1)
    if humids:
        averages["humidity"] = round(sum(humids) / len(humids), 1)
    if lights:
        averages["light"] = round(sum(lights) / len(lights), 0)

    result = {
        "per_zone": per_zone,
        "averages": averages,
        "active_zones": len(per_zone),
    }
    _cache_set("telemetry:summary", json.dumps(result), ttl=60)
    return result


# ──────────────────────────────────────────────────────────────
# Phase 1 — TELEMETRY HISTORY & ANALYTICS
# ──────────────────────────────────────────────────────────────
@app.get("/api/telemetry/history", response_model=list[schemas.TelemetryHistoryResponse])
def get_telemetry_history(
    zone_id: Optional[int] = Query(None, description="Lọc theo zone_id"),
    metric: Optional[Literal["temperature", "humidity", "light"]] = Query(None),
    date_from: datetime = Query(..., description="ISO datetime bắt đầu"),
    date_to: datetime = Query(..., description="ISO datetime kết thúc"),
    interval: Literal["1m", "5m", "15m", "1h", "1d"] = Query("1m"),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    _from = date_from
    _to = date_to
    if _from.tzinfo is None:
        _from = _from.replace(tzinfo=timezone.utc)
    if _to.tzinfo is None:
        _to = _to.replace(tzinfo=timezone.utc)

    q = db.query(models.TelemetryData).filter(
        models.TelemetryData.measured_at >= _from,
        models.TelemetryData.measured_at <= _to,
    )
    if zone_id is not None:
        q = q.filter(models.TelemetryData.zone_id == zone_id)
    if metric is not None:
        col = getattr(models.TelemetryData, metric)
        q = q.filter(col.isnot(None))

    q = q.order_by(models.TelemetryData.measured_at.asc()).limit(limit)
    rows = q.all()

    if interval != "1m":
        interval_map = {
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "1d": timedelta(days=1),
        }
        delta = interval_map[interval]
        grouped: dict[str, list] = {}
        for row in rows:
            ts = row.measured_at.replace(tzinfo=None)
            bucket_start = ts - timedelta(
                minutes=ts.minute % (delta.total_seconds() / 60),
                seconds=ts.second,
                microseconds=ts.microsecond,
            )
            if delta >= timedelta(days=1):
                bucket_start = ts.replace(hour=0, minute=0, second=0, microsecond=0)
            key = bucket_start.isoformat()
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(row)

        averaged = []
        for bucket_ts, items in grouped.items():
            temps = [i.temperature for i in items if i.temperature is not None]
            humids = [i.humidity for i in items if i.humidity is not None]
            lights = [i.light for i in items if i.light is not None]
            averaged.append(models.TelemetryData(
                id=items[0].id,
                zone_id=items[0].zone_id,
                temperature=round(sum(temps) / len(temps), 2) if temps else None,
                humidity=round(sum(humids) / len(humids), 2) if humids else None,
                light=round(sum(lights) / len(lights), 2) if lights else None,
                measured_at=datetime.fromisoformat(bucket_ts).replace(tzinfo=timezone.utc),
            ))
        rows = averaged

    zone_names: dict[int, str] = {}
    for row in rows:
        if row.zone_id not in zone_names:
            z = db.query(models.Zone).filter(models.Zone.id == row.zone_id).first()
            zone_names[row.zone_id] = z.name if z else None

    return [
        schemas.TelemetryHistoryResponse(
            id=row.id,
            zone_id=row.zone_id,
            zone_name=zone_names.get(row.zone_id),
            temperature=row.temperature,
            humidity=row.humidity,
            light=row.light,
            measured_at=row.measured_at,
        )
        for row in rows
    ]


@app.get("/api/telemetry/analytics", response_model=list[schemas.TelemetryAnalyticsRow])
def get_telemetry_analytics(
    zone_id: Optional[int] = Query(None, description="Lọc theo zone_id"),
    date_from: datetime = Query(..., description="ISO datetime bắt đầu"),
    date_to: datetime = Query(..., description="ISO datetime kết thúc"),
    db: Session = Depends(get_db),
):
    _from = date_from
    _to = date_to
    if _from.tzinfo is None:
        _from = _from.replace(tzinfo=timezone.utc)
    if _to.tzinfo is None:
        _to = _to.replace(tzinfo=timezone.utc)

    q = db.query(models.TelemetryData).filter(
        models.TelemetryData.measured_at >= _from,
        models.TelemetryData.measured_at <= _to,
    )
    if zone_id is not None:
        q = q.filter(models.TelemetryData.zone_id == zone_id)

    rows = q.all()

    from collections import defaultdict
    buckets: dict[int, dict[str, list]] = defaultdict(lambda: {"temperature": [], "humidity": [], "light": []})
    for row in rows:
        if row.temperature is not None:
            buckets[row.zone_id]["temperature"].append(row.temperature)
        if row.humidity is not None:
            buckets[row.zone_id]["humidity"].append(row.humidity)
        if row.light is not None:
            buckets[row.zone_id]["light"].append(row.light)

    zone_names: dict[int, str] = {}
    for zid in buckets:
        z = db.query(models.Zone).filter(models.Zone.id == zid).first()
        zone_names[zid] = z.name if z else None

    result = []
    for zid, metrics in buckets.items():
        for metric_name, values in metrics.items():
            if not values:
                continue
            result.append(schemas.TelemetryAnalyticsRow(
                zone_id=zid,
                zone_name=zone_names.get(zid),
                metric=metric_name,
                min=round(min(values), 2),
                max=round(max(values), 2),
                avg=round(sum(values) / len(values), 2),
                count=len(values),
            ))

    return result


# --- 3. WEBSOCKET ---
@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ==========================================
# ALERT LOGS  —  /api/logs/
# ==========================================

def _build_log_response(log: models.AlertLog, db: Session) -> dict:
    zone_name = None
    device_name = None
    if log.zone_id:
        z = db.query(models.Zone).filter(models.Zone.id == log.zone_id).first()
        zone_name = z.name if z else None
    if log.device_id:
        d = db.query(models.Device).filter(models.Device.id == log.device_id).first()
        device_name = d.name if d else None
    return {
        "id": log.id,
        "log_type": log.log_type,
        "severity": log.severity,
        "title": log.title,
        "message": log.message,
        "zone_id": log.zone_id,
        "device_id": log.device_id,
        "action_label": log.action_label,
        "action_type": log.action_type,
        "action_target_id": log.action_target_id,
        "actor": log.actor,
        "is_read": log.is_read,
        "metric_key": log.metric_key,
        "metric_value": log.metric_value,
        "threshold": log.threshold,
        "created_at": log.created_at.isoformat() + "Z" if log.created_at else None,
        "zone_name": zone_name,
        "device_name": device_name,
    }


def log_event(
    db: Session,
    *,
    log_type: str,
    severity: str,
    title: str,
    message: str,
    zone_id: int = None,
    device_id: int = None,
    action_label: str = None,
    action_type: str = None,
    action_target_id: int = None,
    actor: str = "SYSTEM",
    metric_key: str = None,
    metric_value: float = None,
    threshold: float = None,
) -> models.AlertLog:
    entry = models.AlertLog(
        log_type=log_type,
        severity=severity,
        title=title,
        message=message,
        zone_id=zone_id,
        device_id=device_id,
        action_label=action_label,
        action_type=action_type,
        action_target_id=action_target_id,
        actor=actor,
        metric_key=metric_key,
        metric_value=metric_value,
        threshold=threshold,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    zone_name = None
    device_name = None
    if zone_id:
        z = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
        zone_name = z.name if z else None
    if device_id:
        dv = db.query(models.Device).filter(models.Device.id == device_id).first()
        device_name = dv.name if dv else None

    import asyncio
    ws_payload = {
        "_type": "new_log",
        "id": entry.id,
        "log_type": log_type,
        "severity": severity,
        "title": title,
        "message": message,
        "zone_id": zone_id,
        "zone_name": zone_name,
        "device_id": device_id,
        "device_name": device_name,
        "action_label": action_label,
        "action_type": action_type,
        "actor": actor,
        "metric_key": metric_key,
        "metric_value": metric_value,
        "threshold": threshold,
        "is_read": False,
        "created_at": entry.created_at.isoformat() + "Z",
    }
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(manager.broadcast(ws_payload))
    except Exception:
        pass

    return entry


# ── Log endpoints ──────────────────────────────────────────────
@app.get("/api/logs/", response_model=list[schemas.AlertLogResponse])
def get_logs(
    log_type: Optional[str] = Query(None, description="critical|warning|automation|system"),
    severity: Optional[str] = Query(None),
    zone_id: Optional[int] = Query(None),
    is_read: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(models.AlertLog)
    if log_type:
        q = q.filter(models.AlertLog.log_type == log_type)
    if severity:
        q = q.filter(models.AlertLog.severity == severity)
    if zone_id:
        q = q.filter(models.AlertLog.zone_id == zone_id)
    if is_read is not None:
        q = q.filter(models.AlertLog.is_read == is_read)
    logs = q.order_by(models.AlertLog.created_at.desc()).offset(offset).limit(limit).all()
    return [_build_log_response(l, db) for l in logs]


@app.get("/api/logs/unread-count")
def get_unread_count(db: Session = Depends(get_db)):
    count = db.query(models.AlertLog).filter(models.AlertLog.is_read == False).count()
    return {"unread": count}


@app.post("/api/logs/", response_model=schemas.AlertLogResponse, status_code=201)
def create_log(payload: schemas.AlertLogCreate, db: Session = Depends(get_db)):
    entry = log_event(
        db,
        log_type=payload.log_type,
        severity=payload.severity,
        title=payload.title,
        message=payload.message,
        zone_id=payload.zone_id,
        device_id=payload.device_id,
        action_label=payload.action_label,
        action_type=payload.action_type,
        action_target_id=payload.action_target_id,
        actor=payload.actor or "MANUAL",
        metric_key=payload.metric_key,
        metric_value=payload.metric_value,
        threshold=payload.threshold,
    )
    return _build_log_response(entry, db)


@app.patch("/api/logs/{log_id}/read", response_model=schemas.AlertLogResponse)
def mark_log_read(log_id: int, db: Session = Depends(get_db)):
    entry = db.query(models.AlertLog).filter(models.AlertLog.id == log_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Log không tồn tại")
    entry.is_read = True
    db.commit()
    db.refresh(entry)
    return _build_log_response(entry, db)


@app.post("/api/logs/read-all")
def mark_all_read(db: Session = Depends(get_db)):
    updated = db.query(models.AlertLog).filter(models.AlertLog.is_read == False).all()
    for e in updated:
        e.is_read = True
    db.commit()
    return {"marked_read": len(updated)}


@app.delete("/api/logs/{log_id}", status_code=204)
def delete_log(log_id: int, db: Session = Depends(get_db)):
    entry = db.query(models.AlertLog).filter(models.AlertLog.id == log_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Log không tồn tại")
    db.delete(entry)
    db.commit()


# ================================================================
# Phase 2 — DASHBOARD WIDGETS
# ================================================================

@app.get("/api/dashboard/widgets", response_model=list[schemas.DashboardWidgetResponse])
def get_dashboard_widgets(
    user_id: Optional[int] = Query(None, description="Lọc theo user_id (null = tất cả)"),
    db: Session = Depends(get_db),
):
    q = db.query(models.DashboardWidget).filter(models.DashboardWidget.is_active == True)
    if user_id is not None:
        q = q.filter(
            (models.DashboardWidget.user_id == user_id) |
            (models.DashboardWidget.user_id == None)
        )
    else:
        q = q.filter(models.DashboardWidget.user_id == None)
    widgets = q.order_by(models.DashboardWidget.position.asc()).all()
    return widgets


@app.post("/api/dashboard/widgets", response_model=schemas.DashboardWidgetResponse, status_code=201)
def create_dashboard_widget(
    payload: schemas.DashboardWidgetCreate,
    db: Session = Depends(get_db),
):
    max_pos = db.query(func.max(models.DashboardWidget.position)).filter(
        models.DashboardWidget.user_id == payload.user_id
    ).scalar()
    new_position = (max_pos or 0) + 1

    widget = models.DashboardWidget(
        user_id=payload.user_id,
        widget_type=payload.widget_type,
        title=payload.title,
        config=payload.config,
        position=payload.position if payload.position else new_position,
        is_active=payload.is_active if payload.is_active is not None else True,
    )
    db.add(widget)
    db.commit()
    db.refresh(widget)
    return widget


@app.get("/api/dashboard/widgets/{widget_id}", response_model=schemas.DashboardWidgetResponse)
def get_dashboard_widget(widget_id: int, db: Session = Depends(get_db)):
    widget = db.query(models.DashboardWidget).filter(models.DashboardWidget.id == widget_id).first()
    if widget is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy widget")
    return widget


@app.put("/api/dashboard/widgets/{widget_id}", response_model=schemas.DashboardWidgetResponse)
def update_dashboard_widget(
    widget_id: int,
    payload: schemas.DashboardWidgetUpdate,
    db: Session = Depends(get_db),
):
    widget = db.query(models.DashboardWidget).filter(models.DashboardWidget.id == widget_id).first()
    if widget is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy widget")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(widget, key, value)

    db.commit()
    db.refresh(widget)
    return widget


@app.delete("/api/dashboard/widgets/{widget_id}", status_code=204)
def delete_dashboard_widget(widget_id: int, db: Session = Depends(get_db)):
    widget = db.query(models.DashboardWidget).filter(models.DashboardWidget.id == widget_id).first()
    if widget is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy widget")
    db.delete(widget)
    db.commit()
    return


@app.post("/api/dashboard/widgets/reorder")
def reorder_dashboard_widgets(
    order: list[int],
    db: Session = Depends(get_db),
):
    for position, widget_id in enumerate(order):
        widget = db.query(models.DashboardWidget).filter(models.DashboardWidget.id == widget_id).first()
        if widget:
            widget.position = position
    db.commit()
    return {"message": f"Đã cập nhật thứ tự cho {len(order)} widgets"}


# ================================================================
# Phase 3 — REPORT SERVICE
# ================================================================

def _build_report_response(report: models.Report) -> schemas.ReportResponse:
    """Chuyển đổi ORM Report → Pydantic Response."""
    return schemas.ReportResponse(
        id=report.id,
        name=report.name,
        report_type=report.report_type,
        format=report.format,
        date_from=report.date_from,
        date_to=report.date_to,
        zone_ids=report.zone_ids,
        metrics=report.metrics,
        widgets=report.widgets,
        status=report.status,
        file_path=report.file_path,
        file_size=report.file_size,
        created_by=report.created_by,
        created_at=report.created_at,
        completed_at=report.completed_at,
    )


def remove_diacritics(text: str) -> str:
    """Remove Vietnamese diacritical marks."""
    
    if not isinstance(text, str):
        return str(text)

    import unicodedata

    # Normalize unicode
    text = unicodedata.normalize('NFD', text)

    # Remove combining marks
    text = ''.join(
        char for char in text
        if unicodedata.category(char) != 'Mn'
    )

    # Replace đ / Đ manually
    text = text.replace('đ', 'd').replace('Đ', 'D')

    return text


def _render_widgets_to_csv(widgets: list[dict], date_from, date_to, zones, db) -> tuple[list[dict], list[str]]:
    """
    Render widget configuration to CSV data.
    Returns (rows, columns) tuple suitable for CSV export.
    """
    if not widgets or len(widgets) == 0:
        return [], []
    
    rows = []
    all_columns = set()
    
    # Get telemetry data for date range - USE TelemetryData, not Telemetry
    telemetries = db.query(models.TelemetryData).filter(
        models.TelemetryData.measured_at.between(date_from, date_to)
    ).order_by(models.TelemetryData.measured_at.asc()).all()
    
    telemetry_by_zone = {}
    for t in telemetries:
        zid = t.zone_id
        if zid not in telemetry_by_zone:
            telemetry_by_zone[zid] = []
        telemetry_by_zone[zid].append(t)
    
    # Process each widget
    for widget in widgets:
        widget_type = widget.get('type', '')
        widget_config = widget.get('config', {})
        widget_id = widget.get('id', '')
        
        # Get zones for this widget (empty = all zones)
        widget_zone_ids = widget_config.get('zoneIds', [])
        if not widget_zone_ids:
            widget_zone_ids = [z.id for z in zones] if zones else []
        
        # Prepare rows based on widget type
        if widget_type == 'stat':
            metric = widget_config.get('metric', 'temperature')
            aggregation = widget_config.get('aggregation', 'avg')
            
            for zid in widget_zone_ids:
                zone_data = telemetry_by_zone.get(zid, [])
                if not zone_data:
                    continue
                    
                values = [getattr(t, metric, 0) for t in zone_data if hasattr(t, metric) and getattr(t, metric) is not None]
                if not values:
                    continue
                
                if aggregation == 'avg':
                    value = sum(values) / len(values)
                elif aggregation == 'max':
                    value = max(values)
                elif aggregation == 'min':
                    value = min(values)
                elif aggregation == 'sum':
                    value = sum(values)
                else:
                    value = 0
                
                zone_name = next((z.name for z in zones if z.id == zid), f'Zone {zid}')
                col_name = f'{widget_type}_{widget_id}_{remove_diacritics(metric)}'
                all_columns.add(col_name)
                all_columns.add('Zone')
                rows.append({
                    'Zone': remove_diacritics(zone_name),
                    col_name: round(value, 2)
                })
        
        elif widget_type in ['chart', 'barchart']:
            metrics = widget_config.get('metrics', ['temperature'])
            
            for zid in widget_zone_ids:
                zone_data = telemetry_by_zone.get(zid, [])
                if not zone_data:
                    continue
                
                zone_name = next((z.name for z in zones if z.id == zid), f'Zone {zid}')
                
                for t in zone_data:
                    row = {
                        'Timestamp': t.measured_at.isoformat() if t.measured_at else '',
                        'Zone': remove_diacritics(zone_name)
                    }
                    for metric in metrics:
                        col_name = f'{widget_id}_{remove_diacritics(metric)}'
                        val = getattr(t, metric, None)
                        row[col_name] = round(val, 2) if val is not None else ''
                        all_columns.add(col_name)
                    
                    all_columns.add('Timestamp')
                    all_columns.add('Zone')
                    rows.append(row)
        
        elif widget_type == 'table':
            metric = widget_config.get('metric', 'temperature')
            limit = widget_config.get('limit', 50)
            
            for zid in widget_zone_ids:
                zone_data = telemetry_by_zone.get(zid, [])[:limit]
                if not zone_data:
                    continue
                
                zone_name = next((z.name for z in zones if z.id == zid), f'Zone {zid}')
                
                for t in zone_data:
                    col_name = f'{widget_id}_{remove_diacritics(metric)}'
                    val = getattr(t, metric, None)
                    row = {
                        'Timestamp': t.measured_at.isoformat() if t.measured_at else '',
                        'Zone': remove_diacritics(zone_name),
                        col_name: round(val, 2) if val is not None else ''
                    }
                    all_columns.add(col_name)
                    all_columns.add('Timestamp')
                    all_columns.add('Zone')
                    rows.append(row)
        
        elif widget_type == 'summary':
            for zid in widget_zone_ids:
                zone_data = telemetry_by_zone.get(zid, [])
                if not zone_data:
                    continue
                
                zone_name = next((z.name for z in zones if z.id == zid), f'Zone {zid}')
                
                for metric in ['temperature', 'humidity', 'light']:
                    values = [getattr(t, metric, 0) for t in zone_data if hasattr(t, metric) and getattr(t, metric) is not None]
                    if not values:
                        continue
                    
                    row = {
                        'Zone': remove_diacritics(zone_name),
                        'Metric': remove_diacritics(metric),
                        f'{widget_id}_avg': round(sum(values) / len(values), 2),
                        f'{widget_id}_max': max(values),
                        f'{widget_id}_min': min(values),
                        f'{widget_id}_sum': sum(values),
                    }
                    all_columns.update(['Zone', 'Metric', f'{widget_id}_avg', f'{widget_id}_max', f'{widget_id}_min', f'{widget_id}_sum'])
                    rows.append(row)
    
    # Build final rows with all columns
    columns = sorted(list(all_columns))
    final_rows = []
    for row in rows:
        final_row = {}
        for col in columns:
            final_row[col] = row.get(col, '')
        final_rows.append(final_row)
    
    return final_rows, columns


def _generate_csv(data: list[dict], columns: list[str]) -> bytes:
    """Tạo file CSV từ danh sách dict."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue().encode("utf-8")


def _generate_excel(data: list[dict], columns: list[str], sheet_name: str = "Report") -> bytes:
    """Tạo file Excel (.xlsx) từ danh sách dict."""
    try:
        import pandas as pd
        df = pd.DataFrame(data, columns=columns)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        return output.getvalue()
    except ImportError:
        raise HTTPException(status_code=500, detail="pandas/openpyxl chưa được cài đặt.")


def _generate_pdf_with_widgets(widgets: list[dict], rows: list[dict], columns: list[str],
                                report_name: str, date_from: str, date_to: str, zones: list = None) -> bytes:
    """Tạo PDF báo cáo từ widget configuration kèm theo hình ảnh đã chụp từ Frontend."""
    if not HAS_REPORTLAB:
        raise HTTPException(status_code=500, detail="reportlab chưa được cài đặt.")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=report_name, author="SmartFarm HK252")
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'], fontSize=20, leading=24, alignment=TA_CENTER,
        textColor=colors.HexColor('#1b5e20'), fontName=UNICODE_FONT_BOLD
    )
    subtitle_style = ParagraphStyle(
        'CustomSub', parent=styles['Normal'], fontSize=12, leading=16, alignment=TA_CENTER,
        textColor=colors.HexColor('#424242'), fontName=UNICODE_FONT
    )
    header_style = ParagraphStyle(
        'CustomHeader', parent=styles['Heading2'], fontSize=14, leading=18,
        textColor=colors.HexColor('#1b5e20'), fontName=UNICODE_FONT_BOLD
    )
    
    elements = []
    
    # Title Section
    elements.append(Paragraph(report_name, title_style))
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph(f"📅 Từ {date_from} đến {date_to}", subtitle_style))
    elements.append(Spacer(1, 15 * mm))
    
    widget_type_labels = {
        'stat': 'Thống kê', 'chart': 'Biểu đồ đường', 'barchart': 'Biểu đồ cột',
        'gauge': 'Đồng hồ đo', 'table': 'Bảng dữ liệu', 'summary': 'Tóm tắt'
    }

    # Render từng widget dưới dạng hình ảnh
    for idx, widget in enumerate(widgets):
        w_type = widget.get('type', '')
        image_data = widget.get('image_data', '')

        label = widget_type_labels.get(w_type, w_type.upper())
        elements.append(Paragraph(f"{idx + 1}. {label}", header_style))
        elements.append(Spacer(1, 4 * mm))

        if image_data and "base64," in image_data:
            try:
                # Cắt bỏ phần header data:image/png;base64,
                header, encoded = image_data.split(",", 1)
                img_bytes = base64.b64decode(encoded)
                img_buffer = io.BytesIO(img_bytes)
                
                # Chèn hình ảnh vào PDF (Set width khoảng 160mm cho vừa trang A4 dọc)
                img_element = RLImage(img_buffer, width=160*mm, height=100*mm, kind='proportional')
                elements.append(img_element)
            except Exception as e:
                elements.append(Paragraph(f"[Lỗi xử lý hình ảnh: {str(e)}]", styles['Normal']))
        else:
             elements.append(Paragraph("(Không có dữ liệu hình ảnh cho widget này)", styles['Italic']))

        elements.append(Spacer(1, 15 * mm))

    # Footer
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(
        f"--- Tạo bởi SmartFarm HK252 ---", subtitle_style
    ))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def _generate_pdf(data: list[dict], columns: list[str], report_name: str,
                  date_from: str, date_to: str, zone_names: list[str] = None) -> bytes:
    """Tạo file PDF báo cáo với biểu đồ và bảng dữ liệu."""
    if not HAS_REPORTLAB:
        raise HTTPException(status_code=500, detail="reportlab chưa được cài đặt. Chạy: pip install reportlab")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            title=report_name,
                            author="SmartFarm HK252")

    styles = getSampleStyleSheet()

    # Custom styles - use Unicode font for Vietnamese support
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=20, leading=24, alignment=TA_CENTER,
        textColor=colors.HexColor('#1b5e20'),
        fontName=UNICODE_FONT
    )
    subtitle_style = ParagraphStyle(
        'CustomSub', parent=styles['Normal'],
        fontSize=12, leading=16, alignment=TA_CENTER,
        textColor=colors.HexColor('#424242'),
        fontName=UNICODE_FONT
    )
    header_style = ParagraphStyle(
        'CustomHeader', parent=styles['Heading2'],
        fontSize=14, leading=18, textColor=colors.HexColor('#1b5e20'),
        fontName=UNICODE_FONT
    )

    elements = []

    # Title
    elements.append(Spacer(1, 20 * mm))
    elements.append(Paragraph(report_name, title_style))
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph(f"📅 {date_from} → {date_to}", subtitle_style))
    if zone_names:
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(f"📍 Khu vực: {', '.join(zone_names)}", subtitle_style))
    elements.append(Spacer(1, 12 * mm))

    # Summary stats
    elements.append(Paragraph("📊 Tóm tắt dữ liệu", header_style))
    elements.append(Spacer(1, 4 * mm))

    metric_labels = {"temperature": "🌡️ Nhiệt độ (°C)", "humidity": "💧 Độ ẩm (%)", "light": "☀️ Ánh sáng (Lux)"}
    summary_data = []
    for col in columns:
        if col in ("zone_id", "zone_name", "measured_at"):
            continue
        values = [float(r[col]) for r in data if r.get(col) is not None]
        if values:
            summary_data.append([
                metric_labels.get(col, col),
                f"{min(values):.2f}",
                f"{max(values):.2f}",
                f"{sum(values) / len(values):.2f}",
                str(len(values))
            ])

    if summary_data:
        summary_table = Table(
            [["Chỉ số", "Min", "Max", "Trung bình", "Số mẫu"]] + summary_data,
            colWidths=[120 * mm, 70 * mm, 70 * mm, 80 * mm, 60 * mm]
        )
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b5e20')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 10 * mm))

    # Detail table
    elements.append(KeepTogether([
        Paragraph("📋 Chi tiết dữ liệu", header_style),
        Spacer(1, 4 * mm),
    ]))

    display_columns = ["zone_name" if c == "zone_name" else
                       "measured_at" if c == "measured_at" else
                       c.capitalize() for c in columns]

    table_data = [display_columns]
    for row in data[:200]:  # Giới hạn 200 dòng cho PDF
        table_data.append([str(row.get(c, ''))[:30] for c in columns])

    col_widths = [max(100 * mm, 300 * mm // len(columns))] * len(columns)
    detail_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8f0')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(detail_table)

    # Footer
    elements.append(Spacer(1, 15 * mm))
    elements.append(Paragraph(
        f"--- Tạo bởi SmartFarm HK252 · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} ---",
        subtitle_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def _fetch_report_data(
    db: Session,
    zone_ids: Optional[list[int]],
    metrics: Optional[list[str]],
    date_from: datetime,
    date_to: datetime,
) -> tuple[list[dict], list[str]]:
    """
    Query telemetry_data theo filter, trả về (rows, columns).
    Mỗi row là dict: {zone_id, zone_name, temperature, humidity, light, measured_at}
    """
    q = db.query(
        models.TelemetryData.zone_id,
        models.Zone.name.label("zone_name"),
        models.TelemetryData.temperature,
        models.TelemetryData.humidity,
        models.TelemetryData.light,
        models.TelemetryData.measured_at,
    ).join(models.Zone, models.TelemetryData.zone_id == models.Zone.id).filter(
        models.TelemetryData.measured_at >= date_from,
        models.TelemetryData.measured_at <= date_to,
    )

    if zone_ids:
        q = q.filter(models.TelemetryData.zone_id.in_(zone_ids))

    rows_raw = q.order_by(models.TelemetryData.measured_at.asc()).all()

    all_metrics = ["temperature", "humidity", "light"]
    if metrics:
        selected_metrics = [m for m in metrics if m in all_metrics]
    else:
        selected_metrics = all_metrics

    columns = ["zone_id", "zone_name", "measured_at"] + selected_metrics

    rows = []
    for row in rows_raw:
        r: dict = {
            "zone_id": row.zone_id,
            "zone_name": row.zone_name,
            "measured_at": row.measured_at.isoformat() if row.measured_at else None,
        }
        for m in selected_metrics:
            r[m] = getattr(row, m)
        rows.append(r)

    return rows, columns


def _generate_report_file_sync(report_id: int, db: Session):
    """Tạo file báo cáo đồng bộ (gọi từ background task)."""
    db_report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not db_report:
        return

    try:
        db_report.status = "processing"
        db.commit()
        db.refresh(db_report)

        _from = db_report.date_from
        _to = db_report.date_to
        if _from.tzinfo is None:
            _from = _from.replace(tzinfo=timezone.utc)
        if _to.tzinfo is None:
            _to = _to.replace(tzinfo=timezone.utc)

        # =========================================================
        # ĐOẠN SỬA LỖI: TỐI ƯU HÓA TRUY VẤN
        # =========================================================
        is_widget_report = db_report.widgets and len(db_report.widgets) > 0
        fmt = db_report.format
        rows, columns = [], []
        zones = []

        if is_widget_report:
            zones = db.query(models.Zone).all()
            # CHỈ fetch data nếu định dạng là CSV hoặc XLSX
            # Nếu là PDF, bỏ qua vì ảnh đã được Frontend chụp rồi!
            if fmt in ["csv", "xlsx"]:
                rows, columns = _render_widgets_to_csv(db_report.widgets, _from, _to, zones, db)
        else:
            # Traditional report
            rows, columns = _fetch_report_data(db, db_report.zone_ids, db_report.metrics, _from, _to)

        # Đừng return early nếu là PDF chứa widget (vì PDF widget không cần biến rows)
        if not rows and not (is_widget_report and fmt == "pdf"):
            db_report.status = "completed"
            db_report.file_path = None
            db_report.file_size = 0
            db_report.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_report)
            return
        # =========================================================

        if fmt == "csv":
            file_content = _generate_csv(rows, columns)
            ext = "csv"
        elif fmt == "xlsx":
            file_content = _generate_excel(rows, columns)
            ext = "xlsx"
        elif fmt == "pdf":
            # Check if widget-based report
            if is_widget_report:
                file_content = _generate_pdf_with_widgets(
                    widgets=db_report.widgets,
                    rows=rows,
                    columns=columns,
                    report_name=db_report.name,
                    date_from=_from.strftime("%Y-%m-%d %H:%M"),
                    date_to=_to.strftime("%Y-%m-%d %H:%M"),
                    zones=zones
                )
            else:
                # Use traditional PDF generator
                zone_names = None
                if db_report.zone_ids:
                    zones = db.query(models.Zone).filter(models.Zone.id.in_(db_report.zone_ids)).all()
                    zone_names = [z.name for z in zones]
                file_content = _generate_pdf(
                    rows, columns,
                    report_name=db_report.name,
                    date_from=_from.strftime("%Y-%m-%d %H:%M"),
                    date_to=_to.strftime("%Y-%m-%d %H:%M"),
                    zone_names=zone_names,
                )
            ext = "pdf"
        else:
            raise HTTPException(status_code=400, detail=f"Định dạng '{fmt}' không được hỗ trợ")

        filename = f"report_{report_id}_{uuid.uuid4().hex[:8]}.{ext}"
        file_path = REPORTS_DIR / filename
        file_path.write_bytes(file_content)

        db_report.status = "completed"
        db_report.file_path = str(file_path)
        db_report.file_size = len(file_content)
        db_report.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_report)

    except Exception as e:
        print(f"LỖI TẠO BÁO CÁO NGẦM: {e}") # Thêm log in ra lỗi để dễ debug
        db_report.status = "failed"
        db.commit()
        db.refresh(db_report)
        # Bỏ dòng "raise" đi để không làm sập tiến trình ngầm


@app.post("/api/reports/generate", response_model=schemas.ReportResponse, status_code=201)
def generate_report(
    payload: schemas.ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Tạo báo cáo mới (async).
    1. Tạo record trong bảng reports (status=pending)
    2. Đẩy task tạo file vào background
    3. Trả về report_id để client poll trạng thái
    """
    report = models.Report(
        name=payload.name,
        report_type="custom",
        format=payload.format,
        date_from=payload.date_from,
        date_to=payload.date_to,
        zone_ids=payload.zone_ids,
        metrics=payload.metrics,
        widgets=payload.widgets,  # Widget-based report configuration
        status="pending",
        created_by=None,  # TODO: lấy từ JWT current_user
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Đẩy task tạo file vào background
    background_tasks.add_task(_generate_report_file_sync, report.id, db)

    return _build_report_response(report)


@app.get("/api/reports/", response_model=list[schemas.ReportResponse])
def list_reports(db: Session = Depends(get_db)):
    """Lấy danh sách tất cả báo cáo đã tạo."""
    reports = db.query(models.Report).order_by(models.Report.created_at.desc()).all()
    return [_build_report_response(r) for r in reports]


@app.get("/api/reports/{report_id}", response_model=schemas.ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Lấy chi tiết báo cáo theo ID."""
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo")
    return _build_report_response(report)


@app.get("/api/reports/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    """Tải file báo cáo về."""
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo")
    if report.status != "completed":
        raise HTTPException(status_code=400, detail="Báo cáo chưa hoàn thành")
    if report.file_path is None:
        raise HTTPException(status_code=404, detail="File báo cáo không tồn tại")

    file_path = Path(report.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File không tồn tại trên server")

    media_types = {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf",
    }
    media_type = media_types.get(report.format, "application/octet-stream")
    return StreamingResponse(
        file_path.open("rb"),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={file_path.name}"}
    )


@app.delete("/api/reports/{report_id}", status_code=204)
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Xóa báo cáo."""
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo")

    if report.file_path:
        try:
            Path(report.file_path).unlink(missing_ok=True)
        except Exception:
            pass

    db.delete(report)
    db.commit()
    return


# ================================================================
# Phase 4 — SCHEDULED REPORTS (APScheduler)
# ================================================================

def _get_scheduler() -> Optional[BackgroundScheduler]:
    """Singleton scheduler instance."""
    global _report_scheduler
    if _report_scheduler is None and APSCHEDULER_AVAILABLE:
        _report_scheduler = BackgroundScheduler()
        _report_scheduler.start()
    return _report_scheduler


def _scheduled_report_job(report_config: dict):
    """Job tạo báo cáo theo lịch."""
    db = SessionLocal()
    try:
        report = models.Report(
            name=report_config["name"],
            report_type="scheduled",
            format=report_config.get("format", "csv"),
            date_from=report_config["date_from"],
            date_to=report_config["date_to"],
            zone_ids=report_config.get("zone_ids"),
            metrics=report_config.get("metrics"),
            status="processing",
            created_by=report_config.get("created_by"),
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        _generate_report_file_sync(report.id, db)
    except Exception as e:
        print(f"[ScheduledReport] Error: {e}")
    finally:
        db.close()


@app.post("/api/reports/schedule")
def schedule_report(payload: schemas.ScheduledReportCreate, db: Session = Depends(get_db)):
    """Đặt lịch tạo báo cáo tự động (cron expression)."""
    scheduler = _get_scheduler()
    if scheduler is None:
        raise HTTPException(status_code=500, detail="APScheduler chưa được cài đặt.")

    # Tạo report record với status=scheduled
    report = models.Report(
        name=payload.name,
        report_type="scheduled",
        format=payload.format,
        date_from=payload.date_from,
        date_to=payload.date_to,
        zone_ids=payload.zone_ids,
        metrics=payload.metrics,
        status="scheduled",
        created_by=None,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Lưu config cho job
    job_config = {
        "report_id": report.id,
        "name": payload.name,
        "format": payload.format,
        "date_from": payload.date_from,
        "date_to": payload.date_to,
        "zone_ids": payload.zone_ids,
        "metrics": payload.metrics,
    }

    trigger = CronTrigger(
        year=payload.cron_year or "*",
        month=payload.cron_month or "*",
        day=payload.cron_day or "*",
        week=payload.cron_week or "*",
        day_of_week=payload.cron_day_of_week or "*",
        hour=payload.cron_hour or "0",
        minute=payload.cron_minute or "0",
        second=payload.cron_second or "0",
        timezone="Asia/Bangkok",
    )

    scheduler.add_job(
        _scheduled_report_job,
        trigger=trigger,
        args=[job_config],
        id=f"scheduled_report_{report.id}",
        replace_existing=True,
    )

    return {"message": f"Đã đặt lịch báo cáo #{report.id}", "report_id": report.id}


@app.get("/api/reports/schedule/list")
def list_scheduled_reports(db: Session = Depends(get_db)):
    """Lấy danh sách báo cáo đã đặt lịch."""
    reports = db.query(models.Report).filter(
        models.Report.report_type == "scheduled"
    ).order_by(models.Report.created_at.desc()).all()
    return [_build_report_response(r) for r in reports]


@app.delete("/api/reports/schedule/{report_id}")
def cancel_scheduled_report(report_id: int, db: Session = Depends(get_db)):
    """Hủy báo cáo đã đặt lịch."""
    scheduler = _get_scheduler()
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo")

    if scheduler:
        try:
            scheduler.remove_job(f"scheduled_report_{report_id}")
        except Exception:
            pass

    db.delete(report)
    db.commit()
    return {"message": f"Đã hủy báo cáo lịch #{report_id}"}


# ================================================================
# Phase 4 — DASHBOARD WIDGET SERVICE (mở rộng)
# ================================================================

@app.get("/api/dashboard/widget-types")
def get_widget_types():
    """Trả về danh sách widget types khả dụng."""
    return {
        "types": [
            {"key": "stat_card", "label": "Thẻ thống kê", "config_example": {"metric": "temperature", "zone_id": None, "agg": "avg"}},
            {"key": "line_chart", "label": "Biểu đồ đường", "config_example": {"metrics": ["temperature", "humidity"], "zone_ids": [1, 2], "period": "24h"}},
            {"key": "bar_chart", "label": "Biểu đồ cột", "config_example": {"metric": "humidity", "group_by": "zone", "period": "7d"}},
            {"key": "gauge", "label": "Đồng hồ đo", "config_example": {"metric": "temperature", "zone_id": 1, "min": 0, "max": 50}},
            {"key": "live_table", "label": "Bảng realtime", "config_example": {"columns": ["zone", "temperature", "humidity", "light", "timestamp"]}},
        ]
    }


# ── Startup / Shutdown ──────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Khởi tạo scheduler khi server start."""
    global _report_scheduler
    if APSCHEDULER_AVAILABLE and _report_scheduler is None:
        _report_scheduler = BackgroundScheduler()
        _report_scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Dọn dẹp khi server shutdown."""
    global _report_scheduler
    if _report_scheduler:
        _report_scheduler.shutdown()
        _report_scheduler = None
    if REDIS_AVAILABLE:
        try:
            REDIS_CLIENT.close()
        except Exception:
            pass
# ==========================================
# API CHO AI CHATBOT
# ==========================================

@app.post("/api/chat", response_model=schemas.ChatResponse)
def chat_endpoint(chat_req: schemas.ChatMessage):
    """
    Chat với AI Assistant
    
    - message: Câu hỏi từ người dùng
    - session_id: ID phiên chat (để lưu lịch sử)
    
    Example:
    ```json
    {
        "message": "Nhiệt độ tối ưu cho cây cà chua là bao nhiêu?",
        "session_id": "user123"
    }
    ```
    """
    try:
        # Gọi chatbot service
        ai_response = chat_with_ai(
            user_query=chat_req.message,
            session_id=chat_req.session_id,
            context=None  # Có thể thêm context từ DB sau
        )
        
        return schemas.ChatResponse(
            response=ai_response,
            session_id=chat_req.session_id,
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi chatbot: {str(e)}"
        )


@app.delete("/api/chat/history/{session_id}")
def clear_chat_history(session_id: str):
    """Xóa lịch sử chat của một phiên"""
    try:
        clear_history(session_id)
        return {"message": f"Đã xóa lịch sử chat của phiên {session_id}"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xóa lịch sử: {str(e)}"
        )


@app.get("/api/chat/health")
def chat_health_check():
    """Check xem chatbot service có hoạt động không"""
    try:
        # Test kết nối Gemini API
        from ai_config import GEMINI_API_KEY
        if not GEMINI_API_KEY:
            return {
                "status": "error",
                "message": "GEMINI_API_KEY không được cấu hình"
            }
        return {
            "status": "ok",
            "message": "Chatbot service sẵn sàng",
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ==========================================
# API CHO SQL AGENT (Text-to-SQL)
# ==========================================

@app.post("/api/query")
def query_database_endpoint(query_request: dict):
    """
    Execute natural language query against SmartFarm database
    
    Request:
    {
        "question": "Có bao nhiêu khu vực trong hệ thống?",
        "include_ai_explanation": true
    }
    
    Response:
    {
        "success": true,
        "query_result": "...",
        "ai_explanation": "...",
        "timestamp": "..."
    }
    """
    try:
        question = query_request.get("question", "")
        include_explanation = query_request.get("include_ai_explanation", True)
        
        if not question:
            raise HTTPException(status_code=400, detail="Question không được để trống")
        
        # Execute SQL query
        db_result = query_database(question)
        
        response_data = {
            "success": db_result["success"],
            "query_result": db_result["result"],
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None)
        }
        
        # Optionally get AI explanation
        if include_explanation and db_result["success"]:
            explanation = chat_with_ai(
                user_query=f"Hãy giải thích ngắn gọn kết quả này: {db_result['result']}",
                session_id="query_explanation"
            )
            response_data["ai_explanation"] = explanation
        
        return response_data
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi truy vấn: {str(e)}"
        )


@app.get("/api/query/schema")
def get_database_schema():
    """
    Get SmartFarm database schema information
    Useful for understanding available tables and fields
    """
    try:
        from sql_agent import get_schema_info
        schema = get_schema_info()
        return {
            "success": True,
            "schema": schema,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==========================================
# API CHO RAG SYSTEM (Retrieval-Augmented Generation)
# ==========================================

@app.post("/api/rag/retrieve")
def retrieve_rag_documents(request: dict):
    """
    Retrieve relevant agricultural documents based on query
    
    Request:
    {
        "query": "Làm thế nào để ngăn chặn bệnh phấn trắng?",
        "k": 3
    }
    
    Response:
    {
        "success": true,
        "documents": [
            {
                "content": "...",
                "source": "tomato_cultivation.txt",
                "relevance": "high"
            }
        ],
        "timestamp": "2026-05-13T10:30:45"
    }
    """
    try:
        query = request.get("query", "")
        k = request.get("k", 3)
        
        if not query:
            raise HTTPException(status_code=400, detail="Query không được để trống")
        
        # Retrieve documents
        docs = retrieve_documents(query, k=k)
        
        return {
            "success": True,
            "documents": docs,
            "document_count": len(docs),
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi RAG: {str(e)}"
        )


@app.get("/api/rag/status")
def rag_status():
    """
    Check RAG system status and available documents
    """
    try:
        from rag_system import get_rag_system
        vector_store, retriever = get_rag_system()
        
        if vector_store is None:
            return {
                "status": "initializing",
                "message": "Hệ thống RAG đang khởi tạo...",
                "document_count": 0,
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=None)
            }
        
        doc_count = vector_store._collection.count() if hasattr(vector_store, '_collection') else 0
        
        return {
            "status": "ready",
            "message": "Hệ thống RAG sẵn sàng",
            "document_count": doc_count,
            "vector_db": "ChromaDB",
            "embedding_model": "Google Generative AI",
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None)
        }


@app.post("/api/rag/reload")
def reload_rag_documents():
    """
    Reload RAG documents from disk (for development/testing)
    Useful when new documents are added to the documents folder
    """
    try:
        import importlib
        import rag_system
        importlib.reload(rag_system)
        
        # Reinitialize RAG system
        rag_system._vector_store = None
        rag_system._retriever = None
        rag_system.init_rag_system()
        
        return {
            "success": True,
            "message": "RAG documents reloaded successfully",
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi reload: {str(e)}"
        )
