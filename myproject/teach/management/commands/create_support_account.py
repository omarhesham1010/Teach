"""
Management command to create the Support account.
Run with: python manage.py create_support_account
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates the Support account with National ID: SUPPORT_0001'

    def handle(self, *args, **options):
        national_id = 'SUPPORT_0001'
        email = 'support@teachsystem.com'
        password = '1234'

        # Check if support account already exists
        if User.objects.filter(national_id=national_id).exists():
            self.stdout.write(
                self.style.WARNING(f'Support account with National ID {national_id} already exists.')
            )
            return

        # Create support account
        try:
            support_user = User.objects.create_user(
                national_id=national_id,
                email=email,
                password=password,
                first_name='Support',
                is_staff=True,
                is_active=True,
            )
            
            # Create UserCash for support account
            from teach.models import UserCash
            UserCash.objects.get_or_create(
                user=support_user,
                defaults={'cash_amount': 0.00}
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created Support account:\n'
                    f'  National ID: {national_id}\n'
                    f'  Email: {email}\n'
                    f'  Password: {password}\n'
                    f'  is_staff: True'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating Support account: {str(e)}')
            )


