from django.db import models
from assets.models import Asset

class Assessment(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    load_kg = models.FloatField()
    equipment_type = models.CharField(max_length=255, blank=True, null=True)
    is_compliant = models.BooleanField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.name} - {'PASS' if self.is_compliant else 'FAIL'}"