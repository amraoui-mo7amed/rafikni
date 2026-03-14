"""
Dashboard Medical Cases Views

This module contains views for managing medical cases in the Rafikni platform.
It handles listing, creating, and deleting medical cases for patients.

Views:
    - medical_case_list: List all medical cases with filtering and pagination
    - medical_case_create: Create a new medical case with optional payment
    - medical_case_delete: Delete a medical case with permission checks

Decorator Types:
    - @login_required: Ensures user is authenticated
    - @patient_required: Ensures user has patient role
    - @patient_or_admin_required: Allows patients (own cases) or admins (all cases)

Helper Functions (in utils.py):
    - get_all_medical_cases(): Get all cases from all models with type info
    - filter_cases_by_user(): Filter cases based on user permissions

Flow:
    1. Patient views list -> medical_case_list()
    2. Patient creates case -> medical_case_create()
    3. Patient/Admin deletes -> medical_case_delete()
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.contrib import messages
from ..decorators import patient_required, patient_or_admin_required
from ..models import ChildMedicalCase, AdultMedicalCase, ElderlyMedicalCase
from ..utils import (
    notify_admins,
    create_payment,
    get_all_medical_cases,
    filter_cases_by_user,
)
import logging
from django.urls import reverse

logger = logging.getLogger(__name__)


@login_required
@patient_or_admin_required
def medical_case_list(request):
    """
    List all medical cases with filtering and pagination.

    This view displays a paginated list of medical cases. The behavior differs
    based on user role:
    - Admins (is_staff or is_superuser): See all cases from all users
    - Regular users (patients): See only their own cases

    Decorators:
        @login_required: User must be logged in
        @patient_or_admin_required: Patient (own cases) or Admin (all cases)

    Args:
        request: HTTP request object

    Query Parameters:
        q (str): Search query for case full_name or child disorders/syndromes
        category (str): Filter by case type ('child', 'adult', 'elderly')
        page (int): Page number for pagination

    GET Behavior:
        1. Fetches all medical cases from all three models
        2. Filters by user permissions (admin sees all, patient sees own)
        3. Applies category filter if provided
        4. Applies search query if provided
        5. Paginates results (10 per page)
        6. Renders the list template

    Returns:
        HtmlResponse: Rendered template with cases list

    Template Context:
        - cases: Paginated list of medical cases
        - query: Current search query
        - category: Current category filter
        - category_choices: List of (value, label) for dropdown
        - paginator: Paginator object
        - is_admin: Boolean indicating if current user is admin

    Search Logic:
        - Searches in case.full_name (all cases)
        - Additionally searches in disorders and syndromes (child cases only)

    Example URL:
        /dashboard/medical-cases/?q=john&category=child&page=2
    """
    query = request.GET.get("q", "")
    category = request.GET.get("category", "")
    page = request.GET.get("page", 1)

    # Get all cases
    all_cases = get_all_medical_cases()

    # Filter by user (admin sees all, others see only their own)
    all_cases = filter_cases_by_user(all_cases, request.user)

    # Filter by category if specified
    if category:
        all_cases = [c for c in all_cases if c.case_type == category]

    # Filter by search query
    if query:
        filtered_cases = []
        for c in all_cases:
            if query.lower() in c.full_name.lower():
                filtered_cases.append(c)
            elif c.case_type == "child":
                if (
                    hasattr(c, "disorders")
                    and c.disorders
                    and query.lower() in c.disorders.lower()
                ):
                    filtered_cases.append(c)
                elif (
                    hasattr(c, "syndromes")
                    and c.syndromes
                    and query.lower() in c.syndromes.lower()
                ):
                    filtered_cases.append(c)
        all_cases = filtered_cases

    # Pagination
    paginator = Paginator(all_cases, 10)
    try:
        cases_page = paginator.page(page)
    except PageNotAnInteger:
        cases_page = paginator.page(1)
    except EmptyPage:
        cases_page = paginator.page(paginator.num_pages)

    context = {
        "cases": cases_page,
        "query": query,
        "category": category,
        "category_choices": [("child", "طفل"), ("adult", "بالغ"), ("elderly", "مسن")],
        "paginator": paginator,
        "is_admin": request.user.is_staff or request.user.is_superuser,
    }
    return render(request, "dashboard/medical_cases/list.html", context)


@login_required
@patient_required
def medical_case_create(request):
    """
    Create a new medical case with optional payment receipt.

    This view allows patients to create a new medical case. The patient must
    provide a payment receipt image. The case creation and payment are handled
    in an atomic transaction to ensure data integrity.

    Decorators:
        @login_required: User must be logged in
        @patient_required: User must have patient role

    Args:
        request: HTTP request object

    POST Data:
        category (str): Type of case ('child', 'adult', 'elderly')
        full_name (str): Patient's full name
        age (int): Patient's age
        gender (str): 'male' or 'female'
        aphasie (str): 'true' or 'false'
        disorders (str, optional): Child-specific - comma-separated disorders
        syndromes (str, optional): Child-specific - comma-separated syndromes
        intellectual_disability (str, optional): Child-specific disability level
        alzheimer (str, optional): Elderly-specific - 'true' or 'false'
        parkinson (str, optional): Elderly-specific - 'true' or 'false'
        receipt_image (file): Required - payment receipt image
        notes (str, optional): Payment notes

    GET Behavior:
        - Renders the create form with choices for dropdowns

    POST Behavior:
        1. Validates receipt_image is provided
        2. Creates medical case based on category (child/adult/elderly)
        3. Creates Payment linked to the case (within atomic transaction)
        4. Sends notification to admins
        5. Returns JSON response with redirect URL

    Returns:
        GET: HtmlResponse with create form
        POST: JsonResponse with success/error message

    Template Context:
        - category_choices: List of (value, label) for category dropdown
        - gender_choices: List of (value, label) for gender dropdown
        - disability_choices: List of (value, label) for intellectual disability

    Validation:
        - receipt_image is required (returns error if missing)
        - category must be 'child', 'adult', or 'elderly'

    Transaction:
        Uses transaction.atomic() to ensure:
        - Medical case is created only if payment can be created
        - Payment is created only if case is created

    Example POST Request:
        POST /dashboard/medical-cases/create/
        Data:
            category=child
            full_name=أحمد محمد
            age=8
            gender=male
            aphasie=true
            disorders=توحد,تشتت انتباه
            receipt_image=<file>
    """
    category_choices = [("child", "طفل"), ("adult", "بالغ"), ("elderly", "مسن")]
    gender_choices = [("male", "ذكر"), ("female", "أنثى")]
    disability_choices = [
        ("weak", "ضعيف"),
        ("middle", "متوسط"),
        ("hard", "شديد"),
    ]

    if request.method == "POST":
        category = request.POST.get("category")
        receipt_image = request.FILES.get("receipt_image")
        if not receipt_image:
            return JsonResponse(
                {
                    "success": False,
                    "errors": ["يجب إرفاق إيصال الدفع"],
                }
            )

        try:
            with transaction.atomic():
                medical_case = None

                if category == "child":
                    medical_case = ChildMedicalCase.objects.create(
                        user=request.user,
                        full_name=request.POST.get("full_name"),
                        age=request.POST.get("age"),
                        gender=request.POST.get("gender"),
                        aphasie=request.POST.get("aphasie") == "true",
                        disorders=request.POST.get("disorders"),
                        syndromes=request.POST.get("syndromes"),
                        intellectual_disability=request.POST.get(
                            "intellectual_disability"
                        ),
                    )
                elif category == "adult":
                    medical_case = AdultMedicalCase.objects.create(
                        user=request.user,
                        full_name=request.POST.get("full_name"),
                        age=request.POST.get("age"),
                        gender=request.POST.get("gender"),
                        aphasie=request.POST.get("aphasie") == "true",
                    )
                elif category == "elderly":
                    medical_case = ElderlyMedicalCase.objects.create(
                        user=request.user,
                        full_name=request.POST.get("full_name"),
                        age=request.POST.get("age"),
                        gender=request.POST.get("gender"),
                        aphasie=request.POST.get("aphasie") == "true",
                        alzheimer=request.POST.get("alzheimer") == "true",
                        parkinson=request.POST.get("parkinson") == "true",
                    )
                else:
                    return JsonResponse({"success": False, "errors": ["فئة غير صالحة"]})

                # Create payment if receipt image provided
                if receipt_image:
                    create_payment(
                        user=request.user,
                        content_object=medical_case,
                        receipt_image=receipt_image,
                    )

            # Notify admins
            category_display = {"child": "طفل", "adult": "بالغ", "elderly": "مسن"}.get(
                category, ""
            )
            notify_admins(
                request,
                title="حالة طبية جديدة",
                message=f"قام المستخدم {request.user.username} بإضافة حالة طبية جديدة ({category_display})",
                notification_type="info",
                link=reverse("dashboard:medical_case_list") + f"?category={category}",
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "تم إضافة الحالة الطبية بنجاح",
                    "redirect_url": reverse("dashboard:medical_case_list"),
                }
            )
        except Exception as e:
            logger.error(f"Error creating medical case: {str(e)}")
            return JsonResponse({"success": False, "errors": [str(e)]})

    context = {
        "category_choices": category_choices,
        "gender_choices": gender_choices,
        "disability_choices": disability_choices,
    }
    return render(request, "dashboard/medical_cases/create.html", context)


@login_required
@patient_or_admin_required
def medical_case_delete(request, case_type, case_id):
    """
    Delete a medical case with permission checks.

    This view handles deletion of medical cases. Permission logic:
    - Admins can delete any case
    - Regular users can only delete their own cases

    Decorators:
        @login_required: User must be logged in
        @patient_or_admin_required: Patient (own cases) or Admin (all cases)

    Args:
        request: HTTP request object
        case_type (str): Type of case ('child', 'adult', 'elderly')
        case_id (int): ID of the case to delete

    URL Parameters:
        case_type: Maps to model - 'child'->ChildMedicalCase, etc.
        case_id: Primary key of the case

    GET Behavior:
        - Shows confirmation page before deletion

    POST Behavior:
        1. Validates case_type is valid
        2. Checks user has permission to delete
        3. Deletes the case
        4. Redirects to list with success message

    Returns:
        GET: HtmlResponse with confirmation template
        POST: HttpResponseRedirect to list page

    Permission Check:
        - Admin (is_staff or is_superuser): Can delete any case
        - Regular user: Can only delete if case.user == request.user

    Error Handling:
        - Invalid case_type: Redirects with error message
        - Case not found: Redirects with error message
        - Permission denied: Redirects with error message

    Template Context:
        - case: The medical case object
        - case_type: The case type string
        - case_type_display: Arabic display name for case type

    Example URLs:
        GET  /dashboard/medical-cases/delete/child/1/  (show confirmation)
        POST /dashboard/medical-cases/delete/child/1/  (perform delete)
    """
    # Map case types to models
    model_map = {
        "child": ChildMedicalCase,
        "adult": AdultMedicalCase,
        "elderly": ElderlyMedicalCase,
    }

    if case_type not in model_map:
        messages.error(request, "نوع الحالة غير صالح")
        return redirect("dashboard:medical_case_list")

    model = model_map[case_type]

    try:
        case = model.objects.get(id=case_id)
    except model.DoesNotExist:
        messages.error(request, "الحالة غير موجودة")
        return redirect("dashboard:medical_case_list")

    # Check permissions
    is_admin = request.user.is_staff or request.user.is_superuser
    if not is_admin and case.user != request.user:
        messages.error(request, "لا يمكنك حذف حالة ليست ملكك")
        return redirect("dashboard:medical_case_list")

    if request.method == "POST":
        case.delete()
        messages.success(request, "تم حذف الحالة الطبية بنجاح")
        return redirect("dashboard:medical_case_list")

    # GET request - show confirmation page
    context = {
        "case": case,
        "case_type": case_type,
        "case_type_display": {
            "child": "طفل",
            "adult": "بالغ",
            "elderly": "مسن",
        }.get(case_type, ""),
    }
    return render(request, "dashboard/medical_cases/confirm_delete.html", context)
