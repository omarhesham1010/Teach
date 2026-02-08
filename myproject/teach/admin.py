from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import (
    User,
    UserCash,
    LoginCode,
    Conversation,
    Message,
    Course,
    CourseContent,
    Enrollment,
    LessonProgress,
    Transaction,
    Assignment,
    AssignmentSubmission,
    Quiz,
    QuizQuestion,
    QuizOption,
    QuizResult,
    Lesson,
    LessonFile,
    Wallet,
)


# =========================
# Custom User Admin
# =========================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('national_id', 'email', 'first_name', 'second_name', 'gender', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active', 'gender', 'mode', 'created_at')
    search_fields = ('national_id', 'email', 'first_name', 'second_name', 'third_name', 'phone_number')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('national_id', 'email', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'second_name', 'third_name', 'gender', 'phone_number',
                      'father_phone_number', 'mother_phone_number')
        }),
        ('School Info', {
            'fields': ('school_name', 'parents_job', 'government', 'grade', 'division')
        }),
        ('Settings', {'fields': ('mode',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('national_id', 'email', 'password1', 'password2', 'first_name'),
        }),
    )
    
    readonly_fields = ('created_at', 'last_login')


# =========================
# User Cash Admin
# =========================
@admin.register(UserCash)
class UserCashAdmin(admin.ModelAdmin):
    list_display = ('user', 'cash_amount', 'get_user_email')
    list_filter = ('cash_amount',)
    search_fields = ('user__national_id', 'user__email', 'user__first_name')
    readonly_fields = ('user',)
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'


# =========================
# Login Code Admin
# =========================
@admin.register(LoginCode)
class LoginCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'is_used', 'created_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__national_id', 'user__email', 'code')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


# =========================
# Conversations Admin
# =========================
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'support', 'is_closed', 'last_message_at', 'created_at')
    list_filter = ('is_closed', 'created_at')
    search_fields = ('user__national_id', 'support__national_id', 'user__email')
    readonly_fields = ('created_at',)
    ordering = ('-last_message_at', '-created_at')


# =========================
# Messages Admin
# =========================
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'receiver', 'message_type', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read', 'created_at')
    search_fields = ('sender__national_id', 'receiver__national_id', 'message_body')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


# =========================
# Courses Admin
# =========================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'course_name', 'grade', 'division', 'price', 'is_active', 'created_at')
    list_filter = ('is_active', 'grade', 'division', 'created_at')
    search_fields = ('course_name', 'course_description')
    readonly_fields = ('course_id', 'created_at')
    ordering = ('-created_at',)


# =========================
# Course Content Admin
# =========================
@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    list_display = ('content_id', 'course', 'title', 'content_type', 'order_index', 'is_locked', 'created_at')
    list_filter = ('content_type', 'is_locked', 'course', 'created_at')
    search_fields = ('title', 'course__course_name')
    readonly_fields = ('content_id', 'created_at')
    ordering = ('course', 'order_index')


# =========================
# Enrollments Admin
# =========================
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status', 'enrolled_at')
    list_filter = ('status', 'enrolled_at', 'course')
    search_fields = ('user__national_id', 'user__email', 'course__course_name')
    readonly_fields = ('enrolled_at',)
    ordering = ('-enrolled_at',)


# =========================
# Lesson Progress Admin
# =========================
@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'completed_at')
    search_fields = ('user__national_id', 'user__email', 'lesson')
    readonly_fields = ('completed_at',)
    ordering = ('-completed_at',)


# =========================
# Transactions Admin
# =========================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'amount', 'transaction_type', 'created_at')
    list_filter = ('transaction_type', 'created_at', 'course')
    search_fields = ('user__national_id', 'user__email', 'course__course_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


# =========================
# Assignments Admin
# =========================
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('assignment_id', 'content', 'deadline', 'created_at')
    list_filter = ('deadline', 'created_at', 'content__course')
    search_fields = ('content__title', 'description')
    readonly_fields = ('assignment_id', 'created_at')
    ordering = ('-created_at',)


# =========================
# Assignment Submissions Admin
# =========================
@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'assignment', 'submitted_at')
    list_filter = ('submitted_at', 'assignment__content__course')
    search_fields = ('user__national_id', 'user__email', 'assignment__content__title')
    readonly_fields = ('submitted_at',)
    ordering = ('-submitted_at',)


# =========================
# Quizzes Admin
# =========================
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('quiz_id', 'content', 'time_limit', 'total_score', 'created_at')
    list_filter = ('created_at', 'content__course')
    search_fields = ('content__title',)
    readonly_fields = ('quiz_id', 'created_at')
    ordering = ('-created_at',)


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_id', 'quiz', 'question_text_short', 'correct_option')
    list_filter = ('quiz',)
    search_fields = ('question_text', 'quiz__content__title')
    readonly_fields = ('question_id',)
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question Text'


@admin.register(QuizOption)
class QuizOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'option_index', 'option_text_short')
    list_filter = ('question__quiz',)
    search_fields = ('option_text', 'question__question_text')
    
    def option_text_short(self, obj):
        return obj.option_text[:50] + '...' if len(obj.option_text) > 50 else obj.option_text
    option_text_short.short_description = 'Option Text'


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'quiz', 'score', 'submitted_at')
    list_filter = ('submitted_at', 'quiz__content__course')
    search_fields = ('user__national_id', 'user__email', 'quiz__content__title')
    readonly_fields = ('submitted_at',)
    ordering = ('-submitted_at',)


# =========================
# Lessons Admin
# =========================
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('lesson_id', 'content', 'has_video', 'created_at')
    list_filter = ('created_at', 'content__course')
    search_fields = ('content__title', 'lesson_body')
    readonly_fields = ('lesson_id', 'created_at')
    
    def has_video(self, obj):
        return bool(obj.video_url)
    has_video.boolean = True
    has_video.short_description = 'Has Video'


@admin.register(LessonFile)
class LessonFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'lesson', 'file_name', 'file_type')
    list_filter = ('file_type', 'lesson__content__course')
    search_fields = ('file_name', 'lesson__content__title')
    ordering = ('lesson', 'file_name')



@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "updated_at")
