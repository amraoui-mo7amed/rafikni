from functools import lru_cache
from django.urls import reverse, resolve
from user_auth.models import UserProfile
import copy


@lru_cache(maxsize=128)
def get_menu_structure(is_authenticated, role):
    menu_sections = []

    # Home section (All authenticated users)
    if is_authenticated:
        menu_sections.append(
            {
                "label": "القائمة الرئيسية",
                "items": [
                    {
                        "name": "الرئيسية",
                        "url_name": "dashboard:index",
                        "icon": "fa-solid fa-house-chimney",
                    },
                ],
            }
        )

    # Management section (Role-based)
    if role == UserProfile.RoleChoices.ADMIN:
        menu_sections.append(
            {
                "label": "الإدارة",
                "items": [
                    {
                        "name": "المستخدمين",
                        "url_name": "dashboard:user_list",
                        "icon": "fa-solid fa-users",
                    },
                    {
                        "name": "الحالات",
                        "url_name": "dashboard:medical_case_list",
                        "icon": "fa-solid fa-notes-medical",
                    },
                    {
                        "name": "الدورات",
                        "url_name": "dashboard:course_list",
                        "icon": "fa-solid fa-graduation-cap",
                    },
                    {
                        "name": "المدفوعات",
                        "url_name": "dashboard:payment_list",
                        "icon": "fa-solid fa-credit-card",
                    },
                    {
                        "name": "المقالات",
                        "url_name": "dashboard:article_list",
                        "icon": "fa-solid fa-newspaper",
                    },
                    {
                        "name": "الألعاب",
                        "url_name": "dashboard:game_list",
                        "icon": "fa-solid fa-gamepad",
                    },
                    {
                        "name": "طلبات الألعاب",
                        "url_name": "dashboard:game_order_list",
                        "icon": "fa-solid fa-cart-shopping",
                    },
                ],
            }
        )
    elif role == UserProfile.RoleChoices.PATIENT:
        menu_sections.append(
            {
                "label": "الملف الطبي",
                "items": [
                    {
                        "name": "حالاتي الطبية",
                        "url_name": "dashboard:medical_case_list",
                        "icon": "fa-solid fa-notes-medical",
                    },
                ],
            }
        )
        menu_sections.append(
            {
                "label": "التعليم",
                "items": [
                    {
                        "name": "دوراتي",
                        "url_name": "dashboard:my_courses",
                        "icon": "fa-solid fa-book-open",
                    },
                ],
            }
        )
    else:
        # Other roles (doctors, etc.) can also access courses
        menu_sections.append(
            {
                "label": "التعليم",
                "items": [
                    {
                        "name": "الدورات التعليمية",
                        "url_name": "dashboard:course_list",
                        "icon": "fa-solid fa-graduation-cap",
                    },
                ],
            }
        )

    # System section (All authenticated users)
    if is_authenticated:
        system_items = [
            {
                "name": "الملف الشخصي",
                "url_name": "dashboard:profile_update",
                "icon": "fa-solid fa-user-pen",
            },
            {
                "name": "تسجيل الخروج",
                "url_name": "user_auth:logout",
                "icon": "fa-solid fa-right-from-bracket",
                "class": "text-danger",
            },
        ]

        menu_sections.append(
            {
                "label": "النظام",
                "items": system_items,
                "mt_auto": True,
            }
        )
    return menu_sections


def sidebar_menu(request):
    current_url_name = None
    try:
        current_url_name = resolve(request.path_info).url_name
        namespace = resolve(request.path_info).namespace
        if namespace:
            current_url_name = f"{namespace}:{current_url_name}"
    except:
        pass

    user = request.user
    role = getattr(user.profile, "role", None) if hasattr(user, "profile") else None
    
    # Force admin role if superuser for menu visibility
    effective_role = role
    if user.is_superuser:
        effective_role = UserProfile.RoleChoices.ADMIN

    # Get structure from cache
    menu_sections = copy.deepcopy(get_menu_structure(user.is_authenticated, effective_role))

    # Process items for active state and URLs
    for section in menu_sections:
        for item in section["items"]:
            try:
                if item["url_name"] == "#":
                    item["url"] = "#"
                else:
                    item["url"] = reverse(item["url_name"])
            except:
                item["url"] = "#"

            # Simple active state check
            item["active"] = current_url_name == item.get("url_name")

    return {"sidebar_menu": menu_sections}

