import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from accounts.models import User
from courses.models import Course, Lesson

def run():
    print("Creating users...")
    # Instructor
    instructor, created = User.objects.get_or_create(username='instructor1', email='inst@test.com')
    instructor.set_password('pass1234')
    instructor.role = 'INSTRUCTOR'
    instructor.save()
    if created: print("Created instructor1")

    # Student
    student, created = User.objects.get_or_create(username='student1', email='stu@test.com')
    student.set_password('pass1234')
    student.role = 'STUDENT'
    student.save()
    if created: print("Created student1")

    print("Creating course...")
    course, created = Course.objects.get_or_create(
        title='Intro to API Design',
        defaults={
            'description': 'Learn how to design APIs.',
            'instructor': instructor,
            'price': 19.99
        }
    )
    if created: print(f"Created course: {course.title}")
    
    print("Done.")

if __name__ == '__main__':
    run()
