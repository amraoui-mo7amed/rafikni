"""
Payments & Verification Router for Rafikni Platform.
Handles course payment receipt submission and administrative payment reviews.
Enforces atomic synchronization and notification rules.
"""

from typing import Optional
from ninja import Router, File, UploadedFile
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from dashboard.models import (
    Payment,
    CourseEnrollment,
    ChildMedicalCase,
    AdultMedicalCase,
    ElderlyMedicalCase,
)
from dashboard.utils import create_payment, notify_user, notify_admins
from api.security import JWTAuth, AdminAuth
from api.utils import api_response
from api.serializers import serialize_payment
from api.schemas.common import ApiResponseSchema
from api.schemas.payments import (
    PaymentDetailSchema,
    PaginatedPaymentsSchema,
    ReviewPaymentSchema,
)

router = Router()


@router.post("/course-enrollment/{enrollment_id}", auth=JWTAuth(), response={201: ApiResponseSchema[PaymentDetailSchema], 400: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def submit_course_payment_receipt(
    request,
    enrollment_id: int,
    receipt_image: UploadedFile = File(...),
):
    """
    Submit a payment receipt image for a pending course enrollment.
    Created inside an atomic transaction; notifies platform administrators.
    """
    try:
        enrollment = CourseEnrollment.objects.select_related("course").get(
            id=enrollment_id,
            user=request.user,
            status=CourseEnrollment.EnrollmentStatus.PENDING,
        )
    except CourseEnrollment.DoesNotExist:
        return api_response(
            success=False,
            message="طلب التسجيل غير موجود أو تمت معالجته بالفعل",
            errors=["طلب التسجيل غير موجود أو تمت معالجته بالفعل"],
            status=404,
        )

    if not receipt_image:
        return api_response(
            success=False,
            message="يرجى إرفاق صورة إيصال الدفع",
            errors=["يرجى إرفاق صورة إيصال الدفع"],
            status=400,
        )

    try:
        with transaction.atomic():
            payment = create_payment(
                user=request.user,
                content_object=enrollment,
                receipt_image=receipt_image,
            )

        notify_admins(
            title="إيصال دفع جديد لدورة",
            message=f"قام المستخدم {request.user.username} برفع إيصال دفع لدورة {enrollment.course.title}",
            notification_type="info",
            link=reverse("dashboard:payment_list"),
        )

        data = serialize_payment(payment, request)
        return api_response(
            success=True,
            message="تم إرسال إيصال الدفع بنجاح، سيتم مراجعته من قبل الإدارة",
            data=data,
            status=201,
        )
    except Exception as e:
        return api_response(
            success=False,
            message="حدث خطأ أثناء إرسال إيصال الدفع",
            errors=[str(e)],
            status=400,
        )


@router.get("/", auth=AdminAuth(), response=ApiResponseSchema[PaginatedPaymentsSchema])
def list_payments(
    request,
    status: Optional[str] = None,
    content_type: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
):
    """
    Admin: List all payment records with filters for status, type, and user name.
    """
    payments = (
        Payment.objects.all()
        .select_related("user", "user__profile", "reviewed_by", "content_type")
        .order_by("-created_at")
    )

    if q:
        payments = payments.filter(
            Q(user__username__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(user__email__icontains=q)
        )

    if status and status in Payment.PaymentStatus.values:
        payments = payments.filter(status=status)

    if content_type:
        if content_type == "medical":
            medical_cts = ContentType.objects.filter(app_label="dashboard", model__icontains="medicalcase")
            payments = payments.filter(content_type__in=medical_cts)
        elif content_type == "course":
            course_ct = ContentType.objects.get_for_model(CourseEnrollment)
            payments = payments.filter(content_type=course_ct)

    paginator = Paginator(payments, 15)
    try:
        payments_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        payments_page = paginator.page(1)

    items = [serialize_payment(p, request) for p in payments_page]

    pagination_data = {
        "page": payments_page.number,
        "num_pages": paginator.num_pages,
        "total_count": paginator.count,
        "has_next": payments_page.has_next(),
        "has_prev": payments_page.has_previous(),
    }

    return api_response(
        success=True,
        message="تم جلب المدفوعات بنجاح",
        data={"items": items, "pagination": pagination_data},
        status=200,
    )


@router.get("/{payment_id}", auth=AdminAuth(), response={200: ApiResponseSchema[PaymentDetailSchema], 404: ApiResponseSchema[None]})
def get_payment_detail(request, payment_id: int):
    """
    Admin: Retrieve complete payment details, receipt image, and associated entity.
    """
    try:
        payment = Payment.objects.select_related("user", "user__profile", "reviewed_by", "content_type").get(id=payment_id)
        data = serialize_payment(payment, request)
        return api_response(success=True, message="تم جلب تفاصيل الإيصال بنجاح", data=data, status=200)
    except Payment.DoesNotExist:
        return api_response(success=False, message="الإيصال غير موجود", errors=["الإيصال غير موجود"], status=404)


@router.post("/{payment_id}/review", auth=AdminAuth(), response={200: ApiResponseSchema[None], 400: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def review_payment(request, payment_id: int, data: ReviewPaymentSchema):
    """
    Admin: Approve or reject a payment receipt.
    Atomically synchronizes status of target CourseEnrollment or MedicalCase and dispatches alert to user.
    """
    try:
        payment = Payment.objects.select_related("content_type", "user").get(id=payment_id)
    except Payment.DoesNotExist:
        return api_response(success=False, message="الإيصال غير موجود", errors=["الإيصال غير موجود"], status=404)

    action = data.action.lower()
    if action not in ["approve", "reject"]:
        return api_response(success=False, message="إجراء غير صالح (يجب أن يكون approve أو reject)", errors=["إجراء غير صالح"], status=400)

    try:
        with transaction.atomic():
            if action == "approve":
                payment.status = Payment.PaymentStatus.APPROVED
                status_msg = "مقبول"
                notify_type = "success"

                # Synchronize target
                if isinstance(payment.content_object, CourseEnrollment):
                    payment.content_object.status = CourseEnrollment.EnrollmentStatus.APPROVED
                    payment.content_object.approved_by = request.user
                    payment.content_object.approved_at = timezone.now()
                    payment.content_object.save()
                elif isinstance(payment.content_object, (ChildMedicalCase, AdultMedicalCase, ElderlyMedicalCase)):
                    payment.content_object.is_approved = True
                    payment.content_object.save()

            else:  # reject
                payment.status = Payment.PaymentStatus.REJECTED
                status_msg = "مرفوض"
                notify_type = "error"

                if isinstance(payment.content_object, CourseEnrollment):
                    payment.content_object.status = CourseEnrollment.EnrollmentStatus.REJECTED
                    payment.content_object.save()
                elif isinstance(payment.content_object, (ChildMedicalCase, AdultMedicalCase, ElderlyMedicalCase)):
                    payment.content_object.is_approved = False
                    payment.content_object.save()

            payment.reviewed_by = request.user
            payment.reviewed_at = timezone.now()
            payment.save()

            # Disptach user notification
            target_desc = ""
            if isinstance(payment.content_object, CourseEnrollment):
                target_desc = f" لدورة {payment.content_object.course.title}"
            elif isinstance(payment.content_object, (ChildMedicalCase, AdultMedicalCase, ElderlyMedicalCase)):
                target_desc = f" لحالة {payment.content_object.full_name or 'طبيية'}"

            notify_user(
                payment.user,
                title=f"تمت مراجعة الدفع - {status_msg}",
                message=f"تم {status_msg} إيصال الدفع الخاص بك{target_desc}.",
                notification_type=notify_type,
            )

        return api_response(success=True, message=f"تم {status_msg} الدفع بنجاح", status=200)

    except Exception as e:
        return api_response(success=False, message="فشلت مراجعة الدفع", errors=[str(e)], status=400)
