# 🎓 Smart Student Analytics System

A full-stack Student Analytics System developed using **Flask**, **MySQL**, and **Chart.js** to simplify student management, attendance tracking, teacher management, and academic analytics.

## 🌐 Live Demo

🔗 **Live Application:** https://ssas-iaxa.onrender.com

---

## 📌 Features

### 👨‍💼 Admin Module

- Secure Admin Login
- Dashboard with KPI Cards
- Student Management (Add, Update, Delete)
- Teacher Management
- Department Management
- Attendance Analytics
- Academic Performance Analytics
- Student Performance Leaderboard
- At-Risk Student Identification
- Interactive Charts & Reports

### 👨‍🏫 Teacher Module

- Secure Teacher Login
- Personal Dashboard
- Profile Management
- Change Password
- View Department Students
- Mark Student Attendance
- Department-wise Analytics
- Attendance Statistics
- Semester Distribution
- Top Student Performance

---

## 📊 Dashboard Analytics

- Student Count
- Teacher Count
- Department Count
- Average Attendance
- Average CGPA
- Department Distribution
- Semester Distribution
- Gender Distribution
- Attendance Analysis
- Performance Distribution
- Top Performing Students
- At-Risk Students

---

## 🛠️ Tech Stack

### Backend

- Python
- Flask
- SQLAlchemy

### Frontend

- HTML5
- CSS3
- JavaScript
- Jinja2
- Chart.js

### Database

- MySQL
- Aiven Cloud MySQL

### Deployment

- Render
- GitHub

---

## 📁 Project Structure

```
Student_Analytics_System/
│
├── database/
├── models/
├── routes/
├── services/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│
├── config.py
├── app.py
├── requirements.txt
├── README.md
└── .env
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

### Move into Project

```bash
cd Student_Analytics_System
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file.

```env
SECRET_KEY=your_secret_key

DB_HOST=your_host
DB_PORT=your_port
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=student_analytics
```

### Run Application

```bash
python app.py
```

---

## 📈 Database

Cloud database is hosted using **Aiven MySQL**.

The application uses SQLAlchemy ORM for database operations.

---

## 🔒 Security Features

- Password Authentication
- Session Management
- Environment Variables
- Cloud Database Connection
- SQLAlchemy ORM Protection

## 🚀 Future Enhancements

- Student Login Module
- Marks Management
- Result Generation
- PDF Report Generation
- Email Notifications
- AI-based Student Performance Prediction
- Export Reports to Excel and PDF
- Role-based Access Control
- Mobile Responsive Dashboard

---

## 👨‍💻 Developed By

**Krishna Rajoo**

BTech CSE-DS

---

## 📄 License

This project is developed for educational purposes
