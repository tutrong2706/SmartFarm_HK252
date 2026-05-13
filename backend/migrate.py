"""Chạy migration: tạo tất cả bảng từ models.py vào PostgreSQL."""
from database import engine, Base
import models  # Import models để đăng ký metadata

Base.metadata.create_all(bind=engine)
print("✅ Tất cả bảng đã được tạo thành công!")