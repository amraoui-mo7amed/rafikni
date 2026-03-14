
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from ..decorators import admin_required
from ..models import (
    Payment,
    CourseEnrollment,
    Course,
    ChildMedicalCase,
    AdultMedicalCase,
    ElderlyMedicalCase,
)
from ..utils import notify_user, notify_admins
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


@login_required
def payment_submit(request, enrollment_id):
    """
    Submit payment receipt for course enrollment.

    This view allows authenticated users to submit a payment receipt image
    for a pending course enrollment. The payment is created with PENDING
    status and admins are notified to review it.

    Decorators:
        @login_required: User must be logged in to access this view

    Args:
        request: HTTP request object
        enrollment_id (int): ID of the CourseEnrollment to pay for

    GET Behavior:
        - Renders the payment form template with enrollment and course info

    POST Behavior:
        - Validates receipt_image is provided
        - Creates Payment object with PENDING status linked to enrollment
        - Sends notification to admins about new payment
        - Returns JSON response with success/error message

    Returns:
        GET: HTML template (dashboard/courses/payment.html)
        POST: JsonResponse with success status and message

    Template Context:
        - enrollment: The CourseEnrollment object
        - course: The associated Course object

    Example Request:
        POST /dashboard/payments/submit/1/
        POST data: receipt_image=<file>

    Example Response (Success):
        {
            "success": True,
            "message": "تم إرسال إيصال الدفع بنجاح، سيتم مراجعته من قبل الإدارة",
            "redirect_url": "/dashboard/courses/"
        }
    """
    enrollment = get_object_or_404(
        CourseEnrollment,
        id=enrollment_id,
        user=request.user,
        status=CourseEnrollment.EnrollmentStatus.PENDING,
    )

    if request.method == "POST":
        try:
            receipt_image = request.FILES.get("receipt_image")

            if not receipt_image:
                return JsonResponse(
                    {"success": False, "errors": ["يرجى رفع صورة الإيصال"]}
                )

            # Create payment
            payment = Payment.objects.create(
                user=request.user,
                content_object=enrollment,
                receipt_image=receipt_image,
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
    """
    List all payments with filtering and pagination (Admin only).

    This view displays a paginated list of all payments in the system.
    Administrators can filter by:
        - Search query (user name)
        - Payment status (pending, approved, rejected)
        - Content type (course enrollment or medical case)

    Decorators:
        @login_required: User must be logged in
        @admin_required: User must have admin privileges

    Args:
        request: HTTP request object

    Query Parameters:
        q (str): Search query for user username/first_name/last_name
        status (str): Filter by payment status (pending/approved/rejected)
        content_type (str): Filter by content type (course enrollment ID or "medical")
        page (int): Page number for pagination

    GET Behavior:
        - Retrieves all payments with related user and content_type
        - Applies filters based on query parameters
        - Paginates results (15 per page)
        - Renders payment list template

    Returns:
        HtmlResponse: Rendered template with payments list

    Template Context:
        - payments: Paginated Payment queryset
        - query: Current search query
        - status: Current status filter
        - content_type: Current content type filter
        - status_choices: List of (value, label) for status dropdown
        - type_choices: List of (value, label) for content type dropdown
        - paginator: Paginator object for pagination controls

    Filtering Logic:
        1. If 'q' provided: Filter by user name (username, first_name, last_name)
        2. If 'status' provided: Filter by payment status
        3. If 'content_type' provided:
           - "medical": Filter for any medical case content types
           - Other: Filter for specific content type ID

    Example URL:
        /dashboard/payments/?q=john&status=pending&content_type=medical&page=2
    """
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
    """
    Retrieve payment details for modal display (AJAX).

    This view fetches a single payment by ID and renders it as HTML
    for display in a modal popup. Used when admin clicks on a payment
    to view its full details.

    Decorators:
        @login_required: User must be logged in
        @admin_required: User must have admin privileges

    Args:
        request: HTTP request object
        payment_id (int): ID of the Payment to retrieve

    GET Behavior:
        - Fetches the Payment object
        - Renders payment_details_modal.html template
        - Returns JSON with HTML content

    Returns:
        JsonResponse:
            - success: True with HTML in 'html' key
            - success: False with errors if payment not found

    Template Used:
        partials/payment_details_modal.html

    Template Context:
        - payment: The Payment object
        - content_object: The linked object (CourseEnrollment or MedicalCase)

    Example Request:
        GET /dashboard/payments/1/ajax/

    Example Response:
        {
            "success": True,
            "html": "<div class='...'>...</div>"
        }
    """
    payment = get_object_or_404(Payment, id=payment_id)

    html = render_to_string(
        "partials/payment_details_modal.html",
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
    """
    Review and approve/reject a payment (AJAX).

    This view handles the admin decision on a payment. When a payment
    is approved or rejected, it also updates the status of the linked
    content object (CourseEnrollment or MedicalCase).

    Decorators:
        @login_required: User must be logged in
        @admin_required: User must have admin privileges

    Args:
        request: HTTP request object
        payment_id (int): ID of the Payment to review

    POST Behavior:
        - Validates action is 'approve' or 'reject'
        - Updates Payment status accordingly
        - Updates linked content_object status:
            * CourseEnrollment: Sets status to APPROVED/REJECTED
            * MedicalCase (any): Sets is_approved to True/False
        - Records reviewed_by (admin) and reviewed_at (timestamp)
        - Sends notification to the user about the decision

    Returns:
        JsonResponse:
            - success: True with message on success
            - success: False with errors on failure

    Content Object Handling:

        CourseEnrollment (when approved):
            - payment.status = APPROVED
            - enrollment.status = APPROVED
            - enrollment.approved_by = request.user (admin)
            - enrollment.approved_at = timezone.now()

        CourseEnrollment (when rejected):
            - payment.status = REJECTED
            - enrollment.status = REJECTED

        MedicalCase (any type - when approved):
            - payment.status = APPROVED
            - case.is_approved = True

        MedicalCase (any type - when rejected):
            - payment.status = REJECTED
            - case.is_approved = False

    Notification Message:
        - For courses: "تم [مقبول/مرفوض] إيصال الدفع الخاص بك لدورة [course_title]"
        - For medical cases: "تم [مقبول/مرفوض] إيصال الدفع الخاص بك لحالة [case_name]"

    Example Request:
        POST /dashboard/payments/1/review-ajax/
        POST data: action=approve

    Example Response (Success):
        {"success": True, "message": "تم قبول الدفع بنجاح"}

    Example Response (Error):
        {"success": False, "errors": ["إجراء غير صالح"]}
    """
    payment = get_object_or_404(Payment, id=payment_id)

    if request.method == "POST":
        try:
            action = request.POST.get("action")

            if action == "approve":
                payment.status = Payment.PaymentStatus.APPROVED

                # Handle CourseEnrollment
                if isinstance(payment.content_object, CourseEnrollment):
                    payment.content_object.status = (
                        CourseEnrollment.EnrollmentStatus.APPROVED
                    )
                    payment.content_object.approved_by = request.user
                    payment.content_object.approved_at = timezone.now()
                    payment.content_object.save()

                # Handle Medical Cases
                elif isinstance(
                    payment.content_object,
                    (ChildMedicalCase, AdultMedicalCase, ElderlyMedicalCase),
                ):
                    payment.content_object.is_approved = True
                    payment.content_object.save()

                status_msg = "مقبول"
                notify_type = "success"
            elif action == "reject":
                payment.status = Payment.PaymentStatus.REJECTED

                # Handle CourseEnrollment
                if isinstance(payment.content_object, CourseEnrollment):
                    payment.content_object.status = (
                        CourseEnrollment.EnrollmentStatus.REJECTED
                    )
                    payment.content_object.save()

                # Handle Medical Cases - set is_approved to False (already default)
                elif isinstance(
                    payment.content_object,
                    (ChildMedicalCase, AdultMedicalCase, ElderlyMedicalCase),
                ):
                    payment.content_object.is_approved = False
                    payment.content_object.save()

                status_msg = "مرفوض"
                notify_type = "error"
            else:
                return JsonResponse({"success": False, "errors": ["إجراء غير صالح"]})

            payment.reviewed_by = request.user
            payment.reviewed_at = timezone.now()
            payment.save()

            # Notify user
            title = f"تم مراجعة الدفع - {status_msg}"
            message = f"تم {status_msg} إيصال الدفع الخاص بك"

            # Add specific details if it's a course
            if isinstance(payment.content_object, CourseEnrollment):
                message += f" لدورة {payment.content_object.course.title}"
            # Add specific details if it's a medical case
            elif isinstance(
                payment.content_object,
                (ChildMedicalCase, AdultMedicalCase, ElderlyMedicalCase),
            ):
                case = payment.content_object
                message += f" لحالة {case.full_name or 'طبيية'}"

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
