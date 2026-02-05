# Database Migration Guide

## Overview
This project has been updated with a custom User model and comprehensive database schema. Follow these steps to apply the changes.

## ⚠️ Important Notes

1. **Custom User Model**: The project now uses a custom User model with `national_id` as the primary key and USERNAME_FIELD.
2. **Breaking Changes**: This is a major change that requires careful migration handling.
3. **Existing Data**: If you have existing data, you'll need to migrate it carefully or start fresh.

## Migration Steps

### Option 1: Fresh Start (Recommended for Development)

If you're in development and can start fresh:

```bash
# 1. Delete existing database and migrations
rm db.sqlite3
rm -rf teach/migrations/0*.py

# 2. Create new migrations
python manage.py makemigrations

# 3. Apply migrations
python manage.py migrate

# 4. Create superuser (optional)
python manage.py createsuperuser

# 5. Create Support account
python manage.py create_support_account
```

### Option 2: Preserve Existing Data (Advanced)

If you need to preserve existing data:

1. **Backup your database first!**
2. Create a data migration script to transfer existing users
3. Follow Django's custom user model migration guide

## Models Created/Updated

### ✅ Custom User Model
- Primary Key: `national_id` (CharField, unique)
- USERNAME_FIELD: `national_id`
- All required fields included (first_name, second_name, third_name, gender, etc.)
- No username field (removed completely)

### ✅ New Models
1. **UserCash** - Stores user balance separately
2. **Conversation** - Support chat conversations
3. **Message** - Chat messages
4. **CourseContent** - Content items within courses
5. **LessonProgress** - User lesson completion tracking
6. **Transaction** - Payment/enrollment transactions
7. **QuizQuestion, QuizOption, QuizResult** - Enhanced quiz system
8. **Lesson, LessonFile** - Lesson content and files

### ✅ Updated Models
1. **Course** - Added course_id, price, grade, division fields
2. **Enrollment** - Updated to use User.national_id, added status field
3. **Assignment** - Updated to reference CourseContent
4. **AssignmentSubmission** - Updated to use User.national_id

## Support Account

The Support account is created using the management command:
```bash
python manage.py create_support_account
```

**Support Account Details:**
- National ID: `SUPPORT_0001`
- Email: `support@teachsystem.com`
- Password: `1234`
- is_staff: `True`

## Admin Interface

All models are registered in Django Admin. Access at `/admin/` after creating a superuser.

## Authentication Changes

### Login
- Users now log in with their **National ID** (not username)
- The login form field is still named "username" but expects National ID
- Password authentication works the same way

### Code Login
- Still uses email to find users
- Works with the new User model

## Next Steps

1. **Apply migrations** (see steps above)
2. **Create Support account**: `python manage.py create_support_account`
3. **Test authentication** with National ID
4. **Update templates** if needed to reflect National ID instead of username
5. **Create test users** to verify functionality

## Troubleshooting

### Migration Errors
- If you get errors about existing User model, delete `db.sqlite3` and migrations
- Start fresh with `makemigrations` and `migrate`

### Authentication Issues
- Ensure `AUTH_USER_MODEL = 'teach.User'` is in settings.py
- Verify USERNAME_FIELD is set to 'national_id' in User model

### Import Errors
- Replace `from django.contrib.auth.models import User` with `from django.contrib.auth import get_user_model`
- Use `User = get_user_model()` in your code

## Model Relationships Summary

- **User** → OneToOne → **UserCash**
- **User** → ForeignKey → **Conversation** (user, support)
- **User** → ForeignKey → **Message** (sender, receiver)
- **User** → ForeignKey → **Enrollment** → ForeignKey → **Course**
- **Course** → ForeignKey → **CourseContent**
- **CourseContent** → ForeignKey → **Quiz, Lesson, Assignment**
- **User** → ForeignKey → **Transaction** → ForeignKey → **Course**

All foreign keys to User use `to_field='national_id'` for proper relationships.


