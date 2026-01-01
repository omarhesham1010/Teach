from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.STUDENT)

    def __str__(self):
        return f"{self.username} ({self.role})"
