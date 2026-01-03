from rest_framework import serializers
from courses.models import Course, Lesson, Enrollment

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'order', 'course']
        read_only_fields = ['course']

class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(source='instructor.username', read_only=True)
    thumbnail_url = serializers.ReadOnlyField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'instructor', 'instructor_name', 'price', 'thumbnail', 'thumbnail_url', 'created_at', 'lessons']
        read_only_fields = ['instructor', 'created_at']

    def create(self, validated_data):
        # Automatically assign the request user as instructor
        request = self.context.get('request')
        validated_data['instructor'] = request.user
        return super().create(validated_data)

class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = ['id', 'user', 'course', 'course_title', 'enrolled_at']
        read_only_fields = ['user', 'enrolled_at']
        
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)
