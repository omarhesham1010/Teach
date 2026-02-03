from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required


def login_view(request):
   
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("instructor")
        messages.error(request, "Invalid username or password.")

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


def profile_view(request):
    return render(request, "teach/profile.html")


def settings_view(request):
    return render(request, "teach/settings.html")


def messages_view(request):
    return render(request, "teach/messages.html")


def notes_view(request):
    return render(request, "teach/notes.html")


def discussion_view(request):
    return render(request, "teach/discussion.html")
