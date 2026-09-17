"""
General API Utilities for Rafikni Platform.
Provides response envelope builder and media link formatting.
"""

from typing import Any, List, Optional
from django.http import JsonResponse
from django.http import HttpRequest


def api_response(
    success: bool = True,
    message: str = "تمت العملية بنجاح",
    data: Optional[Any] = None,
    errors: Optional[List[str]] = None,
    status: int = 200,
) -> JsonResponse:
    """
    Build a standard unified JSON response dictionary adhering to project specifications.

    Args:
        success: Boolean flag.
        message: Arabic status description.
        data: Optional payload data.
        errors: List of error strings in Arabic.
        status: HTTP status code.

    Returns:
        JsonResponse with standardized envelope.
    """
    payload = {
        "success": success,
        "message": message,
        "errors": errors if errors is not None else ([] if success else [message]),
        "data": data if data is not None else {},
    }
    return JsonResponse(payload, status=status)


def build_absolute_media_url(request: HttpRequest, file_field: Any) -> Optional[str]:
    """
    Convert a Django FileField or ImageField to a complete absolute URL.

    Args:
        request: Current HttpRequest instance.
        file_field: Field instance or None.

    Returns:
        Absolute URL string or None.
    """
    if not file_field:
        return None
    try:
        url = file_field.url
        return request.build_absolute_uri(url)
    except Exception:
        return None
