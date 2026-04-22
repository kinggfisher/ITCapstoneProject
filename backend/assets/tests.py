from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from rest_framework.test import APIClient
from rest_framework import status

from .models import Location, Asset, LoadCapacity
from .extraction import extract_from_text


# Model Tests
class LocationModelTest(TestCase):
    def test_create_location(self):
        loc = Location.objects.create(name="Warehouse A")
        self.assertEqual(str(loc), "Warehouse A")

    def test_location_name_unique(self):
        Location.objects.create(name="Warehouse A")
        with self.assertRaises(IntegrityError):
            Location.objects.create(name="Warehouse A")

    def test_location_str(self):
        loc = Location.objects.create(name="Site B")
        self.assertEqual(str(loc), "Site B")


class AssetModelTest(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name="Site A")

    def test_create_asset(self):
        asset = Asset.objects.create(location=self.location, name="Drawing-001")
        self.assertEqual(str(asset), "Site A - Drawing-001")

    def test_unique_asset_per_location(self):
        Asset.objects.create(location=self.location, name="Drawing-001")
        with self.assertRaises(IntegrityError):
            Asset.objects.create(location=self.location, name="Drawing-001")

    def test_same_name_different_location(self):
        loc2 = Location.objects.create(name="Site B")
        Asset.objects.create(location=self.location, name="Drawing-001")
        # Should not raise
        asset2 = Asset.objects.create(location=loc2, name="Drawing-001")
        self.assertEqual(asset2.location, loc2)

    def test_asset_drawing_file_optional(self):
        asset = Asset.objects.create(location=self.location, name="Drawing-002")
        self.assertFalse(asset.drawing_file)  # blank / null


class LoadCapacityModelTest(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name="Site A")
        self.asset = Asset.objects.create(location=self.location, name="Drawing-001")

    def test_create_load_capacity(self):
        cap = LoadCapacity.objects.create(
            asset=self.asset,
            name=LoadCapacity.CapacityName.MAX_POINT_LOAD,
            metric=LoadCapacity.Metric.KN,
            max_load=50.0,
        )
        self.assertIn("Max Point Load", str(cap))
        self.assertIn("50.0", str(cap))
        self.assertIn("kN", str(cap))

    def test_unique_capacity_name_per_asset(self):
        LoadCapacity.objects.create(
            asset=self.asset,
            name=LoadCapacity.CapacityName.MAX_AXLE_LOAD,
            metric=LoadCapacity.Metric.T,
            max_load=20.0,
        )
        with self.assertRaises(IntegrityError):
            LoadCapacity.objects.create(
                asset=self.asset,
                name=LoadCapacity.CapacityName.MAX_AXLE_LOAD,
                metric=LoadCapacity.Metric.T,
                max_load=30.0,
            )

    def test_capacity_name_choices(self):
        valid_names = [c[0] for c in LoadCapacity.CapacityName.choices]
        self.assertIn("max_point_load", valid_names)
        self.assertIn("max_axle_load", valid_names)
        self.assertIn("max_uniform_distributor_load", valid_names)
        self.assertIn("max_displacement_size", valid_names)


# Extraction Tests

class ExtractionTest(TestCase):
    SAMPLE_TEXT = """
    Project: BuildingA
    Drawing: DA-001
    Max Point Load: 50 kN
    Max Axle Load: 100 t
    Max Uniform Distributed Load: 10 kPa
    Max Displacement Size: 200 kN
    """

    def test_extracts_project(self):
        result = extract_from_text(self.SAMPLE_TEXT)
        self.assertEqual(result["project"], "BuildingA")

    def test_extracts_drawing_number(self):
        result = extract_from_text(self.SAMPLE_TEXT)
        self.assertEqual(result["drawing_number"], "DA-001")

    def test_extracts_max_point_load(self):
        result = extract_from_text(self.SAMPLE_TEXT)
        caps = {c["name"]: c for c in result["capacities"]}
        self.assertIn("max_point_load", caps)
        self.assertEqual(caps["max_point_load"]["value"], 50.0)
        self.assertEqual(caps["max_point_load"]["metric"], "kN")

    def test_extracts_max_axle_load(self):
        result = extract_from_text(self.SAMPLE_TEXT)
        caps = {c["name"]: c for c in result["capacities"]}
        self.assertIn("max_axle_load", caps)
        self.assertEqual(caps["max_axle_load"]["value"], 100.0)
        self.assertEqual(caps["max_axle_load"]["metric"], "t")

    def test_extracts_uniform_distributed_load(self):
        result = extract_from_text(self.SAMPLE_TEXT)
        caps = {c["name"]: c for c in result["capacities"]}
        self.assertIn("max_uniform_distributor_load", caps)
        self.assertEqual(caps["max_uniform_distributor_load"]["value"], 10.0)
        self.assertEqual(caps["max_uniform_distributor_load"]["metric"], "kPa")

    def test_extracts_displacement_size(self):
        result = extract_from_text(self.SAMPLE_TEXT)
        caps = {c["name"]: c for c in result["capacities"]}
        self.assertIn("max_displacement_size", caps)
        self.assertEqual(caps["max_displacement_size"]["value"], 200.0)

    def test_raw_text_preserved(self):
        result = extract_from_text(self.SAMPLE_TEXT)
        self.assertEqual(result["raw_text"], self.SAMPLE_TEXT)

    def test_missing_project_returns_none(self):
        result = extract_from_text("Max Point Load: 50 kN")
        self.assertIsNone(result["project"])

    def test_missing_drawing_returns_none(self):
        result = extract_from_text("Project: BuildingA")
        self.assertIsNone(result["drawing_number"])

    def test_no_capacities_returns_empty_list(self):
        result = extract_from_text("Project: BuildingA\nDrawing: DA-001")
        self.assertEqual(result["capacities"], [])

    def test_case_insensitive_patterns(self):
        text = "MAXIMUM POINT LOAD: 75 kN"
        result = extract_from_text(text)
        caps = {c["name"]: c for c in result["capacities"]}
        self.assertIn("max_point_load", caps)
        self.assertEqual(caps["max_point_load"]["value"], 75.0)

    def test_decimal_values(self):
        text = "Max Point Load: 12.5 kN"
        result = extract_from_text(text)
        caps = {c["name"]: c for c in result["capacities"]}
        self.assertEqual(caps["max_point_load"]["value"], 12.5)


# API Tests — Assets

class LocationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin", password="pass", is_staff=True
        )
        self.user = User.objects.create_user(username="viewer", password="pass")
        self.location = Location.objects.create(name="Site A")

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_locations_authenticated(self):
        self._auth(self.user)
        response = self.client.get("/api/locations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_locations_unauthenticated(self):
        response = self.client.get("/api/locations/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_location(self):
        self._auth(self.admin)
        response = self.client.post("/api/locations/", {"name": "Site B"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Location.objects.filter(name="Site B").exists())

    def test_regular_user_cannot_create_location(self):
        self._auth(self.user)
        response = self.client.post("/api/locations/", {"name": "Site C"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_location(self):
        self._auth(self.admin)
        response = self.client.delete(f"/api/locations/{self.location.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_regular_user_cannot_delete_location(self):
        self._auth(self.user)
        response = self.client.delete(f"/api/locations/{self.location.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AssetAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin", password="pass", is_staff=True
        )
        self.user = User.objects.create_user(username="viewer", password="pass")
        self.location = Location.objects.create(name="Site A")
        self.asset = Asset.objects.create(location=self.location, name="Drawing-001")

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_assets(self):
        self._auth(self.user)
        response = self.client.get("/api/assets/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_assets_by_location(self):
        loc2 = Location.objects.create(name="Site B")
        Asset.objects.create(location=loc2, name="Drawing-X")
        self._auth(self.user)
        response = self.client.get(f"/api/assets/?location={self.location.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [a["name"] for a in response.data]
        self.assertIn("Drawing-001", names)
        self.assertNotIn("Drawing-X", names)

    def test_retrieve_asset_includes_load_capacities(self):
        LoadCapacity.objects.create(
            asset=self.asset,
            name=LoadCapacity.CapacityName.MAX_POINT_LOAD,
            metric=LoadCapacity.Metric.KN,
            max_load=50.0,
        )
        self._auth(self.user)
        response = self.client.get(f"/api/assets/{self.asset.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("load_capacities", response.data)
        self.assertEqual(len(response.data["load_capacities"]), 1)

    def test_retrieve_asset_includes_location_name(self):
        self._auth(self.user)
        response = self.client.get(f"/api/assets/{self.asset.id}/")
        self.assertEqual(response.data["location_name"], "Site A")

    def test_admin_can_create_asset(self):
        self._auth(self.admin)
        response = self.client.post("/api/assets/", {
            "location": self.location.id,
            "name": "Drawing-002",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_cannot_create_asset(self):
        self._auth(self.user)
        response = self.client.post("/api/assets/", {
            "location": self.location.id,
            "name": "Drawing-003",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class LoadCapacityAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin", password="pass", is_staff=True
        )
        self.user = User.objects.create_user(username="viewer", password="pass")
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

    def test_list_load_capacities(self):
        self._auth(self.user)
        response = self.client.get("/api/load-capacities/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_create_load_capacity(self):
        self._auth(self.admin)
        response = self.client.post("/api/load-capacities/", {
            "asset": self.asset.id,
            "name": "max_axle_load",
            "metric": "t",
            "max_load": 20.0,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_cannot_create_load_capacity(self):
        self._auth(self.user)
        response = self.client.post("/api/load-capacities/", {
            "asset": self.asset.id,
            "name": "max_axle_load",
            "metric": "t",
            "max_load": 20.0,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
