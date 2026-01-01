import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course

def inspect_data():
    User = get_user_model()
    print("--- User Role Inspection ---")
    users = User.objects.all()
    if not users.exists():
        print("No users found.")
    
    for u in users:
        print(f"User: '{u.username}' (ID: {u.id}) | Role: '{u.role}' | IsActive: {u.is_active}")
        if u.role == 'INSTRUCTOR':
            print(f"   -> MATCH: Should appear in dropdown.")
        else:
            print(f"   -> MISMATCH: '{u.role}' != 'INSTRUCTOR'")

    print("\n--- Course Configuration Inspection ---")
    print(f"Course.instructor.field.limit_choices_to: {Course.instructor.field.limit_choices_to}")
    print(f"Course.instructor.field.remote_field.model: {Course.instructor.field.remote_field.model}")

if __name__ == "__main__":
    inspect_data()
