"""
Context processors for the frontend application of Rafikni Platform.
Injects global data such as social media and contact links into template context.
"""

from typing import Dict, Any
from .utils import load_social_media


def social_media(request) -> Dict[str, Any]:
    """
    Context processor that injects platform social media and contact information
    into all rendered templates.

    Args:
        request: HttpRequest object.

    Returns:
        Dict[str, Any]: Dictionary with key 'social_media'.
    """
    return {
        "social_media": load_social_media(),
    }
