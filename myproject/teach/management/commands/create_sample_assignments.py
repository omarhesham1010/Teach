"""
Management command to create sample assignments (Image Processing, Machine Learning, Operating Systems).
Run with: python manage.py create_sample_assignments
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from teach.models import Course, CourseContent, Assignment


class Command(BaseCommand):
    help = 'Creates sample assignments for testing the LMS assignment system'

    def handle(self, *args, **options):
        # Use a single sample course and create 3 assignment contents
        course, _ = Course.objects.get_or_create(
            course_name="Sample Course",
            defaults={
                'course_description': 'Sample course for assignments and quizzes',
                'is_active': True,
            }
        )

        now = timezone.now()
        base_open = now - timedelta(days=2)
        base_due = now + timedelta(days=14)

        samples = [
            {
                'title': 'Basic Relationships Between Pixels',
                'course_name': 'Image Processing',
                'course_code': 'CS389/CS486',
                'opened_at': base_open.replace(hour=0, minute=0, second=0, microsecond=0),
                'deadline': (base_due + timedelta(days=0)).replace(hour=23, minute=59, second=59, microsecond=0),
                'description': 'This assignment covers fundamental concepts of image structure and pixel relationships.',
                'objectives': [
                    'Understand and apply concepts of pixel neighborhoods, adjacency, connectivity, paths, regions, and boundaries.',
                    'Compute and interpret distance measures between pixels.',
                    'Analyze region adjacency and disjointness using 4-, 8-, and m-adjacency.',
                    'Perform arithmetic operations on images and test linearity of operators.',
                ],
            },
            {
                'title': 'KNN Classification',
                'course_name': 'Machine Learning',
                'course_code': 'CS501',
                'opened_at': (base_open - timedelta(days=5)).replace(hour=0, minute=0, second=0, microsecond=0),
                'deadline': (base_due + timedelta(days=7)).replace(hour=23, minute=59, second=59, microsecond=0),
                'description': 'Implement and evaluate k-Nearest Neighbors for classification on a provided dataset.',
                'objectives': [
                    'Implement KNN from scratch using Euclidean distance.',
                    'Understand the effect of k on bias-variance tradeoff.',
                    'Compare KNN with at least one other classifier (e.g. decision tree).',
                    'Report accuracy, precision, recall and confusion matrix.',
                ],
            },
            {
                'title': 'CPU Scheduling',
                'course_name': 'Operating Systems',
                'course_code': 'CS405',
                'opened_at': (base_open - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                'deadline': (base_due + timedelta(days=21)).replace(hour=23, minute=59, second=59, microsecond=0),
                'description': 'Simulate and compare CPU scheduling algorithms: FCFS, SJF, Round Robin, and Priority.',
                'objectives': [
                    'Implement FCFS, SJF (non-preemptive), Round Robin, and Priority scheduling.',
                    'Compute average waiting time and average turnaround time for each algorithm.',
                    'Compare algorithms with the same set of processes and discuss tradeoffs.',
                    'Handle edge cases (equal burst times, ties in priority).',
                ],
            },
        ]

        created_count = 0
        for i, s in enumerate(samples, start=1):
            content, content_created = CourseContent.objects.get_or_create(
                course=course,
                title=s['title'],
                content_type='assignment',
                defaults={'order_index': 10 + i}
            )
            if content_created:
                self.stdout.write(self.style.SUCCESS(f'Created content: {content.title}'))

            assignment, assignment_created = Assignment.objects.get_or_create(
                content=content,
                defaults={
                    'description': s['description'],
                    'learning_objectives': '\n'.join(s['objectives']),
                    'opened_at': s['opened_at'],
                    'deadline': s['deadline'],
                    'course_name_display': s['course_name'],
                    'course_code_display': s['course_code'],
                }
            )
            if assignment_created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'Created assignment: {s["course_name"]} - {s["title"]} (ID: {assignment.assignment_id})'
                ))
            else:
                self.stdout.write(self.style.WARNING(f'Assignment already exists: {s["course_name"]} - {s["title"]}'))

        if created_count:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nCreated {created_count} sample assignment(s).\n'
                    'View them at: /assignment/\n'
                    'Upload assignment files (e.g. .docx, .pdf) in Django admin for each assignment.'
                )
            )
        else:
            self.stdout.write(self.style.WARNING('No new assignments created (all already exist).'))
