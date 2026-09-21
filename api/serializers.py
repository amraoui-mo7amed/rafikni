"""
Model Serialization Helpers for Rafikni Platform API.
Converts Django ORM model instances into clean dictionary payloads conforming to Pydantic schemas.
"""

from typing import Any, Dict, List, Optional
from django.contrib.auth.models import User
from user_auth.models import UserProfile
from dashboard.models import (
    ChildMedicalCase,
    AdultMedicalCase,
    ElderlyMedicalCase,
    TreatmentPlan,
    Course,
    Video,
    CourseEnrollment,
    Payment,
    Game,
    GameOrder,
    Article,
    Notification,
)
from .utils import build_absolute_media_url


def serialize_user_profile(user: User, request=None) -> Dict[str, Any]:
    """Serialize User and UserProfile into a dictionary."""
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", "patient") if profile else "patient"
    role_display = profile.get_role_display() if profile else "مريض"
    if user.is_superuser:
        role = "admin"
        role_display = "مدير"

    profile_pic = build_absolute_media_url(request, profile.profile_pic) if profile else None

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": role,
        "role_display": role_display,
        "phone_number": profile.phone_number if profile else None,
        "birthdate": profile.birthdate.strftime("%Y-%m-%d") if profile and profile.birthdate else None,
        "profile_pic": profile_pic,
        "is_active": user.is_active,
        "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M"),
        "last_login": user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else None,
    }


def serialize_medical_case(case: Any, request=None) -> Dict[str, Any]:
    """Serialize any medical case instance (Child, Adult, Elderly)."""
    case_type = getattr(case, "case_type", None)
    if not case_type:
        meta_name = getattr(case._meta, "verbose_name", "")
        if "طفل" in meta_name:
            case_type = "child"
        elif "مسن" in meta_name:
            case_type = "elderly"
        else:
            case_type = "adult"

    type_map = {
        "child": "طفل",
        "adult": "بالغ",
        "elderly": "مسن",
    }

    user = case.user
    user_full_name = user.get_full_name() or user.username

    data = {
        "id": case.id,
        "case_type": case_type,
        "case_type_display": type_map.get(case_type, "حالة طبية"),
        "full_name": case.full_name,
        "age": case.age,
        "gender": case.gender,
        "gender_display": case.get_gender_display() if hasattr(case, "get_gender_display") else None,
        "aphasie": case.aphasie,
        "is_approved": case.is_approved,
        "user_id": user.id,
        "user_username": user.username,
        "user_full_name": user_full_name,
        "disorders": getattr(case, "disorders", None),
        "syndromes": getattr(case, "syndromes", None),
        "intellectual_disability": getattr(case, "intellectual_disability", None),
        "intellectual_disability_display": (
            case.get_intellectual_disability_display()
            if hasattr(case, "get_intellectual_disability_display")
            else None
        ),
        "alzheimer": getattr(case, "alzheimer", None),
        "parkinson": getattr(case, "parkinson", None),
    }
    return data


def serialize_treatment_plan(plan: TreatmentPlan) -> Dict[str, Any]:
    """Serialize TreatmentPlan model instance."""
    case_type = "child"
    if plan.content_type:
        model_name = plan.content_type.model.lower()
        if "adult" in model_name:
            case_type = "adult"
        elif "elderly" in model_name:
            case_type = "elderly"

    creator_name = None
    if plan.created_by:
        creator_name = plan.created_by.get_full_name() or plan.created_by.username

    patient_name = ""
    age = 0
    try:
        case = plan.content_object
        if case:
            patient_name = getattr(case, "full_name", "") or ""
            age = getattr(case, "age", 0) or 0
    except Exception:
        pass

    return {
        "id": plan.id,
        "case_type": case_type,
        "case_id": plan.object_id,
        "patient_name": patient_name,
        "age": age,
        "category": case_type,
        "plan_data": plan.plan_data or {},
        "created_at": plan.created_at.strftime("%Y-%m-%d %H:%M") if plan.created_at else "",
        "updated_at": plan.updated_at.strftime("%Y-%m-%d %H:%M") if plan.updated_at else "",
        "created_by": creator_name,
    }


def serialize_course_card(course: Course, request=None, user=None) -> Dict[str, Any]:
    """Serialize Course for list views."""
    thumbnail_url = build_absolute_media_url(request, course.thumbnail)

    is_enrolled = False
    enrollment_status = None
    if user and user.is_authenticated:
        enrollment = CourseEnrollment.objects.filter(user=user, course=course).first()
        if enrollment:
            is_enrolled = True
            enrollment_status = enrollment.status

    return {
        "id": course.id,
        "title": course.title,
        "price": float(course.price),
        "teacher_name": course.teacher_name,
        "description": course.description,
        "thumbnail": thumbnail_url,
        "tags": course.get_tags_list(),
        "video_count": course.videos.count(),
        "is_enrolled": is_enrolled,
        "enrollment_status": enrollment_status,
    }


def serialize_video(video: Video, request=None, has_access: bool = False) -> Dict[str, Any]:
    """Serialize video with access gating."""
    is_locked = not (video.is_free or has_access)
    video_url = build_absolute_media_url(request, video.video_file) if not is_locked else None

    duration_str = None
    if video.duration:
        total_seconds = int(video.duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        duration_str = f"{minutes:02d}:{seconds:02d}"

    return {
        "id": video.id,
        "title": video.title,
        "description": video.description or "",
        "order": video.order,
        "is_free": video.is_free,
        "duration": duration_str,
        "is_locked": is_locked,
        "video_url": video_url,
    }


def serialize_payment(payment: Payment, request=None) -> Dict[str, Any]:
    """Serialize Payment instance."""
    receipt_url = build_absolute_media_url(request, payment.receipt_image)
    target_obj = payment.content_object

    target_type = "unknown"
    target_id = payment.object_id
    target_title = "غير محدد"

    if isinstance(target_obj, CourseEnrollment):
        target_type = "course"
        target_title = f"دورة: {target_obj.course.title}"
    elif target_obj:
        target_type = "medical"
        target_title = f"حالة: {getattr(target_obj, 'full_name', '')}"

    reviewed_by_name = None
    if payment.reviewed_by:
        reviewed_by_name = payment.reviewed_by.get_full_name() or payment.reviewed_by.username

    return {
        "id": payment.id,
        "user_id": payment.user.id,
        "user_username": payment.user.username,
        "user_email": payment.user.email,
        "user_full_name": payment.user.get_full_name() or payment.user.username,
        "target_type": target_type,
        "target_id": target_id,
        "target_title": target_title,
        "receipt_image_url": receipt_url,
        "status": payment.status,
        "status_display": payment.get_status_display(),
        "created_at": payment.created_at.strftime("%Y-%m-%d %H:%M"),
        "reviewed_at": payment.reviewed_at.strftime("%Y-%m-%d %H:%M") if payment.reviewed_at else None,
        "reviewed_by": reviewed_by_name,
    }


def serialize_game(game: Game, request=None, include_gallery: bool = False) -> Dict[str, Any]:
    """Serialize Game instance."""
    thumbnail_url = build_absolute_media_url(request, game.thumbnail)
    data = {
        "id": game.id,
        "title": game.title,
        "slug": game.slug,
        "price": float(game.price),
        "description": game.description,
        "tags": game.get_tags_list(),
        "thumbnail": thumbnail_url,
        "is_active": game.is_active,
    }
    if include_gallery:
        gallery_urls = [
            build_absolute_media_url(request, img.image)
            for img in game.images.all()
            if img.image
        ]
        data["gallery_images"] = [u for u in gallery_urls if u]
    return data


def serialize_game_order(order: GameOrder) -> Dict[str, Any]:
    """Serialize GameOrder instance."""
    return {
        "id": order.id,
        "game_id": order.game.id,
        "game_title": order.game.title,
        "full_name": order.full_name,
        "phone_number": order.phone_number,
        "wilaya": order.wilaya,
        "commune": order.commune,
        "address": order.address,
        "status": order.status,
        "status_display": order.get_status_display(),
        "user_id": order.user.id if order.user else None,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
    }


def serialize_article(article: Article, request=None, include_content: bool = False) -> Dict[str, Any]:
    """Serialize Article instance."""
    thumbnail_url = build_absolute_media_url(request, article.thumbnail)
    excerpt = article.content[:150] + "..." if len(article.content) > 150 else article.content

    data = {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "category": article.category,
        "category_display": article.get_category_display(),
        "excerpt": excerpt,
        "thumbnail": thumbnail_url,
        "tags": article.get_tags_list(),
        "author_username": article.author.username,
        "is_published": article.is_published,
        "created_at": article.created_at.strftime("%Y-%m-%d"),
    }
    if include_content:
        data["content"] = article.content
        data["updated_at"] = article.updated_at.strftime("%Y-%m-%d %H:%M")
    return data


def serialize_notification(notification: Notification) -> Dict[str, Any]:
    """Serialize Notification instance."""
    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "notification_type": notification.notification_type,
        "is_read": notification.is_read,
        "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M"),
        "read_at": notification.read_at.strftime("%Y-%m-%d %H:%M") if notification.read_at else None,
        "link": notification.link or "",
    }
