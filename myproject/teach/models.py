from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# =========================
# Login Code
# =========================
class LoginCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_codes")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self, minutes=10):
        return timezone.now() > (self.created_at + timezone.timedelta(minutes=minutes))

    def __str__(self):
        return f"{self.user.username} - {self.code}"


# =========================
# Profile
# =========================
class Profile(models.Model):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("instructor", "Instructor"),
        ("admin", "Admin"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")

    # Personal Info
    second_name = models.CharField(max_length=50, blank=True, default="")
    third_name = models.CharField(max_length=50, blank=True, default="")
    gender = models.CharField(max_length=10, blank=True, default="")

    # Contact
    phone_number = models.CharField(max_length=20, blank=True, default="")
    father_phone_number = models.CharField(max_length=20, blank=True, default="")
    mother_phone_number = models.CharField(max_length=20, blank=True, default="")
    gmail = models.EmailField(blank=True, default="")

    # School Info
    school_name = models.CharField(max_length=120, blank=True, default="")
    parents_job = models.CharField(max_length=120, blank=True, default="")
    government = models.CharField(max_length=120, blank=True, default="")
    grade = models.CharField(max_length=50, blank=True, default="")
    division = models.CharField(max_length=20, blank=True, default="")

    # National ID
    national_id = models.CharField(max_length=20, blank=True, default="")

    def __str__(self):
        return f"{self.user.username} ({self.role})"


    @property
    def phone(self):
        return self.phone_number

    @phone.setter
    def phone(self, value):
        self.phone_number = value


# =========================
# Courses
# =========================
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    thumbnail = models.ImageField(upload_to="courses/thumbnails/", blank=True, null=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Section(models.Model):
    course = models.ForeignKey(Course, related_name="sections", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    section = models.ForeignKey(Section, related_name="lessons", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    content = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=1)

    video_url = models.URLField(blank=True, default="")
    video_file = models.FileField(upload_to="lessons/videos/", blank=True, null=True)

    duration_minutes = models.PositiveIntegerField(blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.section.title} - {self.title}"


class LessonMaterial(models.Model):
    lesson = models.ForeignKey(Lesson, related_name="materials", on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True, default="")
    file = models.FileField(upload_to="lessons/materials/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or self.file.name


# =========================
# Enrollment
# =========================
class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("student", "course")

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"


# =========================
# Quiz System
# =========================
class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=500)
    points = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.text[:50]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class QuizSubmission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_submissions")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="submissions")
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0)

    class Meta:
        unique_together = ("student", "quiz")

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"


class QuizAnswer(models.Model):
    submission = models.ForeignKey(QuizSubmission, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ("submission", "question")


# =========================
# Assignments
# =========================
class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True, default="")
    due_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assignment_submissions")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")

    file = models.FileField(upload_to="assignments/submissions/", blank=True, null=True)
    text_answer = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(auto_now_add=True)

    grade = models.FloatField(blank=True, null=True)
    feedback = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("student", "assignment")

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

