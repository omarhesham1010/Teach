from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
import os

class Command(BaseCommand):
    help = 'Debugs the active storage configuration in production.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(f"\n--- DEBUGGING STORAGE SETTINGS ---"))
        
        # 1. Environment Variables Check
        cloudinary_url = os.environ.get('CLOUDINARY_URL')
        self.stdout.write(f"CLOUDINARY_URL in Env: {'FOUND' if cloudinary_url else 'MISSING'}")
        
        # 2. Django Settings Check
        self.stdout.write(f"settings.DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
        self.stdout.write(f"settings.DEBUG: {settings.DEBUG}")
        
        # 3. Cloudinary Storage Config
        cloud_conf = getattr(settings, 'CLOUDINARY_STORAGE', None)
        if cloud_conf:
            self.stdout.write(f"CLOUDINARY_STORAGE: Found with keys {list(cloud_conf.keys())}")
        else:
            self.stdout.write(self.style.ERROR("CLOUDINARY_STORAGE: NOT FOUND or Empty"))

        # 4. Actual Storage Instance Check
        storage_class_name = default_storage.__class__.__name__
        storage_module = default_storage.__class__.__module__
        
        self.stdout.write(self.style.SUCCESS(f"\nACTIVE STORAGE ENGINE: {storage_module}.{storage_class_name}"))
        
        if 'FileSystemStorage' in storage_class_name:
             self.stdout.write(self.style.ERROR("FAIL: Still using Local File System! Check settings logic."))
        elif 'Cloudinary' in storage_class_name:
             self.stdout.write(self.style.SUCCESS("PASS: Using Cloudinary Storage."))
