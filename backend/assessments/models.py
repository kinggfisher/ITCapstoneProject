
from django.db import models
from django.contrib.auth.models import User
from assets.models import Asset, Location, LoadCapacity, LoadCapacityAlias


class Assessment(models.Model):
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="assessments")
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="assessments")
    equipment_type = models.CharField(max_length=64)
    equipment_model = models.TextField(blank=True, null=True)

    load_value = models.FloatField()

    capacity_name = models.CharField(max_length=64, choices=LoadCapacity.CapacityName.choices)
    capacity_metric = models.CharField(max_length=16, choices=LoadCapacity.Metric.choices)
    capacity_limit = models.FloatField()

    is_compliant = models.BooleanField()
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="assessments", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.name} - {'PASS' if self.is_compliant else 'FAIL'}"


class EquipmentCapacityMapping(models.Model):
    equipment_type = models.CharField(max_length=64, unique=True)
    equipment_label = models.CharField(max_length=100)
    capacity_alias = models.ForeignKey(
        LoadCapacityAlias, on_delete=models.PROTECT, related_name="equipment_mappings"
    )

    def __str__(self):
        return f"{self.equipment_label} → {self.capacity_alias.alias}"
