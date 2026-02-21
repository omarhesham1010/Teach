# teach/views.py
import random
import json
import logging
from decimal import Decimal

from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse

from django.db.models import Q, Avg
from django.utils import timezone

from .models import LoginCode, Wallet, Conversation, Message
from .models import Course, Enrollment, Assignment, AssignmentSubmission
from .models import Quiz, QuizQuestion, QuizOption, QuizResult


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
        national_id = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=national_id, password=password)
        if user is not None:
            login(request, user)
            return redirect("instructor")

        messages.error(request, "Invalid National ID or password.")

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
        .order_by("-created_at")
    )

    return render(request, "teach/my_courses.html", {
        "enrollments": enrollments
    })


def course_details(request):
    return render(request, "teach/coursedetails.html")


def course_content(request):
    return render(request, "teach/coursecontent.html")


def assignment(request):
    """Assignments list; links to assignment detail by ID."""
    assignments = (
        Assignment.objects.all()
        .select_related("content", "content__course")
        .order_by("-created_at")[:50]
    )
    return render(request, "teach/assignment.html", {"assignments": assignments})


@login_required
@csrf_protect
def assignment_detail_view(request, assignment_id):
    """Assignment detail page: description, submission form (UI only), and status."""
    assignment_obj = (
        Assignment.objects.filter(assignment_id=assignment_id)
        .select_related("content", "content__course")
        .first()
    )
    if not assignment_obj:
        messages.error(request, "Assignment not found.")
        return redirect("assignment")

    submission = None
    if request.user.is_authenticated:
        submission = (
            AssignmentSubmission.objects.filter(
                assignment=assignment_obj,
                user=request.user,
            ).first()
        )

    if request.method == "POST":
        # UI only: do not save to database yet; file upload remains fake
        messages.info(request, "Submission received (preview only — not saved yet).")
        return redirect("assignment_detail", assignment_id=assignment_id)

    submission_reviewed = (
        getattr(submission, "reviewed", False) if submission else False
    )
    return render(
        request,
        "teach/assignment_detail.html",
        {
            "assignment": assignment_obj,
            "submission": submission,
            "submission_reviewed": submission_reviewed,
        },
    )


def enrollment(request):
    return render(request, "teach/enrollement.html")


@csrf_protect
def signup(request):
    if request.user.is_authenticated:
        return redirect("instructor")
    if request.method == "POST":
        national_id = (request.POST.get("national_id") or "").strip()
        full_name = (request.POST.get("full_name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password", "")
        if not national_id or not email or not full_name or not password:
            messages.error(request, "Please fill in National ID, Full Name, Email, and Password.")
            return render(request, "teach/signup.html")
        if User.objects.filter(national_id=national_id).exists():
            messages.error(request, "This National ID is already registered.")
            return render(request, "teach/signup.html")
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, "teach/signup.html")
        try:
            parts = full_name.split(None, 2)
            first_name = parts[0] if parts else full_name
            second_name = parts[1] if len(parts) > 1 else ""
            third_name = parts[2] if len(parts) > 2 else ""
            new_user = User.objects.create_user(
                national_id=national_id,
                email=email,
                password=password,
                first_name=first_name,
                second_name=second_name,
                third_name=third_name,
            )
        except Exception as e:
            logger.exception("Signup: failed to create user: %s", e)
            messages.error(request, "Could not create account. Please try again.")
            return render(request, "teach/signup.html")

        # Welcome conversation: best-effort; must not block login or redirect
        try:
            create_welcome_conversation_for_user(new_user)
        except Exception as e:
            logger.warning(
                "Signup: welcome conversation failed for user %s: %s",
                new_user.national_id,
                e,
                exc_info=True,
            )

        login(request, new_user)
        messages.success(request, "Welcome! A support conversation has been started for you.")
        return redirect("home")
    return render(request, "teach/signup.html")


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
    return render(request, "teach/profile.html", {
        "user": request.user,
        "wallet_balance": wallet.balance,
        "wallet_updated_at": wallet.updated_at,
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
        return redirect("instructor")

    messages.error(request, "Invalid action.")
    return redirect("login")


@login_required
def edit_user_profile(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", "")
        user.second_name = request.POST.get("second_name", "")
        user.third_name = request.POST.get("third_name", "")
        user.gender = request.POST.get("gender", "")
        user.phone_number = request.POST.get("phone_number", "")
        user.father_phone_number = request.POST.get("father_phone_number", "")
        user.mother_phone_number = request.POST.get("mother_phone_number", "")
        user.school_name = request.POST.get("school_name", "")
        user.parents_job = request.POST.get("parents_job", "")
        user.government = request.POST.get("government", "")
        user.grade = request.POST.get("grade", "")
        user.division = request.POST.get("division", "")
        user.email = request.POST.get("gmail", user.email)
        user.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "teach/edit_user_profile.html", {"user": request.user})


@login_required
def reset_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect("profile")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "teach/reset_password.html", {"form": form})


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
    courses = Course.objects.filter(is_active=True).order_by("-created_at")
    return render(request, "teach/courses.html", {"courses": courses})