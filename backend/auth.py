from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

# Cấu hình khóa bí mật cho JWT (Lấy từ .env file)
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_change_this_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Token sống trong 60 phút

# Cấu hình thuật toán băm mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. Hàm băm mật khẩu
def get_password_hash(password):
    return pwd_context.hash(password)

# 2. Hàm kiểm tra mật khẩu
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 3. Hàm tạo JWT Token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt