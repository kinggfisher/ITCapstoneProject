from rest_framework import serializers
from .models import Assessment
from .mappings import EQUIPMENT_CAPACITY_MAP
from assets.models import LoadCapacity


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = [
            'id', 'location', 'asset', 'equipment_type', 'equipment_model',
            'load_value', 'capacity_name', 'capacity_metric',
            'capacity_limit', 'is_compliant', 'notes', 'created_at',
        ]
        read_only_fields = [
            'capacity_name', 'capacity_metric',
            'capacity_limit', 'is_compliant', 'created_at',
        ]

    def validate(self, data):
        asset = data.get('asset')
        location = data.get('location')
        equipment_type = data.get('equipment_type')
        load_value = data.get('load_value')

        # check asset-location consistency
        if asset.location != location:
            raise serializers.ValidationError({
                "asset": f"Asset '{asset.name}' does not belong to location '{location.name}'."
            })

        # check equipment type mapping
        mapping = EQUIPMENT_CAPACITY_MAP.get(equipment_type)
        if not mapping:
            raise serializers.ValidationError({
                "equipment_type": f"No mapping found for '{equipment_type}'."
            })
        capacity_name, expected_metric, _ = mapping

        # check if asset has the required capacity defined
        try:
            load_capacity = LoadCapacity.objects.get(asset=asset, name=capacity_name)
        except LoadCapacity.DoesNotExist:
            raise serializers.ValidationError({
                "asset": f"Asset '{asset.name}' has no '{capacity_name}' capacity defined."
            })

        # automatically fill in capacity details and compliance result
        data['capacity_name'] = capacity_name
        data['capacity_metric'] = load_capacity.metric
        data['capacity_limit'] = load_capacity.max_load
        data['is_compliant'] = load_value <= load_capacity.max_load
        return data