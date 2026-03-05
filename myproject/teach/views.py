# teach/views.py
import os
import random
import json
import logging
from decimal import Decimal

from django.shortcuts import render, redirect, reverse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse, FileResponse, Http404

from django.db.models import Q, Avg  # Avg for quiz_results_view
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import LoginCode, Wallet, Conversation, Message
from .models import Course, Enrollment, Assignment, AssignmentSubmission, AssignmentSubmissionHistory
from .models import Quiz, QuizQuestion, QuizOption, QuizResult
from .models import LoginCode, Wallet, Course, Enrollment, Lesson, LessonProgress  # ✅ UPDATED


User = get_user_model()

SUPPORT_NATIONAL_ID = "SUPPORT_0001"
logger = logging.getLogger(__name__)

WELCOME_MESSAGE_BODY = (
    "Welcome to the Teach platform 👋\n\n"
    "If you need any help or have any questions, feel free to contact us anytime and we'll be there for you."
)


def get_or_create_conversation(user_a, user_b):
    """
    Get or create a conversation between two users.
    Looks up both (user_a, user_b) and (user_b, user_a); creates with consistent order.
    """
    conv = (
        Conversation.objects.filter(
            Q(user=user_a, support=user_b) | Q(user=user_b, support=user_a)
        )
        .select_related("user", "support")
        .first()
    )
    if conv:
        return conv
    # Create with deterministic order to avoid duplicates
    if user_a.national_id < user_b.national_id:
        return Conversation.objects.create(user=user_a, support=user_b)
    return Conversation.objects.create(user=user_b, support=user_a)


def create_welcome_conversation_for_user(new_user):
    """
    After signup: ensure one conversation with Support exists and one welcome message.
    Uses get_user_model(). Does not crash if Support account is missing.
    Creates no duplicate conversation and no duplicate welcome message.
    Support account never receives a welcome message (skip when user is Support).
    """
    if new_user.national_id == SUPPORT_NATIONAL_ID:
        return
    UserModel = get_user_model()
    try:
        support = UserModel.objects.get(national_id=SUPPORT_NATIONAL_ID)
    except UserModel.DoesNotExist:
        logger.warning(
            "Support account (national_id=%s) does not exist. "
            "Run: python manage.py create_support_account. Skipping welcome conversation.",
            SUPPORT_NATIONAL_ID,
        )
        return

    # Get or create exactly one conversation (no duplicate)
    conv = get_or_create_conversation(new_user, support)

    # Create exactly one welcome message: only if this conversation has no messages yet
    existing_count = Message.objects.filter(conversation=conv).count()
    if existing_count > 0:
        logger.debug(
            "Welcome conversation for user %s already has messages (count=%s). Skipping welcome message.",
            new_user.national_id,
            existing_count,
        )
        return

    welcome_text = WELCOME_MESSAGE_BODY
    Message.objects.create(
        conversation=conv,
        sender=support,
        receiver=new_user,
        message_type="text",
        message_body=welcome_text,
        is_read=False,
    )
    conv.last_message = welcome_text[:200]
    conv.last_message_at = timezone.now()
    conv.save(update_fields=["last_message", "last_message_at"])

    logger.info(
        "Welcome conversation created for user %s: conversation_id=%s, one welcome message added.",
        new_user.national_id,
        conv.id,
    )


@login_required
@require_POST
def toggle_theme(request):
    """API endpoint to save user's theme preference to database."""
    try:
        data = json.loads(request.body)
        mode = data.get('mode', 'Light')
        if mode in ['Dark', 'Light']:
            request.user.mode = mode
            request.user.save(update_fields=['mode'])
            return JsonResponse({'status': 'success', 'mode': mode})
        return JsonResponse({'status': 'error', 'message': 'Invalid mode'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)


@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect("instructor")

    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "")

        # Dual-lookup logic
        user_obj = User.objects.filter(
            Q(email__iexact=identifier) | Q(national_id=identifier)
        ).first()

        if user_obj:
            user = authenticate(request, username=user_obj.national_id, password=password)
            if user is not None:
                login(request, user)
                next_url = request.POST.get('next', '').strip()
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect("instructor")

        messages.error(request, "Invalid Email/National ID or password.")

    return render(request, "teach/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def instructor(request):
    return render(request, "teach/instructor.html")


# ✅ NEW: My Courses (Dynamic)
@login_required
def my_courses_view(request):
    enrollments = (
        Enrollment.objects
        .filter(user=request.user)
        .select_related("course")
        .order_by("-enrolled_at")
    )

    for enrollment in enrollments:
        # 1. Total lessons in this course
        # lessons belong to CourseContent, which belongs to Course
        total_lessons = Lesson.objects.filter(content__course=enrollment.course).count()
        
        # 2. Completed lessons by this user for this course
        # LessonProgress stores lesson ID (lesson_id as string/id)
        # We need to find completed progress records for lessons in this course
        course_lesson_ids = list(Lesson.objects.filter(content__course=enrollment.course).values_list('lesson_id', flat=True))
        
        completed_lessons = LessonProgress.objects.filter(
            user=request.user,
            lesson__in=[str(lid) for lid in course_lesson_ids],
            is_completed=True
        ).count()

        # 3. Calculate percentage
        if total_lessons > 0:
            progress_percent = (completed_lessons / total_lessons) * 100
        else:
            progress_percent = 0
            
        enrollment.progress = round(progress_percent)

    return render(request, "teach/my_courses.html", {
        "enrollments": enrollments
    })


def course_details(request):
    # Fetch a default course to check enrollment against (since page is static)
    default_course = Course.objects.filter(is_active=True).first()
    is_enrolled = False
    
    if request.user.is_authenticated and default_course:
        is_enrolled = Enrollment.objects.filter(
            user=request.user, 
            course=default_course
        ).exists()
        
    return render(request, "teach/coursedetails.html", {
        "is_enrolled": is_enrolled
    })


def course_content(request):
    return render(request, "teach/coursecontent.html")


@login_required
def assignment(request):
    """Assignments list; links to assignment detail by ID."""
    assignments = (
        Assignment.objects.all()
        .select_related("content", "content__course")
        .order_by("-created_at")[:50]
    )
    return render(request, "teach/assignment.html", {"assignments": assignments})


def _assignment_display_info(assignment):
    """Build display strings for course name/code from assignment or linked content."""
    name = (assignment.course_name_display or "").strip()
    code = (assignment.course_code_display or "").strip()
    if name or code:
        return name, code
    try:
        c = assignment.content.course
        return (getattr(c, "course_name", "") or ""), (getattr(c, "course_code", "") or "")
    except Exception:
        return "", ""


def _early_late_text(submission, deadline):
    """Return (text, is_late) for submission timing vs deadline."""
    if not submission or not submission.submitted_at or not deadline:
        return None, False
    from datetime import timedelta
    delta = submission.submitted_at - deadline
    if delta.total_seconds() <= 0:
        days = abs(delta.days) or (abs(delta.total_seconds()) / 86400)
        return f"Submitted early by {int(round(days))} day(s)", False
    days = delta.days or 1
    return f"Submitted late by {days} day(s)", True


def _require_instructor(user):
    """Simple helper to check instructor/admin access."""
    return user.is_staff or user.is_superuser


@login_required
def assignment_file_download_view(request, assignment_id):
    """Serve assignment file for download (instructor-uploaded file)."""
    assignment_obj = (
        Assignment.objects.filter(assignment_id=assignment_id)
        .select_related("content")
        .first()
    )
    if not assignment_obj or not assignment_obj.assignment_file:
        raise Http404("Assignment or file not found.")
    f = assignment_obj.assignment_file
    try:
        filename = os.path.basename(f.name)
        response = FileResponse(f.open("rb"), as_attachment=True, filename=filename)
        return response
    except Exception:
        raise Http404("File not available.")


@login_required
@csrf_protect
def assignment_detail_view(request, assignment_id):
    """Assignment detail: course, dates, objectives, file link, submit form, submission status table."""
    assignment_obj = (
        Assignment.objects.filter(assignment_id=assignment_id)
        .select_related("content", "content__course")
        .first()
    )
    if not assignment_obj:
        messages.error(request, "Assignment not found.")
        return redirect("assignment")

    # There is at most one AssignmentSubmission per (assignment, user)
    submission = None
    active_submission = None
    if request.user.is_authenticated:
        submission = (
            AssignmentSubmission.objects.filter(
                assignment=assignment_obj,
                user=request.user,
            ).first()
        )
        active_submission = submission if submission and not submission.is_deleted else None

    if request.method == "POST":
        action = (request.POST.get("action") or "submit").lower()

        # Do not allow any edits/deletes once graded
        if active_submission and active_submission.grading_status == "graded":
            messages.error(request, "This submission has been graded and can no longer be edited or deleted.")
            return redirect("assignment_detail", assignment_id=assignment_id)

        if action == "delete":
            if not active_submission:
                messages.error(request, "There is no submission to delete.")
                return redirect("assignment_detail", assignment_id=assignment_id)

            # Log deletion (keep previous versions intact)
            AssignmentSubmissionHistory.objects.create(
                assignment=assignment_obj,
                user=request.user,
                action_type="deleted",
                file_name=active_submission.file_path.name if active_submission.file_path else "",
                answer_text=active_submission.answer_text,
            )
            active_submission.is_deleted = True
            active_submission.answer_text = ""
            active_submission.file_path = None
            active_submission.save(update_fields=["is_deleted", "answer_text", "file_path", "updated_at"])
            messages.success(request, "Your submission has been deleted. You can submit a new version before grading.")
            return redirect("assignment_detail", assignment_id=assignment_id)

        # Default: create/update submission (submit or edit)
        answer_text = (request.POST.get("answer_text") or "").strip()
        file_upload = request.FILES.get("file_upload")

        is_new = submission is None
        if is_new:
            submission = AssignmentSubmission(
                assignment=assignment_obj,
                user=request.user,
            )

        submission.answer_text = answer_text
        submission.grading_status = "not_graded"
        submission.is_deleted = False
        if file_upload:
            submission.file_path = file_upload
        submission.save()

        # History entry
        history_action = "submitted" if is_new else "edited"
        history_file = file_upload if file_upload is not None else None
        AssignmentSubmissionHistory.objects.create(
            assignment=assignment_obj,
            user=request.user,
            action_type=history_action,
            file=history_file,
            file_name=file_upload.name if file_upload is not None else (submission.file_path.name if submission.file_path else ""),
            answer_text=answer_text,
        )

        messages.success(request, "Your submission has been saved.")
        return redirect("assignment_detail", assignment_id=assignment_id)

    course_name, course_code = _assignment_display_info(assignment_obj)
    deadline = assignment_obj.deadline
    now = timezone.now()
    time_remaining = None
    if deadline and now < deadline:
        delta = deadline - now
        days, remainder = divmod(int(delta.total_seconds()), 86400)
        hours = remainder // 3600
        time_remaining = f"{days} days {hours} hours remaining"

    display_submission = active_submission
    early_late_text, is_late = _early_late_text(display_submission, deadline)

    objectives_list = []
    if assignment_obj.learning_objectives:
        objectives_list = [
            line.strip() for line in assignment_obj.learning_objectives.splitlines()
            if line.strip()
        ]

    return render(
        request,
        "teach/assignment_detail.html",
        {
            "assignment": assignment_obj,
            "submission": display_submission,
            "course_name": course_name,
            "course_code": course_code,
            "objectives_list": objectives_list,
            "time_remaining": time_remaining,
            "early_late_text": early_late_text,
            "is_late": is_late,
            "is_locked": bool(display_submission and display_submission.grading_status == "graded"),
        },
    )


# =========================
# Instructor assignment dashboards
# =========================


@login_required
def instructor_assignments_dashboard(request):
    if not _require_instructor(request.user):
        messages.error(request, "You do not have permission to access the instructor dashboard.")
        return redirect("instructor")

    assignments = (
        Assignment.objects
        .select_related("content", "content__course")
        .order_by("-created_at")[:100]
    )
    return render(
        request,
        "teach/instructor_assignments.html",
        {"assignments": assignments},
    )


@login_required
def instructor_assignment_submissions(request, assignment_id):
    if not _require_instructor(request.user):
        messages.error(request, "You do not have permission to view submissions.")
        return redirect("instructor")

    assignment_obj = (
        Assignment.objects.filter(assignment_id=assignment_id)
        .select_related("content", "content__course")
        .first()
    )
    if not assignment_obj:
        messages.error(request, "Assignment not found.")
        return redirect("instructor_assignments_dashboard")

    submissions = (
        AssignmentSubmission.objects
        .filter(assignment=assignment_obj, is_deleted=False)
        .select_related("user")
        .order_by("user__first_name", "user__second_name")
    )

    return render(
        request,
        "teach/instructor_assignment_submissions.html",
        {
            "assignment": assignment_obj,
            "submissions": submissions,
        },
    )


@login_required
@csrf_protect
def instructor_grade_submission(request, assignment_id, national_id):
    if not _require_instructor(request.user):
        messages.error(request, "You do not have permission to grade submissions.")
        return redirect("instructor")

    assignment_obj = (
        Assignment.objects.filter(assignment_id=assignment_id)
        .select_related("content", "content__course")
        .first()
    )
    if not assignment_obj:
        messages.error(request, "Assignment not found.")
        return redirect("instructor_assignments_dashboard")

    submission = (
        AssignmentSubmission.objects.select_related("user")
        .filter(assignment=assignment_obj, user__national_id=national_id)
        .first()
    )
    if not submission:
        messages.error(request, "Submission not found.")
        return redirect("instructor_assignment_submissions", assignment_id=assignment_id)

    if request.method == "POST":
        grade_raw = (request.POST.get("grade") or "").strip()
        comments = (request.POST.get("feedback") or "").strip()
        try:
            grade_value = Decimal(grade_raw) if grade_raw else None
        except Exception:
            messages.error(request, "Please enter a valid numeric grade.")
            return redirect("instructor_grade_submission", assignment_id=assignment_id, national_id=national_id)

        if grade_value is not None and grade_value < 0:
            messages.error(request, "Grade cannot be negative.")
            return redirect("instructor_grade_submission", assignment_id=assignment_id, national_id=national_id)

        submission.grade = grade_value
        submission.submission_comments = comments
        submission.grading_status = "graded"
        submission.save(update_fields=["grade", "submission_comments", "grading_status", "updated_at"])

        messages.success(request, "Grade saved. Submission is now locked for the student.")
        return redirect("instructor_assignment_submissions", assignment_id=assignment_id)

    return render(
        request,
        "teach/instructor_grade_submission.html",
        {
            "assignment": assignment_obj,
            "submission": submission,
        },
    )


@login_required
def instructor_submission_history(request, assignment_id, national_id):
    if not _require_instructor(request.user):
        messages.error(request, "You do not have permission to view submission history.")
        return redirect("instructor")

    assignment_obj = (
        Assignment.objects.filter(assignment_id=assignment_id)
        .select_related("content", "content__course")
        .first()
    )
    if not assignment_obj:
        messages.error(request, "Assignment not found.")
        return redirect("instructor_assignments_dashboard")

    history_qs = (
        AssignmentSubmissionHistory.objects
        .filter(assignment=assignment_obj, user__national_id=national_id)
        .select_related("user")
        .order_by("created_at")
    )

    if history_qs:
        student = history_qs[0].user
    else:
        # Fallback: get user from active submission, if any
        active = AssignmentSubmission.objects.filter(
            assignment=assignment_obj,
            user__national_id=national_id,
        ).select_related("user").first()
        student = active.user if active else None

    return render(
        request,
        "teach/instructor_submission_history.html",
        {
            "assignment": assignment_obj,
            "history": history_qs,
            "student": student,
        },
    )


@login_required
def instructor_history_file_download(request, history_id):
    if not _require_instructor(request.user):
        messages.error(request, "You do not have permission to download history files.")
        return redirect("instructor")

    history = AssignmentSubmissionHistory.objects.select_related("assignment").filter(id=history_id).first()
    if not history or not history.file:
        raise Http404("History file not found.")

    try:
        filename = os.path.basename(history.file.name) or history.file_name or "submission"
        return FileResponse(history.file.open("rb"), as_attachment=True, filename=filename)
    except Exception:
        raise Http404("File not available.")


def enrollment(request):
    return render(request, "teach/enrollement.html")


@csrf_protect
@csrf_protect
def signup(request):
    if request.user.is_authenticated:
        logout(request)

    errors = {}
    if request.method == "POST":
        data = request.POST
        first_name = data.get("first_name", "").strip()
        second_name = data.get("second_name", "").strip()
        third_name = data.get("third_name", "").strip()
        gender = data.get("gender", "")
        phone_number = data.get("phone_number", "").strip()
        father_phone_number = data.get("father_phone_number", "").strip()
        school_name = data.get("school_name", "").strip()
        parents_job = data.get("parents_job", "").strip()
        government = data.get("government", "")
        grade = data.get("grade", "")
        division = data.get("division", "")
        gmail = data.get("gmail", "").strip().lower()
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")
        national_id = data.get("national_id", "").strip()

        # Manual Validation
        required_fields = {
            "first_name": first_name,
            "gender": gender,
            "phone_number": phone_number,
            "father_phone_number": father_phone_number,
            "government": government,
            "grade": grade,
            "gmail": gmail,
            "password": password,
            "confirm_password": confirm_password,
            "national_id": national_id,
        }

        for field, value in required_fields.items():
            if not value:
                errors[field] = f"{field.replace('_', ' ').capitalize()} is required."

        if not errors:
            if User.objects.filter(email__iexact=gmail).exists():
                errors["gmail"] = "This email is already in use."
            
            if User.objects.filter(national_id=national_id).exists():
                errors["national_id"] = "This National ID is already in use."

            if len(password) < 8 or not any(char.isdigit() for char in password):
                errors["password"] = "Password must be at least 8 characters and include a number."
            
            if password != confirm_password:
                errors["confirm_password"] = "Passwords do not match."

        if not errors:
            try:
                user = User.objects.create_user(
                    national_id=national_id,
                    email=gmail,
                    password=password,
                    first_name=first_name,
                    second_name=second_name,
                    third_name=third_name,
                    gender=gender,
                    phone_number=phone_number,
                    father_phone_number=father_phone_number,
                    school_name=school_name,
                    parents_job=parents_job,
                    government=government,
                    grade=grade,
                    division=division,
                )
                messages.success(request, "Account created successfully. Please login.")
                return redirect("login")
            except Exception as e:
                errors["form"] = f"An unexpected error occurred: {str(e)}"

    return render(request, "teach/signup.html", {
        "errors": errors,
        "gender_choices": User.GENDER_CHOICES,
        "government_choices": User.GOVERNMENT_CHOICES,
        "grade_choices": User.GRADE_CHOICES,
        "division_choices": User.DIVISION_CHOICES,
    })


@login_required
def quiz(request):
    """Quizzes list; links to quiz detail by ID."""
    quizzes = (
        Quiz.objects.all()
        .select_related("content", "content__course")
        .prefetch_related("questions")
        .order_by("-created_at")[:50]
    )
    # Add question count, attempts info, and best score to each quiz
    quizzes_list = []
    for q in quizzes:
        question_count = q.questions.count()
        user_attempts = QuizResult.objects.filter(user=request.user, quiz=q).count()
        remaining_attempts = max(0, q.max_attempts - user_attempts)
        # Get best score
        best_result = (
            QuizResult.objects.filter(user=request.user, quiz=q)
            .order_by("-score")
            .first()
        )
        best_score = best_result.score if best_result else None
        quizzes_list.append({
            "quiz": q,
            "question_count": question_count,
            "user_attempts": user_attempts,
            "remaining_attempts": remaining_attempts,
            "max_attempts": q.max_attempts,
            "best_score": best_score,
            "has_attempts_left": remaining_attempts > 0,
        })
    return render(request, "teach/quiz.html", {"quizzes": quizzes_list})


@login_required
def quiz_detail_view(request, quiz_id):
    """Quiz detail page: display questions with timer and navigation."""
    quiz_obj = (
        Quiz.objects.filter(quiz_id=quiz_id)
        .select_related("content", "content__course")
        .prefetch_related("questions__options")
        .first()
    )
    if not quiz_obj:
        messages.error(request, "Quiz not found.")
        return redirect("quiz")

    questions = list(quiz_obj.questions.all())
    if not questions:
        messages.error(request, "This quiz has no questions.")
        return redirect("quiz")

    # Check attempts
    user_attempts = QuizResult.objects.filter(user=request.user, quiz=quiz_obj).count()
    remaining_attempts = max(0, quiz_obj.max_attempts - user_attempts)
    
    if remaining_attempts <= 0:
        messages.error(request, f"You have reached the maximum number of attempts ({quiz_obj.max_attempts}) for this quiz.")
        return redirect("quiz")

    # Prepare questions with options for template (JSON serializable)
    questions_json = []
    for q in questions:
        options = list(q.options.all().order_by("option_index"))
        questions_json.append({
            "question_id": q.question_id,
            "question_text": q.question_text,
            "options": [
                {"option_index": opt.option_index, "option_text": opt.option_text}
                for opt in options
            ],
        })

    # Get next attempt number
    next_attempt = user_attempts + 1

    return render(
        request,
        "teach/quiz_detail.html",
        {
            "quiz": quiz_obj,
            "questions_json": json.dumps(questions_json),
            "total_questions": len(questions_json),
            "time_limit_minutes": quiz_obj.time_limit,
            "remaining_attempts": remaining_attempts,
            "current_attempt": next_attempt,
            "max_attempts": quiz_obj.max_attempts,
        },
    )


@login_required
def quiz_results_view(request, quiz_id):
    """Quiz results/details page: show all attempts, best score, and details."""
    quiz_obj = (
        Quiz.objects.filter(quiz_id=quiz_id)
        .select_related("content", "content__course")
        .first()
    )
    if not quiz_obj:
        messages.error(request, "Quiz not found.")
        return redirect("quiz")

    # Get all user's attempts for this quiz
    user_results = (
        QuizResult.objects.filter(user=request.user, quiz=quiz_obj)
        .order_by("-submitted_at")
    )
    
    # Calculate stats
    best_result = user_results.order_by("-score").first()
    best_score = best_result.score if best_result else None
    total_attempts = user_results.count()
    remaining_attempts = max(0, quiz_obj.max_attempts - total_attempts)
    average_score = (
        user_results.aggregate(avg_score=Avg("score"))["avg_score"] or 0
    )

    return render(
        request,
        "teach/quiz_results.html",
        {
            "quiz": quiz_obj,
            "results": user_results,
            "best_score": best_score,
            "total_attempts": total_attempts,
            "remaining_attempts": remaining_attempts,
            "max_attempts": quiz_obj.max_attempts,
            "average_score": round(average_score, 2),
        },
    )


@login_required
@csrf_protect
@require_POST
def quiz_submit_view(request, quiz_id):
    """Submit quiz answers, calculate score, save result."""
    quiz_obj = Quiz.objects.filter(quiz_id=quiz_id).prefetch_related("questions__options").first()
    if not quiz_obj:
        return JsonResponse({"success": False, "error": "Quiz not found."}, status=404)

    questions = list(quiz_obj.questions.all())
    if not questions:
        return JsonResponse({"success": False, "error": "Quiz has no questions."}, status=400)

    # Get answers from POST (question_id -> selected_option_index)
    answers = {}
    for q in questions:
        answer_key = f"question_{q.question_id}"
        selected = request.POST.get(answer_key)
        if selected:
            try:
                answers[q.question_id] = int(selected)
            except ValueError:
                pass

    # Calculate score (backend validation)
    correct_count = 0
    total_count = len(questions)
    for q in questions:
        selected_option = answers.get(q.question_id)
        if selected_option and selected_option == q.correct_option:
            correct_count += 1

    wrong_count = total_count - correct_count
    score_percentage = (correct_count / total_count * 100) if total_count > 0 else 0

    # Get next attempt number
    user_attempts = QuizResult.objects.filter(user=request.user, quiz=quiz_obj).count()
    next_attempt = user_attempts + 1

    # Check if user exceeded max attempts
    if next_attempt > quiz_obj.max_attempts:
        return JsonResponse(
            {"success": False, "error": f"You have reached the maximum number of attempts ({quiz_obj.max_attempts})."},
            status=400
        )

    # Save result with attempt number
    result = QuizResult.objects.create(
        user=request.user,
        quiz=quiz_obj,
        attempt_number=next_attempt,
        score=score_percentage,
    )

    # Determine feedback message
    if score_percentage >= 90:
        feedback = "Excellent Work! 🎉"
    elif score_percentage >= 70:
        feedback = "Keep Up! 👍"
    else:
        feedback = "Practice More! 💪"

    # Calculate remaining attempts
    remaining_attempts = max(0, quiz_obj.max_attempts - next_attempt)

    return JsonResponse(
        {
            "success": True,
            "score": round(score_percentage, 2),
            "correct": correct_count,
            "wrong": wrong_count,
            "total": total_count,
            "feedback": feedback,
            "remaining_attempts": remaining_attempts,
            "current_attempt": next_attempt,
            "max_attempts": quiz_obj.max_attempts,
        }
    )


def submission_success(request):
    return render(request, "teach/submissionsuccess.html")


@login_required
def profile_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    # Determine user role
    user = request.user
    if user.is_superuser:
        user_role = "Super Admin"
    elif user.is_staff:
        user_role = "Instructor"
    else:
        user_role = "Student"

    return render(request, "teach/profile.html", {
        "user": user,
        "wallet_balance": wallet.balance,
        "wallet_updated_at": wallet.updated_at,
        "user_role": user_role,
    })


def settings_view(request):
    return render(request, "teach/settings.html")


@login_required
def messages_view(request):
    """Messages page: list conversations where user is participant; search by phone/National ID."""
    # Ensure every account has a conversation with Support and one welcome message (idempotent)
    create_welcome_conversation_for_user(request.user)

    conversations = (
        Conversation.objects.filter(
            Q(user=request.user) | Q(support=request.user)
        )
        .select_related("user", "support")
        .order_by("-last_message_at", "-created_at")
    )
    # Resolve "other" participant and unread count per conversation
    conv_list = []
    for c in conversations:
        other = c.support if c.user_id == request.user.national_id else c.user
        unread = Message.objects.filter(
            conversation=c, receiver=request.user, is_read=False
        ).count()
        conv_list.append(
            {
                "conversation": c,
                "other": other,
                "unread_count": unread,
                "last_at": c.last_message_at or c.created_at,
            }
        )
    return render(
        request,
        "teach/messages/conversations.html",
        {"conversations": conv_list},
    )


@login_required
def chat_detail_view(request, conversation_id):
    """Chat detail: show messages, mark as read when opened."""
    conv = (
        Conversation.objects.filter(
            Q(user=request.user) | Q(support=request.user)
        )
        .select_related("user", "support")
        .filter(pk=conversation_id)
        .first()
    )
    if not conv:
        messages.error(request, "Conversation not found.")
        return redirect("messages")
    # Mark all messages where receiver = current user as read
    Message.objects.filter(
        conversation=conv, receiver=request.user, is_read=False
    ).update(is_read=True)
    msgs = (
        Message.objects.filter(conversation=conv)
        .select_related("sender", "receiver")
        .order_by("created_at")
    )
    other = conv.support if conv.user_id == request.user.national_id else conv.user
    # Sidebar: other conversations for desktop layout
    other_conversations = (
        Conversation.objects.filter(
            Q(user=request.user) | Q(support=request.user)
        )
        .exclude(pk=conv.pk)
        .select_related("user", "support")
        .order_by("-last_message_at", "-created_at")[:20]
    )
    conv_list = []
    for c in other_conversations:
        o = c.support if c.user_id == request.user.national_id else c.user
        conv_list.append({"conversation": c, "other": o})
    return render(
        request,
        "teach/messages/chat_detail.html",
        {
            "conversation": conv,
            "messages": msgs,
            "other": other,
            "sidebar_conversations": conv_list,
        },
    )


@login_required
@require_POST
@csrf_protect
def send_message_view(request):
    """Send a message: create message, update conversation, set is_read=False for receiver."""
    conversation_id = request.POST.get("conversation_id")
    body = (request.POST.get("message_body") or "").strip()
    if not body:
        return JsonResponse({"success": False, "error": "Message cannot be empty."}, status=400)
    conv = (
        Conversation.objects.filter(
            Q(user=request.user) | Q(support=request.user)
        )
        .filter(pk=conversation_id)
        .first()
    )
    if not conv:
        return JsonResponse({"success": False, "error": "Conversation not found."}, status=404)
    receiver = conv.support if conv.user_id == request.user.national_id else conv.user
    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        receiver=receiver,
        message_type="text",
        message_body=body,
        is_read=False,
    )
    conv.last_message = body[:200]
    conv.last_message_at = timezone.now()
    conv.save(update_fields=["last_message", "last_message_at"])
    return JsonResponse(
        {
            "success": True,
            "message_id": msg.pk,
            "created_at": msg.created_at.isoformat(),
        }
    )


@login_required
def search_user_for_chat_view(request):
    """Search user by phone or national_id for starting a new conversation."""
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"found": False, "error": "Enter phone or National ID."})
    user_model = get_user_model()
    other = user_model.objects.filter(
        Q(phone_number=q)
        | Q(father_phone_number=q)
        | Q(mother_phone_number=q)
        | Q(national_id=q)
    ).exclude(national_id=request.user.national_id).first()
    if not other:
        return JsonResponse({"found": False, "error": "User not found."})
    conv = get_or_create_conversation(request.user, other)
    return JsonResponse(
        {
            "found": True,
            "conversation_id": conv.pk,
            "redirect_url": reverse("chat_detail", kwargs={"conversation_id": conv.pk}),
            "other_name": other.get_full_name() or other.get_short_name() or other.national_id,
            "other_id": other.national_id,
        }
    )


def notes_view(request):
    return render(request, "teach/notes.html")


def discussion_view(request):
    return render(request, "teach/discussion.html")


@csrf_protect
def login_code_view(request):
    if request.user.is_authenticated:
        return redirect("instructor")

    if request.method != "POST":
        return redirect("login")

    action = request.POST.get("action")
    identifier = request.POST.get("identifier", "").strip().lower()
    code_entered = request.POST.get("code", "").strip()

    if not identifier:
        messages.error(request, "Please enter your email.")
        return redirect("login")

    try:
        user = User.objects.get(email__iexact=identifier)
    except User.DoesNotExist:
        messages.error(request, "No account found with this email.")
        return redirect("login")

    if action == "send":
        otp = f"{random.randint(0, 999999):06d}"
        LoginCode.objects.filter(user=user, is_used=False).update(is_used=True)
        LoginCode.objects.create(user=user, code=otp)

        send_mail(
            subject="Your Login Code",
            message=f"Your login code is: {otp}\nThis code expires in 10 minutes.",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[user.email],
            fail_silently=False,
        )

        messages.success(request, "Code sent to your email. Please check inbox/spam.")
        return redirect("login")

    if action == "verify":
        if not code_entered or len(code_entered) != 6:
            messages.error(request, "Please enter the 6-digit code.")
            return redirect("login")

        latest = (
            LoginCode.objects.filter(user=user, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not latest:
            messages.error(request, "No active code found. Please request a new one.")
            return redirect("login")

        if latest.is_expired(minutes=10):
            latest.is_used = True
            latest.save(update_fields=["is_used"])
            messages.error(request, "Code expired. Please request a new code.")
            return redirect("login")

        if latest.code != code_entered:
            messages.error(request, "Invalid code. Please try again.")
            return redirect("login")

        latest.is_used = True
        latest.save(update_fields=["is_used"])

        login(request, user)
        next_url = (request.POST.get("next") or "").strip()
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect("instructor")

    messages.error(request, "Invalid action.")
    return redirect("login")


@login_required
def edit_user_profile(request):
    user = request.user
    errors = {}

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        second_name = request.POST.get("second_name", "").strip()
        third_name = request.POST.get("third_name", "").strip()
        gender = request.POST.get("gender", "")
        phone_number = request.POST.get("phone_number", "").strip()
        father_phone_number = request.POST.get("father_phone_number", "").strip()
        school_name = request.POST.get("school_name", "").strip()
        parents_job = request.POST.get("parents_job", "").strip()
        government = request.POST.get("government", "")
        grade = request.POST.get("grade", "")
        division = request.POST.get("division", "")
        gmail = request.POST.get("gmail", "").strip()

        # Validation Logic
        if not first_name:
            errors['first_name'] = "First name is required."
        
        if not gmail:
            errors['gmail'] = "Email is required."
        elif "@" not in gmail or "." not in gmail:
            errors['gmail'] = "Enter a valid email address."
        elif User.objects.filter(email__iexact=gmail).exclude(national_id=user.national_id).exists():
            errors['gmail'] = "This email is already in use by another account."


        prefixes = ['010', '011', '012', '015']
        if phone_number:
            is_valid_phone = phone_number.isdigit() and len(phone_number) == 11 and any(phone_number.startswith(p) for p in prefixes)
            if not is_valid_phone:
                errors['phone_number'] = "Please enter a valid phone number."

        if father_phone_number:
            is_valid_father = father_phone_number.isdigit() and len(father_phone_number) == 11 and any(father_phone_number.startswith(p) for p in prefixes)
            if not is_valid_father:
                errors['father_phone_number'] = "Please enter a valid phone number."

        if not errors:
            user.first_name = first_name
            user.second_name = second_name
            user.third_name = third_name
            user.gender = gender
            user.phone_number = phone_number
            user.father_phone_number = father_phone_number
            user.school_name = school_name
            user.parents_job = parents_job
            user.government = government
            user.grade = grade
            user.division = division
            user.email = gmail
            user.save()

            messages.success(request, "Profile updated successfully.")
            return redirect("profile")

    return render(request, "teach/edit_user_profile.html", {
        "user": user,
        "errors": errors,
    })


@login_required
def reset_password(request):
    errors = {}
    if request.method == "POST":
        old_password = request.POST.get("old_password", "")
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        # Validation Logic
        if not old_password:
            errors['old_password'] = "Old password is required."
        elif not request.user.check_password(old_password):
            errors['old_password'] = "Incorrect old password."

        if not new_password:
            errors['new_password'] = "New password is required."
        elif len(new_password) < 8:
            errors['new_password'] = "Password must be at least 8 characters long."
        elif not any(char.isdigit() for char in new_password):
            errors['new_password'] = "Password must contain at least one number."

        if not confirm_password:
            errors['confirm_password'] = "Please confirm your new password."
        elif new_password != confirm_password:
            errors['confirm_password'] = "Passwords don't match."

        if not errors:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password updated successfully.")
            return redirect("profile")

    return render(request, "teach/reset_password.html", {"errors": errors})


@login_required
def add_money_to_wallet(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST":
        amount_str = request.POST.get("amount", "").strip()

        try:
            amount = Decimal(amount_str)
        except:
            messages.error(request, "Please enter a valid amount.")
            return redirect("add_money_to_wallet")

        if amount <= 0:
            messages.error(request, "Amount must be greater than 0.")
            return redirect("add_money_to_wallet")

        wallet.balance = wallet.balance + amount
        wallet.save()

        messages.success(request, f"Added {amount} EGP to your wallet.")
        return redirect("profile")

    return render(request, "teach/add_money_to_wallet.html", {
        "wallet_balance": wallet.balance,
    })
@login_required
def courses(request):
    grade_filter = request.GET.get('grade')
    division_filter = request.GET.get('division')
    search_query = request.GET.get('search', '').strip()
    
    courses_qs = Course.objects.filter(is_active=True).order_by("-created_at")
    
    if grade_filter:
        courses_qs = courses_qs.filter(grade=grade_filter)
        
    if division_filter:
        courses_qs = courses_qs.filter(division=division_filter)

    if search_query:
        courses_qs = courses_qs.filter(course_name__icontains=search_query)
        
    return render(request, "teach/courses.html", {
        "courses": courses_qs,
        "selected_grade": grade_filter,
        "selected_division": division_filter,
        "selected_search": search_query,
        "grade_choices": Course.GRADE_CHOICES,
        "division_choices": Course.DIVISION_CHOICES,
    })