"""
Frontend utilities for Rafikni Platform.
Provides helper functions for loading platform assets and configurations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


def load_social_media() -> Dict[str, Any]:
    """
    Load social media links and contact details from social_media.json in the project root.

    Returns:
        Dict[str, Any]: Dictionary mapping platform keys (facebook, tiktok, instagram, email, youtube, phone)
                        to their respective URLs or contact strings.
    """
    json_path = Path(settings.BASE_DIR) / "social_media.json"
    default_data: Dict[str, Any] = {
        "facebook": "",
        "tiktok": "",
        "instagram": "",
        "email": "",
        "youtube": "",
        "phone": "",
    }

    if not json_path.exists():
        logger.warning(f"social_media.json not found at {json_path}")
        return default_data

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {**default_data, **data}
            return default_data
    except Exception as e:
        logger.error(f"Failed to read social_media.json: {str(e)}")
        return default_data
