# 🌱 SmartFarm HK252 - Hệ Thống Nông Trại Thông Minh

> **Nền tảng quản lý nông trại toàn diện** với khả năng theo dõi thời gian thực, tối ưu hóa cây trồng, và hỗ trợ quyết định thông qua AI chatbot.

---

## 📋 Mục Lục
1. [Tổng Quan Dự Án](#tổng-quan-dự-án)
2. [Các Tính Năng Chính](#các-tính-năng-chính)
3. [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
4. [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
5. [Hướng Dẫn Cài Đặt](#hướng-dẫn-cài-đặt)
6. [Tài Liệu API](#tài-liệu-api)
7. [Cấu Trúc Cơ Sở Dữ Liệu](#cấu-trúc-cơ-sở-dữ-liệu)
8. [Hướng Dẫn Sử Dụng](#hướng-dẫn-sử-dụng)
9. [Hệ Thống AI Chatbot](#hệ-thống-ai-chatbot)
10. [Bảo Mật](#bảo-mật)
11. [Khắc Phục Sự Cố](#khắc-phục-sự-cố)

---

## 🎯 Tổng Quan Dự Án

**SmartFarm HK252** là một giải pháp quản lý nông trại hiện đại, được xây dựng với:
- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Frontend**: React 18 + Vite + Material-UI v5
- **AI/ML**: OpenAI API, RAG (Retrieval-Augmented Generation), SQL Agent cho tương tác tự nhiên
- **Real-time**: WebSocket cho cập nhật dữ liệu cảm biến trực tiếp

Dự án cho phép nông dân và quản lý viên:
- 📊 Giám sát thời gian thực các điều kiện môi trường (nhiệt độ, độ ẩm, ánh sáng)
- 🤖 Hỏi đáp với AI chatbot để nhận lời khuyên nông nghiệp
- 📈 Tạo báo cáo chi tiết và lập kế hoạch canh tác
- ⚠️ Nhận cảnh báo khi các chỉ số vượt ngưỡng
- 🎛️ Tùy chỉnh bảng điều khiển với các widget dạng drag-and-drop

---

## ✨ Các Tính Năng Chính

### 1. **Quản Lý Khu Vực & Cây Trồng**
- Tạo/sửa/xóa các khu vực canh tác (zones)
- Cấu hình cài đặt tối ưu cho từng loại cây (nhiệt độ, độ ẩm, ánh sáng)
- Theo dõi trạng thái khu vực theo thời gian thực

### 2. **Quản Lý Thiết Bị IoT**
- Kết nối và quản lý các cảm biến và bộ điều khiển
- Xem trạng thái hoạt động của từng thiết bị
- Gán thiết bị cho các khu vực cụ thể
- Đồng bộ dữ liệu từ các gateway

### 3. **Thu Thập & Theo Dõi Dữ Liệu Telemetry**
- Ghi nhận dữ liệu cảm biến: nhiệt độ, độ ẩm, ánh sáng, độ ẩm đất, CO₂, v.v.
- Phân tích xu hướng dữ liệu theo thời gian
- Lịch sử đầy đủ của các số liệu trong từng khu vực
- API phân tích (Analytics) cho truy vấn dữ liệu nâng cao

### 4. **Hệ Thống Cảnh Báo & Nhật Ký**
- Cảnh báo tự động khi giá trị cảm biến vượt ngưỡng
- Phân loại cảnh báo theo mức độ (critical, warning, info)
- Ghi lại tất cả các sự kiện hệ thống
- Đánh dấu cảnh báo là đã đọc
- WebSocket cho cập nhật cảnh báo thời gian thực

### 5. **Bảng Điều Khiển Tùy Chỉnh (Dashboard)**
- Widgets drag-and-drop có thể sắp xếp
- Nhiều loại widget: biểu đồ, bảng dữ liệu, chỉ số chính, v.v.
- Lưu cấu hình widget per user
- Cải thiện trải nghiệm người dùng với giao diện Material-UI

### 6. **Tạo & Quản Lý Báo Cáo**
- Tạo báo cáo PDF chi tiết về sản xuất, sức khỏe cây trồng
- Lập lịch tự động tạo báo cáo theo định kỳ
- Xuất dữ liệu dưới dạng CSV
- Tải xuống báo cáo PDF với biểu đồ và thông tin chi tiết

### 7. **Xác Thực & Quản Lý Người Dùng**
- Đăng ký và đăng nhập với JWT tokens
- Bảo mật với bcrypt hashing cho mật khẩu
- OAuth2 password flow
- Token lưu trong localStorage (frontend)

### 8. **AI Chatbot Thông Minh**
- **Chat Interface**: Tương tác tự nhiên với bot
- **SQL Agent**: Tự động truy vấn cơ sở dữ liệu để trả lời câu hỏi về dữ liệu
- **RAG System**: Truy xuất tài liệu nông học để cung cấp lời khuyên chuyên môn
- **Session Management**: Lưu lịch sử chat per session
- Chi tiết xem [Hệ Thống AI Chatbot](#hệ-thống-ai-chatbot)

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────┐
│              Frontend (React + Vite)                │
│         ┌─────────────────────────────────┐         │
│         │  Login | Dashboard | Reports    │         │
│         │  Devices | Crops | Chat         │         │
│         └─────────────────┬───────────────┘         │
│                           │                          │
└───────────────────────────┼──────────────────────────┘
                            │ HTTP/WebSocket
┌───────────────────────────┼──────────────────────────┐
│              Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────┐   │
│  │  API Routes (Auth, Zones, Devices, Reports) │   │
│  │  Chat Engine | SQL Agent | RAG System       │   │
│  └──────────────────────────────────────────────┘   │
│                           │                          │
│         ┌─────────────────┴────────────────┐        │
│         │                                  │        │
│    ┌────▼────┐                      ┌─────▼─────┐   │
│    │PostgreSQL│                      │ OpenAI API│   │
│    │(Zones,   │                      │(GPT-4)    │   │
│    │Devices,  │                      └───────────┘   │
│    │Telemetry)│                                      │
│    └──────────┘                                      │
└─────────────────────────────────────────────────────┘
```

---

## 📦 Yêu Cầu Hệ Thống

### Backend
- **Python**: >= 3.10
- **PostgreSQL**: >= 12
- **OpenAI API Key**: Cho AI Chatbot (tùy chọn nhưng khuyến nghị)
- **Git**: Cho quản lý phiên bản

### Frontend
- **Node.js**: >= 18
- **npm** hoặc **yarn**: >= 9.x

### Biến Môi Trường Bắt Buộc
```
DATABASE_URL=postgresql://user:password@localhost:5432/smartfarm
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-...  # Cho AI chatbot
```

---

## 🚀 Hướng Dẫn Cài Đặt

### A. Chuẩn Bị Cơ Sở Dữ Liệu PostgreSQL

1. **Cài đặt PostgreSQL** (nếu chưa có):
   - Windows: Tải từ https://www.postgresql.org/download/windows/
   - Linux: `sudo apt-get install postgresql`
   - macOS: `brew install postgresql`

2. **Tạo database**:
   ```bash
   psql -U postgres
   CREATE DATABASE smartfarm;
   \q
   ```

3. **Ghi nhớ credentials**: `postgresql://postgres:password@localhost:5432/smartfarm`

### B. Cài Đặt & Chạy Backend

1. **Clone hoặc mở dự án**:
   ```bash
   cd backend
   ```

2. **Tạo virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Cài đặt dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Cấu hình biến môi trường**:
   - Tạo file `.env` trong thư mục `backend/`:
   ```
   DATABASE_URL=postgresql://postgres:password@localhost:5432/smartfarm
   SECRET_KEY=your-super-secret-key-change-this-in-production
   OPENAI_API_KEY=sk-your-api-key-here
   ```

5. **Chạy migration (tạo bảng)**:
   ```bash
   python migrate.py
   ```

6. **Khởi động server**:
   ```bash
   uvicorn main:app --reload
   ```
   - Server chạy tại: **http://localhost:8000**
   - Swagger UI: **http://localhost:8000/docs**
   - ReDoc: **http://localhost:8000/redoc**

7. **(Tùy chọn) Seed dữ liệu mẫu**:
   ```bash
   python seed.py
   ```

### C. Cài Đặt & Chạy Frontend

1. **Mở thư mục frontend**:
   ```bash
   cd ../frontend
   ```

2. **Cài đặt dependencies**:
   ```bash
   npm install
   ```

3. **Khởi động dev server**:
   ```bash
   npm run dev
   ```
   - Ứng dụng chạy tại: **http://localhost:5173**

4. **Build cho production** (nếu cần):
   ```bash
   npm run build
   npm run preview
   ```

---

## 📡 Tài Liệu API

### Cấu Trúc Chung Của Request/Response

**Request Header**:
```http
Content-Type: application/json
Authorization: Bearer <token>  # Bắt buộc với các endpoint protected
```

**Response Format**:
```json
{
  "id": 1,
  "created_at": "2026-05-27T10:30:00Z",
  ...
}
```

### 1. **Authentication (Xác Thực)**

#### Đăng Ký
```http
POST /api/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "Tên Người Dùng"
}

Response: 200 OK
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "Tên Người Dùng"
}
```

#### Đăng Nhập
```http
POST /api/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=secure_password

Response: 200 OK
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 2. **Quản Lý Khu Vực (Zones)**

#### Tạo Khu Vực
```http
POST /api/zones/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Vùng Cà Chua",
  "description": "Mô tả khu vực",
  "crop_setting_id": 1
}

Response: 201 Created
{
  "id": 1,
  "name": "Vùng Cà Chua",
  "description": "Mô tả khu vực",
  "crop_setting_id": 1,
  "created_at": "2026-05-27T10:30:00Z"
}
```

#### Lấy Danh Sách Khu Vực
```http
GET /api/zones/
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": 1,
    "name": "Vùng Cà Chua",
    "description": "Mô tả khu vực",
    "crop_setting_id": 1
  },
  ...
]
```

#### Xem Chi Tiết Khu Vực
```http
GET /api/zones/{zone_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "id": 1,
  "name": "Vùng Cà Chua",
  "description": "Mô tả khu vực",
  "crop_setting_id": 1,
  "devices": [
    {"id": 1, "name": "Sensor Nhiệt Độ", ...},
    ...
  ]
}
```

#### Cập Nhật Khu Vực
```http
PUT /api/zones/{zone_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Vùng Cà Chua - Cập Nhật",
  "crop_setting_id": 2
}

Response: 200 OK
{...}
```

#### Xóa Khu Vực
```http
DELETE /api/zones/{zone_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "id": 1,
  "name": "Vùng Cà Chua"
}
```

### 3. **Quản Lý Thiết Bị (Devices)**

#### Lấy Danh Sách Thiết Bị
```http
GET /api/devices/
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": 1,
    "name": "Sensor Nhiệt Độ",
    "zone_id": 1,
    "type_id": 1,
    "is_active": true,
    "pin_connector": "GPIO_17"
  },
  ...
]
```

#### Gán Thiết Bị Cho Khu Vực
```http
POST /api/zones/{zone_id}/devices/{device_id}
Authorization: Bearer <token>

Response: 201 Created
{
  "id": 1,
  "name": "Sensor Nhiệt Độ",
  "zone_id": 1,
  "type_id": 1,
  "is_active": true
}
```

#### Gỡ Thiết Bị Khỏi Khu Vực
```http
DELETE /api/zones/{zone_id}/devices/{device_id}
Authorization: Bearer <token>

Response: 200 OK
{...}
```

### 4. **Cấu Hình Cây Trồng (Crop Settings)**

#### Tạo Cấu Hình Cây Trồng
```http
POST /api/crop-settings/
Authorization: Bearer <token>
Content-Type: application/json

{
  "crop_name": "Cà Chua",
  "temp_min": 18,
  "temp_max": 28,
  "humid_min": 50,
  "humid_max": 80,
  "light_min": 200,
  "light_max": 500,
  "light_type": "LED",
  "auto_mode": true
}

Response: 201 Created
{...}
```

#### Lấy Danh Sách Cây Trồng
```http
GET /api/crop-settings/
Authorization: Bearer <token>

Response: 200 OK
[{...}]
```

#### Xem Chi Tiết Cây Trồng
```http
GET /api/crop-settings/{crop_id}
Authorization: Bearer <token>

Response: 200 OK
{...}
```

#### Cập Nhật Cây Trồng
```http
PUT /api/crop-settings/{crop_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "temp_max": 30
}

Response: 200 OK
{...}
```

#### Xóa Cây Trồng
```http
DELETE /api/crop-settings/{crop_id}
Authorization: Bearer <token>

Response: 204 No Content
```

### 5. **Telemetry - Dữ Liệu Cảm Biến**

#### Gửi Dữ Liệu Telemetry
```http
POST /api/telemetry
Authorization: Bearer <token>
Content-Type: application/json

{
  "zone_id": 1,
  "device_id": 1,
  "temperature": 25.5,
  "humidity": 65,
  "light_intensity": 350,
  "soil_moisture": 70
}

Response: 201 Created
{
  "id": 1,
  "zone_id": 1,
  "device_id": 1,
  "temperature": 25.5,
  "humidity": 65,
  "created_at": "2026-05-27T10:30:00Z"
}
```

#### Lấy Tóm Tắt Telemetry
```http
GET /api/telemetry/summary
Authorization: Bearer <token>

Response: 200 OK
{
  "zone_1": {
    "latest_temperature": 25.5,
    "latest_humidity": 65,
    "avg_temperature_24h": 24.8,
    ...
  }
}
```

#### Lịch Sử Telemetry
```http
GET /api/telemetry/history?zone_id=1&limit=50&offset=0
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": 1,
    "zone_id": 1,
    "temperature": 25.5,
    "humidity": 65,
    "created_at": "2026-05-27T10:30:00Z"
  },
  ...
]
```

#### Analytics / Phân Tích Dữ Liệu
```http
GET /api/telemetry/analytics?zone_id=1&metric=temperature&days=7
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "timestamp": "2026-05-27T00:00:00Z",
    "value": 25.5,
    "min": 20.0,
    "max": 28.0,
    "avg": 24.5
  },
  ...
]
```

#### WebSocket - Telemetry Real-time
```javascript
// Frontend (JavaScript)
const ws = new WebSocket('ws://localhost:8000/ws/telemetry');

ws.onopen = () => {
  console.log('Connected to telemetry stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Telemetry update:', data);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

### 6. **Alert Logs - Cảnh Báo & Nhật Ký**

#### Lấy Danh Sách Cảnh Báo
```http
GET /api/logs/?page=1&limit=20&severity=warning
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": 1,
    "title": "Nhiệt độ quá cao",
    "message": "Nhiệt độ vùng 1 đã vượt 30°C",
    "severity": "warning",
    "zone_id": 1,
    "is_read": false,
    "created_at": "2026-05-27T10:30:00Z"
  },
  ...
]
```

#### Tạo Cảnh Báo
```http
POST /api/logs/
Authorization: Bearer <token>
Content-Type: application/json

{
  "log_type": "sensor",
  "severity": "critical",
  "title": "Sensor Lỗi",
  "message": "Sensor nhiệt độ trong zone 1 mất kết nối",
  "zone_id": 1,
  "metric_key": "temperature",
  "metric_value": null
}

Response: 201 Created
{...}
```

#### Đánh Dấu Cảnh Báo Là Đã Đọc
```http
POST /api/logs/read-all
Authorization: Bearer <token>

Response: 200 OK
{
  "updated": 5
}
```

#### Xóa Cảnh Báo
```http
DELETE /api/logs/{log_id}
Authorization: Bearer <token>

Response: 204 No Content
```

### 7. **Dashboard Widgets - Bảng Điều Khiển**

#### Lấy Danh Sách Widget
```http
GET /api/dashboard/widgets
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": 1,
    "title": "Biểu Đồ Nhiệt Độ",
    "widget_type": "line_chart",
    "position": 0,
    "config": {
      "zone_id": 1,
      "metric": "temperature"
    }
  },
  ...
]
```

#### Tạo Widget
```http
POST /api/dashboard/widgets
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Biểu Đồ Nhiệt Độ",
  "widget_type": "line_chart",
  "position": 0,
  "config": {
    "zone_id": 1,
    "metric": "temperature",
    "days": 7
  }
}

Response: 201 Created
{...}
```

#### Cập Nhật Widget
```http
PUT /api/dashboard/widgets/{widget_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Biểu Đồ Nhiệt Độ - Cập Nhật",
  "position": 1
}

Response: 200 OK
{...}
```

#### Xóa Widget
```http
DELETE /api/dashboard/widgets/{widget_id}
Authorization: Bearer <token>

Response: 204 No Content
```

#### Sắp Xếp Lại Widget
```http
POST /api/dashboard/widgets/reorder
Authorization: Bearer <token>
Content-Type: application/json

{
  "widget_ids": [1, 3, 2, 4]
}

Response: 200 OK
{
  "reordered": [1, 3, 2, 4]
}
```

### 8. **Reports - Báo Cáo**

#### Tạo Báo Cáo
```http
POST /api/reports/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Báo Cáo Tháng 5",
  "description": "Báo cáo chi tiết hoạt động tháng 5",
  "zone_id": 1,
  "date_from": "2026-05-01",
  "date_to": "2026-05-31",
  "include_charts": true,
  "include_telemetry": true
}

Response: 201 Created
{
  "id": "report_123_abc",
  "title": "Báo Cáo Tháng 5",
  "status": "generating",
  "created_at": "2026-05-27T10:30:00Z"
}
```

#### Lấy Danh Sách Báo Cáo
```http
GET /api/reports/?page=1&limit=10
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": "report_123_abc",
    "title": "Báo Cáo Tháng 5",
    "file_path": "/reports/report_123_abc.pdf",
    "created_at": "2026-05-27T10:30:00Z",
    "status": "completed"
  },
  ...
]
```

#### Tải Báo Cáo PDF
```http
GET /api/reports/{report_id}/download
Authorization: Bearer <token>

Response: 200 OK
[Binary PDF Content]
Content-Type: application/pdf
Content-Disposition: attachment; filename="report.pdf"
```

#### Lập Lịch Báo Cáo Tự Động
```http
POST /api/reports/schedule
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Báo Cáo Hàng Tuần",
  "zone_id": 1,
  "schedule": "weekly",  # daily, weekly, monthly
  "day_of_week": "monday",
  "time": "09:00"
}

Response: 201 Created
{...}
```

### 9. **Chat AI - Chatbot Thông Minh**

#### Gửi Tin Nhắn Chat
```http
POST /api/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Cà chua của tôi bị bệnh gì? Cây ở vùng 1 có số liệu gì?",
  "session_id": "user_123_session_1"
}

Response: 200 OK
{
  "response": "Dựa trên dữ liệu của bạn trong vùng 1...",
  "type": "text",
  "sources": ["database", "rag_documents"],
  "session_id": "user_123_session_1"
}
```

#### Xóa Lịch Sử Chat
```http
DELETE /api/chat/history/{session_id}
Authorization: Bearer <token>

Response: 204 No Content
```

#### Kiểm Tra Trạng Thái Chatbot
```http
GET /api/chat/health

Response: 200 OK
{
  "status": "healthy",
  "openai_api": "connected",
  "rag_system": "ready",
  "sql_agent": "ready"
}
```

#### Truy Vấn SQL Trực Tiếp
```http
POST /api/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "question": "Có bao nhiêu khu vực và thiết bị trong hệ thống?"
}

Response: 200 OK
{
  "answer": "Hệ thống có 3 khu vực và 12 thiết bị.",
  "query": "SELECT COUNT(DISTINCT zone_id) as zones, COUNT(*) as devices FROM devices;",
  "results": [
    {"zones": 3, "devices": 12}
  ]
}
```

#### Lấy Schema Cơ Sở Dữ Liệu
```http
GET /api/query/schema
Authorization: Bearer <token>

Response: 200 OK
{
  "tables": {
    "zones": {
      "columns": ["id", "name", "description", "crop_setting_id", ...]
    },
    "devices": {
      "columns": ["id", "name", "zone_id", "type_id", "is_active", ...]
    },
    ...
  }
}
```

#### Truy Xuất Tài Liệu RAG
```http
POST /api/rag/retrieve
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "Làm thế nào để ngăn chặn bệnh phấn trắng trên cà chua?",
  "k": 3
}

Response: 200 OK
{
  "documents": [
    {
      "source": "tomato_cultivation.txt",
      "content": "Bệnh phấn trắng là...",
      "relevance_score": 0.95
    },
    ...
  ]
}
```

#### Kiểm Tra Trạng Thái RAG
```http
GET /api/rag/status

Response: 200 OK
{
  "status": "ready",
  "total_documents": 3,
  "documents": [
    "cucumber_cultivation.txt",
    "lettuce_cultivation.txt",
    "tomato_cultivation.txt"
  ]
}
```

---

## 🗄️ Cấu Trúc Cơ Sở Dữ Liệu

### Sơ Đồ ER (Entity-Relationship)

```
┌──────────────────┐
│      User        │
├──────────────────┤
│ id (PK)          │
│ email (UQ)       │
│ password_hash    │
│ full_name        │
│ created_at       │
└──────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  CropSetting     │◄────────│      Zone        │
├──────────────────┤         ├──────────────────┤
│ id (PK)          │         │ id (PK)          │
│ crop_name        │         │ name             │
│ temp_min         │         │ description      │
│ temp_max         │         │ crop_setting_id  │
│ humid_min        │         │ (FK)             │
│ humid_max        │         │ created_at       │
│ light_min        │         └──────────────────┘
│ light_max        │                  │
│ auto_mode        │                  │
└──────────────────┘                  │ 1:N
                                      │
                         ┌────────────┴──────────────┐
                         │                           │
                    ┌────▼──────────┐      ┌────────▼─────┐
                    │    Device     │      │  AlertLog    │
                    ├───────────────┤      ├──────────────┤
                    │ id (PK)       │      │ id (PK)      │
                    │ name          │      │ log_type     │
                    │ zone_id (FK)  │      │ severity     │
                    │ type_id (FK)  │      │ zone_id (FK) │
                    │ is_active     │      │ device_id(FK)│
                    │ pin_connector │      │ title        │
                    └───────┬────────┘      │ message      │
                            │              │ is_read      │
                   ┌────────┴──────────┐   │ created_at   │
                   │                   │   └──────────────┘
            ┌──────▼─────┐      ┌──────▼────────┐
            │ DeviceType  │      │   Telemetry  │
            ├─────────────┤      ├───────────────┤
            │ id (PK)     │      │ id (PK)       │
            │ name        │      │ zone_id (FK)  │
            │ category    │      │ device_id(FK) │
            └─────────────┘      │ temperature   │
                                 │ humidity      │
                                 │ light_intens. │
                                 │ soil_moisture │
                                 │ created_at    │
                                 └───────────────┘

┌────────────────────┐    ┌──────────────────────┐
│ DashboardWidget    │    │  Report              │
├────────────────────┤    ├──────────────────────┤
│ id (PK)            │    │ id (PK)              │
│ user_id (FK)       │    │ title                │
│ title              │    │ file_path            │
│ widget_type        │    │ generated_by(FK-User)│
│ position           │    │ zone_id (FK)         │
│ config (JSON)      │    │ date_from            │
│ created_at         │    │ date_to              │
└────────────────────┘    │ created_at           │
                          │ status               │
                          └──────────────────────┘
```

### Mô Tả Chi Tiết Các Bảng

#### 1. **users**
Lưu trữ thông tin người dùng hệ thống
```sql
id INT PRIMARY KEY
email VARCHAR UNIQUE NOT NULL
password_hash VARCHAR NOT NULL
full_name VARCHAR
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### 2. **crop_settings**
Cài đặt tối ưu cho từng loại cây trồng
```sql
id INT PRIMARY KEY
crop_name VARCHAR NOT NULL
temp_min FLOAT
temp_max FLOAT
humid_min FLOAT
humid_max FLOAT
light_min FLOAT
light_max FLOAT
light_type VARCHAR  -- 'LED', 'Natural', 'Mixed', etc.
auto_mode BOOLEAN DEFAULT FALSE
```

#### 3. **zones**
Đại diện cho một khu vực canh tác trong nông trại
```sql
id INT PRIMARY KEY
name VARCHAR NOT NULL
description TEXT
crop_setting_id INT FOREIGN KEY
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### 4. **device_types**
Loại thiết bị có sẵn
```sql
id INT PRIMARY KEY
name VARCHAR  -- 'Temperature Sensor', 'Humidity Sensor', etc.
category VARCHAR  -- 'sensor', 'actuator', 'controller', etc.
```

#### 5. **devices**
Thiết bị IoT vật lý kết nối với hệ thống
```sql
id INT PRIMARY KEY
name VARCHAR NOT NULL
zone_id INT FOREIGN KEY
type_id INT FOREIGN KEY
is_active BOOLEAN DEFAULT FALSE
pin_connector VARCHAR  -- 'GPIO_17', 'I2C_0x48', etc.
```

#### 6. **telemetry**
Dữ liệu cảm biến ghi nhận theo thời gian thực
```sql
id INT PRIMARY KEY
zone_id INT FOREIGN KEY
device_id INT FOREIGN KEY
temperature FLOAT
humidity FLOAT
light_intensity FLOAT
soil_moisture FLOAT
co2_level FLOAT
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### 7. **alert_logs**
Nhật ký cảnh báo hệ thống
```sql
id INT PRIMARY KEY
log_type VARCHAR  -- 'sensor', 'system', 'user_action', etc.
severity VARCHAR  -- 'critical', 'warning', 'info'
zone_id INT FOREIGN KEY (nullable)
device_id INT FOREIGN KEY (nullable)
title VARCHAR NOT NULL
message TEXT NOT NULL
is_read BOOLEAN DEFAULT FALSE
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### 8. **dashboard_widgets**
Widgets trên bảng điều khiển người dùng
```sql
id INT PRIMARY KEY
user_id INT FOREIGN KEY
title VARCHAR NOT NULL
widget_type VARCHAR  -- 'line_chart', 'gauge', 'table', etc.
position INT  -- Order on dashboard
config JSON  -- Widget configuration (zone_id, metric, etc.)
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### 9. **reports**
Báo cáo được tạo
```sql
id VARCHAR PRIMARY KEY  -- 'report_10_ec43ef46'
title VARCHAR NOT NULL
file_path VARCHAR  -- '/reports/report_10_ec43ef46.pdf'
generated_by INT FOREIGN KEY (User)
zone_id INT FOREIGN KEY (nullable)
status VARCHAR  -- 'generating', 'completed', 'failed'
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

---

## 📖 Hướng Dẫn Sử Dụng

### 1. **Đăng Ký & Đăng Nhập**

1. Truy cập **http://localhost:5173**
2. Nếu chưa có tài khoản, click "Đăng Ký" và điền thông tin
3. Nhập email và mật khẩu để đăng nhập
4. Token sẽ được lưu vào localStorage tự động

### 2. **Tạo & Quản Lý Khu Vực**

1. Trên Dashboard, chọn **"Quản Lý Khu Vực"**
2. Click **"Thêm Khu Vực Mới"**
3. Điền tên, mô tả, và chọn loại cây trồng
4. Click **"Lưu"** để tạo

**Để cập nhật khu vực:**
- Click biểu tượng **Edit** trên card khu vực
- Chỉnh sửa các trường cần thiết
- Click **"Cập Nhật"**

**Để xóa khu vực:**
- Click biểu tượng **Trash** trên card
- Xác nhận xóa

### 3. **Quản Lý Thiết Bị**

1. Chọn **"Quản Lý Thiết Bị"**
2. Xem danh sách tất cả thiết bị
3. Để gán thiết bị cho khu vực:
   - Click **"Gán Khu Vực"**
   - Chọn khu vực từ dropdown
   - Click **"Lưu"**

### 4. **Cấu Hình Cây Trồng**

1. Chọn **"Cài Đặt Cây Trồng"**
2. Click **"Thêm Cây Trồng Mới"** hoặc chọn loại có sẵn
3. Nhập các giá trị tối ưu:
   - Khoảng nhiệt độ (°C)
   - Khoảng độ ẩm (%)
   - Yêu cầu ánh sáng (lux)
   - Loại ánh sáng (LED, Natural, Mixed)
4. Bật/tắt **"Chế độ Tự Động"** nếu cần

### 5. **Xem Dữ Liệu Cảm Biến (Telemetry)**

**Trên Dashboard:**
- Các widget hiển thị dữ liệu thời gian thực
- Hover chuột lên biểu đồ để xem chi tiết

**Lịch Sử Chi Tiết:**
1. Chọn **"Dữ Liệu Cảm Biến"** → **"Lịch Sử"**
2. Chọn khu vực và ngày tháng
3. Xem bảng dữ liệu chi tiết

**Phân Tích:**
1. Chọn **"Dữ Liệu Cảm Biến"** → **"Phân Tích"**
2. Chọn chỉ số để phân tích (nhiệt độ, độ ẩm, v.v.)
3. Xem biểu đồ xu hướng 7 ngày, 30 ngày

### 6. **Tạo Báo Cáo**

1. Chọn **"Báo Cáo"** → **"Tạo Báo Cáo Mới"**
2. Điền các thông tin:
   - Tiêu đề báo cáo
   - Chọn khu vực
   - Chọn khoảng ngày
   - Chọn những gì cần bao gồm (biểu đồ, dữ liệu, v.v.)
3. Click **"Tạo Báo Cáo"** → chờ hoàn tất
4. Click **"Tải Xuống"** để lấy file PDF

**Lập Lịch Báo Cáo Tự Động:**
1. Chọn **"Báo Cáo"** → **"Lập Lịch"**
2. Điền thông tin:
   - Tiêu đề
   - Tần suất (Hàng ngày, Hàng tuần, Hàng tháng)
   - Thời gian tạo
3. Click **"Lưu Lịch"**

### 7. **Sử Dụng Chatbot AI**

1. Chọn **"Chat AI"** trên sidebar
2. Gõ câu hỏi của bạn, ví dụ:
   - "Cà chua của tôi bị bệnh gì?"
   - "Có bao nhiêu khu vực trong hệ thống?"
   - "Tôi nên tăng độ ẩm lên bao nhiêu?"
3. Bot sẽ:
   - Tự động truy vấn cơ sở dữ liệu để lấy thông tin
   - Tìm kiếm tài liệu nông học liên quan
   - Cung cấp câu trả lời toàn diện

### 8. **Tùy Chỉnh Dashboard**

1. Trên Dashboard, click **"Chỉnh Sửa"**
2. Kéo thả các widget để sắp xếp lại vị trí
3. Click biểu tượng **"+"** để thêm widget mới
4. Click biểu tượng **"X"** để xóa widget
5. Click **"Lưu Bố Cục"** khi hoàn tất

---

## 🤖 Hệ Thống AI Chatbot

### Tổng Quan

SmartFarm tích hợp một AI chatbot thông minh có 3 bộ phận chính:

1. **Chat Interface** - Giao diện chat thân thiện
2. **SQL Agent** - Truy vấn cơ sở dữ liệu tự động
3. **RAG System** - Truy xuất tài liệu nông học

### Kiến Trúc Chi Tiết

```
┌─────────────────────────────────┐
│    Frontend: ChatBot.jsx         │
│  (Chat UI, message display)      │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│    Backend: /api/chat            │
├─────────────────────────────────┤
│ 1. Nhận message từ user          │
│ 2. Tự động nhận dạng loại truy vấn│
│ 3. Gọi SQL Agent hoặc RAG nếu cần│
│ 4. Gộp kết quả lại              │
│ 5. Gửi response tới frontend    │
└──────────────┬──────────────────┘
               │
        ┌──────┴─────────┐
        │                │
   ┌────▼─────┐     ┌────▼─────────┐
   │SQL Agent │     │ RAG System    │
   │(Query DB)│     │(Documents)    │
   └──────────┘     └───────────────┘
        │                │
        ▼                ▼
   ┌──────────┐    ┌──────────────────┐
   │PostgreSQL│    │Vector Database   │
   │(Zones,   │    │(Chroma.sqlite3)  │
   │Devices,  │    │Embeddings)       │
   │Telemetry)│    │                  │
   └──────────┘    │ Docs:            │
                   │ - tomato.txt     │
                   │ - cucumber.txt   │
                   │ - lettuce.txt    │
                   └──────────────────┘
```

### Cách Sử Dụng Chat

#### Ví Dụ 1: Truy Vấn Dữ Liệu (SQL Agent)
```
User: "Có bao nhiêu khu vực trong hệ thống?"

Bot Response:
- Tự động tạo SQL query: SELECT COUNT(*) FROM zones
- Trả về: "Hệ thống có 3 khu vực: Vùng Cà Chua, Vùng Rau Muống, Vùng Dưa Lưới"
```

#### Ví Dụ 2: Lời Khuyên Nông Học (RAG)
```
User: "Làm thế nào để ngăn chặn bệnh phấn trắng trên cà chua?"

Bot Response:
- Tìm kiếm tài liệu liên quan
- Trích xuất thông tin từ: cucumber_cultivation.txt
- Trả về: "Bệnh phấn trắng có thể được ngăn chặn bằng... [chi tiết từ tài liệu]"
```

#### Ví Dụ 3: Phân Tích Dữ Liệu + Lời Khuyên
```
User: "Cà chua trong vùng 1 cần gì?"

Bot Response:
- SQL: Lấy dữ liệu về vùng 1 (nhiệt độ hiện tại, độ ẩm, cây trồng)
- RAG: Tìm kiếm yêu cầu tối ưu cho cà chua
- Trả về: "Vùng 1 hiện tại: 26°C, 65% độ ẩm. Cà chua cần... [khuyến nghị]"
```

### File & Thư Mục Liên Quan

```
backend/
├── chatbot.py          # Chat interface & history management
├── sql_agent.py        # SQL query generation & execution
├── rag_system.py       # Document retrieval & embedding
├── ai_config.py        # OpenAI API configuration
├── data/
│   └── agricultural_docs/  # Tài liệu nông học
│       ├── tomato_cultivation.txt
│       ├── cucumber_cultivation.txt
│       └── lettuce_cultivation.txt
└── main.py             # Chat API endpoints
```

### API Endpoints Liên Quan

| Endpoint | Method | Mô Tả |
|----------|--------|-------|
| `/api/chat` | POST | Gửi tin nhắn và nhận response |
| `/api/chat/health` | GET | Kiểm tra trạng thái chatbot |
| `/api/chat/history/{session_id}` | DELETE | Xóa lịch sử chat |
| `/api/query` | POST | Truy vấn SQL trực tiếp |
| `/api/query/schema` | GET | Lấy schema cơ sở dữ liệu |
| `/api/rag/retrieve` | POST | Tìm kiếm tài liệu |
| `/api/rag/status` | GET | Trạng thái RAG system |

### Cấu Hình OpenAI API

1. **Lấy API Key**:
   - Truy cập https://platform.openai.com/api-keys
   - Tạo key mới
   - Copy key

2. **Thiết lập trong `.env`**:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

3. **Kiểm tra Kết Nối**:
   ```bash
   # Chạy lệnh test
   curl http://localhost:8000/api/chat/health
   
   # Response
   {
     "status": "healthy",
     "openai_api": "connected",
     "rag_system": "ready"
   }
   ```

### Test Chatbot

#### Với cURL
```bash
# Test câu hỏi đơn giản
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Xin chào!",
    "session_id": "default"
  }'

# Test truy vấn dữ liệu
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Có bao nhiêu khu vực?",
    "session_id": "default"
  }'

# Test lời khuyên nông học
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Làm thế nào để chăm sóc cà chua?",
    "session_id": "default"
  }'
```

#### Với Python
```python
import requests
import json

BASE_URL = "http://localhost:8000"

def chat(message, session_id="default"):
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "message": message,
            "session_id": session_id
        }
    )
    return response.json()

# Test
result = chat("Cà chua cần bao nhiêu độ ẩm?")
print(result['response'])
```

#### Chạy Test Suite
```bash
cd backend

# Test chatbot
python test_chatbot.py

# Test SQL Agent
python test_sql_agent.py

# Test RAG system
python test_rag.py

# Hoặc chạy tất cả
pytest tests/ -v
```

---

## 🔒 Bảo Mật

### Mật Khẩu
- ✅ Hashing với **bcrypt** (salt rounds: 12)
- ✅ Never store plain text passwords
- ✅ Password validation on registration

### Authentication
- ✅ **JWT (JSON Web Tokens)** cho API authorization
- ✅ Token trong `Authorization: Bearer <token>` header
- ✅ Token expiry: 7 ngày (cấu hình trong code)

### CORS
- ✅ Enabled cho `http://localhost:5173` (frontend)
- ⚠️ Cập nhật cho domain production

### Environment Variables
```env
# NEVER commit these!
SECRET_KEY=your-super-secret-key-min-32-chars
DATABASE_URL=postgresql://user:password@localhost:5432/smartfarm
OPENAI_API_KEY=sk-...
```

### Các Thực Hành Tốt Nhất
1. **Never expose SECRET_KEY** - Tạo key ngẫu nhiên trên production
2. **Use HTTPS** - Trên production, luôn dùng HTTPS
3. **SQL Injection Prevention** - SQLAlchemy ORM đã bảo vệ
4. **CORS Validation** - Chỉ allow trusted domains
5. **Rate Limiting** - Xem xét thêm rate limiting cho API
6. **Input Validation** - Pydantic schemas đã validate

---

## 🐛 Khắc Phục Sự Cố

### Backend Không Chạy

#### ❌ Lỗi: `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Giải pháp
source venv/bin/activate  # Hoặc: venv\Scripts\activate
pip install -r requirements.txt
```

#### ❌ Lỗi: `SQLALCHEMY_DATABASE_URL is not set`
```bash
# Giải pháp
# Tạo file .env trong thư mục backend/
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/smartfarm" > .env
```

#### ❌ Lỗi: `Connection refused (Postgres)`
```bash
# Kiểm tra Postgres đang chạy
# Windows
pg_isready -h localhost -p 5432

# Linux/macOS
sudo service postgresql status
# hoặc
brew services list | grep postgres
```

#### ❌ Lỗi: `OPENAI_API_KEY not found`
```bash
# Giải pháp
# Thêm vào .env
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

### Frontend Không Chạy

#### ❌ Lỗi: `npm: command not found`
```bash
# Cài đặt Node.js từ https://nodejs.org/
# Hoặc với package manager:
# macOS
brew install node

# Linux
sudo apt-get install nodejs npm
```

#### ❌ Lỗi: `npm ERR! peer dep missing`
```bash
# Giải pháp
npm install --legacy-peer-deps
```

#### ❌ Port 5173 đã được sử dụng
```bash
# Chạy trên port khác
npm run dev -- --port 5174
```

### API Không Phản Hồi

#### ❌ CORS Error: `Access to XMLHttpRequest from origin blocked`
```bash
# Giải pháp: Backend cần cấu hình CORS
# File: backend/main.py
# Kiểm tra:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### ❌ 401 Unauthorized
```bash
# Giải pháp: Token hết hạn hoặc không được gửi
# Đăng nhập lại để lấy token mới
# Kiểm tra localStorage:
localStorage.getItem('token')  # Phải có giá trị
```

#### ❌ 404 Not Found trên endpoint nào đó
```bash
# Kiểm tra Swagger docs
curl http://localhost:8000/docs
# Tìm đúng endpoint path
```

### Chat AI Không Hoạt Động

#### ❌ `OpenAI API key invalid`
```bash
# Giải pháp
# 1. Kiểm tra key có đúng không
# 2. Kiểm tra key không hết hạn
# 3. Kiểm tra key có đủ credits không
# 4. Cập nhật .env và restart server
```

#### ❌ `RAG system not ready`
```bash
# Giải pháp
# 1. Kiểm tra tài liệu trong: backend/data/agricultural_docs/
# 2. Reload documents:
curl -X POST http://localhost:8000/api/rag/reload

# 3. Kiểm tra status:
curl http://localhost:8000/api/rag/status
```

### Database Không Đồng Bộ

#### ❌ Bảng không tồn tại
```bash
# Giải pháp: Chạy migration
cd backend
python migrate.py

# Hoặc xóa DB và tạo lại
# PostgreSQL:
dropdb smartfarm
createdb smartfarm
python migrate.py
```

#### ❌ Dữ liệu cũ hoặc sai lệch
```bash
# Giải pháp: Reset và seed lại
cd backend
python reset_devices.py  # Reset thiết bị
python seed.py           # Seed dữ liệu mẫu
```

---

## 📚 Tài Liệu Bổ Sung

- [COMPLETE_AI_CHATBOT_GUIDE.md](COMPLETE_AI_CHATBOT_GUIDE.md) - Hướng dẫn chi tiết về chatbot
- [PROJECT_COMPLETION_REPORT.md](PROJECT_COMPLETION_REPORT.md) - Báo cáo hoàn thành dự án
- [CHAT_HISTORY_GUIDE.md](CHAT_HISTORY_GUIDE.md) - Hướng dẫn chat history
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Tham chiếu nhanh
