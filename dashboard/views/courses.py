from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_POST
from ..decorators import admin_required
from ..models import Course, Video, CourseEnrollment, Payment
import logging
import json

logger = logging.getLogger(__name__)


@login_required
def course_list(request):
    """List all courses for patients, manage for admin"""
    query = request.GET.get("q", "")
    page = request.GET.get("page", 1)
    is_admin = request.user.is_staff or request.user.is_superuser

    courses = Course.objects.filter(is_active=True)

    if query:
        courses = courses.filter(
            Q(title__icontains=query)
            | Q(teacher_name__icontains=query)
            | Q(tags__icontains=query)
        )

    # Pagination
    paginator = Paginator(courses, 9)
    try:
        courses_page = paginator.page(page)
    except PageNotAnInteger:
        courses_page = paginator.page(1)
    except EmptyPage:
        courses_page = paginator.page(paginator.num_pages)

    # Get user's enrollments
    user_enrollments = {}
    if not is_admin and request.user.is_authenticated:
        enrollments = CourseEnrollment.objects.filter(user=request.user)
        user_enrollments = {e.course_id: e for e in enrollments}

    context = {
        "courses": courses_page,
        "query": query,
        "paginator": paginator,
        "is_admin": is_admin,
        "user_enrollments": user_enrollments,
    }
    return render(request, "dashboard/courses/list.html", context)


@login_required
@admin_required
def course_create(request):
    if request.method == "POST":
        """Create a new course (admin only)"""
        title = request.POST.get("title")
        price = request.POST.get("price")
        teacher_name = request.POST.get("teacher_name")
        description = request.POST.get("description")
        tags = request.POST.get("tags", "")
        if not all([title, price, teacher_name]):
            return JsonResponse(
                {"success": False, "errors": ["يرجى ملء الحقول المطلوبة"]}
            )

        try:
            # Create course
            course = Course.objects.create(
                title=title,
                price=price,
                teacher_name=teacher_name,
                description=description,
                tags=tags,
                created_by=request.user,
            )

            # Handle thumbnail if uploaded
            if request.FILES.get("thumbnail"):
                course.thumbnail = request.FILES["thumbnail"]
                course.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "تم إنشاء الدورة بنجاح",
                    "redirect_url": reverse(
                        "dashboard:course_detail", args=[course.id]
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error creating course: {str(e)}")
            return JsonResponse(
                {
                    "success": False,
                    "errors": ["حدث خطأ أثناء إنشاء الدورة"],
                    "redirect_url": reverse("dashboard:course_list"),
                }
            )

    return render(request, "dashboard/courses/create.html")


@login_required
@admin_required
@require_POST
def video_upload(request, course_id):
    """Upload a video for a course (admin only)"""
    try:
        course = get_object_or_404(Course, id=course_id)

        title = request.POST.get("title")
        description = request.POST.get("description", "")
        video_file = request.FILES.get("video_file")
        order = request.POST.get("order", 0)

        if not video_file:
            return JsonResponse(
                {"success": False, "errors": ["لم يتم اختيار ملف الفيديو"]}
            )

        # Create video
        video = Video.objects.create(
            course=course,
            title=title,
            description=description,
            video_file=video_file,
            order=order,
        )

        # First video is automatically free
        if course.videos.count() == 1:
            video.is_free = True
            video.save()

        return JsonResponse(
            {
                "success": True,
                "message": "تم رفع الفيديو بنجاح",
                "video_id": video.id,
                "is_free": video.is_free,
            }
        )

    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        return JsonResponse({"success": False, "errors": ["حدث خطأ أثناء رفع الفيديو"]})


@login_required
@admin_required
def course_delete(request, course_id):
    """Delete a course (admin only)"""
    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        course.delete()
        return JsonResponse({"success": True, "message": "تم حذف الدورة بنجاح"})

    return render(request, "dashboard/courses/confirm_delete.html", {"course": course})


@login_required
@admin_required
def course_edit(request, course_id):
    """Edit a course (admin only)"""
    course = get_object_or_404(Course, id=course_id)

    if request.method == "POST":
        try:
            # Update course fields
            course.title = request.POST.get("title")
            course.price = request.POST.get("price")
            course.teacher_name = request.POST.get("teacher_name")
            course.description = request.POST.get("description")
            course.tags = request.POST.get("tags", "")
            course.is_active = request.POST.get("is_active") == "on"

            # Handle thumbnail if uploaded
            if request.FILES.get("thumbnail"):
                course.thumbnail = request.FILES["thumbnail"]

            course.save()

            messages.success(request, "تم تحديث الدورة بنجاح")
            return redirect("dashboard:course_detail", course_id=course.id)

        except Exception as e:
            logger.error(f"Error updating course: {str(e)}")
            messages.error(request, "حدث خطأ أثناء تحديث الدورة")

    context = {
        "course": course,
    }
    return render(request, "dashboard/courses/edit.html", context)


@login_required
def course_detail(request, course_id):
    """View course details and videos"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    videos = course.videos.all()

    # Check if user is enrolled
    enrollment = None
    has_paid_access = False

    if request.user.is_authenticated:
        try:
            enrollment = CourseEnrollment.objects.get(user=request.user, course=course)
            has_paid_access = (
                enrollment.status == CourseEnrollment.EnrollmentStatus.APPROVED
            )
        except CourseEnrollment.DoesNotExist:
            pass

    is_admin = request.user.is_staff or request.user.is_superuser

    # Get enrollment counts
    approved_count = course.enrollments.filter(
        status=CourseEnrollment.EnrollmentStatus.APPROVED
    ).count()
    pending_count = course.enrollments.filter(
        status=CourseEnrollment.EnrollmentStatus.PENDING
    ).count()
    rejected_count = course.enrollments.filter(
        status=CourseEnrollment.EnrollmentStatus.REJECTED
    ).count()

    # Get payments for this course (admin only)
    payments = None
    payment_stats = None
    if is_admin:
        payments = Payment.objects.filter(enrollment__course=course).order_by(
            "-created_at"
        )
        payment_stats = {
            "pending": payments.filter(status=Payment.PaymentStatus.PENDING).count(),
            "approved": payments.filter(status=Payment.PaymentStatus.APPROVED).count(),
            "rejected": payments.filter(status=Payment.PaymentStatus.REJECTED).count(),
        }

    context = {
        "course": course,
        "videos": videos,
        "enrollment": enrollment,
        "has_paid_access": has_paid_access or is_admin,
        "is_admin": is_admin,
        "approved_count": approved_count,
        "pending_count": pending_count,
        "rejected_count": rejected_count,
        "payments": payments,
        "payment_stats": payment_stats,
    }
    return render(request, "dashboard/courses/detail.html", context)


@login_required
def course_enroll(request, course_id):
    """Enroll in a course (for free courses) or initiate payment"""
    course = get_object_or_404(Course, id=course_id, is_active=True)

    if request.method == "POST":
        try:
            # Check if already enrolled
            enrollment, created = CourseEnrollment.objects.get_or_create(
                user=request.user,
                course=course,
                defaults={"status": CourseEnrollment.EnrollmentStatus.PENDING},
            )

            if not created:
                return JsonResponse(
                    {"success": False, "errors": ["أنت مسجل بالفعل في هذه الدورة"]}
                )

            # If course is free, auto-approve
            if course.price == 0:
                enrollment.status = CourseEnrollment.EnrollmentStatus.APPROVED
                enrollment.save()
                return JsonResponse(
                    {
                        "success": True,
                        "message": "تم التسجيل في الدورة بنجاح",
                        "redirect_url": reverse(
                            "dashboard:course_detail", args=[course_id]
                        ),
                    }
                )

            # For paid courses, return payment required
            return JsonResponse(
                {
                    "success": True,
                    "message": "تم بدء عملية التسجيل، يرجى إكمال الدفع",
                    "requires_payment": True,
                    "enrollment_id": enrollment.id,
                }
            )

        except Exception as e:
            logger.error(f"Error enrolling in course: {str(e)}")
            return JsonResponse({"success": False, "errors": ["حدث خطأ أثناء التسجيل"]})

    return render(request, "dashboard/courses/enroll.html", {"course": course})


@login_required
def payment_submit(request, enrollment_id):
    """Submit payment receipt for course enrollment"""
    enrollment = get_object_or_404(
        CourseEnrollment,
        id=enrollment_id,
        user=request.user,
        status=CourseEnrollment.EnrollmentStatus.PENDING,
    )

    if request.method == "POST":
        try:
            receipt_image = request.FILES.get("receipt_image")
            amount = request.POST.get("amount")
            notes = request.POST.get("notes", "")

            if not receipt_image:
                return JsonResponse(
                    {"success": False, "errors": ["يرجى رفع صورة الإيصال"]}
                )

            # Create payment
            Payment.objects.create(
                enrollment=enrollment,
                receipt_image=receipt_image,
                amount=amount or enrollment.course.price,
                notes=notes,
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "تم إرسال إيصال الدفع بنجاح، سيتم مراجعته من قبل الإدارة",
                    "redirect_url": reverse("dashboard:course_list"),
                }
            )

        except Exception as e:
            logger.error(f"Error submitting payment: {str(e)}")
            return JsonResponse(
                {"success": False, "errors": ["حدث خطأ أثناء إرسال الإيصال"]}
            )

    return render(
        request,
        "dashboard/courses/payment.html",
        {"enrollment": enrollment, "course": enrollment.course},
    )


@login_required
@admin_required
def payment_review(request, payment_id):
    """Review and approve/reject payment (admin only)"""
    payment = get_object_or_404(Payment, id=payment_id)

    if request.method == "POST":
        try:
            action = request.POST.get("action")
            notes = request.POST.get("notes", "")

            if action == "approve":
                payment.status = Payment.PaymentStatus.APPROVED
                payment.enrollment.status = CourseEnrollment.EnrollmentStatus.APPROVED
                payment.enrollment.approved_by = request.user
            elif action == "reject":
                payment.status = Payment.PaymentStatus.REJECTED
                payment.enrollment.status = CourseEnrollment.EnrollmentStatus.REJECTED
            else:
                return JsonResponse({"success": False, "errors": ["إجراء غير صالح"]})

            payment.notes = notes
            payment.reviewed_by = request.user
            payment.save()
            payment.enrollment.save()

            return JsonResponse({"success": True, "message": "تمت مراجعة الدفع بنجاح"})

        except Exception as e:
            logger.error(f"Error reviewing payment: {str(e)}")
            return JsonResponse(
                {"success": False, "errors": ["حدث خطأ أثناء مراجعة الدفع"]}
            )

    return render(
        request,
        "dashboard/courses/payment_review.html",
        {
            "payment": payment,
            "enrollment": payment.enrollment,
            "course": payment.enrollment.course,
        },
    )


@login_required
@admin_required
def payment_list(request):
    """List all pending payments for admin review"""
    status = request.GET.get("status", "pending")

    payments = Payment.objects.filter(status=status).select_related(
        "enrollment__user", "enrollment__course"
    )

    # Get counts for each status
    pending_count = Payment.objects.filter(status="pending").count()
    approved_count = Payment.objects.filter(status="approved").count()
    rejected_count = Payment.objects.filter(status="rejected").count()

    context = {
        "payments": payments,
        "status": status,
        "status_choices": [
            ("pending", "قيد المراجعة"),
            ("approved", "مقبول"),
            ("rejected", "مرفوض"),
        ],
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
    }
    return render(request, "dashboard/courses/payment_list.html", context)


@login_required
@admin_required
def enrollment_approve(request, enrollment_id):
    """Approve enrollment (admin only)"""
    enrollment = get_object_or_404(CourseEnrollment, id=enrollment_id)

    if request.method == "POST":
        try:
            notes = request.POST.get("notes", "")

            enrollment.status = CourseEnrollment.EnrollmentStatus.APPROVED
            enrollment.approved_by = request.user
            enrollment.notes = notes
            enrollment.save()

            # Also approve associated payment if exists
            if hasattr(enrollment, "payment"):
                enrollment.payment.status = Payment.PaymentStatus.APPROVED
                enrollment.payment.reviewed_by = request.user
                enrollment.payment.save()

            return JsonResponse({"success": True, "message": "تم قبول التسجيل بنجاح"})
        except Exception as e:
            logger.error(f"Error approving enrollment: {str(e)}")
            return JsonResponse(
                {"success": False, "errors": ["حدث خطأ أثناء قبول التسجيل"]}
            )

    return JsonResponse({"success": False, "errors": ["طريقة طلب غير صالحة"]})


@login_required
@admin_required
def enrollment_reject(request, enrollment_id):
    """Reject enrollment (admin only)"""
    enrollment = get_object_or_404(CourseEnrollment, id=enrollment_id)

    if request.method == "POST":
        try:
            notes = request.POST.get("notes", "")

            if not notes:
                return JsonResponse(
                    {"success": False, "errors": ["يرجى إدخال سبب الرفض"]}
                )

            enrollment.status = CourseEnrollment.EnrollmentStatus.REJECTED
            enrollment.notes = notes
            enrollment.save()

            # Also reject associated payment if exists
            if hasattr(enrollment, "payment"):
                enrollment.payment.status = Payment.PaymentStatus.REJECTED
                enrollment.payment.reviewed_by = request.user
                enrollment.payment.save()

            return JsonResponse({"success": True, "message": "تم رفض التسجيل"})
        except Exception as e:
            logger.error(f"Error rejecting enrollment: {str(e)}")
            return JsonResponse(
                {"success": False, "errors": ["حدث خطأ أثناء رفض التسجيل"]}
            )

    return JsonResponse({"success": False, "errors": ["طريقة طلب غير صالحة"]})


@login_required
@admin_required
def enrollment_revoke(request, enrollment_id):
    """Revoke approved enrollment (admin only)"""
    enrollment = get_object_or_404(CourseEnrollment, id=enrollment_id)

    if request.method == "POST":
        try:
            enrollment.status = CourseEnrollment.EnrollmentStatus.PENDING
            enrollment.approved_by = None
            enrollment.save()

            # Also revoke associated payment if exists
            if hasattr(enrollment, "payment"):
                enrollment.payment.status = Payment.PaymentStatus.PENDING
                enrollment.payment.reviewed_by = None
                enrollment.payment.save()

            return JsonResponse({"success": True, "message": "تم سحب القبول بنجاح"})
        except Exception as e:
            logger.error(f"Error revoking enrollment: {str(e)}")
            return JsonResponse(
                {"success": False, "errors": ["حدث خطأ أثناء سحب القبول"]}
            )

    return JsonResponse({"success": False, "errors": ["طريقة طلب غير صالحة"]})


@login_required
def my_courses(request):
    """List user's enrolled courses"""
    enrollments = (
        CourseEnrollment.objects.filter(user=request.user)
        .select_related("course")
        .order_by("-enrolled_at")
    )

    context = {
        "enrollments": enrollments,
    }
    return render(request, "dashboard/courses/my_courses.html", context)
