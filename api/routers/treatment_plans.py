"""
AI Treatment Plans Router for Rafikni Platform.
Handles Gemini AI-driven clinical plan generation and retrieval.
"""

from typing import Optional
from ninja import Router
from django.contrib.contenttypes.models import ContentType

from dashboard.models import ChildMedicalCase, AdultMedicalCase, ElderlyMedicalCase, TreatmentPlan
from dashboard.gemini_utils import generate_treatment_plan
from dashboard.utils import notify_user
from api.security import AdminAuth, PatientOrAdminAuth
from api.utils import api_response
from api.serializers import serialize_treatment_plan
from api.schemas.common import ApiResponseSchema
from api.schemas.plans import TreatmentPlanSchema

router = Router()

MODEL_MAP = {
    "child": ChildMedicalCase,
    "adult": AdultMedicalCase,
    "elderly": ElderlyMedicalCase,
}


@router.post("/generate/{case_type}/{case_id}", auth=AdminAuth(), response={200: ApiResponseSchema[TreatmentPlanSchema], 400: ApiResponseSchema[None], 422: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def generate_ai_treatment_plan(request, case_type: str, case_id: int):
    """
    Generate or regenerate an AI clinical treatment plan for a medical case using Google Gemini.
    Restricted exclusively to platform administrators.
    """
    if case_type not in MODEL_MAP:
        return api_response(success=False, message="نوع الحالة غير صالح", errors=["نوع الحالة غير صالح"], status=400)

    model = MODEL_MAP[case_type]
    try:
        case = model.objects.select_related("user").get(id=case_id)
    except model.DoesNotExist:
        return api_response(success=False, message="الحالة غير موجودة", errors=["الحالة غير موجودة"], status=404)

    try:
        plan_data = generate_treatment_plan(case)
        content_type = ContentType.objects.get_for_model(model)

        plan, created = TreatmentPlan.objects.update_or_create(
            content_type=content_type,
            object_id=case_id,
            defaults={
                "plan_data": plan_data,
                "created_by": request.user,
            },
        )

        # Real-time alert to patient
        notify_user(
            case.user,
            title="خطة علاجية جديدة",
            message=f"تم إعداد خطة علاجية للحالة: {case.full_name or ''}. يمكنك الاطلاع عليها الآن.",
            notification_type="success",
        )

        plan_dict = serialize_treatment_plan(plan)
        msg = "تم إنشاء الخطة العلاجية بنجاح" if created else "تم تحديث الخطة العلاجية بنجاح"
        return api_response(success=True, message=msg, data=plan_dict, status=200)

    except Exception as e:
        error_msg = str(e)
        status_code = 422 if "quota" in error_msg.lower() or "limit" in error_msg.lower() else 400
        return api_response(
            success=False,
            message="فشل توليد الخطة العلاجية",
            errors=[error_msg],
            status=status_code,
        )


@router.get("/{case_type}/{case_id}", auth=PatientOrAdminAuth(), response={200: ApiResponseSchema[Optional[TreatmentPlanSchema]], 403: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def get_ai_treatment_plan(request, case_type: str, case_id: int):
    """
    Retrieve the clinical treatment plan for a medical case.
    Accessible by the case owner (patient) or platform administrators.
    """
    if case_type not in MODEL_MAP:
        return api_response(success=False, message="نوع الحالة غير صالح", errors=["نوع الحالة غير صالح"], status=400)

    model = MODEL_MAP[case_type]
    try:
        case = model.objects.select_related("user").get(id=case_id)
    except model.DoesNotExist:
        return api_response(success=False, message="الحالة غير موجودة", errors=["الحالة غير موجودة"], status=404)

    is_admin = request.user.is_superuser or getattr(request.user.profile, "role", None) == "admin"
    if not is_admin and case.user != request.user:
        return api_response(
            success=False,
            message="لا يمكنك استعراض خطة علاجية لحالة ليست ملكك",
            errors=["لا يمكنك استعراض خطة علاجية لحالة ليست ملكك"],
            status=403,
        )

    content_type = ContentType.objects.get_for_model(model)
    try:
        plan = TreatmentPlan.objects.select_related("created_by").get(
            content_type=content_type, object_id=case_id
        )
        data = serialize_treatment_plan(plan)
        return api_response(success=True, message="تم جلب الخطة العلاجية بنجاح", data=data, status=200)
    except TreatmentPlan.DoesNotExist:
        return api_response(
            success=True,
            message="لا توجد خطة علاجية مسجلة لهذه الحالة بعد",
            data=None,
            status=200,
        )
