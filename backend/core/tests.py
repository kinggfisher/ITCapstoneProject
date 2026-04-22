from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from core.permissions import IsAdmin, IsUser, IsAdminOrReadOnly
from core.email_utils import (
    _build_subject,
    _build_plain,
    _build_html,
    send_compliance_failure_alert,
)


# Permission Tests
class IsAdminPermissionTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.perm = IsAdmin()

    def _make_request(self, user):
        request = self.factory.get("/")
        request.user = user
        return request

    def test_staff_user_allowed(self):
        user = User.objects.create_user("admin", is_staff=True)
        self.assertTrue(self.perm.has_permission(self._make_request(user), None))

    def test_regular_user_denied(self):
        user = User.objects.create_user("viewer")
        self.assertFalse(self.perm.has_permission(self._make_request(user), None))

    def test_unauthenticated_denied(self):
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.perm.has_permission(request, None))


class IsAdminOrReadOnlyPermissionTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.perm = IsAdminOrReadOnly()
        self.admin = User.objects.create_user("admin", is_staff=True)
        self.viewer = User.objects.create_user("viewer")

    def _make_request(self, method, user):
        request = getattr(self.factory, method.lower())("/")
        request.user = user
        return request

    def test_admin_can_post(self):
        self.assertTrue(self.perm.has_permission(self._make_request("POST", self.admin), None))

    def test_admin_can_delete(self):
        self.assertTrue(self.perm.has_permission(self._make_request("DELETE", self.admin), None))

    def test_viewer_can_get(self):
        self.assertTrue(self.perm.has_permission(self._make_request("GET", self.viewer), None))

    def test_viewer_cannot_post(self):
        self.assertFalse(self.perm.has_permission(self._make_request("POST", self.viewer), None))

    def test_viewer_cannot_put(self):
        self.assertFalse(self.perm.has_permission(self._make_request("PUT", self.viewer), None))


# Email Utils Tests

def _make_mock_assessment():
    """Build a lightweight mock Assessment-like object."""
    assessment = MagicMock()
    assessment.asset.name = "Drawing-001"
    assessment.asset.location.name = "Site A"
    assessment.get_equipment_type_display.return_value = "Crane with outriggers"
    assessment.equipment_model = "Liebherr LTM"
    assessment.load_value = 60.0
    assessment.capacity_metric = "kN"
    assessment.capacity_limit = 50.0
    assessment.notes = None
    return assessment


class BuildSubjectTest(TestCase):
    def test_subject_contains_asset_name(self):
        assessment = _make_mock_assessment()
        subject = _build_subject(assessment)
        self.assertIn("Drawing-001", subject)
        self.assertIn("FAILED", subject)


class BuildPlainTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="engineer", password="pass", email="eng@test.com"
        )
        self.assessment = _make_mock_assessment()

    def test_plain_contains_asset_name(self):
        text = _build_plain(self.user, self.assessment)
        self.assertIn("Drawing-001", text)

    def test_plain_contains_location(self):
        text = _build_plain(self.user, self.assessment)
        self.assertIn("Site A", text)

    def test_plain_contains_load_values(self):
        text = _build_plain(self.user, self.assessment)
        self.assertIn("60.0", text)
        self.assertIn("50.0", text)

    def test_plain_contains_username(self):
        text = _build_plain(self.user, self.assessment)
        self.assertIn("engineer", text)

    def test_plain_no_notes_section_when_none(self):
        self.assessment.notes = None
        text = _build_plain(self.user, self.assessment)
        self.assertNotIn("Notes:", text)

    def test_plain_includes_notes_when_set(self):
        self.assessment.notes = "Check the east wing"
        text = _build_plain(self.user, self.assessment)
        self.assertIn("Check the east wing", text)


class BuildHtmlTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="engineer", password="pass", first_name="Alice"
        )
        self.assessment = _make_mock_assessment()

    def test_html_contains_failed_label(self):
        html = _build_html(self.user, self.assessment)
        self.assertIn("FAILED", html)

    def test_html_contains_asset_name(self):
        html = _build_html(self.user, self.assessment)
        self.assertIn("Drawing-001", html)

    def test_html_contains_location(self):
        html = _build_html(self.user, self.assessment)
        self.assertIn("Site A", html)

    def test_html_contains_load_value(self):
        html = _build_html(self.user, self.assessment)
        self.assertIn("60.0", html)

    def test_html_notes_row_absent_when_none(self):
        self.assessment.notes = None
        html = _build_html(self.user, self.assessment)
        self.assertNotIn("Check the east wing", html)

    def test_html_notes_row_present_when_set(self):
        self.assessment.notes = "Check the east wing"
        html = _build_html(self.user, self.assessment)
        self.assertIn("Check the east wing", html)


class SendComplianceAlertTest(TestCase):
    def setUp(self):
        self.user_with_email = User.objects.create_user(
            username="engineer", password="pass", email="eng@test.com"
        )
        self.user_no_email = User.objects.create_user(
            username="noemail", password="pass", email=""
        )
        self.assessment = _make_mock_assessment()

    @patch("core.email_utils.settings")
    def test_no_op_when_alerts_disabled(self, mock_settings):
        mock_settings.EMAIL_ALERTS_ENABLED = False
        with patch("core.email_utils._send_via_gmail") as mock_gmail:
            send_compliance_failure_alert(self.user_with_email, self.assessment)
            mock_gmail.assert_not_called()

    @patch("core.email_utils.settings")
    def test_no_op_when_user_has_no_email(self, mock_settings):
        mock_settings.EMAIL_ALERTS_ENABLED = True
        mock_settings.EMAIL_PROVIDER = "gmail"
        with patch("core.email_utils._send_via_gmail") as mock_gmail:
            send_compliance_failure_alert(self.user_no_email, self.assessment)
            mock_gmail.assert_not_called()

    @patch("core.email_utils.settings")
    def test_gmail_called_when_provider_gmail(self, mock_settings):
        mock_settings.EMAIL_ALERTS_ENABLED = True
        mock_settings.EMAIL_PROVIDER = "gmail"
        with patch("core.email_utils._send_via_gmail") as mock_gmail:
            send_compliance_failure_alert(self.user_with_email, self.assessment)
            mock_gmail.assert_called_once_with(self.user_with_email, self.assessment)

    @patch("core.email_utils.settings")
    def test_resend_called_when_provider_resend(self, mock_settings):
        mock_settings.EMAIL_ALERTS_ENABLED = True
        mock_settings.EMAIL_PROVIDER = "resend"
        with patch("core.email_utils._send_via_resend") as mock_resend:
            send_compliance_failure_alert(self.user_with_email, self.assessment)
            mock_resend.assert_called_once_with(self.user_with_email, self.assessment)

    @patch("core.email_utils.settings")
    def test_email_exception_does_not_raise(self, mock_settings):
        """Sending failures must never propagate to callers."""
        mock_settings.EMAIL_ALERTS_ENABLED = True
        mock_settings.EMAIL_PROVIDER = "gmail"
        with patch("core.email_utils._send_via_gmail", side_effect=Exception("SMTP down")):
            # Should not raise
            send_compliance_failure_alert(self.user_with_email, self.assessment)


# Core Views Tests

class HomeViewTest(TestCase):
    def test_home_returns_json(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())


class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="engineer", password="pass")

    def test_logout_requires_authentication(self):
        response = self.client.post("/api/logout/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_token(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/logout/", {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Successfully logged out")

    def test_logout_with_invalid_refresh_token(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/logout/", {"refresh": "not-a-real-token"})
        # Invalid token → 400 from the blacklist call
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ExtractDesignCriteriaViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_no_file_returns_400(self):
        response = self.client.post("/api/extract/", {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_unsupported_file_type_returns_400(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("doc.txt", b"some content", content_type="text/plain")
        response = self.client.post("/api/extract/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_image_file_returns_400(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("photo.png", b"\x89PNG\r\n", content_type="image/png")
        response = self.client.post("/api/extract/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("core.views.extract_text_from_file", return_value="Project: BuildingA\nDrawing: DA-001\nMax Point Load: 50 kN")
    def test_valid_pdf_returns_extracted_data(self, mock_extract):
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("test.pdf", b"%PDF-1.4 ...", content_type="application/pdf")
        response = self.client.post("/api/extract/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("project", response.data)
        self.assertIn("capacities", response.data)

    @patch("core.views.extract_text_from_file", return_value="   ")
    def test_empty_text_returns_400(self, mock_extract):
        from django.core.files.uploadedfile import SimpleUploadedFile
        file = SimpleUploadedFile("test.pdf", b"%PDF-1.4 ...", content_type="application/pdf")
        response = self.client.post("/api/extract/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)


# JWT Auth Flow
class JWTAuthFlowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_obtain_token(self):
        response = self.client.post("/api/token/", {
            "username": "testuser",
            "password": "testpass123",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_wrong_credentials_denied(self):
        response = self.client.post("/api/token/", {
            "username": "testuser",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        tokens = self.client.post("/api/token/", {
            "username": "testuser",
            "password": "testpass123",
        }).data
        response = self.client.post("/api/token/refresh/", {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_access_protected_endpoint_with_token(self):
        tokens = self.client.post("/api/token/", {
            "username": "testuser",
            "password": "testpass123",
        }).data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = self.client.get("/api/assessments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_endpoint_without_token(self):
        response = self.client.get("/api/assessments/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
