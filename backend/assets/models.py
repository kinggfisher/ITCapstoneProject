
from django.db import models


class Location(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Asset(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="assets")
    name = models.CharField(max_length=255)
    drawing_file = models.FileField(upload_to='drawings/', blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["location", "name"], name="unique_asset_per_location")
        ]

    def __str__(self):
        return f"{self.location.name} - {self.name}"


class LoadCapacity(models.Model):
    class CapacityName(models.TextChoices):
        MAX_POINT_LOAD = "max_point_load", "Max Point Load"
        MAX_AXLE_LOAD = "max_axle_load", "Max Axle Load"
        # fixed typo in "distributor" and added "uniform" to match the original name
        MAX_UNIFORM_DISTRIBUTOR_LOAD = "max_uniform_distributor_load", "Max Uniform Distributor Load"   
        MAX_DISPLACEMENT_SIZE = "max_displacement_size", "Max Displacement Size"

    class Metric(models.TextChoices):
        KN = "kN", "kilonewtons (kN)"
        T = "t", "tonnes (t)"
        KPA = "kPa", "kilopascal (kPa)"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="load_capacities")
    name = models.CharField(max_length=64, choices=CapacityName.choices)
    metric = models.CharField(max_length=16, choices=Metric.choices)
    max_load = models.FloatField()
    details = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["asset", "name"], name="unique_capacity_name_per_asset")
        ]

    def __str__(self):
        return f"{self.asset} - {self.get_name_display()}: {self.max_load} {self.metric}"
