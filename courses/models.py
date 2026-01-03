from django.db import models
from django.conf import settings


class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses', limit_choices_to={'role': 'INSTRUCTOR'})
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Updated thumbnail field
    thumbnail = models.ImageField(upload_to='Teach/Courses/', blank=True, null=True)
    
    is_deleted = models.BooleanField(default=False) # Soft delete

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def thumbnail_url(self):
        """Returns the Cloudinary URL or a placeholder if no image exists."""
        if self.thumbnail:
            return self.thumbnail.url
        # Fallback placeholder (ensure your cloud_name is correct in production or use a generic public one)
        # Using a generic placeholder for now as requested example
        cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', 'demo') 
        return f"https://res.cloudinary.com/{cloud_name}/image/upload/v1/Teach/placeholder_course.png"

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Video(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    duration = models.DurationField(null=True, blank=True)

    def __str__(self):
        return self.title

class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user} -> {self.course}"
