from django.core.management.base import BaseCommand
from assets.models import Location, Asset, LoadCapacity, LoadCapacityAlias
from assessments.models import EquipmentCapacityMapping

ASSETS = [
    {
        "location": "Port of Bunbury",
        "name": "Berth 5",
        "load_capacities": [
            {"name": "max_point_load",              "max_load": 1000,  "metric": "kN"},
            {"name": "max_axle_load",               "max_load": 87.4,  "metric": "t"},
            {"name": "max_uniform_distributor_load","max_load": 40,    "metric": "kPa"},
            {"name": "max_displacement_size",       "max_load": 68100, "metric": "t"},
        ],
    },
    {
        "location": "Port of Bunbury",
        "name": "Berth 8",
        "load_capacities": [
            {"name": "max_point_load",              "max_load": 2642,  "metric": "kN"},
            {"name": "max_axle_load",               "max_load": 87.4,  "metric": "t"},
            {"name": "max_uniform_distributor_load","max_load": 40,    "metric": "kPa"},
            {"name": "max_displacement_size",       "max_load": 72000, "metric": "t"},
        ],
    },
    {
        "location": "University of Western Australia",
        "name": "Engineering Courtyard",
        "load_capacities": [
            {"name": "max_axle_load",               "max_load": 20.0,  "metric": "t"},
            {"name": "max_uniform_distributor_load","max_load": 15,    "metric": "kPa"},
        ],
    },
    {
        "location": "University of Western Australia",
        "name": "Main Campus Loading Bay",
        "load_capacities": [
            {"name": "max_point_load",              "max_load": 750,   "metric": "kN"},
            {"name": "max_axle_load",               "max_load": 35.0,  "metric": "t"},
        ],
    },
]

EQUIPMENT_MAPPINGS = [
    ("crane_with_outriggers",  "Crane with outriggers",       "max_point_load",               "Max Outrigger Load"),
    ("mobile_crane",           "Mobile crane",                "max_axle_load",                "Max Axle Load"),
    ("heavy_vehicle",          "Heavy vehicle",               "max_axle_load",                "Max Axle Load"),
    ("elevated_work_platform", "Elevated Work Platform",      "max_point_load",               "Max Wheel Load"),
    ("storage_load",           "Storage Load",                "max_uniform_distributor_load", "Uniform Distributor Load"),
    ("vessel",                 "Vessel",                      "max_displacement_size",        "Displacement"),
]


class Command(BaseCommand):
    help = "Seed sample assets, load capacities, and equipment mappings"

    def handle(self, *args, **kwargs):
        self._seed_assets()
        self._seed_equipment_mappings()
        self.stdout.write(self.style.SUCCESS("Sample data seeded successfully."))

    def _seed_assets(self):
        for entry in ASSETS:
            location, _ = Location.objects.get_or_create(name=entry["location"])
            asset, created = Asset.objects.get_or_create(location=location, name=entry["name"])
            if created:
                self.stdout.write(f"  Created asset: {asset}")
            for lc in entry["load_capacities"]:
                LoadCapacity.objects.get_or_create(
                    asset=asset,
                    name=lc["name"],
                    defaults={"max_load": lc["max_load"], "metric": lc["metric"]},
                )

    def _seed_equipment_mappings(self):
        for equipment_type, label, capacity_name, alias_text in EQUIPMENT_MAPPINGS:
            alias, _ = LoadCapacityAlias.objects.get_or_create(
                alias=alias_text,
                defaults={"capacity_name": capacity_name},
            )
            EquipmentCapacityMapping.objects.get_or_create(
                equipment_type=equipment_type,
                defaults={"equipment_label": label, "capacity_alias": alias},
            )
