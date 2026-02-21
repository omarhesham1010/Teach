"""
Management command to create a sample quiz with questions and options.
Run with: python manage.py create_sample_quiz
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from teach.models import Course, CourseContent, Quiz, QuizQuestion, QuizOption

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a sample quiz with questions and options for testing'

    def handle(self, *args, **options):
        # Check if sample quiz already exists
        existing_quiz = Quiz.objects.filter(content__title__icontains="Sample Quiz").first()
        if existing_quiz:
            self.stdout.write(
                self.style.WARNING('Sample quiz already exists. Skipping creation.')
            )
            return

        # Create or get a sample course
        course, created = Course.objects.get_or_create(
            course_name="Sample Course",
            defaults={
                'course_description': 'A sample course for testing quizzes',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created course: {course.course_name}'))

        # Create course content (Quiz type)
        content, created = CourseContent.objects.get_or_create(
            course=course,
            title="Sample Quiz - Introduction to Web Development",
            content_type='quiz',
            defaults={'order_index': 1}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created content: {content.title}'))

        # Create quiz
        quiz = Quiz.objects.create(
            content=content,
            time_limit=15,  # 15 minutes
            total_score=100,
            max_attempts=3,  # Allow 3 attempts
        )
        self.stdout.write(self.style.SUCCESS(f'Created quiz: Quiz {quiz.quiz_id}'))

        # Question 1
        q1 = QuizQuestion.objects.create(
            quiz=quiz,
            question_text="What does HTML stand for?",
            correct_option=1,  # Option 1 is correct
        )
        QuizOption.objects.create(question=q1, option_text="Hypertext Markup Language", option_index=1)
        QuizOption.objects.create(question=q1, option_text="High Tech Modern Language", option_index=2)
        QuizOption.objects.create(question=q1, option_text="Home Tool Markup Language", option_index=3)
        QuizOption.objects.create(question=q1, option_text="Hyperlink and Text Markup Language", option_index=4)
        self.stdout.write('  Created Question 1')

        # Question 2
        q2 = QuizQuestion.objects.create(
            quiz=quiz,
            question_text="Which CSS property is used to change the text color?",
            correct_option=1,
        )
        QuizOption.objects.create(question=q2, option_text="color", option_index=1)
        QuizOption.objects.create(question=q2, option_text="text-color", option_index=2)
        QuizOption.objects.create(question=q2, option_text="font-color", option_index=3)
        QuizOption.objects.create(question=q2, option_text="text-style", option_index=4)
        self.stdout.write('  Created Question 2')

        # Question 3
        q3 = QuizQuestion.objects.create(
            quiz=quiz,
            question_text="What is the correct way to declare a JavaScript variable?",
            correct_option=3,  # Option 3 (let x = 5;) is correct
        )
        QuizOption.objects.create(question=q3, option_text="variable x = 5;", option_index=1)
        QuizOption.objects.create(question=q3, option_text="v x = 5;", option_index=2)
        QuizOption.objects.create(question=q3, option_text="let x = 5;", option_index=3)
        QuizOption.objects.create(question=q3, option_text="x := 5;", option_index=4)
        self.stdout.write('  Created Question 3')

        # Question 4
        q4 = QuizQuestion.objects.create(
            quiz=quiz,
            question_text="Which HTTP method is used to send data to a server?",
            correct_option=2,  # Option 2 (POST) is correct
        )
        QuizOption.objects.create(question=q4, option_text="GET", option_index=1)
        QuizOption.objects.create(question=q4, option_text="POST", option_index=2)
        QuizOption.objects.create(question=q4, option_text="PUT", option_index=3)
        QuizOption.objects.create(question=q4, option_text="DELETE", option_index=4)
        self.stdout.write('  Created Question 4')

        # Question 5
        q5 = QuizQuestion.objects.create(
            quiz=quiz,
            question_text="What does CSS stand for?",
            correct_option=1,
        )
        QuizOption.objects.create(question=q5, option_text="Cascading Style Sheets", option_index=1)
        QuizOption.objects.create(question=q5, option_text="Computer Style Sheets", option_index=2)
        QuizOption.objects.create(question=q5, option_text="Creative Style Sheets", option_index=3)
        QuizOption.objects.create(question=q5, option_text="Colorful Style Sheets", option_index=4)
        self.stdout.write('  Created Question 5')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully created sample quiz!\n'
                f'  Quiz ID: {quiz.quiz_id}\n'
                f'  Title: {content.title}\n'
                f'  Questions: 5\n'
                f'  Time Limit: {quiz.time_limit} minutes\n'
                f'\nAccess it at: /quiz/{quiz.quiz_id}/'
            )
        )
