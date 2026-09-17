"""
Educational Courses & Video Academy Router for Rafikni Platform.
Endpoints for public catalog, video gating, course enrollment, and admin curriculum management.
"""

from typing import Optional, List
from ninja import Router, Form, File, UploadedFile
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from dashboard.models import Course, Video, CourseEnrollment, Payment
from dashboard.utils import notify_user
from api.security import JWTAuth, AdminAuth
from api.utils import api_response, build_absolute_media_url
from api.serializers import (
    serialize_course_card,
    serialize_video,
)
from api.schemas.common import ApiResponseSchema
from api.schemas.courses import (
    CourseCardSchema,
    CourseDetailSchema,
    PaginatedCoursesSchema,
    EnrollmentResponseSchema,
    EnrolledCourseSchema,
    VideoStreamSchema,
)

router = Router()


@router.get("/", response=ApiResponseSchema[PaginatedCoursesSchema])
def list_courses(request, q: Optional[str] = None, page: int = 1):
    """
    Public catalog of all active educational courses.
    """
    courses = Course.objects.filter(is_active=True).prefetch_related("videos")
    if q:
        courses = courses.filter(
            Q(title__icontains=q) | Q(teacher_name__icontains=q) | Q(tags__icontains=q)
        )

    paginator = Paginator(courses, 12)
    try:
        courses_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        courses_page = paginator.page(1)

    items = [serialize_course_card(c, request, request.user if request.user.is_authenticated else None) for c in courses_page]

    pagination_data = {
        "page": courses_page.number,
        "num_pages": paginator.num_pages,
        "total_count": paginator.count,
        "has_next": courses_page.has_next(),
        "has_prev": courses_page.has_previous(),
    }

    return api_response(
        success=True,
        message="تم جلب الدورات بنجاح",
        data={"items": items, "pagination": pagination_data},
        status=200,
    )


@router.get("/{course_id}", response={200: ApiResponseSchema[CourseDetailSchema], 404: ApiResponseSchema[None]})
def get_course_detail(request, course_id: int):
    """
    Course syllabus and details. Video 0 is free; other videos are locked unless enrolled.
    """
    try:
        course = Course.objects.prefetch_related("videos").get(id=course_id, is_active=True)
    except Course.DoesNotExist:
        return api_response(success=False, message="الدورة غير موجودة", errors=["الدورة غير موجودة"], status=404)

    has_paid_access = False
    enrollment_status = None

    if request.user.is_authenticated:
        if request.user.is_superuser or getattr(request.user.profile, "role", None) == "admin":
            has_paid_access = True
        else:
            enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
            if enrollment:
                enrollment_status = enrollment.status
                has_paid_access = (enrollment.status == CourseEnrollment.EnrollmentStatus.APPROVED)

    videos = course.videos.all().order_by("order", "created_at")
    serialized_videos = [serialize_video(v, request, has_access=has_paid_access) for v in videos]

    thumbnail_url = build_absolute_media_url(request, course.thumbnail)

    data = {
        "id": course.id,
        "title": course.title,
        "price": float(course.price),
        "teacher_name": course.teacher_name,
        "description": course.description,
        "thumbnail": thumbnail_url,
        "tags": course.get_tags_list(),
        "video_count": len(serialized_videos),
        "videos": serialized_videos,
        "has_paid_access": has_paid_access,
        "enrollment_status": enrollment_status,
    }

    return api_response(success=True, message="تم جلب تفاصيل الدورة بنجاح", data=data, status=200)


@router.post("/{course_id}/enroll", auth=JWTAuth(), response={200: ApiResponseSchema[EnrollmentResponseSchema], 400: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def enroll_course(request, course_id: int):
    """
    Enroll in an educational course.
    Free courses are automatically approved; paid courses require payment receipt upload.
    """
    try:
        course = Course.objects.get(id=course_id, is_active=True)
    except Course.DoesNotExist:
        return api_response(success=False, message="الدورة غير موجودة", errors=["الدورة غير موجودة"], status=404)

    enrollment, created = CourseEnrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={"status": CourseEnrollment.EnrollmentStatus.PENDING},
    )

    if not created and enrollment.status == CourseEnrollment.EnrollmentStatus.APPROVED:
        return api_response(
            success=False,
            message="أنت مسجل بالفعل في هذه الدورة ومقبول اشتراكك",
            errors=["أنت مسجل بالفعل في هذه الدورة ومقبول اشتراكك"],
            status=400,
        )

    # Free course
    if course.price == 0:
        enrollment.status = CourseEnrollment.EnrollmentStatus.APPROVED
        enrollment.save()
        return api_response(
            success=True,
            message="تم التسجيل في الدورة المجانية بنجاح",
            data={
                "enrollment_id": enrollment.id,
                "status": enrollment.status,
                "requires_payment": False,
                "message": "تم تفعيل اشتراكك تلقائياً.",
            },
            status=200,
        )

    # Paid course
    return api_response(
        success=True,
        message="تم بدء عملية التسجيل، يرجى إكمال إرسال وصل الدفع",
        data={
            "enrollment_id": enrollment.id,
            "status": enrollment.status,
            "requires_payment": True,
            "message": "يرجى رفع إيصال الدفع عبر الحساب البريدي للمراجعة.",
        },
        status=200,
    )


@router.get("/my/enrollments", auth=JWTAuth(), response=ApiResponseSchema[List[EnrolledCourseSchema]])
def get_my_courses(request):
    """
    Retrieve all courses enrolled by the currently authenticated user.
    """
    enrollments = (
        CourseEnrollment.objects.filter(user=request.user)
        .select_related("course")
        .prefetch_related("course__videos")
        .order_by("-enrolled_at")
    )

    items = []
    for e in enrollments:
        items.append({
            "enrollment_id": e.id,
            "status": e.status,
            "status_display": e.get_status_display(),
            "enrolled_at": e.enrolled_at.strftime("%Y-%m-%d %H:%M"),
            "course": serialize_course_card(e.course, request, request.user),
        })

    return api_response(success=True, message="تم جلب دوراتي بنجاح", data=items, status=200)


@router.get("/{course_id}/videos/{video_id}", response={200: ApiResponseSchema[VideoStreamSchema], 403: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def get_video_stream_info(request, course_id: int, video_id: int):
    """
    Get direct media streaming URL for a course video.
    Free videos are open; paid videos require approved enrollment or admin access.
    """
    try:
        video = Video.objects.select_related("course").get(id=video_id, course_id=course_id)
    except Video.DoesNotExist:
        return api_response(success=False, message="الفيديو غير موجود", errors=["الفيديو غير موجود"], status=404)

    has_access = False
    if video.is_free:
        has_access = True
    elif request.user.is_authenticated:
        if request.user.is_superuser or getattr(request.user.profile, "role", None) == "admin":
            has_access = True
        else:
            enrollment = CourseEnrollment.objects.filter(
                user=request.user, course_id=course_id, status=CourseEnrollment.EnrollmentStatus.APPROVED
            ).first()
            if enrollment:
                has_access = True

    if not has_access:
        return api_response(
            success=False,
            message="هذا الفيديو مخصص للمشتركين المسجلين فقط. يرجى الاشتراك للوصول للمحتوى.",
            errors=["هذا الفيديو مخصص للمشتركين المسجلين فقط."],
            status=403,
        )

    video_url = build_absolute_media_url(request, video.video_file)

    duration_str = None
    if video.duration:
        total_seconds = int(video.duration.total_seconds())
        duration_str = f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"

    data = {
        "id": video.id,
        "course_id": video.course.id,
        "course_title": video.course.title,
        "title": video.title,
        "description": video.description or "",
        "video_url": video_url,
        "duration": duration_str,
        "is_free": video.is_free,
    }

    return api_response(success=True, message="تم تجهيز الفيديو للتشغيل", data=data, status=200)


# ---------------- Admin Operations ----------------

@router.post("/", auth=AdminAuth(), response={201: ApiResponseSchema[CourseCardSchema], 400: ApiResponseSchema[None]})
def create_course(
    request,
    title: str = Form(...),
    price: float = Form(...),
    teacher_name: str = Form(...),
    description: str = Form(...),
    tags: Optional[str] = Form(""),
    thumbnail: Optional[UploadedFile] = File(None),
):
    """Admin: Create a new educational course."""
    try:
        course = Course.objects.create(
            title=title,
            price=price,
            teacher_name=teacher_name,
            description=description,
            tags=tags or "",
            thumbnail=thumbnail,
            created_by=request.user,
        )
        return api_response(
            success=True,
            message="تم إنشاء الدورة بنجاح",
            data=serialize_course_card(course, request, request.user),
            status=201,
        )
    except Exception as e:
        return api_response(success=False, message="فشل إنشاء الدورة", errors=[str(e)], status=400)


@router.delete("/{course_id}", auth=AdminAuth(), response={200: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def delete_course(request, course_id: int):
    """Admin: Delete an educational course."""
    try:
        course = Course.objects.get(id=course_id)
        course.delete()
        return api_response(success=True, message="تم حذف الدورة بنجاح", status=200)
    except Course.DoesNotExist:
        return api_response(success=False, message="الدورة غير موجودة", errors=["الدورة غير موجودة"], status=404)


@router.post("/{course_id}/videos", auth=AdminAuth(), response={201: ApiResponseSchema[dict], 400: ApiResponseSchema[None]})
def upload_course_video(
    request,
    course_id: int,
    title: str = Form(...),
    description: Optional[str] = Form(""),
    order: int = Form(0),
    video_file: UploadedFile = File(...),
):
    """Admin: Upload an MP4 video for a course."""
    try:
        course = Course.objects.get(id=course_id)
        video = Video.objects.create(
            course=course,
            title=title,
            description=description or "",
            video_file=video_file,
            order=order,
        )
        if course.videos.count() == 1:
            video.is_free = True
            video.save()

        return api_response(
            success=True,
            message="تم رفع الفيديو بنجاح",
            data={"video_id": video.id, "is_free": video.is_free},
            status=201,
        )
    except Exception as e:
        return api_response(success=False, message="فشل رفع الفيديو", errors=[str(e)], status=400)


@router.post("/enrollments/{enrollment_id}/approve", auth=AdminAuth(), response={200: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def approve_course_enrollment(request, enrollment_id: int):
    """Admin: Approve course enrollment and linked payment."""
    try:
        enrollment = CourseEnrollment.objects.select_related("course", "user").get(id=enrollment_id)
        enrollment.status = CourseEnrollment.EnrollmentStatus.APPROVED
        enrollment.approved_by = request.user
        enrollment.save()

        # Synchronize payment
        enrollment_type = ContentType.objects.get_for_model(CourseEnrollment)
        payment = Payment.objects.filter(content_type=enrollment_type, object_id=enrollment.id).first()
        if payment:
            payment.status = Payment.PaymentStatus.APPROVED
            payment.reviewed_by = request.user
            payment.save()

        notify_user(
            enrollment.user,
            title="تم قبول التسجيل",
            message=f"تم قبول تسجيلك في دورة {enrollment.course.title}. يمكنك الآن الوصول للمحتوى الكامل.",
            notification_type="success",
        )
        return api_response(success=True, message="تم قبول التسجيل بنجاح", status=200)
    except CourseEnrollment.DoesNotExist:
        return api_response(success=False, message="التسجيل غير موجود", errors=["التسجيل غير موجود"], status=404)
