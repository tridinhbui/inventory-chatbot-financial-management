# 🚀 Hướng Dẫn Chạy App

## Cách 1: Script Tự Động (Khuyến nghị)

```bash
./start_simple.sh
```

## Cách 2: Chạy Thủ Công

### Bước 1: Tạo Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Bước 2: Cài Đặt Dependencies
```bash
pip install fastapi uvicorn[standard] psycopg2-binary python-dotenv pandas numpy pyodbc pydantic
```

### Bước 3: Chạy Backend (Terminal 1)
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Bước 4: Chạy Frontend (Terminal 2)
```bash
cd frontend
python -m http.server 8080
```

## 📍 Truy Cập

- **Frontend Dashboard**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## ⚠️ Lưu Ý

1. **Database Connection**: 
   - App sẽ chạy nhưng cần database để hiển thị data
   - Có thể test với sample data hoặc mock data

2. **Port Conflicts**:
   - Nếu port 8000 hoặc 8080 đã được sử dụng:
   ```bash
   lsof -ti:8000 | xargs kill -9
   lsof -ti:8080 | xargs kill -9
   ```

3. **Dependencies Issues**:
   - Nếu gặp lỗi cài đặt, dùng virtual environment
   - Hoặc: `pip install --user -r requirements.txt`

## 🐛 Troubleshooting

**Lỗi: ModuleNotFoundError**
```bash
# Đảm bảo đã activate virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

**Lỗi: Port already in use**
```bash
# Kill processes trên port
lsof -ti:8000 | xargs kill -9
lsof -ti:8080 | xargs kill -9
```

**Lỗi: Database connection**
- App vẫn chạy được nhưng không có data
- Có thể test với mock data hoặc sample data generator

## ✅ Kiểm Tra App Đã Chạy

```bash
# Check backend
curl http://localhost:8000/health

# Check frontend
curl http://localhost:8080

# Check processes
ps aux | grep uvicorn
ps aux | grep http.server
```

