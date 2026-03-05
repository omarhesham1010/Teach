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
    path("course-content/", views.course_content, name="course_content"),##################
    path("assignment/", views.assignment, name="assignment"),
    path("assignment/<int:assignment_id>/", views.assignment_detail_view, name="assignment_detail"),
    path("assignment/<int:assignment_id>/download/", views.assignment_file_download_view, name="assignment_file_download"),
    path("enrollment/", views.enrollment, name="enrollment"),
    path("signup/", views.signup, name="signup"),
    path("quiz/", views.quiz, name="quiz"),
    path("quiz/<int:quiz_id>/", views.quiz_detail_view, name="quiz_detail"),
    path("quiz/<int:quiz_id>/results/", views.quiz_results_view, name="quiz_results"),
    path("quiz/<int:quiz_id>/submit/", views.quiz_submit_view, name="quiz_submit"),
    path("submission-success/", views.submission_success, name="submission_success"),
    path("profile/", views.profile_view, name="profile"),
    path("settings/", views.settings_view, name="settings"),
    path("messages/", views.messages_view, name="messages"),
    path("messages/chat/<int:conversation_id>/", views.chat_detail_view, name="chat_detail"),
    path("messages/send/", views.send_message_view, name="send_message"),
    path("messages/search-user/", views.search_user_for_chat_view, name="search_user_chat"),
    path("notes/", views.notes_view, name="notes"),
    path("discussion/", views.discussion_view, name="discussion"),
    path("my-courses/", views.my_courses_view, name="my_courses"),
    path("wallet/add/", views.add_money_to_wallet, name="add_money_to_wallet"),
    path("course-content/", views.course_content, name="course_content_static"), ##################
    path("api/toggle-theme/", views.toggle_theme, name="toggle_theme"),
    # Instructor assignment dashboards
    path(
        "instructor/assignments/",
        views.instructor_assignments_dashboard,
        name="instructor_assignments_dashboard",
    ),
    path(
        "instructor/assignments/<int:assignment_id>/submissions/",
        views.instructor_assignment_submissions,
        name="instructor_assignment_submissions",
    ),
    path(
        "instructor/assignments/<int:assignment_id>/submissions/<str:national_id>/grade/",
        views.instructor_grade_submission,
        name="instructor_grade_submission",
    ),
    path(
        "instructor/assignments/<int:assignment_id>/submissions/<str:national_id>/history/",
        views.instructor_submission_history,
        name="instructor_submission_history",
    ),
    path(
        "instructor/submission-history/<int:history_id>/download/",
        views.instructor_history_file_download,
        name="instructor_history_file_download",
    ),
]
