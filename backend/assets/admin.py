from django.contrib import admin
from .models import Asset, Location, LoadCapacity

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'location']
    list_filter = ['location']

@admin.register(LoadCapacity)
class LoadCapacityAdmin(admin.ModelAdmin):
    list_display = ['asset', 'name', 'max_load', 'metric']
    list_filter = ['name', 'metric']
