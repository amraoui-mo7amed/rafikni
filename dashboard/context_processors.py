from django.urls import reverse, resolve
from user_auth.models import UserProfile

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

    menu_sections = []

    # Home section (All authenticated users)
    if user.is_authenticated:
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
    if role == UserProfile.RoleChoices.ADMIN or user.is_superuser:
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
                        "name": "الحالات الطبية",
                        "url_name": "dashboard:medical_case_list",
                        "icon": "fa-solid fa-notes-medical",
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

    # System section (All authenticated users)
    if user.is_authenticated:
        system_items = []

        # Admin specific system items
        if role == "admin" or user.is_superuser:
            system_items.append(
                {
                    "name": "إعدادات البريد",
                    "url_name": "dashboard:email_settings",
                    "icon": "fa-solid fa-envelope-open-text",
                }
            )

        # Common system items
        system_items.extend(
            [
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
        )

        menu_sections.append(
            {
                "label": "النظام",
                "items": system_items,
                "mt_auto": True,
            }
        )

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
