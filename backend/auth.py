import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer

# Load biến môi trường từ file .env
load_dotenv()

# Cấu hình khóa bí mật cho JWT (Lấy từ .env file)
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_change_this_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Token sống trong 60 phút

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# Khởi tạo bộ băm mật khẩu mới thay thế cho passlib
password_hash = PasswordHash((Argon2Hasher(),))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

# 3. Hàm tạo JWT Token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 4. Hàm giải mã JWT Token
def decode_token(token: str):
    """Decode and verify JWT token, return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")