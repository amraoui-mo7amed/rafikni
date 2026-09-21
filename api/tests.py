"""
Comprehensive Automated Test Suite for Rafikni RESTful API v1 (Django Ninja).
Covers Authentication, RBAC, Medical Cases, Atomic Payments, Courses,
Games, Articles, Geo endpoints, and Gemini AI Treatment Plans.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from user_auth.models import UserProfile
from dashboard.models import (
    ChildMedicalCase,
    AdultMedicalCase,
    Payment,
    Course,
    Video,
    CourseEnrollment,
    Game,
    GameOrder,
    Article,
    TreatmentPlan,
    Notification,
)
from api.jwt_auth import generate_tokens_for_user


class ApiBaseTestCase(TestCase):
    """Base setup with admin, doctor, and patient users with JWT credentials."""

    def setUp(self):
        self.client = Client()

        # 1. Admin User
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@rafikni.dz",
            password="AdminPassword123!",
            first_name="Admin",
            last_name="System",
            is_staff=True,
            is_superuser=True,
        )
        self.admin_profile = self.admin_user.profile
        self.admin_profile.phone_number = "0550112233"
        self.admin_profile.save()
        self.admin_tokens = generate_tokens_for_user(self.admin_user)
        self.admin_token = self.admin_tokens["access_token"]
        self.admin_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}

        # 2. Patient User
        self.patient_user = User.objects.create_user(
            username="patientuser",
            email="patient@rafikni.dz",
            password="PatientPassword123!",
            first_name="Fatima",
            last_name="Zahra",
        )
        self.patient_profile = self.patient_user.profile
        self.patient_profile.phone_number = "0660445566"
        self.patient_profile.save()
        self.patient_tokens = generate_tokens_for_user(self.patient_user)
        self.patient_token = self.patient_tokens["access_token"]
        self.patient_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.patient_token}"}

        # 3. Doctor User
        self.doc_user = User.objects.create_user(
            username="doctoruser",
            email="doctor@rafikni.dz",
            password="DoctorPassword123!",
            first_name="Dr. Ahmed",
            last_name="Mansouri",
        )
        self.doc_profile = self.doc_user.profile
        self.doc_profile.role = UserProfile.RoleChoices.DOC
        self.doc_profile.phone_number = "0770778899"
        self.doc_profile.save()
        self.doc_tokens = generate_tokens_for_user(self.doc_user)
        self.doc_token = self.doc_tokens["access_token"]
        self.doc_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.doc_token}"}


class AuthAndRbacApiTests(ApiBaseTestCase):
    """Test authentication endpoints, token issuance, refresh, and RBAC matrix."""

    @patch("api.routers.auth.send_styled_email")
    def test_signup_success(self, mock_email):
        """Verify patient signup creates user, profile, and sends activation email."""
        payload = {
            "username": "newpatient",
            "email": "newpatient@rafikni.dz",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "first_name": "Karim",
            "last_name": "Belkacem",
            "phone_number": "0555998877",
            "birthdate": "1995-04-12",
        }
        response = self.client.post(
            "/api/v1/auth/signup",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(User.objects.filter(username="newpatient").exists())

    @patch("api.routers.auth.send_styled_email")
    def test_signup_atomic_rollback_on_email_failure(self, mock_email):
        """Verify patient signup rolls back atomically if sending activation email fails."""
        mock_email.side_effect = Exception("SMTP Connection Refused")
        payload = {
            "username": "atomicuser",
            "email": "atomicuser@rafikni.dz",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "first_name": "Atomic",
            "last_name": "Test",
        }
        response = self.client.post(
            "/api/v1/auth/signup",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        # Ensure user creation was completely rolled back
        self.assertFalse(User.objects.filter(username="atomicuser").exists())

    @patch("api.routers.auth.send_styled_email")
    def test_signup_atomic_rollback_when_email_returns_zero(self, mock_email):
        """Verify patient signup rolls back atomically if email sending returns zero (no email delivered)."""
        mock_email.return_value = 0
        payload = {
            "username": "atomiczero_api",
            "email": "atomiczero_api@rafikni.dz",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "first_name": "AtomicZero",
            "last_name": "Test",
        }
        response = self.client.post(
            "/api/v1/auth/signup",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        # Ensure account is not created if the email is not sent
        self.assertFalse(User.objects.filter(username="atomiczero_api").exists())

    def test_login_success(self):
        """Verify login returns valid tokens and profile."""
        payload = {
            "username": "patientuser",
            "password": "PatientPassword123!",
        }
        response = self.client.post(
            "/api/v1/auth/login",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("access_token", data["data"])
        self.assertEqual(data["data"]["user"]["username"], "patientuser")

    def test_login_invalid_credentials(self):
        """Verify login failure returns 401 and Arabic error message."""
        payload = {
            "username": "patientuser",
            "password": "WrongPassword999!",
        }
        response = self.client.post(
            "/api/v1/auth/login",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertTrue(len(data["errors"]) > 0)

    def test_refresh_token_endpoint(self):
        """Verify refresh token endpoint provides a fresh access token."""
        refresh = self.patient_tokens["refresh_token"]
        response = self.client.post(
            "/api/v1/auth/token/refresh",
            data=json.dumps({"refresh_token": refresh}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("access_token", data["data"])

    def test_rbac_patient_forbidden_on_admin_endpoint(self):
        """Verify patient receives 403 when requesting admin-only endpoint."""
        response = self.client.get(
            "/api/v1/users/",
            **self.patient_headers,
        )
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data["success"])

    def test_unauthorized_when_token_missing(self):
        """Verify protected endpoint returns 401 when no token is provided."""
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertFalse(data["success"])

    def test_get_current_user_profile(self):
        """Verify GET /api/v1/auth/me returns current user data."""
        response = self.client.get(
            "/api/v1/auth/me",
            **self.patient_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["username"], "patientuser")


class MedicalCaseAndPaymentTests(ApiBaseTestCase):
    """Test child/adult case creation, atomic payment attachment, and admin review."""

    def test_create_child_case_atomic_with_payment(self):
        """Test POST /api/v1/medical-cases/ creates case and linked pending payment."""
        dummy_receipt = SimpleUploadedFile(
            "receipt.jpg", b"fake_receipt_bytes", content_type="image/jpeg"
        )
        payload = {
            "category": "child",
            "full_name": "أمين بن علي",
            "age": 6,
            "gender": "male",
            "aphasie": "false",
            "disorders": "توحد",
            "syndromes": "",
            "intellectual_disability": "weak",
            "receipt_image": dummy_receipt,
        }
        response = self.client.post(
            "/api/v1/medical-cases/",
            data=payload,
            **self.patient_headers,
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        case_id = data["data"]["id"]

        # Verify DB records
        case = ChildMedicalCase.objects.get(id=case_id)
        self.assertEqual(case.full_name, "أمين بن علي")
        self.assertFalse(case.is_approved)

        # Verify Payment was atomically created for this case
        payment = Payment.objects.filter(
            user=self.patient_user,
            status=Payment.PaymentStatus.PENDING,
            object_id=case.id,
        ).first()
        self.assertIsNotNone(payment)

    def test_payment_review_approves_case_atomically(self):
        """Test admin approving payment marks target MedicalCase is_approved = True."""
        case = AdultMedicalCase.objects.create(
            user=self.patient_user,
            full_name="فاطمة الزهراء",
            age=25,
            gender="female",
            is_approved=False,
        )
        dummy_receipt = SimpleUploadedFile(
            "rec.jpg", b"receipt", content_type="image/jpeg"
        )
        payment = Payment.objects.create(
            user=self.patient_user,
            receipt_image=dummy_receipt,
            status=Payment.PaymentStatus.PENDING,
            content_object=case,
        )

        # Admin reviews payment -> approve
        payload = {"action": "approve", "notes": "تم التحقق من الوصل بنجاح"}
        response = self.client.post(
            f"/api/v1/payments/{payment.id}/review",
            data=json.dumps(payload),
            content_type="application/json",
            **self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)

        # Reload records
        payment.refresh_from_db()
        case.refresh_from_db()

        self.assertEqual(payment.status, Payment.PaymentStatus.APPROVED)
        self.assertTrue(case.is_approved)


class CoursesAndVideoTests(ApiBaseTestCase):
    """Test educational courses, video locking mechanism, and enrollment."""

    def setUp(self):
        super().setUp()
        self.free_course = Course.objects.create(
            title="مقدمة في طيف التوحد",
            description="دورة تمهيدية مجانية",
            price=0,
            is_active=True,
            created_by=self.admin_user,
        )
        dummy_video = SimpleUploadedFile(
            "video.mp4", b"fake_mp4_bytes", content_type="video/mp4"
        )
        self.v1 = Video.objects.create(
            course=self.free_course,
            title="الدرس الأول (مقدمة)",
            video_file=dummy_video,
            order=0,
            is_free=True,
        )
        self.v2 = Video.objects.create(
            course=self.free_course,
            title="الدرس الثاني (المفاهيم الأساسية)",
            video_file=dummy_video,
            order=1,
            is_free=False,
        )

    def test_public_courses_catalog(self):
        """Verify public access to course catalog."""
        response = self.client.get("/api/v1/courses/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["data"]["items"]), 1)

    def test_course_detail_video_locking(self):
        """Verify free video is unlocked, paid video is locked without enrollment."""
        response = self.client.get(f"/api/v1/courses/{self.free_course.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        videos = data["data"]["videos"]
        self.assertFalse(videos[0]["is_locked"])
        self.assertTrue(videos[1]["is_locked"])

    def test_free_course_enrollment_auto_approves(self):
        """Verify enrolling in free course grants instant approved status."""
        response = self.client.post(
            f"/api/v1/courses/{self.free_course.id}/enroll",
            **self.patient_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "approved")
        self.assertFalse(data["data"]["requires_payment"])


class GamesAndArticlesTests(ApiBaseTestCase):
    """Test therapeutic games, COD orders, and educational articles."""

    def setUp(self):
        super().setUp()
        self.game = Game.objects.create(
            title="مكعب التركيز الحركي",
            slug="focus-cube",
            description="لعبة مخصصة لتنمية المهارات الحركية الدقيقة",
            price=2800,
            is_active=True,
        )
        self.article = Article.objects.create(
            title="كيفية التعامل مع نوبات الغضب لدى أطفال التوحد",
            slug="autism-temper-tantrums",
            content="محتوى توعوي وإرشادي للأسر...",
            category=Article.CategoryChoices.AFTER_BIRTH,
            author=self.admin_user,
            is_published=True,
        )

    def test_games_catalog_and_detail(self):
        """Verify games listing and single item detail."""
        response = self.client.get("/api/v1/games/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        detail_resp = self.client.get(f"/api/v1/games/{self.game.slug}")
        self.assertEqual(detail_resp.status_code, 200)
        detail_data = detail_resp.json()
        self.assertEqual(detail_data["data"]["title"], "مكعب التركيز الحركي")

    def test_place_cod_order(self):
        """Verify placing cash-on-delivery order for games."""
        payload = {
            "game_id": self.game.id,
            "full_name": "سليم عيسى",
            "phone_number": "0551234567",
            "wilaya": "الجزائر",
            "commune": "باب الوادي",
            "address": "حي النصر، عمارة 4",
        }
        response = self.client.post(
            "/api/v1/games/orders",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["success"])
        order_id = data["data"]["id"]

        order = GameOrder.objects.get(id=order_id)
        self.assertEqual(order.full_name, "سليم عيسى")

    def test_articles_catalog_and_filter(self):
        """Verify article listing with stage filter."""
        response = self.client.get("/api/v1/articles/?category=after_birth")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["data"]), 1)


class GeoAndAnalyticsTests(ApiBaseTestCase):
    """Test Algerian geographic data lookups and admin dashboard analytics."""

    def test_algerian_wilayas_list(self):
        """Verify GET /api/v1/geo/wilayas returns 58 wilayas."""
        response = self.client.get("/api/v1/geo/wilayas")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 58)

    def test_algerian_communes_lookup(self):
        """Verify GET /api/v1/geo/communes returns communes for Algiers (16)."""
        response = self.client.get("/api/v1/geo/communes?wilaya_code=16")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["data"]), 0)

    def test_admin_analytics_overview(self):
        """Verify admin can access system overview analytics metrics."""
        response = self.client.get(
            "/api/v1/analytics/overview",
            **self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("total_users", data["data"])
        self.assertIn("pending_payments", data["data"])


class TreatmentPlanMockTests(ApiBaseTestCase):
    """Test Gemini AI treatment plan generation and patient retrieval."""

    @patch("api.routers.treatment_plans.generate_treatment_plan")
    def test_admin_generate_ai_plan(self, mock_gemini):
        """Verify admin triggering Gemini plan generation saves TreatmentPlan."""
        mock_gemini.return_value = {
            "sections": [
                {
                    "title": "التقييم الشامل",
                    "content": "تقييم أولي يوضح تحسن في التواصل البصري",
                    "icon": "clipboard-check",
                },
                {
                    "title": "الأهداف العلاجية",
                    "content": "تحسين الاستجابة للنداء وزيادة التركيز",
                    "icon": "bullseye",
                },
                {
                    "title": "الخطة المقترحة",
                    "content": "جلسات تخاطب مرتين أسبوعياً وتدريبات منزلية",
                    "icon": "calendar-alt",
                },
                {
                    "title": "توصيات للأسرة",
                    "content": "تقليل التعرض للشاشات واستخدام البطاقات المصورة",
                    "icon": "heart",
                },
                {
                    "title": "المتابعة والتقييم",
                    "content": "إعادة التقييم بعد مرور شهرين",
                    "icon": "chart-line",
                },
            ]
        }

        case = AdultMedicalCase.objects.create(
            user=self.patient_user,
            full_name="فاطمة",
            age=22,
            gender="female",
            is_approved=True,
        )

        response = self.client.post(
            f"/api/v1/treatment-plans/generate/adult/{case.id}",
            **self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # Patient retrieves the generated plan
        get_resp = self.client.get(
            f"/api/v1/treatment-plans/adult/{case.id}",
            **self.patient_headers,
        )
        self.assertEqual(get_resp.status_code, 200)
        plan_data = get_resp.json()
        self.assertTrue(plan_data["success"])
        self.assertEqual(len(plan_data["data"]["plan_data"]["sections"]), 5)


class OpenApiDocsTests(ApiBaseTestCase):
    """Verify OpenAPI specification and Redoc documentation endpoints are restricted to admins."""

    def test_unauthenticated_docs_redirects_to_login(self):
        """Verify GET /api/v1/docs redirects unauthenticated users to login page."""
        response = self.client.get("/api/v1/docs", HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.headers.get("Location", ""))

    def test_unauthenticated_openapi_json_returns_403(self):
        """Verify GET /api/v1/openapi.json returns 403 Forbidden for unauthenticated users."""
        response = self.client.get("/api/v1/openapi.json")
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data["success"])

    def test_admin_can_access_redoc_docs(self):
        """Verify admin user can access Redoc documentation at /api/v1/docs."""
        self.client.force_login(self.admin_user)
        response = self.client.get("/api/v1/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"redoc", response.content.lower())

    def test_admin_can_access_openapi_json(self):
        """Verify admin user can retrieve OpenAPI specification with token or session."""
        response = self.client.get(
            "/api/v1/openapi.json",
            **self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertIn("openapi", schema)
        self.assertIn("paths", schema)
        self.assertEqual(schema["info"]["title"], "Rafikni RESTful API")


