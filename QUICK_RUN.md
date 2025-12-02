# Quick Start Guide - Run the Application

## 🚀 Cách Chạy App

### Option 1: Python Script (Recommended)
```bash
python3 run_app.py
```

### Option 2: Bash Script
```bash
./run_app.sh
```

### Option 3: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python3 -m http.server 8080
```

## 📍 Access Points

- **Frontend Dashboard**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 Interview Preparation

### Xem Project Description
```bash
python3 project_description.py
```

### Đọc Interview Q&A
```bash
cat INTERVIEW_QUESTIONS.md
```

### Các File Quan Trọng
- `project_description.py` - Script mô tả toàn bộ dự án
- `INTERVIEW_QUESTIONS.md` - Câu hỏi và câu trả lời interview
- `README.md` - Tài liệu đầy đủ
- `FEATURES.md` - Chi tiết các tính năng

## 🔧 Setup Lần Đầu

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Setup Database:**
```bash
# Setup Redshift
python3 scripts/setup_database.py

# Generate sample data (optional)
python3 scripts/generate_sample_data.py
```

3. **Run ETL (optional):**
```bash
python3 etl/pipeline.py
```

4. **Start App:**
```bash
python3 run_app.py
```

## 💡 Tips

- Sử dụng User ID: 1 (nếu đã có sample data)
- Check API docs tại `/docs` để xem tất cả endpoints
- Frontend tự động mở browser khi start
- Press Ctrl+C để stop tất cả services

## 🐛 Troubleshooting

**Port đã được sử dụng:**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 8080
lsof -ti:8080 | xargs kill -9
```

**Missing dependencies:**
```bash
pip install -r requirements.txt
```

**Database connection error:**
- Check `.env` file
- Verify database credentials
- Ensure databases are accessible

