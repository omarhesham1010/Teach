from rest_framework import viewsets, permissions, status, decorators
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from courses.models import Course, Lesson, Enrollment
from .serializers import CourseListSerializer, CourseDetailSerializer, LessonSerializer, EnrollmentSerializer
from .permissions import IsInstructorOrReadOnly, IsOwnerOrReadOnly

class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing courses.
    """
    queryset = Course.objects.filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsInstructorOrReadOnly, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    def perform_destroy(self, instance):
        # Soft delete
        instance.is_deleted = True
        instance.save()

    @decorators.action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        course = self.get_object()
        user = request.user
        
        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response({'detail': 'Already enrolled.'}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = EnrollmentSerializer(data={'course': course.id}, context={'request': request})
        if serializer.is_valid():
            serializer.save(course=course) # course already in validated_data via data but good to be explicit or if serializer ignored it
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @decorators.action(detail=True, methods=['get', 'post'], permission_classes=[IsOwnerOrReadOnly])
    def lessons(self, request, pk=None):
        course = self.get_object()
        
        if request.method == 'GET':
            lessons = course.lessons.all()
            serializer = LessonSerializer(lessons, many=True)
            return Response(serializer.data)
        
        if request.method == 'POST':
            serializer = LessonSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(course=course)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet to list user's enrollments.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)
