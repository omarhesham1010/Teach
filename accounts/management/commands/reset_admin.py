from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Resets admin access for a specific user safely.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = "omar_h"
        # Use environment variable for safety, fallback to a temp password if absolutely needed
        new_password = os.environ.get("ADMIN_RESET_PASSWORD", "TemporaryPass123!")

        try:
            user = User.objects.get(username=username)
            self.stdout.write(f"Found user: {username}")
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"User {username} not found. Creating..."))
            user = User(username=username)

        # Update credentials and permissions
        user.set_password(new_password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        
        # Ensure role is set to ADMIN (specific to your project)
        if hasattr(user, 'role'):
            user.role = 'ADMIN'

        user.save()
        
        self.stdout.write(self.style.SUCCESS(
            f"Successfully reset access for '{username}'.\n"
            f"Password: {new_password}\n"
            f"Status: is_staff=True, is_superuser=True, role='ADMIN'\n"
            f"IMPORTANT: Change this password immediately after logging in!"
        ))
