from django.urls import reverse, resolve

def sidebar_menu(request):
    current_url_name = None
    try:
        current_url_name = resolve(request.path_info).url_name
        namespace = resolve(request.path_info).namespace
        if namespace:
            current_url_name = f"{namespace}:{current_url_name}"
    except:
        pass

    menu_sections = [
        {
            "label": "القائمة الرئيسية",
            "items": [
                {
                    "name": "الرئيسية",
                    "url_name": "dashboard:index",
                    "icon": "fa-solid fa-house-chimney",
                }
            ],
        },
        {
            "label": "النظام",
            "items": [
                {
                    "name": "إعدادات البريد",
                    "url_name": "dashboard:email_settings",
                    "icon": "fa-solid fa-envelope-open-text",
                },
                {
                    "name": "تسجيل الخروج",
                    "url_name": "user_auth:logout",
                    "icon": "fa-solid fa-right-from-bracket",
                    "class": "text-danger",
                }
            ],
            "mt_auto": True
        },
    ]

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
            item["active"] = (current_url_name == item.get("url_name"))

    return {"sidebar_menu": menu_sections}
