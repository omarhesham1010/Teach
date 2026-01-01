import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model

def fix_data():
    User = get_user_model()
    username = 'omar'
    try:
        u = User.objects.get(username=username)
        print(f"Found User: '{u.username}' | Current Role: '{u.role}'")
        
        if u.role != 'INSTRUCTOR':
            print("Updating role to 'INSTRUCTOR'...")
            u.role = 'INSTRUCTOR'
            u.save()
            print("SUCCESS: Role updated.")
        else:
            print("Role is already correct.")
            
    except User.DoesNotExist:
        print(f"User '{username}' not found.")

if __name__ == "__main__":
    fix_data()
