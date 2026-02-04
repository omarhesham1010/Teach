from django.contrib import admin
from .models import (
    Profile,
    Course, Section, Lesson, LessonMaterial,
    Enrollment,
    Quiz, Question, Choice, QuizSubmission, QuizAnswer,
    Assignment, AssignmentSubmission
)

# =========================
# Profile
# =========================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone_number")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "phone")


# =========================
# Courses / Content
# =========================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title",)
    ordering = ("title",)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    ordering = ("course", "order")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "order", "is_published", "created_at")
    list_filter = ("is_published", "section__course")
    search_fields = ("title", "section__title", "section__course__title")
    ordering = ("section", "order")


@admin.register(LessonMaterial)
class LessonMaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "uploaded_at")
    list_filter = ("lesson__section__course",)
    search_fields = ("title", "lesson__title")


# =========================
# Enrollment
# =========================
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "enrolled_at", "is_active")
    list_filter = ("is_active", "course")
    search_fields = ("student__username", "student__email", "course__title")
    ordering = ("-enrolled_at",)


# =========================
# Quizzes
# =========================
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "is_published", "created_at")
    list_filter = ("is_published", "course")
    search_fields = ("title", "course__title")
    ordering = ("-created_at",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "points")
    list_filter = ("quiz",)
    search_fields = ("text", "quiz__title")


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct")
    list_filter = ("is_correct", "question__quiz")
    search_fields = ("text", "question__text")


@admin.register(QuizSubmission)
class QuizSubmissionAdmin(admin.ModelAdmin):
    list_display = ("student", "quiz", "score", "submitted_at")
    list_filter = ("quiz",)
    search_fields = ("student__username", "student__email", "quiz__title")
    ordering = ("-submitted_at",)


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ("submission", "question", "selected_choice")
    search_fields = ("submission__student__username", "question__text", "selected_choice__text")


# =========================
# Assignments
# =========================
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "due_date", "created_at")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    ordering = ("-created_at",)


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ("student", "assignment", "submitted_at", "grade")
    list_filter = ("assignment__course",)
    search_fields = ("student__username", "student__email", "assignment__title")
    ordering = ("-submitted_at",)


