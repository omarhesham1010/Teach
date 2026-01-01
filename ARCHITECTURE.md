# Django Backend Architecture

## System Overview
This is a standard specialized Django backend designed for an online teaching platform. It serves as the API and Admin interface for the platform.

### Core Apps
- **`accounts`**: Custom User model (`User`) with role-based access control (`ADMIN`, `INSTRUCTOR`, `STUDENT`).
- **`courses`**: Manages `Course`, `Lesson`, `Video` content structure.
- **`exams`**: (Placeholder) Will manage quizzes/exams linked to courses.
- **`payments`**: (Placeholder) Will manage transactions and subscriptions.

### Data Flow
1.  **Admin Panel**: The internal CMS. Admin/Instructors log in here to create courses, upload videos, and manage users.
    -   *Flow*: Admin User -> Django Admin -> PostgreSQL Database.
2.  **API (Future React Frontend)**: The frontend will consume data via REST API (Django Rest Framework).
    -   *Flow*: Student -> React App -> Django API -> PostgreSQL Database.

### Database Schema Key Points
-   **User**: Central entity. `role` field determines permission (e.g., only `INSTRUCTOR` role can own a Course).
-   **Course**: Linked to `User` (Instructor) via ForeignKey.
    -   *Constraint*: `limit_choices_to={'role': 'INSTRUCTOR'}` enforces that only Instructors can be assigned to courses.
-   **Media**:
    -   **Development**: Local filesystem storage (configured in `local.py`).
    -   **Production**: Cloudinary (configured in `base.py`).

## Deployment (Render)
-   **Build Command**: `sh build.sh` (Migrates DB, Creates Superuser, Collects Static).
-   **Start Command**: `gunicorn config.wsgi:application`
-   **Database**: Managed PostgreSQL on Render.
-   **Static Files**: Served via `Whitenoise` with compression.
