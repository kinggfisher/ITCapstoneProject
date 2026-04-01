from rest_framework import serializers
from .models import Asset, Location, LoadCapacity

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class LoadCapacitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadCapacity
        fields = '__all__'

class AssetSerializer(serializers.ModelSerializer):
    load_capacities = LoadCapacitySerializer(many=True, read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = Asset
        fields = ['id', 'name', 'location', 'location_name', 'load_capacities']
