"""
Social Media and Platform Contact Information Router for Rafikni Platform.
Provides endpoints to retrieve official contact channels, social networks, and support links.
"""

from ninja import Router

from frontend.utils import load_social_media
from api.utils import api_response
from api.schemas.common import ApiResponseSchema
from api.schemas.social_media import SocialMediaSchema

router = Router()


@router.get("/", response=ApiResponseSchema[SocialMediaSchema])
def get_social_media(request):
    """
    Retrieve official platform social media channels, support email, and phone contact.
    Public endpoint accessible without authentication for web, mobile apps, and third-party consumers.
    """
    data = load_social_media()
    return api_response(
        success=True,
        message="تم جلب روابط التواصل الاجتماعي بنجاح",
        data=data,
        status=200,
    )
