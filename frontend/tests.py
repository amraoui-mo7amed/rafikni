"""
Frontend unit tests for Rafikni Platform.
Tests landing page rendering and social_media integration from social_media.json.
"""

from django.test import TestCase, Client
from django.urls import reverse
from frontend.utils import load_social_media


class FrontendLandingPageTests(TestCase):
    """Test landing page rendering and social media integration."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("frontend:index")

    def test_load_social_media_utility(self):
        """Verify load_social_media reads keys from social_media.json."""
        data = load_social_media()
        self.assertIsInstance(data, dict)
        self.assertIn("facebook", data)
        self.assertIn("instagram", data)
        self.assertIn("email", data)
        self.assertIn("phone", data)
        self.assertIn("youtube", data)

    def test_landing_page_renders_social_media(self):
        """Verify landing page renders social media and contact links in the footer."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertIn("social_media", response.context)

        social = response.context["social_media"]
        if social.get("email"):
            self.assertContains(response, social["email"])
        if social.get("phone"):
            self.assertContains(response, social["phone"])
        if social.get("facebook"):
            self.assertContains(response, social["facebook"])
        if social.get("instagram"):
            self.assertContains(response, social["instagram"])
