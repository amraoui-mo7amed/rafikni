from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from unittest.mock import patch, MagicMock
import json

from user_auth.models import UserProfile
from user_auth.views.auth import (
    login_view,
    signup_view,
    activate_view,
    lost_password_view,
    password_reset_confirm_view,
    logout_view,
    send_styled_email,
)
from dashboard.models import EmailConfiguration


class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            is_active=True,
        )
        self.url = reverse("user_auth:login")

    def test_login_get_request(self):
        """Test that login page renders correctly"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth.html")

    def test_login_post_success(self):
        """Test successful login"""
        response = self.client.post(
            self.url,
            {"username": "testuser", "password": "testpass123"},
        )
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "تم تسجيل الدخول بنجاح")
        self.assertEqual(data["redirect_url"], reverse("dashboard:index"))

    def test_login_post_inactive_user(self):
        """Test login with inactive user"""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            self.url,
            {"username": "testuser", "password": "testpass123"},
        )
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("يرجى تفعيل حسابك من خلال البريد الإلكتروني أولاً", data["errors"])

    def test_login_post_wrong_password(self):
        """Test login with wrong password"""
        response = self.client.post(
            self.url,
            {"username": "testuser", "password": "wrongpassword"},
        )
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("اسم المستخدم أو كلمة المرور غير صحيحة", data["errors"])

    def test_login_post_nonexistent_user(self):
        """Test login with non-existent user"""
        response = self.client.post(
            self.url,
            {"username": "nonexistent", "password": "testpass123"},
        )
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("اسم المستخدم أو كلمة المرور غير صحيحة", data["errors"])

    def test_login_redirects_if_authenticated(self):
        """Test that authenticated user is redirected"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard:index"))


class SignupViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("user_auth:signup")
        self.valid_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpass123",
            "confirm_password": "newpass123",
        }

    def test_signup_get_request(self):
        """Test that signup page renders correctly"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth.html")

    def test_signup_post_success(self):
        """Test successful signup"""
        response = self.client.post(self.url, self.valid_data)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("تم إنشاء الحساب بنجاح", data["message"])

        user = User.objects.get(username="newuser")
        self.assertFalse(user.is_active)
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(user.profile.role, UserProfile.RoleChoices.PATIENT)

    def test_signup_missing_fields(self):
        """Test signup with missing fields"""
        response = self.client.post(
            self.url,
            {"username": "", "email": "", "password": "", "confirm_password": ""},
        )
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("يرجى ملء جميع الحقول", data["errors"])

    def test_signup_password_mismatch(self):
        """Test signup with password mismatch"""
        data = self.valid_data.copy()
        data["confirm_password"] = "differentpass"
        response = self.client.post(self.url, data)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("كلمات المرور غير متطابقة", data["errors"])

    def test_signup_duplicate_username(self):
        """Test signup with duplicate username"""
        User.objects.create_user(
            username="newuser", email="existing@example.com", password="testpass123"
        )
        response = self.client.post(self.url, self.valid_data)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("اسم المستخدم موجود بالفعل", data["errors"])

    def test_signup_duplicate_email(self):
        """Test signup with duplicate email"""
        User.objects.create_user(
            username="existinguser", email="new@example.com", password="testpass123"
        )
        response = self.client.post(self.url, self.valid_data)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("البريد الإلكتروني مستخدم بالفعل", data["errors"])

    def test_signup_redirects_if_authenticated(self):
        """Test that authenticated user is redirected"""
        user = User.objects.create_user(
            username="loggedin", email="logged@example.com", password="testpass123"
        )
        self.client.login(username="loggedin", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("dashboard:index"))


class ActivateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            is_active=False,
        )
        self.token = default_token_generator.make_token(self.user)
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.url = reverse(
            "user_auth:activate", kwargs={"uidb64": self.uid, "token": self.token}
        )

    def test_activate_success(self):
        """Test successful account activation"""
        response = self.client.get(self.url)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "activation_success.html")

    def test_activate_invalid_uid(self):
        """Test activation with invalid UID"""
        url = reverse(
            "user_auth:activate",
            kwargs={"uidb64": "invalid-uid", "token": self.token},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth.html")
        self.assertIn("error_message", response.context)

    def test_activate_invalid_token(self):
        """Test activation with invalid token"""
        url = reverse(
            "user_auth:activate",
            kwargs={"uidb64": self.uid, "token": "invalid-token-12345"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth.html")


class LostPasswordViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            is_active=True,
        )
        self.url = reverse("user_auth:lost_password")

    def test_lost_password_get_request(self):
        """Test that lost password page renders correctly"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth.html")

    def test_lost_password_post_success(self):
        """Test successful password reset request"""
        response = self.client.post(self.url, {"email": "test@example.com"})
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("تم إرسال رابط تعيين كلمة المرور", data["message"])

    def test_lost_password_post_missing_email(self):
        """Test password reset request without email"""
        response = self.client.post(self.url, {"email": ""})
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("يرجى إدخال البريد الإلكتروني", data["errors"])

    def test_lost_password_post_nonexistent_email(self):
        """Test password reset request with non-existent email"""
        response = self.client.post(self.url, {"email": "nonexistent@example.com"})
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("البريد الإلكتروني غير موجود", data["errors"])


class PasswordResetConfirmViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            is_active=True,
        )
        self.token = default_token_generator.make_token(self.user)
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.url = reverse(
            "user_auth:password_reset_confirm",
            kwargs={"uidb64": self.uid, "token": self.token},
        )

    def test_reset_confirm_get_valid_token(self):
        """Test that password reset confirm page renders with valid token"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth.html")

    def test_reset_confirm_get_invalid_token(self):
        """Test that invalid token shows error"""
        url = reverse(
            "user_auth:password_reset_confirm",
            kwargs={"uidb64": self.uid, "token": "invalid-token"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth.html")
        self.assertIn("error_message", response.context)

    def test_reset_confirm_post_success(self):
        """Test successful password reset"""
        response = self.client.post(
            self.url,
            {"password": "newpassword123", "confirm_password": "newpassword123"},
        )
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "تم تغيير كلمة المرور بنجاح")
        self.assertEqual(data["redirect_url"], reverse("user_auth:login"))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

    def test_reset_confirm_post_password_mismatch(self):
        """Test password reset with mismatching passwords"""
        response = self.client.post(
            self.url,
            {"password": "newpassword123", "confirm_password": "differentpass"},
        )
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("كلمات المرور غير متطابقة", data["errors"])

    def test_reset_confirm_post_missing_password(self):
        """Test password reset with missing password"""
        response = self.client.post(
            self.url,
            {"password": "", "confirm_password": ""},
        )
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("يرجى إدخال كلمة المرور الجديدة", data["errors"])


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.url = reverse("user_auth:logout")

    def test_logout_success(self):
        """Test successful logout"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("user_auth:login"))


class SendStyledEmailTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        Site.objects.create(domain="example.com", name="Example")

    @patch("user_auth.views.auth.logger")
    def test_send_styled_email_without_config(self, mock_logger):
        """Test sending email without EmailConfiguration"""
        request = self.factory.get("/")
        request.META["SERVER_NAME"] = "example.com"
        request.META["SERVER_PORT"] = "80"

        with patch("user_auth.views.auth.EmailMessage") as mock_email_class:
            mock_email = MagicMock()
            mock_email_class.return_value = mock_email

            send_styled_email(
                request,
                self.user,
                "Test Subject",
                "emails/email_verification.html",
                {"activation_url": "http://example.com/activate"},
            )

            mock_email_class.assert_called_once()
            mock_email.send.assert_called_once_with(fail_silently=False)
            mock_logger.info.assert_called()

    @patch("user_auth.views.auth.logger")
    def test_send_styled_email_with_config(self, mock_logger):
        """Test sending email with EmailConfiguration"""
        EmailConfiguration.objects.create(
            name="Test Config",
            email_host="smtp.example.com",
            email_port=587,
            email_host_user="test@example.com",
            email_host_password="password",
            default_from_email="noreply@example.com",
            is_active=True,
        )

        request = self.factory.get("/")
        request.META["SERVER_NAME"] = "example.com"
        request.META["SERVER_PORT"] = "80"

        with patch("user_auth.views.auth.EmailMessage") as mock_email_class:
            mock_email = MagicMock()
            mock_email_class.return_value = mock_email

            send_styled_email(
                request,
                self.user,
                "Test Subject",
                "emails/email_verification.html",
                {"activation_url": "http://example.com/activate"},
            )

            call_kwargs = mock_email_class.call_args.kwargs
            self.assertEqual(call_kwargs["from_email"], "noreply@example.com")

    @patch("user_auth.views.auth.logger")
    def test_send_styled_email_failure(self, mock_logger):
        """Test email sending failure"""
        request = self.factory.get("/")
        request.META["SERVER_NAME"] = "example.com"
        request.META["SERVER_PORT"] = "80"

        with patch("user_auth.views.auth.EmailMessage") as mock_email_class:
            mock_email = MagicMock()
            mock_email.send.side_effect = Exception("SMTP Error")
            mock_email_class.return_value = mock_email

            with self.assertRaises(Exception):
                send_styled_email(
                    request,
                    self.user,
                    "Test Subject",
                    "emails/email_verification.html",
                    {"activation_url": "http://example.com/activate"},
                )

            mock_logger.error.assert_called()


class EmailTemplateTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

    def test_email_verification_template_renders(self):
        """Test that email verification template renders correctly"""
        from django.template.loader import render_to_string

        context = {
            "user": self.user,
            "domain": "example.com",
            "protocol": "http",
            "activation_url": "http://example.com/activate/test",
        }

        html = render_to_string("emails/email_verification.html", context)
        self.assertIn(self.user.username, html)
        self.assertIn("http://example.com/activate/test", html)
        self.assertIn("تفعيل الحساب", html)

    def test_password_reset_template_renders(self):
        """Test that password reset template renders correctly"""
        from django.template.loader import render_to_string

        context = {
            "user": self.user,
            "domain": "example.com",
            "protocol": "http",
            "reset_url": "http://example.com/reset/test",
        }

        html = render_to_string("emails/password_reset.html", context)
        self.assertIn(self.user.username, html)
        self.assertIn("http://example.com/reset/test", html)
        self.assertIn("تعيين كلمة مرور جديدة", html)
