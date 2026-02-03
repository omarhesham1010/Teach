# 🧑‍🎓 Teach Management System

A web-based clinic management system built with **Django** to manage patients, appointments, and clinic operations.

---

## 📌 Project Requirements

Before running the project, make sure you have the following installed:

### 🔹 1. Python
- Python **3.10 or higher**
- Download from: https://www.python.org/downloads/

Check Python version:
```bash
python --version
```

---

### 🔹 2. Virtual Environment (venv)
Used to isolate project dependencies.

---

### 🔹 3. Django
- Django **5.2.10**

---

## ⚙️ Project Setup & Installation

### 1️⃣ Download or Clone the Project
```bash
git clone <repository-url>
```
Or download the ZIP file and extract it.

---

### 2️⃣ Go to Project Directory
```bash
cd DEnt-Clinic
```

---

### 3️⃣ Create Virtual Environment
```bash
python -m venv venv
```

Activate the virtual environment:

**Windows**
```bash
venv\Scripts\activate
```

**Mac / Linux**
```bash
source venv/bin/activate
```

---

### 4️⃣ Install Dependencies
```bash
pip install django
```

Verify Django installation:
```bash
python -m django --version
```

---

## 🗄️ Database Setup

Run migrations to set up the database:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 👤 Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

Enter username, email, and password when prompted.

---

## ▶️ Run the Development Server
```bash
python manage.py runserver
```

Open your browser and visit:
```
http://127.0.0.1:8000/
```

Admin panel:
```
http://127.0.0.1:8000/admin
```

---

## 📂 Project Structure
```
DEnt-Clinic/
│
├── manage.py
├── myproject/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── clinic/
│   ├── models.py
│   ├── views.py
│   ├── admin.py
│   └── migrations/
│
└── venv/
```

---

## 🚨 Notes
- This project uses Django’s development server.
- Do not use it in production without proper deployment setup.
- Always activate the virtual environment before running commands.

---

## 👨‍💻 Author
Developed by **Team : Omar - Mahmoud - Noureen**  
Faculty of Computer Science & Information 
MSA University

---

## 📜 License
This project is created for educational purposes only. 
## test2