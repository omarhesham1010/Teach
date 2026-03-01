from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.conf import settings


# =========================
# Custom User Manager
# =========================
class CustomUserManager(BaseUserManager):
    def create_user(self, national_id, email, password=None, **extra_fields):
        if not national_id:
            raise ValueError('The National ID must be set')
        if not email:
            raise ValueError('The Email must be set')
        
        email = self.normalize_email(email)
        user = self.model(national_id=national_id, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, national_id, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(national_id, email, password, **extra_fields)


# =========================
# Custom User Model
# =========================
class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    MODE_CHOICES = [
        ('Dark', 'Dark'),
        ('Light', 'Light'),
    ]

    GOVERNMENT_CHOICES = [
        ('Cairo', 'Cairo'),
        ('Alexandria', 'Alexandria'),
        ('Giza', 'Giza'),
        ('Shubra El Kheima', 'Shubra El Kheima'),
        ('Port Said', 'Port Said'),
        ('Suez', 'Suez'),
        ('Luxor', 'Luxor'),
        ('Aswan', 'Aswan'),
        ('Ismailia', 'Ismailia'),
        ('Faiyum', 'Faiyum'),
        ('Zagazig', 'Zagazig'),
        ('Damietta', 'Damietta'),
        ('Asyut', 'Asyut'),
        ('Minya', 'Minya'),
        ('Beni Suef', 'Beni Suef'),
        ('Qena', 'Qena'),
        ('Sohag', 'Sohag'),
        ('Hurghada', 'Hurghada'),
        ('Mansoura', 'Mansoura'),
        ('Tanta', 'Tanta'),
        ('Other', 'Other'),
    ]

    GRADE_CHOICES = [
        ('1', 'Grade 1'),
        ('2', 'Grade 2'),
        ('3', 'Grade 3'),
        ('4', 'Grade 4'),
        ('5', 'Grade 5'),
        ('6', 'Grade 6'),
        ('7', 'Grade 7'),
        ('8', 'Grade 8'),
        ('9', 'Grade 9'),
        ('10', 'Grade 10'),
        ('11', 'Grade 11'),
        ('12', 'Grade 12'),
    ]

    DIVISION_CHOICES = [
        ('Science', 'Science'),
        ('Mathematics', 'Mathematics'),
        ('Literature', 'Literature'),
    ]

    # Primary Key
    national_id = models.CharField(max_length=20, unique=True, primary_key=True)
    
    # Name fields
    first_name = models.CharField(max_length=50)
    second_name = models.CharField(max_length=50, blank=True, default='')
    third_name = models.CharField(max_length=50, blank=True, default='')
    
    # Personal info
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, default='')
    
    # Contact
    phone_number = models.CharField(max_length=20, blank=True, default='')
    father_phone_number = models.CharField(max_length=20, blank=True, default='')
    # mother_phone_number = models.CharField(max_length=20, blank=True, default='')
    
    # School info
    school_name = models.CharField(max_length=120, blank=True, default='')
    parents_job = models.CharField(max_length=120, blank=True, default='')
    government = models.CharField(max_length=50, choices=GOVERNMENT_CHOICES, blank=True, default='')
    grade = models.CharField(max_length=10, choices=GRADE_CHOICES, blank=True, default='')
    division = models.CharField(max_length=20, choices=DIVISION_CHOICES, blank=True, default='')
    
    # Authentication
    email = models.EmailField(unique=True)
    # Password is handled by AbstractBaseUser
    
    # Settings
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='Light')
    
    # Permissions
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Manager
    objects = CustomUserManager()
    
    # Use national_id as username field
    USERNAME_FIELD = 'national_id'
    REQUIRED_FIELDS = ['email', 'first_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.first_name} ({self.national_id})"

    def get_full_name(self):
        return f"{self.first_name} {self.second_name} {self.third_name}".strip()

    def get_short_name(self):
        return self.first_name


# =========================
# User Cash (Security Separation)
# =========================
class UserCash(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cash',
        to_field='national_id'
    )
    cash_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    class Meta:
        verbose_name = 'User Cash'
        verbose_name_plural = 'User Cash'

    def __str__(self):
        return f"{self.user.national_id} - {self.cash_amount}"


# =========================
# Login Code
# =========================
class LoginCode(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="login_codes",
        to_field='national_id'
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self, minutes=10):
        return timezone.now() > (self.created_at + timezone.timedelta(minutes=minutes))

    def __str__(self):
        return f"{self.user.national_id} - {self.code}"


# =========================
# Conversations (Support Chat)
# =========================
class Conversation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_conversations',
        to_field='national_id'
    )
    support = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='support_conversations',
        to_field='national_id',
        null=True,
        blank=True
    )
    last_message = models.TextField(blank=True, default='')
    last_message_at = models.DateTimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_message_at', '-created_at']

    def __str__(self):
        return f"Conversation {self.id} - {self.user.national_id}"


# =========================
# Messages
# =========================
class Message(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        to_field='national_id'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages',
        to_field='national_id'
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    message_body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message {self.id} - {self.sender.national_id} to {self.receiver.national_id}"


# =========================
# Courses
# =========================
class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=200)
    course_description = models.TextField(blank=True, default='')
    course_image = models.ImageField(
        upload_to='courses/images/',
        blank=True,
        null=True
    )
    
    GRADE_CHOICES = [
        ('1', 'Grade 1'), ('2', 'Grade 2'), ('3', 'Grade 3'),
        ('4', 'Grade 4'), ('5', 'Grade 5'), ('6', 'Grade 6'),
        ('7', 'Grade 7'), ('8', 'Grade 8'), ('9', 'Grade 9'),
        ('10', 'Grade 10'), ('11', 'Grade 11'), ('12', 'Grade 12'),
    ]
    
    DIVISION_CHOICES = [
        ('Science', 'Science'),
        ('Mathematics', 'Mathematics'),
        ('Literature', 'Literature'),
        ('General', 'General'),
    ]

    grade = models.CharField(max_length=10, choices=GRADE_CHOICES, blank=True, default='')
    division = models.CharField(max_length=20, choices=DIVISION_CHOICES, blank=True, default='')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def title(self):
        return self.course_name

    def __str__(self):
        return self.course_name


# =========================
# Course Content
# =========================
class CourseContent(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('lesson', 'Lesson'),
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
    ]

    content_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='contents',
        to_field='course_id'
    )
    title = models.CharField(max_length=200)
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES
    )
    order_index = models.PositiveIntegerField(default=1)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order_index', 'created_at']
        unique_together = ['course', 'order_index']

    def __str__(self):
        return f"{self.course.course_name} - {self.title}"


# =========================
# Enrollments
# =========================
class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
        to_field='national_id'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        to_field='course_id'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.national_id} enrolled in {self.course.course_name}"


# =========================
# Lesson Progress
# =========================
class LessonProgress(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        to_field='national_id'
    )
    lesson = models.CharField(max_length=200)  # Can be lesson_id or lesson identifier
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson')
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.user.national_id} - {self.lesson}"


# =========================
# Transactions
# =========================
class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('enroll', 'Enroll'),
        ('purchase', 'Purchase'),
        ('refund', 'Refund'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        to_field='national_id'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='transactions',
        to_field='course_id'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='enroll'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.national_id} - {self.transaction_type} - {self.amount}"


# =========================
# Assignments
# =========================
class Assignment(models.Model):
    assignment_id = models.AutoField(primary_key=True)
    content = models.ForeignKey(
        CourseContent,
        on_delete=models.CASCADE,
        related_name='assignments',
        to_field='content_id'
    )
    description = models.TextField()
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Assignment {self.assignment_id} - {self.content.title}"


# =========================
# Assignment Submissions
# =========================
class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        to_field='assignment_id'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignment_submissions',
        to_field='national_id'
    )
    answer_text = models.TextField(blank=True, default='')
    file_path = models.FileField(
        upload_to='assignments/submissions/',
        blank=True,
        null=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('assignment', 'user')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.national_id} - Assignment {self.assignment.assignment_id}"


# =========================
# Quizzes
# =========================
class Quiz(models.Model):
    quiz_id = models.AutoField(primary_key=True)
    content = models.ForeignKey(
        CourseContent,
        on_delete=models.CASCADE,
        related_name='quizzes',
        to_field='content_id'
    )
    time_limit = models.PositiveIntegerField(help_text='Time limit in minutes', default=30)
    total_score = models.PositiveIntegerField(default=100)
    max_attempts = models.PositiveIntegerField(help_text='Maximum number of attempts allowed', default=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Quiz {self.quiz_id} - {self.content.title}"


class QuizQuestion(models.Model):
    question_id = models.AutoField(primary_key=True)
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        to_field='quiz_id'
    )
    question_text = models.TextField()
    correct_option = models.PositiveIntegerField(help_text='Index of correct option (1-based)')

    class Meta:
        ordering = ['question_id']

    def __str__(self):
        return f"Question {self.question_id} - {self.question_text[:50]}"


class QuizOption(models.Model):
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='options',
        to_field='question_id'
    )
    option_text = models.CharField(max_length=500)
    option_index = models.PositiveIntegerField(help_text='Option index (1-based)')

    class Meta:
        unique_together = ('question', 'option_index')
        ordering = ['option_index']

    def __str__(self):
        return f"Option {self.option_index} - {self.option_text[:50]}"


class QuizResult(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_results',
        to_field='national_id'
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='results',
        to_field='quiz_id'
    )
    attempt_number = models.PositiveIntegerField(default=1)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'quiz', 'attempt_number')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user.national_id} - Quiz {self.quiz.quiz_id} - Score: {self.score}"


# =========================
# Lessons
# =========================
class Lesson(models.Model):
    lesson_id = models.AutoField(primary_key=True)
    content = models.ForeignKey(
        CourseContent,
        on_delete=models.CASCADE,
        related_name='lessons',
        to_field='content_id'
    )

    
    raw_content = models.TextField(blank=True, default='')

    video_embed_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Lesson {self.lesson_id} - {self.content.title}"



class LessonFile(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('doc', 'DOC'),
        ('docx', 'DOCX'),
        ('ppt', 'PPT'),
        ('pptx', 'PPTX'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('other', 'Other'),
    ]

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='files',
        to_field='lesson_id'
    )
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='lessons/files/')
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        default='other'
    )

    class Meta:
        ordering = ['file_name']

    def __str__(self):
        return f"{self.lesson.content.title} - {self.file_name}"




class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet"
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.balance} EGP"

