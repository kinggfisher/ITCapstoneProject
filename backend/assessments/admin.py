from django.contrib import admin
from .models import Assessment


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("asset", "is_compliant", "equipment_type", "created_at")
    list_filter = ("is_compliant", "equipment_type")
    search_fields = ("asset__name",)
