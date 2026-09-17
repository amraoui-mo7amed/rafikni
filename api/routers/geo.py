"""
Algerian Geographic Data Router for Rafikni Platform.
Endpoints for retrieving 58 Algerian Wilayas and cascading Communes from algeria.json.
"""

from typing import List, Optional
from ninja import Router

from dashboard.utils import get_algeria_wilayas, get_algeria_communes
from api.utils import api_response
from api.schemas.common import ApiResponseSchema
from api.schemas.geo import WilayaSchema, CommuneSchema

router = Router()


@router.get("/wilayas", response=ApiResponseSchema[List[WilayaSchema]])
def list_wilayas(request):
    """
    Retrieve all 58 Algerian wilayas sorted by numerical code.
    """
    wilayas = get_algeria_wilayas()
    items = [{"code": code, "name": name} for code, name in wilayas]
    return api_response(success=True, message="تم جلب الولايات بنجاح", data=items, status=200)


@router.get("/communes", response={200: ApiResponseSchema[List[CommuneSchema]], 400: ApiResponseSchema[None]})
def list_communes(request, wilaya_code: str):
    """
    Retrieve all communes belonging to a specific wilaya code (e.g. '16' for Alger).
    """
    if not wilaya_code:
        return api_response(success=False, message="رمز الولاية مطلوب", errors=["رمز الولاية مطلوب"], status=400)

    # Format single digit codes with leading zero if needed
    code_str = f"{int(wilaya_code):02d}" if wilaya_code.isdigit() else wilaya_code

    communes = get_algeria_communes(code_str)
    items = [{"id": cid, "name": cname} for cid, cname in communes]
    return api_response(success=True, message="تم جلب البلديات بنجاح", data=items, status=200)
