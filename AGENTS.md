# Agent Instructions for Rafikni

Rafikni is a Django-based platform designed to support families and children with special needs (Autism, ADHD, Orthophony). This document provides essential guidelines for agents working on this codebase.

---

## 🛠 1. Build, Lint, and Test Commands

### Environment Setup
- **Install Dependencies:** `pip install -r requirements.txt`
- **Environment Variables:** Create a `.env` file in the root based on settings in `core/settings.py` (needs `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`).
- **Database Migrations:** 
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```
- **Run Development Server:** `python manage.py runserver`

### Linting and Formatting
- **Template Linting:** Uses `djlint` for Django templates.
    - Check: `djlint . --check`
    - Reformat: `djlint . --reformat`
- **Python Style:** Follow PEP 8. Standard Django conventions apply.

### Testing
- **Run All Tests:** `python manage.py test`
- **Run Specific App:** `python manage.py test user_auth`
- **Run Single Test Class:** `python manage.py test user_auth.tests.AuthTests`
- **Run Single Test Method:** `python manage.py test user_auth.tests.AuthTests.test_login_success`

---

## 🎨 2. Code Style and Conventions

### Python (Django)
- **Framework:** Django 6.0+
- **Views:** 
    - Prefer **Function-Based Views (FBVs)** for simplicity, especially for AJAX-heavy logic.
    - Organize views in a `views/` directory within each app (e.g., `user_auth/views/auth.py`).
- **Naming Conventions:**
    - Variables & Functions: `snake_case` (e.g., `login_view`, `user_data`).
    - Classes & Models: `PascalCase` (e.g., `PatientProfile`, `MedicalRecord`).
- **Imports:**
    - Standard library imports first.
    - Third-party imports (Django, etc.) second.
    - Local app imports third.
    - Use absolute imports when possible (e.g., `from user_auth.models import User`).

### API and Error Handling
- **AJAX Interactions:** Use `JsonResponse` for frontend-backend communication.
- **Response Structure:** Maintain a consistent JSON format:
    ```json
    {
        "success": true,
        "message": "تمت العملية بنجاح", // Arabic success message
        "errors": [],                 // List of error strings
        "data": {}                    // Optional payload
    }
    ```
- **Error Handling:** Always wrap complex view logic in `try...except` blocks. Catch specific exceptions where possible, and return user-friendly Arabic messages in the `errors` list.

### Frontend and Templates
- **Localization:** 
    - Primary Language: **Arabic (ar-sa)**.
    - Direction: **RTL (Right-to-Left)**. 
    - Always use `dir="rtl"` and `lang="ar"` in the root HTML tag.
- **Static Assets:** 
    - Global assets: `/static/`
    - App-specific: `/<app_name>/static/<app_name>/[css|js|img]/`
- **CSS:** Uses **Bootstrap 5 (RTL version)**. Custom styles should be modular.
- **Icons:** **Font Awesome 6** is available via CDN.
- **Templates:** Use Django's template inheritance (`{% extends ... %}`, `{% block ... %}`).

---

## 📂 3. Repository Structure

- **`core/`**: Central configuration (settings, main URLs, ASGI/WSGI).
- **`user_auth/`**: Authentication system, user profiles, and session management.
- **`backend/`**: Business logic, database models for patients, records, and specialists.
- **`frontend/`**: Landing pages, public-facing templates, and UI components.
- **`static/`**: Global static files (CSS/JS).
- **`templates/`**: Global template fragments (partials, base layouts).

---

## 🔐 4. Security Guidelines

- **CSRF Protection:** Always include `{% csrf_token %}` in HTML forms. For AJAX `POST` requests, ensure the `X-CSRFToken` header is set.
- **Authentication:** Use Django's built-in `authenticate`, `login`, and `logout` functions. Always check `request.user.is_authenticated` where appropriate.
- **Sensitive Data:** Never hardcode secrets. Use `os.getenv` or `dotenv` to load values from `.env`.
- **Database Safety:** Use Django ORM's built-in protection against SQL injection. Avoid raw SQL queries.

---

## 📝 5. Development Workflow

1. **Analysis:** Check existing models in `backend/models.py` or `user_auth/models.py` before adding new fields.
2. **Migrations:** Always run `makemigrations` and `migrate` after changing models.
3. **Frontend:** When modifying templates, ensure the RTL layout remains intact. Test responsiveness for mobile users.
4. **Verification:** Run `python manage.py test` before finalizing any PR.

---

## 🚀 6. Common Django Patterns in Rafikni

### Function-Based Views (FBV) with AJAX
Most interactive features use FBVs that return `JsonResponse`. Example pattern:
```python
def my_feature_view(request):
    if request.method == "POST":
        try:
            # logic here
            return JsonResponse({"success": True, "message": "نجحت العملية"})
        except Exception as e:
            return JsonResponse({"success": False, "errors": [str(e)]})
    return render(request, "my_feature.html")
```

### Context Processors and Global Data
Check `core/settings.py` for global context processors. Currently, it uses standard Django processors.

### Static File Versioning
In templates, we often use `{% now "U" %}` to bust cache for CSS/JS during development:
`<link href="{% static 'css/index.css' %}?v={% now 'U' %}" rel="stylesheet" />`

---

## 🤖 7. Agent Mandates

- **Arabic First:** All user-facing strings, including error messages and success alerts, MUST be in Arabic.
- **RTL Compliance:** When adding new UI components, verify they work correctly in a Right-to-Left layout. Use Bootstrap's RTL classes (e.g., `ms-*` instead of `mr-*`).
- **Function over Class:** Favor Function-Based Views unless Class-Based Views are explicitly requested or provide significant complexity reduction.
- **Atomic Commits:** Keep changes modular. One migration set per feature.


## 8. Development Guidelines

### 8.1. Error Handling
- **Always** use `{% include "partials/errorList.html" with form_id="<form_id>" %}` to display form errors.
- **Never** use `{% if form.errors %}` directly in templates.
- never use a custom form handeling except if i told you

### 8.2. Brand Consistency 
- always use the same color palette and typography as the existing project.
- **Never** use colors or fonts that are not already used in the project.
- always use ```templates/partials/styled_select.html``` instead of every select tag 
- always use ```templates/partials/ultra_image_upload.html``` instead of every image upload input

## 8.3. Project Stucture 

- always separate the js and css from the template 
- always use ```{% block extra_css %}{% endblock extra_css %}``` and ```{% block extra_js %}{% endblock extra_js %}``` for the extra css and js

- the reusable components files must exist in ```templates/partials/```, ```static/css/```, ```static/js/```  

- never ever do something i didnt tell you, always stick to my orders 
- always use ``notify-send`` to alert me for the finished tasks 
- all delete buttons must use sweet alert as a confirmation 
- always use data attributes instead of using hardcoded urls 
