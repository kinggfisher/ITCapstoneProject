from django.contrib import admin
from .models import Asset, Location, LoadCapacity, LoadCapacityAlias

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

@admin.register(LoadCapacityAlias)
class LoadCapacityAliasAdmin(admin.ModelAdmin):
    list_display = ['alias', 'capacity_name']
    list_filter = ['capacity_name']