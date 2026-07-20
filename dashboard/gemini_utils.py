"""
Gemini AI Utilities for Treatment Plan Generation

This module handles communication with Google Gemini API to generate
structured treatment plans for medical cases in the Rafikni platform.

The Gemini API is used via the free tier (Google AI Studio / Gemini API).
Configuration:
    GEMINI_API_KEY - Set in .env file
    GEMINI_MODEL - defaults to "gemini-2.0-flash" (free tier model)
"""

import json
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)


def get_gemini_api_key():
    """Get Gemini API key from settings or environment."""
    key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
    if not key:
        logger.warning("GEMINI_API_KEY is not configured")
    return key


def build_case_prompt(case):
    """
    Build a detailed Arabic prompt for Gemini from a medical case.

    Args:
        case: A ChildMedicalCase, AdultMedicalCase, or ElderlyMedicalCase instance

    Returns:
        str: Formatted prompt string in Arabic
    """
    lines = ["أنت مختص في العلاج والتأهيل للأطفال والبالغين ذوي الاحتياجات الخاصة."]
    lines.append("قم بإنشاء خطة علاجية مفصلة باللغة العربية بناءً على معلومات الحالة التالية:")
    lines.append("")
    lines.append(f"الاسم: {case.full_name or 'غير محدد'}")
    lines.append(f"العمر: {case.age or 'غير محدد'} سنة")
    lines.append(f"الجنس: {dict(case.genderChoices.choices).get(case.gender, 'غير محدد')}")

    case_type = getattr(case, "case_type", None)
    if not case_type:
        meta_verbose = getattr(case._meta, "verbose_name", "")
        if "طفل" in meta_verbose:
            case_type = "child"
        elif "مسن" in meta_verbose:
            case_type = "elderly"
        elif "بالغ" in meta_verbose:
            case_type = "adult"
    if case_type == "child":
        lines.append(f"الاضطرابات: {getattr(case, 'disorders', None) or 'لا يوجد'}")
        lines.append(f"المتلازمات: {getattr(case, 'syndromes', None) or 'لا يوجد'}")
        disability = getattr(case, "intellectual_disability", None)
        if disability:
            lines.append(
                f"الإعاقة الذهنية: {dict(case.IntellectualDisabilityChoices.choices).get(disability, 'غير محدد')}"
            )
    elif case_type == "elderly":
        lines.append(f"ألزهايمر: {'نعم' if getattr(case, 'alzheimer', False) else 'لا'}")
        lines.append(f"باركنسون: {'نعم' if getattr(case, 'parkinson', False) else 'لا'}")

    lines.append(f"الحبسة الكلامية: {'نعم' if case.aphasie else 'لا'}")
    lines.append("")
    lines.append(
        "يجب أن يكون الرد بصيغة JSON فقط ولا شيء غير JSON. "
        "استخدم المفتاح 'sections' الذي يحتوي على مصفوفة من العناصر. "
        "كل عنصر يحتوي على: 'title' (عنوان القسم)، 'icon' (أيقونة Font Awesome بدون fa-)، "
        "'content' (نص وصفي)، 'steps' (مصفوفة من الخطوات العملية كنصوص)."
    )
    lines.append("")
    lines.append("الأقسام المطلوبة:")
    lines.append("1. التقييم - وصف التقييم الأولي للحالة")
    lines.append("2. الأهداف - الأهداف العلاجية قصيرة وطويلة المدى")
    lines.append("3. الخطة العلاجية - التمارين والأنشطة المقترحة")
    lines.append("4. توصيات - توصيات للأهل والمربين")
    lines.append("5. المتابعة - خطة المتابعة والتقييم الدوري")
    lines.append("")
    lines.append("مثال على الصيغة المطلوبة:")
    lines.append(
        '{"sections": [{"title": "التقييم", "icon": "clipboard-list", "content": "...", "steps": ["...", "..."]}]}'
    )

    return "\n".join(lines)


def generate_treatment_plan(case):
    """
    Generate a treatment plan for a medical case using Gemini API.

    Args:
        case: A ChildMedicalCase, AdultMedicalCase, or ElderlyMedicalCase instance

    Returns:
        dict: Parsed JSON with 'sections' array, or None on failure
    """
    api_key = get_gemini_api_key()
    if not api_key:
        raise Exception(
            "مفتاح GEMINI_API_KEY غير مضبط. يرجى إضافته في ملف .env"
        )

    prompt = build_case_prompt(case)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        model = genai.GenerativeModel(model_name)

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 4096,
            },
        )

        raw = response.text.strip()
        # Remove markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0]
        if raw.startswith("json"):
            raw = raw[4:].strip()

        data = json.loads(raw)

        if not isinstance(data, dict) or "sections" not in data:
            msg = "استجابة Gemini لا تحتوي على 'sections'"
            logger.error(msg)
            raise Exception(msg)

        return data

    except ImportError:
        raise Exception(
            "مكتبة google-generativeai غير مثبتة. يرجى تشغيل: pip install google-generativeai"
        )
    except json.JSONDecodeError as e:
        raise Exception(f"فشل في قراءة استجابة Gemini: {str(e)}")
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate" in error_msg.lower():
            raise Exception(
                "تم تجاوز حد الاستخدام المجاني لـ Gemini. "
                "انتظر قليلاً وحاول مرة أخرى، أو قم بترقية حسابك على "
                "https://ai.google.dev"
            )
        logger.error(f"Gemini API error: {error_msg}")
        raise
