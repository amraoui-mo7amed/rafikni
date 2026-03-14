from django.shortcuts import render, get_object_or_404
from dashboard.models import Course, CourseEnrollment, Payment
from django.contrib.contenttypes.models import ContentType


def course_list(request):
    """Public list of all active courses"""
    courses = Course.objects.filter(is_active=True).order_by("-created_at")
    return render(request, "courses/list.html", {"courses": courses})


def course_detail(request, course_id):
    """Detailed view of a course with enrollment/payment options"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    videos = course.videos.all()

    enrollment = None
    has_payment = False

    if request.user.is_authenticated and request.user.profile.role == "patient":
        enrollment = CourseEnrollment.objects.filter(
            user=request.user, course=course
        ).first()
        if enrollment:
            # Check if payment exists for this enrollment
            enrollment_type = ContentType.objects.get_for_model(CourseEnrollment)
            has_payment = Payment.objects.filter(
                content_type=enrollment_type, object_id=enrollment.id
            ).exists()

    context = {
        "course": course,
        "videos": videos,
        "enrollment": enrollment,
        "has_payment": has_payment,
    }
    return render(request, "courses/detail.html", context)
