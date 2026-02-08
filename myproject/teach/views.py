import random

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
from django.conf import settings
from .models import LoginCode
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash






User = get_user_model()


@csrf_protect
def login_view(request):
    
    if request.user.is_authenticated:
        return redirect("instructor")

    if request.method == "POST":
        national_id = request.POST.get("username", "").strip()  # Form field is still "username" but contains national_id
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


def courses(request):
    return render(request, "teach/courses.html")


def course_details(request):
    return render(request, "teach/coursedetails.html")


def course_content(request):
    return render(request, "teach/coursecontent.html")


def assignment(request):
    return render(request, "teach/assignment.html")


def enrollment(request):
    return render(request, "teach/enrollement.html")


def signup(request):
    return render(request, "teach/signup.html")


def quiz(request):
    return render(request, "teach/quiz.html")


def quiz_submit(request):
    return render(request, "teach/quizsummit.html")


def submission_success(request):
    return render(request, "teach/submissionsuccess.html")



@login_required
def profile_view(request):
    # User model now contains all profile fields directly
    return render(request, "teach/profile.html", {"user": request.user})


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
    """
    Code Login from the same login page:
    - action=send   -> send OTP to user's email
    - action=verify -> verify OTP and login
    """
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

    # identifier = Email
    try:
        user = User.objects.get(email__iexact=identifier)
    except User.DoesNotExist:
        messages.error(request, "No account found with this email.")
        return redirect("login")

    # ===== SEND CODE =====
    if action == "send":
        otp = f"{random.randint(0, 999999):06d}"

        # deactivate old codes
        LoginCode.objects.filter(user=user, is_used=False).update(is_used=True)

        # create new code
        LoginCode.objects.create(user=user, code=otp)

        # send email (real send if EMAIL settings configured)
        send_mail(
            subject="Your Login Code",
            message=f"Your login code is: {otp}\nThis code expires in 10 minutes.",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[user.email],
            fail_silently=False,
        )

        messages.success(request, "Code sent to your email. Please check inbox/spam.")
        return redirect("login")

    # ===== VERIFY CODE =====
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
        user.email = request.POST.get("gmail", user.email)  # Update email if provided
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

