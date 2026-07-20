from django.urls import path
from dashboard.views import (
    main,
    settings,
    users,
    medical_cases,
    courses,
    notifications,
    payments,
    articles,
    games,
    treatment_plans,
)

app_name = "dashboard"

urlpatterns = [
    path("", main.index, name="index"),
    path("test-notification/", main.test_notification, name="test_notification"),
    # User Management
    path("users/", users.user_list, name="user_list"),
    path("users/create-doctor/", users.doctor_create, name="doctor_create"),
    path("users/<int:pk>/", users.user_detail, name="user_detail"),
    path("users/<int:pk>/delete/", users.user_delete, name="user_delete"),
    path(
        "users/<int:pk>/toggle-status/",
        users.user_toggle_status,
        name="user_toggle_status",
    ),
    path("profile/update/", users.profile_update, name="profile_update"),
    # Medical Cases
    path("medical-cases/", medical_cases.medical_case_list, name="medical_case_list"),
    path(
        "medical-cases/create/",
        medical_cases.medical_case_create,
        name="medical_case_create",
    ),
    path(
        "medical-cases/<str:case_type>/<int:case_id>/delete/",
        medical_cases.medical_case_delete,
        name="medical_case_delete",
    ),
    # Courses
    path("courses/", courses.course_list, name="course_list"),
    path("courses/create/", courses.course_create, name="course_create"),
    path("courses/<int:course_id>/", courses.course_detail, name="course_detail"),
    path("courses/<int:course_id>/edit/", courses.course_edit, name="course_edit"),
    path(
        "courses/<int:course_id>/delete/", courses.course_delete, name="course_delete"
    ),
    path(
        "courses/<int:course_id>/videos/upload/",
        courses.video_upload,
        name="video_upload",
    ),
    path(
        "courses/<int:course_id>/enroll/", courses.course_enroll, name="course_enroll"
    ),
    path(
        "courses/payment/<int:enrollment_id>/submit/",
        payments.payment_submit,
        name="payment_submit",
    ),
    # Payments (Generic)
    path("payments/", payments.payment_list, name="payment_list"),
    path(
        "payments/<int:payment_id>/ajax/",
        payments.payment_detail_ajax,
        name="payment_detail_ajax",
    ),
    path(
        "payments/<int:payment_id>/review-ajax/",
        payments.payment_review_ajax,
        name="payment_review_ajax",
    ),
    # Enrollment Management
    path(
        "courses/enrollment/<int:enrollment_id>/approve/",
        courses.enrollment_approve,
        name="enrollment_approve",
    ),
    path(
        "courses/enrollment/<int:enrollment_id>/reject/",
        courses.enrollment_reject,
        name="enrollment_reject",
    ),
    path(
        "courses/enrollment/<int:enrollment_id>/revoke/",
        courses.enrollment_revoke,
        name="enrollment_revoke",
    ),
    path("courses/my-courses/", courses.my_courses, name="my_courses"),
    # Notifications
    path(
        "notifications/stream/",
        notifications.notifications_stream,
        name="notifications_stream",
    ),
    path(
        "notifications/unread-count/",
        notifications.get_unread_count,
        name="notifications_unread_count",
    ),
    path(
        "notifications/list/",
        notifications.get_notifications,
        name="notifications_list",
    ),
    path(
        "notifications/<int:notification_id>/read/",
        notifications.mark_as_read,
        name="notification_mark_read",
    ),
    path(
        "notifications/mark-all-read/",
        notifications.mark_all_as_read,
        name="notifications_mark_all_read",
    ),
    path(
        "notifications/<int:notification_id>/delete/",
        notifications.delete_notification,
        name="notification_delete",
    ),
    # Articles
    path("articles/", articles.article_list, name="article_list"),
    path("articles/create/", articles.article_create, name="article_create"),
    path("articles/<int:pk>/edit/", articles.article_edit, name="article_edit"),
    path("articles/<int:pk>/delete/", articles.article_delete, name="article_delete"),
    # Games
    path("games/", games.game_list, name="game_list"),
    path("games/create/", games.game_create, name="game_create"),
    path("games/<int:pk>/edit/", games.game_edit, name="game_edit"),
    path("games/<int:pk>/delete/", games.game_delete, name="game_delete"),
    path("games/orders/", games.game_order_list, name="game_order_list"),
    path("games/orders/<int:pk>/status/", games.game_order_status, name="game_order_status"),
    # Treatment Plans
    path(
        "treatment-plans/generate/<str:case_type>/<int:case_id>/",
        treatment_plans.generate_plan,
        name="treatment_plan_generate",
    ),
    path(
        "treatment-plans/get/<str:case_type>/<int:case_id>/",
        treatment_plans.get_plan,
        name="treatment_plan_get",
    ),
]
