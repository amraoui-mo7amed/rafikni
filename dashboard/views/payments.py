from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from ..decorators import admin_required
from ..models import Payment, CourseEnrollment, Course
from ..utils import notify_user, notify_admins
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


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
            payment = Payment.objects.create(
                user=request.user,
                content_object=enrollment,
                receipt_image=receipt_image,
                amount=amount or enrollment.course.price,
                notes=notes,
            )

            # Notify admins
            notify_admins(
                request,
                title="إيصال دفع جديد",
                message=f"قام المستخدم {request.user.username} برفع إيصال دفع لدورة {enrollment.course.title}",
                notification_type="info",
                link=reverse("dashboard:payment_list"),
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
def payment_list(request):
    """List all payments with filters (Admin only)"""
    query = request.GET.get("q", "")
    status = request.GET.get("status", "")
    content_type_id = request.GET.get("content_type", "")
    page = request.GET.get("page", 1)

    payments = (
        Payment.objects.all()
        .select_related("user", "reviewed_by", "content_type")
        .order_by("-created_at")
    )

    if query:
        payments = payments.filter(
            Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(amount__icontains=query)
        )

    if status:
        payments = payments.filter(status=status)

    if content_type_id:
        if content_type_id == "medical":
            # Filter for any of the medical case content types
            medical_cts = ContentType.objects.filter(
                app_label="dashboard", model__icontains="medicalcase"
            )
            payments = payments.filter(content_type__in=medical_cts)
        else:
            payments = payments.filter(content_type_id=content_type_id)

    # Pagination
    paginator = Paginator(payments, 15)
    try:
        payments_page = paginator.page(page)
    except PageNotAnInteger:
        payments_page = paginator.page(1)
    except EmptyPage:
        payments_page = paginator.page(paginator.num_pages)

    status_choices = Payment.PaymentStatus.choices

    # Get available content types for filtering
    course_ct = ContentType.objects.get_for_model(CourseEnrollment)
    type_choices = [
        (str(course_ct.id), "دورات تعليمية"),
        ("medical", "حالات طبية"),
    ]

    context = {
        "payments": payments_page,
        "query": query,
        "status": status,
        "content_type": content_type_id,
        "status_choices": status_choices,
        "type_choices": type_choices,
        "paginator": paginator,
    }
    return render(request, "dashboard/payments/list.html", context)


@login_required
@admin_required
def payment_detail_ajax(request, payment_id):
    """Return payment details for modal content"""
    payment = get_object_or_404(Payment, id=payment_id)

    html = render_to_string(
        "dashboard/payments/partials/payment_detail_modal.html",
        {
            "payment": payment,
            "content_object": payment.content_object,
        },
        request=request,
    )

    return JsonResponse({"success": True, "html": html})


@login_required
@admin_required
def payment_review_ajax(request, payment_id):
    """Review and approve/reject payment via AJAX"""
    payment = get_object_or_404(Payment, id=payment_id)

    if request.method == "POST":
        try:
            action = request.POST.get("action")
            notes = request.POST.get("notes", "")

            if action == "approve":
                payment.status = Payment.PaymentStatus.APPROVED
                # Handle specific content objects
                if isinstance(payment.content_object, CourseEnrollment):
                    payment.content_object.status = (
                        CourseEnrollment.EnrollmentStatus.APPROVED
                    )
                    payment.content_object.approved_by = request.user
                    payment.content_object.approved_at = timezone.now()
                    payment.content_object.save()

                status_msg = "مقبول"
                notify_type = "success"
            elif action == "reject":
                payment.status = Payment.PaymentStatus.REJECTED
                if isinstance(payment.content_object, CourseEnrollment):
                    payment.content_object.status = (
                        CourseEnrollment.EnrollmentStatus.REJECTED
                    )
                    payment.content_object.save()

                status_msg = "مرفوض"
                notify_type = "error"
            else:
                return JsonResponse({"success": False, "errors": ["إجراء غير صالح"]})

            payment.notes = notes
            payment.reviewed_by = request.user
            payment.reviewed_at = timezone.now()
            payment.save()

            # Notify user
            title = f"تم مراجعة الدفع - {status_msg}"
            message = f"تم {status_msg} إيصال الدفع الخاص بك بمبلغ {payment.amount} د.ج"

            # Add specific details if it's a course
            if isinstance(payment.content_object, CourseEnrollment):
                message += f" لدورة {payment.content_object.course.title}"

            notify_user(
                payment.user,
                title=title,
                message=message,
                notification_type=notify_type,
            )

            return JsonResponse(
                {"success": True, "message": f"تم {status_msg} الدفع بنجاح"}
            )

        except Exception as e:
            logger.error(f"Error reviewing payment: {str(e)}")
            return JsonResponse({"success": False, "errors": [str(e)]})

    return JsonResponse({"success": False, "errors": ["طريقة طلب غير صالحة"]})
