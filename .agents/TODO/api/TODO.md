# Rafikni Platform - Django Ninja API Implementation Checklist & Roadmap
# Step-by-Step Engineering Execution Plan for API v1

---

## 📋 Overview

This roadmap defines the granular, actionable checklist for developing the Rafikni RESTful API (`/api/v1/`) using **Django Ninja (`django-ninja`)**. Each step is organized as an actionable checkbox item (`- [ ]`) containing:
- **HTTP Method** and **Endpoint Path**.
- **Django Ninja Security / RBAC** (`auth=JWTAuth()`, `auth=AdminAuth()`, `auth=PatientAuth()`, or unauthenticated).
- **Request Schema / Payload** (Pydantic Schema or `ninja.File`/`ninja.UploadedFile`).
- **Expected Success Response** conforming to the unified `ApiResponseSchema[T]` (`{success, message, errors, data}`).
- **Business Logic Rules** (Atomic transactions, payment creation, Gemini AI parsing, notifications).

---

## 🧱 Phase 1: Django Ninja Core Setup & Architecture

- [x] **1.1 Dependency Installation & Project Configuration:**
  - Add `django-ninja` to [`requirements.txt`](file:///Users/amraouimohamed/sites/rafikni/requirements.txt).
  - Run `pip install django-ninja`.
  - Create the `api/` directory structure (`api/schemas/`, `api/routers/`).

- [x] **1.2 NinjaAPI Instance Setup (`api/main.py` & `api/urls.py`):**
  - Initialize `api = NinjaAPI(title="Rafikni API", version="1.0.0", docs_url="/docs")`.
  - Wire `path("api/v1/", api.urls)` in [`core/urls.py`](file:///Users/amraouimohamed/sites/rafikni/core/urls.py).

- [x] **1.3 Unified Base Schemas (`api/schemas/common.py`):**
  - Implement `ApiResponseSchema[T]` adhering to:
    ```python
    class ApiResponseSchema(Schema, Generic[T]):
        success: bool = True
        message: str = "تمت العملية بنجاح"
        errors: List[str] = []
        data: Optional[T] = None
    ```
  - Implement `PaginationMetaSchema` (`page`, `num_pages`, `total_count`, `has_next`, `has_prev`).

- [x] **1.4 JWT Authentication & Django Ninja Security (`api/jwt_auth.py` & `api/security.py`):**
  - Implement `generate_tokens_for_user(user)` producing 60-minute Access and 30-day Refresh tokens using `pyjwt`.
  - Implement `decode_token(token)`.
  - Implement `JWTAuth(HttpBearer)`: Attaches authenticated `request.user`.
  - Implement `AdminAuth(JWTAuth)`: Enforces `user.is_superuser` or `user.profile.role == 'admin'`.
  - Implement `PatientAuth(JWTAuth)`: Enforces `user.profile.role == 'patient'`.
  - Implement `DoctorAuth(JWTAuth)`: Enforces `user.profile.role == 'doc'`.

- [x] **1.5 Shared Media & Exception Utilities (`api/utils.py`):**
  - Implement `build_absolute_media_url(request, file_field)` helper.
  - Register global NinjaAPI exception handlers for `ValidationError` and generic exceptions to always return `{success: false, message: "...", errors: [...]}`.

---

## 🔐 Phase 2: Authentication & Account Management Router (`/api/v1/auth/`)

### 2.1 User Registration
- [x] **Endpoint:** `POST /api/v1/auth/signup/`
  - **Router:** `auth_router.post("/signup", response={201: ApiResponseSchema[None], 400: ApiResponseSchema[None]})`
  - **RBAC:** Public / Unauthenticated.
  - **Request Schema:** `SignupSchema(username, email, password, confirm_password)`.
  - **Logic:**
    - Validate required fields and password match.
    - Check username and email uniqueness.
    - Execute within `with transaction.atomic():`: create user (`is_active = False`) and `UserProfile` (`role = 'patient'`).
    - Generate activation token and dispatch verification email via `emails/email_verification.html`.
  - **Response:** `201 Created` with Arabic message: *"تم إنشاء الحساب بنجاح. يرجى التحقق من بريدك الإلكتروني لتفعيل الحساب."*.

### 2.2 User Login
- [x] **Endpoint:** `POST /api/v1/auth/login/`
  - **Router:** `auth_router.post("/login", response={200: ApiResponseSchema[TokenResponseSchema], 401: ApiResponseSchema[None]})`
  - **RBAC:** Public / Unauthenticated.
  - **Request Schema:** `LoginSchema(username, password)`.
  - **Logic:**
    - Authenticate via `authenticate(request, username=..., password=...)`.
    - Check `user.is_active`. If inactive, return `401 Unauthorized` with Arabic message: *"يرجى تفعيل حسابك من خلال البريد الإلكتروني أولاً"*.
    - Generate JWT access and refresh tokens.
  - **Response:** `200 OK` containing tokens and user profile payload:
    ```json
    {
      "success": true,
      "message": "تم تسجيل الدخول بنجاح",
      "data": {
        "access_token": "...",
        "refresh_token": "...",
        "user": {
          "id": 1,
          "username": "ahmed",
          "email": "ahmed@example.com",
          "first_name": "أحمد",
          "last_name": "محمد",
          "role": "patient",
          "profile_pic": "https://..."
        }
      }
    }
    ```

### 2.3 Refresh Access Token
- [x] **Endpoint:** `POST /api/v1/auth/token/refresh/`
  - **Router:** `auth_router.post("/token/refresh", response={200: ApiResponseSchema[dict], 401: ApiResponseSchema[None]})`
  - **RBAC:** Public.
  - **Request Schema:** `RefreshTokenSchema(refresh_token)`.
  - **Logic:** Validate token type is `refresh`, check expiration, verify active user, issue new 60-minute access token.
  - **Response:** `200 OK` with `{"access_token": "..."}`.

### 2.4 Account Activation
- [x] **Endpoint:** `POST /api/v1/auth/activate/`
  - **Router:** `auth_router.post("/activate", response={200: ApiResponseSchema[None], 400: ApiResponseSchema[None]})`
  - **RBAC:** Public.
  - **Request Schema:** `ActivateSchema(uidb64, token)`.
  - **Logic:** Decode user ID, verify token with `default_token_generator`, activate user (`user.is_active = True`).
  - **Response:** `200 OK` with Arabic message: *"تم تفعيل حسابك بنجاح. يمكنك الآن تسجيل الدخول."*.

### 2.5 Request Password Reset
- [x] **Endpoint:** `POST /api/v1/auth/lost-password/`
  - **Router:** `auth_router.post("/lost-password", response={200: ApiResponseSchema[None], 404: ApiResponseSchema[None]})`
  - **RBAC:** Public.
  - **Request Schema:** `LostPasswordSchema(email)`.
  - **Logic:** Lookup user by email, generate password reset token, dispatch styled email via `emails/password_reset.html`.
  - **Response:** `200 OK` with message: *"تم إرسال رابط تعيين كلمة المرور إلى بريدك الإلكتروني"*.

### 2.6 Confirm Password Reset
- [x] **Endpoint:** `POST /api/v1/auth/password-reset-confirm/`
  - **Router:** `auth_router.post("/password-reset-confirm", response={200: ApiResponseSchema[None], 400: ApiResponseSchema[None]})`
  - **RBAC:** Public.
  - **Request Schema:** `PasswordResetConfirmSchema(uidb64, token, password, confirm_password)`.
  - **Logic:** Validate token, check password match, apply `user.set_password(password)` and save.
  - **Response:** `200 OK` with message: *"تم تغيير كلمة المرور بنجاح"*.

### 2.7 Get Current User Profile
- [x] **Endpoint:** `GET /api/v1/auth/me/`
  - **Router:** `auth_router.get("/me", auth=JWTAuth(), response=ApiResponseSchema[UserProfileOutSchema])`
  - **RBAC:** Authenticated User.
  - **Response:** `200 OK` with user details: ID, username, email, first/last names, role, phone number, birthdate, and full avatar URL.

### 2.8 Update Current User Profile
- [x] **Endpoint:** `PUT /api/v1/auth/me/` (or `PATCH`)
  - **Router:** `auth_router.put("/me", auth=JWTAuth(), response=ApiResponseSchema[UserProfileOutSchema])`
  - **RBAC:** Authenticated User.
  - **Request:** Form parameters (`first_name`, `last_name`, `email`, `phone_number`, `birthdate`) and optional `profile_pic: UploadedFile = File(None)`.
  - **Logic:** Validate email uniqueness (excluding current user), update user and profile fields atomically, store avatar in `media/profiles/`.
  - **Response:** `200 OK` with updated profile data.

---

## 🩺 Phase 3: Medical Cases Router (`/api/v1/medical-cases/`)

### 3.1 List Medical Cases
- [x] **Endpoint:** `GET /api/v1/medical-cases/`
  - **Router:** `cases_router.get("/", auth=JWTAuth(), response=ApiResponseSchema[PaginatedCasesSchema])`
  - **RBAC:** Patient or Admin.
  - **Query Parameters:** `q: Optional[str] = None`, `category: Optional[str] = None`, `page: int = 1`.
  - **Logic:**
    - If patient: filter `c.user == request.user`.
    - If admin: return all cases across all users with patient username.
  - **Response:** `200 OK` with paginated case objects and pagination metadata.

### 3.2 Get Medical Case Details
- [x] **Endpoint:** `GET /api/v1/medical-cases/{case_type}/{case_id}/`
  - **Router:** `cases_router.get("/{case_type}/{case_id}", auth=JWTAuth(), response=ApiResponseSchema[CaseDetailSchema])`
  - **RBAC:** Case Owner (Patient) or Admin.
  - **Logic:** Validate `case_type` (`child`, `adult`, `elderly`). Enforce ownership permissions. Return all fields including `is_approved`.
  - **Response:** `200 OK` with full case details.

### 3.3 Create Medical Case with Payment Receipt (Atomic Mandate)
- [x] **Endpoint:** `POST /api/v1/medical-cases/`
  - **Router:** `cases_router.post("/", auth=PatientAuth(), response={201: ApiResponseSchema[CaseDetailSchema], 400: ApiResponseSchema[None]})`
  - **RBAC:** Patient Only.
  - **Request Body (Multipart):**
    - Form fields: `category` (`child` / `adult` / `elderly`), `full_name`, `age`, `gender` (`male`/`female`), `aphasie` (`true`/`false`).
    - Child fields: `disorders`, `syndromes`, `intellectual_disability` (`weak`/`middle`/`hard`).
    - Elderly fields: `alzheimer` (`true`/`false`), `parkinson` (`true`/`false`).
    - Mandatory File: `receipt_image: UploadedFile = File(...)`.
  - **Business Rules (Per AGENTS.md):**
    - Require `receipt_image` (return `400 Bad Request` if missing).
    - Wrap creation in `with transaction.atomic():`.
    - Instantiate corresponding model (`ChildMedicalCase`, `AdultMedicalCase`, or `ElderlyMedicalCase`).
    - Call `dashboard.utils.create_payment(user=request.user, content_object=case, receipt_image=receipt_image)`.
    - Dispatch real-time alert to admins via `dashboard.utils.notify_admins`.
  - **Response:** `201 Created` with Arabic message: *"تم إضافة الحالة الطبية بنجاح وهي قيد المراجعة"*.

### 3.4 Delete Medical Case
- [x] **Endpoint:** `DELETE /api/v1/medical-cases/{case_type}/{case_id}/`
  - **Router:** `cases_router.delete("/{case_type}/{case_id}", auth=JWTAuth(), response=ApiResponseSchema[None])`
  - **RBAC:** Case Owner (Patient) or Admin.
  - **Logic:** Check ownership permission, delete case record and associated media.
  - **Response:** `200 OK` with message: *"تم حذف الحالة الطبية بنجاح"*.

### 3.5 Case Choices Metadata
- [x] **Endpoint:** `GET /api/v1/medical-cases/choices/`
  - **Router:** `cases_router.get("/choices", response=ApiResponseSchema[CaseChoicesSchema])`
  - **RBAC:** Public / Authenticated.
  - **Response:** `200 OK` containing Arabic labels and keys for categories, gender, and intellectual disability levels.

---

## 🧠 Phase 4: AI Treatment Plans Router (`/api/v1/treatment-plans/`)

### 4.1 Generate Treatment Plan via Gemini AI
- [x] **Endpoint:** `POST /api/v1/treatment-plans/generate/{case_type}/{case_id}/`
  - **Router:** `plans_router.post("/generate/{case_type}/{case_id}", auth=AdminAuth(), response=ApiResponseSchema[TreatmentPlanSchema])`
  - **RBAC:** Admin Only.
  - **Logic:**
    - Fetch case by type and ID.
    - Invoke `dashboard.gemini_utils.generate_treatment_plan(case)`.
    - Validate parsed JSON contains `sections` with the 5 clinical areas: Assessment (`التقييم`), Goals (`الأهداف`), Plan (`الخطة العلاجية`), Recommendations (`التوصيات`), and Follow-up (`المتابعة`).
    - Save or update via `TreatmentPlan.objects.update_or_create(content_type=..., object_id=..., defaults={"plan_data": data, "created_by": request.user})`.
    - Send real-time notification to the patient via `notify_user`.
    - Gracefully catch API quota errors and return `422 Unprocessable` with a friendly Arabic message.
  - **Response:** `200 OK` with saved `plan_data` and timestamps.

### 4.2 Get Treatment Plan
- [x] **Endpoint:** `GET /api/v1/treatment-plans/{case_type}/{case_id}/`
  - **Router:** `plans_router.get("/{case_type}/{case_id}", auth=JWTAuth(), response=ApiResponseSchema[Optional[TreatmentPlanSchema]])`
  - **RBAC:** Case Owner (Patient) or Admin.
  - **Logic:** Retrieve `TreatmentPlan` for the target case. If none exists, return `plan_data: null`.
  - **Response:** `200 OK` with `plan_data`, `created_at`, and author metadata.

---

## 🎓 Phase 5: Educational Courses & Videos Router (`/api/v1/courses/`)

### 5.1 Courses Catalog
- [x] **Endpoint:** `GET /api/v1/courses/`
  - **Router:** `courses_router.get("/", response=ApiResponseSchema[PaginatedCoursesSchema])`
  - **RBAC:** Public / Authenticated.
  - **Query Parameters:** `q: Optional[str] = None`, `page: int = 1`.
  - **Logic:** Filter `is_active = True`. If user is authenticated, attach user's enrollment status (`is_enrolled`, `status`).
  - **Response:** `200 OK` with course cards list.

### 5.2 Course Details & Syllabus
- [x] **Endpoint:** `GET /api/v1/courses/{course_id}/`
  - **Router:** `courses_router.get("/{course_id}", response=ApiResponseSchema[CourseDetailSchema])`
  - **RBAC:** Public / Authenticated.
  - **Logic:**
    - Fetch course and associated `Video` items ordered by `order`.
    - Determine video locking status:
      - Video 0 (`is_free = True`): Unlocked for all.
      - Subsequent videos: Locked unless user has `CourseEnrollment.status == 'approved'` or is admin.
  - **Response:** `200 OK` with course details, videos list, and access status flag.

### 5.3 Course Enrollment
- [x] **Endpoint:** `POST /api/v1/courses/{course_id}/enroll/`
  - **Router:** `courses_router.post("/{course_id}/enroll", auth=JWTAuth(), response=ApiResponseSchema[EnrollmentResponseSchema])`
  - **RBAC:** Authenticated User.
  - **Logic:**
    - Check if enrollment already exists.
    - If `course.price == 0` (Free): Set `status = 'approved'`, return immediate access.
    - If `course.price > 0` (Paid): Set `status = 'pending'`, return `requires_payment: true` with `enrollment_id` for receipt submission.
  - **Response:** `200 OK` with status and instructions.

### 5.4 My Enrolled Courses
- [x] **Endpoint:** `GET /api/v1/courses/my-courses/`
  - **Router:** `courses_router.get("/my-courses", auth=JWTAuth(), response=ApiResponseSchema[List[EnrolledCourseSchema]])`
  - **RBAC:** Authenticated User.
  - **Response:** `200 OK` with list of user enrollments and course cards.

### 5.5 Video Streaming & Playback Info
- [x] **Endpoint:** `GET /api/v1/courses/{course_id}/videos/{video_id}/`
  - **Router:** `courses_router.get("/{course_id}/videos/{video_id}", response=ApiResponseSchema[VideoStreamSchema])`
  - **RBAC:** Public if `video.is_free`, else Approved Enrolled User or Admin.
  - **Logic:** Enforce paid content gating. Return direct media URL, title, description, duration.
  - **Response:** `200 OK` with video streaming metadata.

### 5.6 Admin Course Management Endpoints
- [x] **Create Course:** `POST /api/v1/courses/` (`auth=AdminAuth()`, `thumbnail: UploadedFile = File(None)`).
- [x] **Edit Course:** `PUT /api/v1/courses/{course_id}/` (`auth=AdminAuth()`).
- [x] **Delete Course:** `DELETE /api/v1/courses/{course_id}/` (`auth=AdminAuth()`).
- [x] **Upload Video:** `POST /api/v1/courses/{course_id}/videos/` (`auth=AdminAuth()`, `video_file: UploadedFile = File(...)`). Auto-mark first video as `is_free = True`.
- [x] **Delete Video:** `DELETE /api/v1/courses/videos/{video_id}/` (`auth=AdminAuth()`).
- [x] **Approve Enrollment:** `POST /api/v1/courses/enrollments/{enrollment_id}/approve/` (`auth=AdminAuth()`). Synchronize linked payment, notify user.
- [x] **Reject Enrollment:** `POST /api/v1/courses/enrollments/{enrollment_id}/reject/` (`auth=AdminAuth()`). Requires rejection reason in notes, synchronize linked payment, notify user.
- [x] **Revoke Enrollment:** `POST /api/v1/courses/enrollments/{enrollment_id}/revoke/` (`auth=AdminAuth()`). Reset enrollment and linked payment to pending.

---

## 💳 Phase 6: Payments & Verification Router (`/api/v1/payments/`)

### 6.1 Submit Course Payment Receipt
- [x] **Endpoint:** `POST /api/v1/payments/course-enrollment/{enrollment_id}/`
  - **Router:** `payments_router.post("/course-enrollment/{enrollment_id}", auth=JWTAuth(), response={201: ApiResponseSchema[None], 400: ApiResponseSchema[None]})`
  - **RBAC:** Enrollment Owner.
  - **Request Body:** `receipt_image: UploadedFile = File(...)`.
  - **Logic:**
    - Verify enrollment belongs to `request.user` and status is `PENDING`.
    - Create `Payment` record inside `transaction.atomic()`.
    - Alert admins via `notify_admins`.
  - **Response:** `201 Created` with message: *"تم إرسال إيصال الدفع بنجاح، سيتم مراجعته من قبل الإدارة"*.

### 6.2 Admin List Payments
- [x] **Endpoint:** `GET /api/v1/payments/`
  - **Router:** `payments_router.get("/", auth=AdminAuth(), response=ApiResponseSchema[PaginatedPaymentsSchema])`
  - **RBAC:** Admin Only.
  - **Query Parameters:** `status: Optional[str] = None`, `content_type: Optional[str] = None`, `q: Optional[str] = None`, `page: int = 1`.
  - **Response:** `200 OK` with paginated payment cards and full receipt image URLs.

### 6.3 Admin Payment Details
- [x] **Endpoint:** `GET /api/v1/payments/{payment_id}/`
  - **Router:** `payments_router.get("/{payment_id}", auth=AdminAuth(), response=ApiResponseSchema[PaymentDetailSchema])`
  - **RBAC:** Admin Only.
  - **Response:** `200 OK` with payer info, target entity details (course or medical case), and review status.

### 6.4 Admin Review Payment (Approve / Reject Sync)
- [x] **Endpoint:** `POST /api/v1/payments/{payment_id}/review/`
  - **Router:** `payments_router.post("/{payment_id}/review", auth=AdminAuth(), response=ApiResponseSchema[None])`
  - **RBAC:** Admin Only.
  - **Request Schema:** `ReviewPaymentSchema(action: "approve" | "reject")`.
  - **Logic (Atomic State Sync):**
    - Execute within `with transaction.atomic():`.
    - Update `payment.status`, `payment.reviewed_by = request.user`, `payment.reviewed_at = timezone.now()`.
    - Synchronize target object:
      - If `CourseEnrollment`: set `enrollment.status = APPROVED` (or `REJECTED`).
      - If `MedicalCase`: set `case.is_approved = True` (or `False`).
    - Send real-time notification to user via `notify_user`.
  - **Response:** `200 OK` with message: *"تم قبول الدفع بنجاح"* or *"تم رفض الدفع بنجاح"*.

---

## 🎮 Phase 7: Educational Games & COD Orders Router (`/api/v1/games/`)

### 7.1 List Games Catalog
- [x] **Endpoint:** `GET /api/v1/games/`
  - **Router:** `games_router.get("/", response=ApiResponseSchema[List[GameCardSchema]])`
  - **RBAC:** Public.
  - **Response:** `200 OK` with active games list (title, slug, price, thumbnail, tags).

### 7.2 Game Details & Gallery
- [x] **Endpoint:** `GET /api/v1/games/{slug}/`
  - **Router:** `games_router.get("/{slug}", response=ApiResponseSchema[GameDetailSchema])`
  - **RBAC:** Public.
  - **Response:** `200 OK` with game description and full gallery images list.

### 7.3 Place Cash on Delivery (COD) Order
- [x] **Endpoint:** `POST /api/v1/games/orders/`
  - **Router:** `games_router.post("/orders", response={201: ApiResponseSchema[None], 400: ApiResponseSchema[None]})`
  - **RBAC:** Public / Guest or Authenticated.
  - **Request Schema:** `PlaceOrderSchema(game_id, full_name, phone_number, wilaya, commune, address)`.
  - **Logic:**
    - Validate delivery fields.
    - Create `GameOrder` with status `PENDING`.
    - Attach `user` if request is authenticated.
    - Notify admins via `notify_admins`.
  - **Response:** `201 Created` with message: *"تم استلام طلبك بنجاح! سنتصل بك قريباً لتأكيد التوصيل."*.

### 7.4 Admin Games & Orders Management
- [x] **Create Game:** `POST /api/v1/games/` (`auth=AdminAuth()`, `thumbnail: UploadedFile = File(...)`, gallery images).
- [x] **Edit Game:** `PUT /api/v1/games/{game_id}/` (`auth=AdminAuth()`).
- [x] **Delete Game:** `DELETE /api/v1/games/{game_id}/` (`auth=AdminAuth()`).
- [x] **List COD Orders:** `GET /api/v1/games/orders/` (`auth=AdminAuth()`).
- [x] **Update Order Status:** `POST /api/v1/games/orders/{order_id}/status/` (`auth=AdminAuth()`): update status to `confirmed`, `delivered`, or `cancelled`.

---

## 📰 Phase 8: Articles & Health Knowledge Base Router (`/api/v1/articles/`)

### 8.1 List Published Articles
- [x] **Endpoint:** `GET /api/v1/articles/`
  - **Router:** `articles_router.get("/", response=ApiResponseSchema[List[ArticleCardSchema]])`
  - **RBAC:** Public.
  - **Query Parameters:** `category: Optional[str] = None`, `q: Optional[str] = None`.
  - **Response:** `200 OK` with published articles list.

### 8.2 Article Details & Related Articles
- [x] **Endpoint:** `GET /api/v1/articles/{slug}/`
  - **Router:** `articles_router.get("/{slug}", response=ApiResponseSchema[ArticleDetailSchema])`
  - **RBAC:** Public.
  - **Logic:** Fetch article by slug. Retrieve up to 6 related articles from same category.
  - **Response:** `200 OK` with article content and related items list.

### 8.3 Admin Article Operations
- [x] **Admin List All:** `GET /api/v1/admin/articles/` (`auth=AdminAuth()`).
- [x] **Create Article:** `POST /api/v1/articles/` (`auth=AdminAuth()`, `thumbnail: UploadedFile = File(None)`).
- [x] **Edit Article:** `PUT /api/v1/articles/{article_id}/` (`auth=AdminAuth()`).
- [x] **Delete Article:** `DELETE /api/v1/articles/{article_id}/` (`auth=AdminAuth()`).

---

## 🔔 Phase 9: Real-Time Notifications Router (`/api/v1/notifications/`)

### 9.1 Unread Notifications Count
- [x] **Endpoint:** `GET /api/v1/notifications/unread-count/`
  - **Router:** `notifications_router.get("/unread-count", auth=JWTAuth(), response=ApiResponseSchema[dict])`
  - **RBAC:** Authenticated User.
  - **Response:** `200 OK` with `{"count": 3}`.

### 9.2 List Notifications
- [x] **Endpoint:** `GET /api/v1/notifications/`
  - **Router:** `notifications_router.get("/", auth=JWTAuth(), response=ApiResponseSchema[List[NotificationSchema]])`
  - **RBAC:** Authenticated User.
  - **Response:** `200 OK` with top 50 notifications for current user.

### 9.3 Mark Single Notification as Read
- [x] **Endpoint:** `POST /api/v1/notifications/{notification_id}/read/`
  - **Router:** `notifications_router.post("/{notification_id}/read", auth=JWTAuth(), response=ApiResponseSchema[None])`
  - **RBAC:** Notification Owner.
  - **Response:** `200 OK`.

### 9.4 Mark All Notifications as Read
- [x] **Endpoint:** `POST /api/v1/notifications/mark-all-read/`
  - **Router:** `notifications_router.post("/mark-all-read", auth=JWTAuth(), response=ApiResponseSchema[None])`
  - **RBAC:** Authenticated User.
  - **Response:** `200 OK`.

### 9.5 Delete Notification
- [x] **Endpoint:** `DELETE /api/v1/notifications/{notification_id}/`
  - **Router:** `notifications_router.delete("/{notification_id}", auth=JWTAuth(), response=ApiResponseSchema[None])`
  - **RBAC:** Notification Owner.
  - **Response:** `200 OK`.

---

## 👥 Phase 10: User Management & Doctor Onboarding Router (`/api/v1/users/`)

### 10.1 Admin List Users
- [x] **Endpoint:** `GET /api/v1/users/`
  - **Router:** `users_router.get("/", auth=AdminAuth(), response=ApiResponseSchema[PaginatedUsersSchema])`
  - **RBAC:** Admin Only.
  - **Query Parameters:** `q: Optional[str] = None`, `role: Optional[str] = None`, `status: Optional[str] = None`, `page: int = 1`.
  - **Logic:** Exclude superuser accounts from modifications.
  - **Response:** `200 OK` with paginated user list.

### 10.2 Admin User Details
- [x] **Endpoint:** `GET /api/v1/users/{user_id}/`
  - **Router:** `users_router.get("/{user_id}", auth=AdminAuth(), response=ApiResponseSchema[UserDetailSchema])`
  - **RBAC:** Admin Only.
  - **Response:** `200 OK` with detailed profile data.

### 10.3 Toggle User Active / Banned Status
- [x] **Endpoint:** `POST /api/v1/users/{user_id}/toggle-status/`
  - **Router:** `users_router.post("/{user_id}/toggle-status", auth=AdminAuth(), response=ApiResponseSchema[None])`
  - **RBAC:** Admin Only.
  - **Logic:** Guard against modifying superusers. Toggle `is_active` state.
  - **Response:** `200 OK` with message: *"تم تفعيل المستخدم بنجاح"* or *"تم حظر المستخدم بنجاح"*.

### 10.4 Delete User
- [x] **Endpoint:** `DELETE /api/v1/users/{user_id}/`
  - **Router:** `users_router.delete("/{user_id}", auth=AdminAuth(), response=ApiResponseSchema[None])`
  - **RBAC:** Admin Only.
  - **Logic:** Guard against deleting superusers. Remove user and profile.
  - **Response:** `200 OK` with message: *"تم حذف المستخدم بنجاح"*.

### 10.5 Create Doctor Account with Automated Credentials
- [x] **Endpoint:** `POST /api/v1/users/create-doctor/`
  - **Router:** `users_router.post("/create-doctor", auth=AdminAuth(), response={201: ApiResponseSchema[None], 400: ApiResponseSchema[None]})`
  - **RBAC:** Admin Only.
  - **Request Body (Multipart):** `username`, `email`, `first_name`, `last_name`, `phone_number`, `birthdate`, `profile_pic: UploadedFile = File(None)`.
  - **Logic:**
    - Validate username and email uniqueness.
    - Generate secure 12-char random password via `generate_secure_password()`.
    - Run inside `with transaction.atomic():`.
    - Create user with `role = RoleChoices.DOC`.
    - Dispatch login credentials email via `send_doctor_credentials_email()`. If email fails, transaction is rolled back.
    - Notify other admins.
  - **Response:** `201 Created` with message: *"تم إنشاء حساب الطبيب بنجاح. تم إرسال بيانات الدخول إلى البريد الإلكتروني."*.

---

## 🗺️ Phase 11: Algerian Geographic Data Router (`/api/v1/geo/`)

### 11.1 List 58 Algerian Wilayas
- [x] **Endpoint:** `GET /api/v1/geo/wilayas/`
  - **Router:** `geo_router.get("/wilayas", response=ApiResponseSchema[List[WilayaSchema]])`
  - **RBAC:** Public.
  - **Logic:** Parse `algeria.json` using `dashboard.utils.get_algeria_wilayas()`, sort by code.
  - **Response:** `200 OK` with `[{"code": "01", "name": "أدرار"}, ...]`.

### 11.2 List Communes by Wilaya Code
- [x] **Endpoint:** `GET /api/v1/geo/communes/`
  - **Router:** `geo_router.get("/communes", response=ApiResponseSchema[List[CommuneSchema]])`
  - **RBAC:** Public.
  - **Query Parameters:** `wilaya_code: str`.
  - **Logic:** Filter communes for target wilaya code using `dashboard.utils.get_algeria_communes(wilaya_code)`.
  - **Response:** `200 OK` with `[{"id": 22, "name": "تيمقتن"}, ...]`.

---

## 📊 Phase 12: Admin Analytics Router (`/api/v1/analytics/`)

### 12.1 Dashboard Analytics Overview
- [x] **Endpoint:** `GET /api/v1/analytics/overview/`
  - **Router:** `analytics_router.get("/overview", auth=AdminAuth(), response=ApiResponseSchema[AnalyticsOverviewSchema])`
  - **RBAC:** Admin Only.
  - **Response:** `200 OK` with metrics:
    - Total users, active users, inactive users.
    - New users joined this month and monthly growth rate percentage.
    - Breakdown of users by role (`patient`, `doc`, `admin`).
    - Pending payments count and pending COD orders count.

---

## 🧪 Phase 13: Testing, Verification & OpenAPI Documentation

- [x] **13.1 Authentication & RBAC Tests:**
  - Automated tests verifying JWT token issuance and expiration.
  - Test verifying `401 Unauthorized` for missing/invalid bearer tokens.
  - Test verifying `403 Forbidden` for patients attempting admin actions.

- [x] **13.2 Atomic Payment & Case Tests:**
  - Verify case creation fails and rolls back cleanly if payment creation fails.
  - Verify payment approval synchronizes target enrollment or medical case status.

- [x] **13.3 Gemini AI Plan Generation Mock Tests:**
  - Test Gemini AI parsing, model persistence, and patient notification dispatch.

- [x] **13.4 Django Ninja OpenAPI Docs Verification:**
  - Verify interactive Swagger UI is live at `/api/v1/docs`.
  - Verify Redoc is accessible at `/api/v1/redoc`.
  - Verify every user-facing message returned is in proper Arabic.
