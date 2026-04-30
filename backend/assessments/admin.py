from django.contrib import admin
from .models import Assessment, EquipmentCapacityMapping

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['asset', 'location', 'equipment_type', 'load_value', 'is_compliant', 'created_at']
    list_filter = ['is_compliant', 'equipment_type']

@admin.register(EquipmentCapacityMapping)
class EquipmentCapacityMappingAdmin(admin.ModelAdmin):
    list_display = ['equipment_type', 'capacity_name', 'load_label']