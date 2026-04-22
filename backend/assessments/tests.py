from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock

from assets.models import Location, Asset, LoadCapacity
from assessments.models import Assessment
from .serializers import AssessmentSerializer
from .mappings import EQUIPMENT_CAPACITY_MAP


# Shared helpers

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


# Model Tests

class AssessmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.location = Location.objects.create(name="Site A")
        self.asset = Asset.objects.create(location=self.location, name="Drawing-001")
        self.capacity = LoadCapacity.objects.create(
            asset=self.asset,
            name=LoadCapacity.CapacityName.MAX_POINT_LOAD,
            metric=LoadCapacity.Metric.KN,
            max_load=50.0,
        )

    def _make_assessment(self, load_value, compliant):
        return Assessment.objects.create(
            location=self.location,
            asset=self.asset,
            equipment_type=Assessment.EquipmentType.CRANE_WITH_OUTRIGGERS,
            load_value=load_value,
            capacity_name=LoadCapacity.CapacityName.MAX_POINT_LOAD,
            capacity_metric=LoadCapacity.Metric.KN,
            capacity_limit=50.0,
            is_compliant=compliant,
            created_by=self.user,
        )

    def test_str_pass(self):
        a = self._make_assessment(30.0, True)
        self.assertIn("PASS", str(a))
        self.assertIn("Drawing-001", str(a))

    def test_str_fail(self):
        a = self._make_assessment(70.0, False)
        self.assertIn("FAIL", str(a))

    def test_equipment_type_choices(self):
        choices = [c[0] for c in Assessment.EquipmentType.choices]
        self.assertIn("crane_with_outriggers", choices)
        self.assertIn("mobile_crane", choices)
        self.assertIn("heavy_vehicle", choices)
        self.assertIn("elevated_work_platform", choices)
        self.assertIn("storage_load", choices)
        self.assertIn("vessel", choices)

    def test_optional_fields(self):
        a = self._make_assessment(30.0, True)
        self.assertIsNone(a.equipment_model)
        self.assertIsNone(a.notes)


# Mappings Tests

class MappingsTest(TestCase):
    def test_all_equipment_types_mapped(self):
        expected = {
            "crane_with_outriggers",
            "mobile_crane",
            "heavy_vehicle",
            "elevated_work_platform",
            "storage_load",
            "vessel",
        }
        self.assertEqual(set(EQUIPMENT_CAPACITY_MAP.keys()), expected)

    def test_crane_with_outriggers_maps_to_max_point_load(self):
        capacity_name, _ = EQUIPMENT_CAPACITY_MAP["crane_with_outriggers"]
        self.assertEqual(capacity_name, LoadCapacity.CapacityName.MAX_POINT_LOAD)

    def test_mobile_crane_maps_to_max_axle_load(self):
        capacity_name, _ = EQUIPMENT_CAPACITY_MAP["mobile_crane"]
        self.assertEqual(capacity_name, LoadCapacity.CapacityName.MAX_AXLE_LOAD)

    def test_heavy_vehicle_maps_to_max_axle_load(self):
        capacity_name, _ = EQUIPMENT_CAPACITY_MAP["heavy_vehicle"]
        self.assertEqual(capacity_name, LoadCapacity.CapacityName.MAX_AXLE_LOAD)

    def test_ewp_maps_to_max_point_load(self):
        capacity_name, _ = EQUIPMENT_CAPACITY_MAP["elevated_work_platform"]
        self.assertEqual(capacity_name, LoadCapacity.CapacityName.MAX_POINT_LOAD)

    def test_storage_load_maps_to_udl(self):
        capacity_name, _ = EQUIPMENT_CAPACITY_MAP["storage_load"]
        self.assertEqual(capacity_name, LoadCapacity.CapacityName.MAX_UNIFORM_DISTRIBUTOR_LOAD)

    def test_vessel_maps_to_displacement(self):
        capacity_name, _ = EQUIPMENT_CAPACITY_MAP["vessel"]
        self.assertEqual(capacity_name, LoadCapacity.CapacityName.MAX_DISPLACEMENT_SIZE)

    def test_each_mapping_has_two_values(self):
        for key, value in EQUIPMENT_CAPACITY_MAP.items():
            self.assertEqual(len(value), 2, f"Mapping for '{key}' should have exactly 2 values")


# Serializer Tests

class AssessmentSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.location = Location.objects.create(name="Site A")
        self.asset = Asset.objects.create(location=self.location, name="Drawing-001")
        self.capacity = LoadCapacity.objects.create(
            asset=self.asset,
            name=LoadCapacity.CapacityName.MAX_POINT_LOAD,
            metric=LoadCapacity.Metric.KN,
            max_load=50.0,
        )

    def _base_data(self, **overrides):
        data = {
            "location": self.location.id,
            "asset": self.asset.id,
            "equipment_type": "crane_with_outriggers",
            "load_value": 30.0,
        }
        data.update(overrides)
        return data

    def test_valid_data_is_compliant(self):
        serializer = AssessmentSerializer(data=self._base_data(load_value=30.0))
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertTrue(serializer.validated_data["is_compliant"])

    def test_load_exceeds_capacity_not_compliant(self):
        serializer = AssessmentSerializer(data=self._base_data(load_value=60.0))
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertFalse(serializer.validated_data["is_compliant"])

    def test_load_exactly_at_limit_is_compliant(self):
        serializer = AssessmentSerializer(data=self._base_data(load_value=50.0))
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertTrue(serializer.validated_data["is_compliant"])

    def test_capacity_fields_auto_populated(self):
        serializer = AssessmentSerializer(data=self._base_data(load_value=30.0))
        self.assertTrue(serializer.is_valid(), serializer.errors)
        data = serializer.validated_data
        self.assertEqual(data["capacity_name"], LoadCapacity.CapacityName.MAX_POINT_LOAD)
        self.assertEqual(data["capacity_metric"], LoadCapacity.Metric.KN)
        self.assertEqual(data["capacity_limit"], 50.0)

    def test_asset_not_in_location_invalid(self):
        other_loc = Location.objects.create(name="Site B")
        other_asset = Asset.objects.create(location=other_loc, name="Drawing-X")
        serializer = AssessmentSerializer(data={
            "location": self.location.id,
            "asset": other_asset.id,
            "equipment_type": "crane_with_outriggers",
            "load_value": 30.0,
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("asset", serializer.errors)

    def test_unknown_equipment_type_invalid(self):
        serializer = AssessmentSerializer(data=self._base_data(equipment_type="jet_ski"))
        self.assertFalse(serializer.is_valid())

    def test_missing_capacity_for_equipment_type(self):
        """Asset has only max_point_load — using mobile_crane (needs max_axle_load) should fail."""
        serializer = AssessmentSerializer(data=self._base_data(equipment_type="mobile_crane"))
        self.assertFalse(serializer.is_valid())
        self.assertIn("asset", serializer.errors)

    def test_metric_taken_from_db_not_hardcoded(self):
        """Ensure metric in response reflects stored LoadCapacity, not a hardcoded value."""
        asset2 = Asset.objects.create(location=self.location, name="Drawing-002")
        LoadCapacity.objects.create(
            asset=asset2,
            name=LoadCapacity.CapacityName.MAX_AXLE_LOAD,
            metric=LoadCapacity.Metric.T,
            max_load=20.0,
        )
        serializer = AssessmentSerializer(data={
            "location": self.location.id,
            "asset": asset2.id,
            "equipment_type": "mobile_crane",
            "load_value": 10.0,
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["capacity_metric"], "t")


# API Tests — Assessments

class AssessmentAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="engineer", password="pass", email="eng@test.com"
        )
        self.admin = User.objects.create_user(
            username="admin", password="pass", is_staff=True
        )
        self.location = Location.objects.create(name="Site A")
        self.asset = Asset.objects.create(location=self.location, name="Drawing-001")
        self.capacity = LoadCapacity.objects.create(
            asset=self.asset,
            name=LoadCapacity.CapacityName.MAX_POINT_LOAD,
            metric=LoadCapacity.Metric.KN,
            max_load=50.0,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _create_payload(self, load_value=30.0, equipment_type="crane_with_outriggers"):
        return {
            "location": self.location.id,
            "asset": self.asset.id,
            "equipment_type": equipment_type,
            "load_value": load_value,
        }

    def test_unauthenticated_cannot_access(self):
        response = self.client.get("/api/assessments/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_assessments(self):
        self._auth(self.user)
        response = self.client.get("/api/assessments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_compliant_assessment(self):
        self._auth(self.user)
        with patch("assessments.views.send_compliance_failure_alert") as mock_email:
            response = self.client.post("/api/assessments/", self._create_payload(load_value=30.0))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_compliant"])
        self.assertEqual(response.data["result"], "PASS")
        mock_email.assert_not_called()

    def test_create_non_compliant_assessment(self):
        self._auth(self.user)
        with patch("assessments.views.send_compliance_failure_alert") as mock_email:
            response = self.client.post("/api/assessments/", self._create_payload(load_value=75.0))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["is_compliant"])
        self.assertEqual(response.data["result"], "FAIL")
        mock_email.assert_called_once()

    def test_assessment_saves_created_by(self):
        self._auth(self.user)
        with patch("assessments.views.send_compliance_failure_alert"):
            response = self.client.post("/api/assessments/", self._create_payload())
        self.assertEqual(response.data["created_by"], self.user.username)

    def test_assessment_id_returned(self):
        self._auth(self.user)
        with patch("assessments.views.send_compliance_failure_alert"):
            response = self.client.post("/api/assessments/", self._create_payload())
        self.assertIn("assessment_id", response.data)
        self.assertIsNotNone(response.data["assessment_id"])

    def test_invalid_equipment_type_returns_400(self):
        self._auth(self.user)
        response = self.client.post("/api/assessments/", self._create_payload(equipment_type="spaceship"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_asset_location_mismatch_returns_400(self):
        self._auth(self.user)
        other_loc = Location.objects.create(name="Site B")
        other_asset = Asset.objects.create(location=other_loc, name="Drawing-X")
        response = self.client.post("/api/assessments/", {
            "location": self.location.id,
            "asset": other_asset.id,
            "equipment_type": "crane_with_outriggers",
            "load_value": 30.0,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_failure_does_not_break_response(self):
        """Email errors must not propagate to the API caller."""
        self._auth(self.user)
        with patch(
            "assessments.views.send_compliance_failure_alert",
            side_effect=Exception("SMTP error")
        ):
            response = self.client.post(
                "/api/assessments/", self._create_payload(load_value=75.0)
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["is_compliant"])


# API Tests — Equipment Options

class EquipmentOptionsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="viewer", password="pass")

    def test_unauthenticated_cannot_list(self):
        response = self.client.get("/api/equipment-options/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_can_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/equipment-options/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_returns_all_equipment_types(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/equipment-options/")
        values = [item["value"] for item in response.data]
        for key in EQUIPMENT_CAPACITY_MAP:
            self.assertIn(key, values)

    def test_response_shape(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/equipment-options/")
        for item in response.data:
            self.assertIn("value", item)
            self.assertIn("label", item)
            self.assertIn("load_label", item)
            self.assertIn("capacity_name", item)


# API Tests — Assessment History

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
