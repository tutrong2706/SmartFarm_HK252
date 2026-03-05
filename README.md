# SmartFarm HK252

Hệ thống nông trại thông minh gồm **FastAPI + PostgreSQL** backend và **React + Vite + MUI** frontend.

## Kiến trúc thư mục
- `backend/`: FastAPI, SQLAlchemy, JWT, CRUD Zones, Auth ([backend/main.py](backend/main.py))
- `frontend/`: React + Vite UI, login/Dashboard ([frontend/package.json](frontend/package.json))

## Yêu cầu môi trường
- Python >= 3.10, Node.js >= 18
- PostgreSQL với DB url đã cấu hình trong [backend/database.py](backend/database.py) (`SQLALCHEMY_DATABASE_URL`)

## Cài đặt & chạy Backend
1) Tạo venv và cài gói:
```sh
cd backend
python -m venv venv
venv/Scripts/activate  # hoặc source venv/bin/activate
pip install -r requirements.txt
```
2) Khởi động server:
```sh
uvicorn main:app --reload
```
3) Swagger UI: `http://localhost:8000/docs`

## Cài đặt & chạy Frontend
```sh
cd frontend
npm install
npm run dev
```
Ứng dụng chạy tại `http://localhost:5173`.

## Luồng đăng nhập/đăng ký
- Đăng ký: `POST /api/register`
- Đăng nhập (OAuth2 form): `POST /api/login` → nhận `access_token`, lưu vào `localStorage` (được dùng bởi ProtectedRoute trong Dashboard).

## CRUD Khu vực (Zones)
- `POST /api/zones/` tạo khu vực
- `GET /api/zones/` lấy danh sách
- `GET /api/zones/{id}` xem chi tiết
- `PUT /api/zones/{id}` cập nhật
- `DELETE /api/zones/{id}` xóa

## Ghi chú bảo mật
- Đặt biến `SECRET_KEY` và DB URL vào biến môi trường/.env (thay cho giá trị hardcode trong code).
