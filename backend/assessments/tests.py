from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from assets.models import Location, Asset, LoadCapacity
from assessments.models import Assessment


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def create_assessment(user, asset, location, load_value=500.0, is_compliant=True):
    return Assessment.objects.create(
        location=location,
        asset=asset,
        equipment_type="crane_with_outriggers",
        load_value=load_value,
        capacity_name="max_point_load",
        capacity_metric="kN",
        capacity_limit=1000.0,
        is_compliant=is_compliant,
        created_by=user,
    )


class AssessmentHistoryTests(APITestCase):
    def setUp(self):
        self.url = reverse("assessment-history-list")

        self.user = User.objects.create_user(username="alice", password="pass")
        self.other_user = User.objects.create_user(username="bob", password="pass")

        self.location = Location.objects.create(name="Port of Bunbury")
        self.asset = Asset.objects.create(name="Berth 5", location=self.location)
        LoadCapacity.objects.create(
            asset=self.asset,
            name="max_point_load",
            metric="kN",
            max_load=1000.0,
        )

    def auth(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_tokens(user)}")

    # --- authentication ---

    def test_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- empty history ---

    def test_returns_empty_list_when_no_assessments(self):
        self.auth(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    # --- returns own records ---

    def test_returns_own_assessments(self):
        self.auth(self.user)
        create_assessment(self.user, self.asset, self.location)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    # --- response fields ---

    def test_response_fields(self):
        self.auth(self.user)
        create_assessment(self.user, self.asset, self.location, load_value=850.0, is_compliant=True)
        data = self.client.get(self.url).json()[0]

        self.assertIn("id", data)
        self.assertEqual(data["asset_name"], "Berth 5")
        self.assertEqual(data["location_name"], "Port of Bunbury")
        self.assertEqual(data["load_label"], "Max Outrigger Load")
        self.assertEqual(data["load_value"], 850.0)
        self.assertEqual(data["capacity_metric"], "kN")
        self.assertTrue(data["is_compliant"])
        self.assertIn("created_at", data)

    # --- isolation between users ---

    def test_does_not_return_other_users_assessments(self):
        self.auth(self.user)
        create_assessment(self.other_user, self.asset, self.location)  # bob's record
        response = self.client.get(self.url)
        self.assertEqual(response.json(), [])

    def test_only_returns_own_records_when_mixed(self):
        create_assessment(self.user, self.asset, self.location)
        create_assessment(self.user, self.asset, self.location)
        create_assessment(self.other_user, self.asset, self.location)

        self.auth(self.user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.json()), 2)

    # --- ordering ---

    def test_ordered_most_recent_first(self):
        a1 = create_assessment(self.user, self.asset, self.location)
        a2 = create_assessment(self.user, self.asset, self.location)
        # a2 was created after a1, should appear first
        self.auth(self.user)
        ids = [item["id"] for item in self.client.get(self.url).json()]
        self.assertEqual(ids, [a2.id, a1.id])

    # --- compliance values ---

    def test_non_compliant_assessment(self):
        self.auth(self.user)
        create_assessment(self.user, self.asset, self.location, is_compliant=False)
        data = self.client.get(self.url).json()[0]
        self.assertFalse(data["is_compliant"])
