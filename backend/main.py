from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
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
    access_token = auth.create_access_token(data={"sub": user.username, "role": user.role})
    
    return {"access_token": access_token, "token_type": "bearer"}