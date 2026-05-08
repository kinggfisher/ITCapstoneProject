from rest_framework import serializers
from .models import Assessment
from .mappings import get_equipment_capacity_map
from assets.models import LoadCapacity


class AssessmentSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Assessment
        fields = [
            'id', 'location', 'asset', 'equipment_type', 'equipment_model',
            'load_value', 'capacity_name', 'capacity_metric',
            'capacity_limit', 'is_compliant', 'notes', 'created_by', 'created_by_username', 'created_at',
        ]
        read_only_fields = [
            'capacity_name', 'capacity_metric',
            'capacity_limit', 'is_compliant', 'created_by', 'created_by_username', 'created_at',
        ]

    def validate(self, data):
        asset = data.get('asset')
        location = data.get('location')
        equipment_type = data.get('equipment_type')
        load_value = data.get('load_value')

        # Validate asset belongs to selected location
        if asset.location != location:
            raise serializers.ValidationError({
                "asset": f"Asset '{asset.name}' does not belong to location '{location.name}'."
            })

        # Look up capacity mapping
        mapping = get_equipment_capacity_map().get(equipment_type)
        if not mapping:
            raise serializers.ValidationError({
                "equipment_type": f"No mapping found for '{equipment_type}'."
            })

        # unpack only two values — metric removed from mapping
        capacity_name, load_label = mapping

        # Query matching LoadCapacity from database
        try:
            load_capacity = LoadCapacity.objects.get(asset=asset, name=capacity_name)
        except LoadCapacity.DoesNotExist:
            raise serializers.ValidationError({
                "asset": f"Asset '{asset.name}' has no '{capacity_name}' capacity defined."
            })

        # Auto-populate system fields
        data['capacity_name'] = capacity_name
        # This ensures metric is always consistent with what's stored in LoadCapacity
        data['capacity_metric'] = load_capacity.metric
        data['capacity_limit'] = load_capacity.max_load
        data['is_compliant'] = load_value <= load_capacity.max_load

        return data

class AssessmentHistorySerializer(serializers.ModelSerializer):
    asset_name     = serializers.CharField(source='asset.name', read_only=True)
    location_name  = serializers.CharField(source='asset.location.name', read_only=True)
    load_label     = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            'id',
            'asset_name',
            'location_name',
            'load_label',
            'load_value',
            'capacity_metric',
            'capacity_limit',
            'is_compliant',
            'created_at',
        ]

    def get_load_label(self, obj):
        mapping = get_equipment_capacity_map().get(obj.equipment_type)
        return mapping[1] if mapping else obj.capacity_name