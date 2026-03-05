from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib import messages
from ..decorators import patient_required, patient_or_admin_required
from ..models import ChildMedicalCase, AdultMedicalCase, ElderlyMedicalCase
from ..utils import notify_admins
import logging
from django.urls import reverse

logger = logging.getLogger(__name__)


def get_all_medical_cases():
    """Helper to get all medical cases with type info"""
    all_cases = []

    for c in ChildMedicalCase.objects.all():
        c.case_type = "child"
        c.case_type_display = "طفل"
        c.case_model = "ChildMedicalCase"
        all_cases.append(c)

    for c in AdultMedicalCase.objects.all():
        c.case_type = "adult"
        c.case_type_display = "بالغ"
        c.case_model = "AdultMedicalCase"
        all_cases.append(c)

    for c in ElderlyMedicalCase.objects.all():
        c.case_type = "elderly"
        c.case_type_display = "مسن"
        c.case_model = "ElderlyMedicalCase"
        all_cases.append(c)

    # Sort by ID descending (newer first)
    all_cases.sort(key=lambda x: x.id, reverse=True)
    return all_cases


def filter_cases_by_user(cases, user):
    """Filter cases to show only user's cases, unless user is admin"""
    if user.is_staff or user.is_superuser:
        return cases
    return [c for c in cases if c.user == user]


@login_required
@patient_or_admin_required
def medical_case_list(request):
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
    category_choices = [("child", "طفل"), ("adult", "بالغ"), ("elderly", "مسن")]
    gender_choices = [("male", "ذكر"), ("female", "أنثى")]
    disability_choices = [
        ("weak", "ضعيف"),
        ("middle", "متوسط"),
        ("hard", "شديد"),
    ]

    if request.method == "POST":
        category = request.POST.get("category")
        try:
            if category == "child":
                ChildMedicalCase.objects.create(
                    user=request.user,
                    full_name=request.POST.get("full_name"),
                    age=request.POST.get("age"),
                    gender=request.POST.get("gender"),
                    aphasie=request.POST.get("aphasie") == "true",
                    disorders=request.POST.get("disorders"),
                    syndromes=request.POST.get("syndromes"),
                    intellectual_disability=request.POST.get("intellectual_disability"),
                )
            elif category == "adult":
                AdultMedicalCase.objects.create(
                    user=request.user,
                    full_name=request.POST.get("full_name"),
                    age=request.POST.get("age"),
                    gender=request.POST.get("gender"),
                    aphasie=request.POST.get("aphasie") == "true",
                )
            elif category == "elderly":
                ElderlyMedicalCase.objects.create(
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
    Delete a medical case.
    Admins can delete any case, regular users can only delete their own.
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
