from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Course, Lesson, Video, Enrollment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'price', 'created_at')
    list_filter = ('created_at', 'instructor')
    search_fields = ('title', 'description')
    
    # Explicitly removing any raw_id or autocomplete to force standard Select dropdown
    raw_id_fields = []
    autocomplete_fields = []

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "instructor":
            User = get_user_model()
            # Explicitly filter for INSTRUCTOR role
            kwargs["queryset"] = User.objects.filter(role="INSTRUCTOR")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'duration')
    list_filter = ('lesson__course',)
    search_fields = ('title', 'lesson__title')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at')
    search_fields = ('user__username', 'course__title')
    list_filter = ('enrolled_at',)
