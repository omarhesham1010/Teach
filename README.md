# Teach Platform Backend

## Prerequisites
- Python 3.11+
- PostgreSQL
- Git

## Setup Instructions

### 1. Clone & Environment
```bash
git clone <repo_url>
cd Teach
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Setup
Ensure PostgreSQL is running and create the database:
```sql
CREATE DATABASE teach_db;
```
*(Or use pgAdmin / `createdb teach_db` if in PATH)*

### 3. Configuration
Copy the example environment file:
```bash
copy .env.example .env
```
Edit `.env` if you have different DB credentials.

### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Run Server
```bash
python manage.py runserver
```

## Project Structure
- `config/`: Project settings & entry points (base, local, production).
- `accounts/`: Custom User model & roles.
- `courses/`: Course, Lesson, Video models.
- `exams/`: Exam logic (skeleton).
