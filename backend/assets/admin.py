from django.contrib import admin
from .models import Asset

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'max_load_kg', 'material_grade']
    search_fields = ['name', 'location']