from django.contrib import admin
from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "material_grade")
    search_fields = ("name", "location__name")

    @admin.display(description="Material grade")
    def material_grade(self, obj):
        if hasattr(obj, "material") and obj.material:
            return getattr(obj.material, "grade", None)
        if hasattr(obj, "material_grade") and obj.material_grade:
            return obj.material_grade
        return None
