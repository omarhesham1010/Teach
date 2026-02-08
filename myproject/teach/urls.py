from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("reset-password/", views.reset_password, name="reset_password"),
    path("login/code/", views.login_code_view, name="login_code"),
    path("profile/edit/", views.edit_user_profile, name="edit_user_profile"),
    path("instructor/", views.instructor, name="instructor"),
    path("courses/", views.courses, name="courses"),
    path("course-details/", views.course_details, name="course_details"),
    path("course-content/", views.course_content, name="course_content"),
    path("assignment/", views.assignment, name="assignment"),
    path("enrollment/", views.enrollment, name="enrollment"),
    path("signup/", views.signup, name="signup"),
    path("quiz/", views.quiz, name="quiz"),
    path("quiz-submit/", views.quiz_submit, name="quiz_submit"),
    path("submission-success/", views.submission_success, name="submission_success"),
    path("profile/", views.profile_view, name="profile"),
    path("settings/", views.settings_view, name="settings"),
    path("messages/", views.messages_view, name="messages"),
    path("notes/", views.notes_view, name="notes"),
    path("discussion/", views.discussion_view, name="discussion"),
]
