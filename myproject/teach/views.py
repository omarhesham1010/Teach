# teach/views.py
import random
import json
from decimal import Decimal

from django.shortcuts import render, redirect
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
from django.http import JsonResponse

from .models import LoginCode, Wallet, Course, Enrollment, Lesson, LessonProgress  # ✅ UPDATED


User = get_user_model()


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
                next_url = request.POST.get('next')
                if next_url:
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
    return render(request, "teach/coursedetails.html")


def course_content(request):
    return render(request, "teach/coursecontent.html")


def assignment(request):
    return render(request, "teach/assignment.html")


def enrollment(request):
    return render(request, "teach/enrollement.html")


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


def quiz(request):
    return render(request, "teach/quiz.html")


def quiz_submit(request):
    return render(request, "teach/quizsummit.html")


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


def messages_view(request):
    return render(request, "teach/messages.html")


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
        next_url = request.POST.get("next")
        if next_url:
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
    
    if search_query:
        courses_qs = courses_qs.filter(course_name__icontains=search_query)
        
    if grade_filter:
        courses_qs = courses_qs.filter(grade=grade_filter)
        
    if division_filter:
        courses_qs = courses_qs.filter(division=division_filter)
        
    return render(request, "teach/courses.html", {
        "courses": courses_qs,
        "selected_grade": grade_filter,
        "selected_division": division_filter,
        "selected_search": search_query,
        "grade_choices": Course.GRADE_CHOICES,
        "division_choices": Course.DIVISION_CHOICES,
    })