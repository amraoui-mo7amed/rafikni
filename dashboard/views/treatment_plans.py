"""
Treatment Plan Views

This module handles generating and viewing AI-powered treatment plans
for medical cases using the Google Gemini API.

Views:
    - generate_treatment_plan: Generate a new plan (AJAX POST, admin only)
    - get_treatment_plan: Get existing plan data (AJAX GET)

Flow:
    1. Admin clicks "إنشاء خطة علاجية" in case list
    2. AJAX POST to generate endpoint
    3. Backend builds prompt from case data → calls Gemini API
    4. Parses JSON response → saves TreatmentPlan → returns JSON to frontend
    5. Frontend renders the plan in a modal
"""

import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST

from ..decorators import admin_required
from ..models import (
    ChildMedicalCase,
    AdultMedicalCase,
    ElderlyMedicalCase,
    TreatmentPlan,
)
from ..gemini_utils import generate_treatment_plan
from ..utils import notify_user

logger = logging.getLogger(__name__)

MODEL_MAP = {
    "child": ChildMedicalCase,
    "adult": AdultMedicalCase,
    "elderly": ElderlyMedicalCase,
}


@login_required
@admin_required
@require_POST
def generate_plan(request, case_type, case_id):
    """
    Generate a treatment plan for a medical case using Gemini AI.

    This endpoint is called via AJAX POST by an admin. It:
    1. Fetches the medical case
    2. Builds a structured Arabic prompt from case data
    3. Calls Gemini API to generate the plan
    4. Parses the JSON response
    5. Saves/updates the TreatmentPlan
    6. Notifies the patient
    7. Returns the plan data as JSON

    Decorators:
        @login_required: User must be logged in
        @admin_required: User must have admin role

    Args:
        request: HTTP request object
        case_type (str): 'child', 'adult', or 'elderly'
        case_id (int): ID of the medical case

    Returns:
        JsonResponse: {
            "success": true/false,
            "plan_data": { ... } or None,
            "message": "...",
            "errors": [...]
        }
    """
    if case_type not in MODEL_MAP:
        return JsonResponse(
            {"success": False, "errors": ["نوع الحالة غير صالح"]}
        )

    model = MODEL_MAP[case_type]
    try:
        case = model.objects.get(id=case_id)
    except model.DoesNotExist:
        return JsonResponse(
            {"success": False, "errors": ["الحالة غير موجودة"]}
        )

    try:
        plan_data = generate_treatment_plan(case)

        # Save or update the plan
        content_type = ContentType.objects.get_for_model(model)
        plan, created = TreatmentPlan.objects.update_or_create(
            content_type=content_type,
            object_id=case_id,
            defaults={
                "plan_data": plan_data,
                "created_by": request.user,
            },
        )

        # Notify the patient
        notify_user(
            case.user,
            title="خطة علاجية جديدة",
            message=(
                f"تم إنشاء خطة علاجية للحالة: {case.full_name or ''}. "
                "يمكنك الاطلاع عليها من خلال لوحة التحكم."
            ),
            notification_type="success",
        )

        return JsonResponse(
            {
                "success": True,
                "message": "تم إنشاء الخطة العلاجية بنجاح" if created else "تم تحديث الخطة العلاجية بنجاح",
                "plan_data": plan_data,
                "plan_id": plan.id,
            }
        )

    except Exception as e:
        logger.error(f"Error generating treatment plan: {str(e)}")
        return JsonResponse(
            {"success": False, "errors": [str(e)]}
        )


@login_required
@admin_required
def get_plan(request, case_type, case_id):
    """
    Get an existing treatment plan for a medical case.

    Decorators:
        @login_required: User must be logged in
        @admin_required: User must have admin role

    Args:
        request: HTTP request object
        case_type (str): 'child', 'adult', or 'elderly'
        case_id (int): ID of the medical case

    Returns:
        JsonResponse with plan data or empty if no plan exists
    """
    if case_type not in MODEL_MAP:
        return JsonResponse({"success": False, "errors": ["نوع الحالة غير صالح"]})

    model = MODEL_MAP[case_type]
    content_type = ContentType.objects.get_for_model(model)

    try:
        plan = TreatmentPlan.objects.get(
            content_type=content_type, object_id=case_id
        )
        return JsonResponse(
            {
                "success": True,
                "plan_data": plan.plan_data,
                "plan_id": plan.id,
                "created_at": plan.created_at.isoformat(),
                "created_by": plan.created_by.get_full_name()
                or plan.created_by.username,
            }
        )
    except TreatmentPlan.DoesNotExist:
        return JsonResponse({"success": True, "plan_data": None})
