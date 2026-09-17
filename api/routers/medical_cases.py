"""
Medical Cases Router for Rafikni Platform.
Handles listing, creating, retrieving, and deleting Child, Adult, and Elderly cases.
Strictly enforces atomic transaction and payment creation rules.
"""

from typing import Optional, List
from ninja import Router, Form, File, UploadedFile
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse

from dashboard.models import ChildMedicalCase, AdultMedicalCase, ElderlyMedicalCase
from dashboard.utils import (
    create_payment,
    notify_admins,
    get_all_medical_cases,
    filter_cases_by_user,
)
from api.security import JWTAuth, PatientAuth, PatientOrAdminAuth
from api.utils import api_response
from api.serializers import serialize_medical_case
from api.schemas.common import ApiResponseSchema
from api.schemas.cases import (
    CaseDetailSchema,
    PaginatedCasesSchema,
    CaseChoicesSchema,
    ChoiceItemSchema,
)

router = Router()

MODEL_MAP = {
    "child": ChildMedicalCase,
    "adult": AdultMedicalCase,
    "elderly": ElderlyMedicalCase,
}


@router.get("/choices", response=ApiResponseSchema[CaseChoicesSchema])
def get_case_choices(request):
    """
    Retrieve choices for case category, gender, and intellectual disability levels.
    """
    categories = [
        ChoiceItemSchema(value="child", label="طفل"),
        ChoiceItemSchema(value="adult", label="بالغ"),
        ChoiceItemSchema(value="elderly", label="مسن"),
    ]
    genders = [
        ChoiceItemSchema(value="male", label="ذكر"),
        ChoiceItemSchema(value="female", label="أنثى"),
    ]
    disability_levels = [
        ChoiceItemSchema(value="weak", label="ضعيف"),
        ChoiceItemSchema(value="middle", label="متوسط"),
        ChoiceItemSchema(value="hard", label="شديد"),
    ]

    return api_response(
        success=True,
        message="تم جلب الخيارات بنجاح",
        data={
            "categories": [c.dict() for c in categories],
            "genders": [g.dict() for g in genders],
            "disability_levels": [d.dict() for d in disability_levels],
        },
        status=200,
    )


@router.get("/", auth=PatientOrAdminAuth(), response=ApiResponseSchema[PaginatedCasesSchema])
def list_medical_cases(
    request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
):
    """
    List medical cases with pagination and search.
    Patients view only their own records; Administrators view all records.
    """
    all_cases = get_all_medical_cases()
    all_cases = filter_cases_by_user(all_cases, request.user)

    if category and category in MODEL_MAP:
        all_cases = [c for c in all_cases if c.case_type == category]

    if q:
        query_str = q.lower()
        filtered = []
        for c in all_cases:
            if c.full_name and query_str in c.full_name.lower():
                filtered.append(c)
            elif c.case_type == "child":
                if hasattr(c, "disorders") and c.disorders and query_str in c.disorders.lower():
                    filtered.append(c)
                elif hasattr(c, "syndromes") and c.syndromes and query_str in c.syndromes.lower():
                    filtered.append(c)
        all_cases = filtered

    paginator = Paginator(all_cases, 10)
    try:
        cases_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        cases_page = paginator.page(1)

    items = [serialize_medical_case(c, request) for c in cases_page]

    pagination_data = {
        "page": cases_page.number,
        "num_pages": paginator.num_pages,
        "total_count": paginator.count,
        "has_next": cases_page.has_next(),
        "has_prev": cases_page.has_previous(),
    }

    return api_response(
        success=True,
        message="تم جلب الحالات بنجاح",
        data={"items": items, "pagination": pagination_data},
        status=200,
    )


@router.get("/{case_type}/{case_id}", auth=PatientOrAdminAuth(), response={200: ApiResponseSchema[CaseDetailSchema], 403: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def get_medical_case_detail(request, case_type: str, case_id: int):
    """
    Retrieve detailed medical case information. Enforces owner or administrator access.
    """
    if case_type not in MODEL_MAP:
        return api_response(success=False, message="نوع الحالة غير صالح", errors=["نوع الحالة غير صالح"], status=404)

    model = MODEL_MAP[case_type]
    try:
        case = model.objects.select_related("user").get(id=case_id)
    except model.DoesNotExist:
        return api_response(success=False, message="الحالة غير موجودة", errors=["الحالة غير موجودة"], status=404)

    is_admin = request.user.is_superuser or getattr(request.user.profile, "role", None) == "admin"
    if not is_admin and case.user != request.user:
        return api_response(
            success=False,
            message="لا يمكنك عرض تفاصيل حالة ليست ملكك",
            errors=["لا يمكنك عرض تفاصيل حالة ليست ملكك"],
            status=403,
        )

    case.case_type = case_type
    data = serialize_medical_case(case, request)
    return api_response(success=True, message="تم جلب تفاصيل الحالة بنجاح", data=data, status=200)


@router.post("/", auth=PatientAuth(), response={201: ApiResponseSchema[CaseDetailSchema], 400: ApiResponseSchema[None]})
def create_medical_case(
    request,
    category: str = Form(...),
    full_name: str = Form(...),
    age: int = Form(...),
    gender: str = Form("male"),
    aphasie: str = Form("false"),
    disorders: Optional[str] = Form(None),
    syndromes: Optional[str] = Form(None),
    intellectual_disability: Optional[str] = Form(None),
    alzheimer: Optional[str] = Form(None),
    parkinson: Optional[str] = Form(None),
    receipt_image: UploadedFile = File(...),
):
    """
    Create a new medical case with an attached payment receipt.
    Executed inside an atomic transaction; automatically registers payment and notifies administrators.
    """
    if not receipt_image:
        return api_response(
            success=False,
            message="يجب إرفاق إيصال الدفع",
            errors=["يجب إرفاق إيصال الدفع"],
            status=400,
        )

    if category not in MODEL_MAP:
        return api_response(
            success=False,
            message="فئة الحالة غير صالحة",
            errors=["فئة الحالة غير صالحة"],
            status=400,
        )

    is_aphasie = str(aphasie).lower() in ["true", "1", "yes"]

    try:
        with transaction.atomic():
            medical_case = None

            if category == "child":
                medical_case = ChildMedicalCase.objects.create(
                    user=request.user,
                    full_name=full_name,
                    age=age,
                    gender=gender,
                    aphasie=is_aphasie,
                    disorders=disorders,
                    syndromes=syndromes,
                    intellectual_disability=intellectual_disability,
                )
            elif category == "adult":
                medical_case = AdultMedicalCase.objects.create(
                    user=request.user,
                    full_name=full_name,
                    age=age,
                    gender=gender,
                    aphasie=is_aphasie,
                )
            elif category == "elderly":
                medical_case = ElderlyMedicalCase.objects.create(
                    user=request.user,
                    full_name=full_name,
                    age=age,
                    gender=gender,
                    aphasie=is_aphasie,
                    alzheimer=str(alzheimer).lower() in ["true", "1", "yes"],
                    parkinson=str(parkinson).lower() in ["true", "1", "yes"],
                )

            # Mandatory: create payment using dashboard.utils.create_payment
            create_payment(
                user=request.user,
                content_object=medical_case,
                receipt_image=receipt_image,
            )

        category_display = {"child": "طفل", "adult": "بالغ", "elderly": "مسن"}.get(category, "")
        notify_admins(
            title="حالة طبية جديدة",
            message=f"قام المستخدم {request.user.username} بإضافة حالة طبية جديدة ({category_display})",
            notification_type="info",
            link=reverse("dashboard:medical_case_list") + f"?category={category}",
        )

        medical_case.case_type = category
        data = serialize_medical_case(medical_case, request)
        return api_response(
            success=True,
            message="تم إضافة الحالة الطبية بنجاح وهي قيد المراجعة",
            data=data,
            status=201,
        )

    except Exception as e:
        return api_response(
            success=False,
            message="حدث خطأ أثناء حفظ الحالة الطبية",
            errors=[str(e)],
            status=400,
        )


@router.delete("/{case_type}/{case_id}", auth=PatientOrAdminAuth(), response={200: ApiResponseSchema[None], 403: ApiResponseSchema[None], 404: ApiResponseSchema[None]})
def delete_medical_case(request, case_type: str, case_id: int):
    """
    Delete a medical case record. Allowed for the case owner or platform administrators.
    """
    if case_type not in MODEL_MAP:
        return api_response(success=False, message="نوع الحالة غير صالح", errors=["نوع الحالة غير صالح"], status=404)

    model = MODEL_MAP[case_type]
    try:
        case = model.objects.get(id=case_id)
    except model.DoesNotExist:
        return api_response(success=False, message="الحالة غير موجودة", errors=["الحالة غير موجودة"], status=404)

    is_admin = request.user.is_superuser or getattr(request.user.profile, "role", None) == "admin"
    if not is_admin and case.user != request.user:
        return api_response(
            success=False,
            message="لا يمكنك حذف حالة ليست ملكك",
            errors=["لا يمكنك حذف حالة ليست ملكك"],
            status=403,
        )

    case.delete()
    return api_response(success=True, message="تم حذف الحالة الطبية بنجاح", status=200)
