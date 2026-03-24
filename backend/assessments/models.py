
from django.db import models
from assets.models import Asset, Location, LoadCapacity


class Assessment(models.Model):
    class EquipmentType(models.TextChoices):
        CRANE_WITH_OUTRIGGERS = "crane_with_outriggers", "Crane with outriggers"
        MOBILE_CRANE = "mobile_crane", "Mobile crane"
        HEAVY_VEHICLE = "heavy_vehicle", "Heavy vehicle"
        ELEVATED_WORK_PLATFORM = "elevated_work_platform", "Elevated Work Platform"
        STORAGE_LOAD = "storage_load", "Storage Load"
        VESSEL = "vessel", "Vessel"

 
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="assessments")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="assessments")
    equipment_type = models.CharField(max_length=64, choices=EquipmentType.choices)
    equipment_model = models.TextField(blank=True, null=True)

    # The dynamic load parameter value (user enters only the number)
    load_value = models.FloatField()

    # Record what we compared against (audit trail)
    capacity_name = models.CharField(max_length=64, choices=LoadCapacity.CapacityName.choices)
    capacity_metric = models.CharField(max_length=16, choices=LoadCapacity.Metric.choices)
    capacity_limit = models.FloatField()

    is_compliant = models.BooleanField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.name} - {'PASS' if self.is_compliant else 'FAIL'}"
