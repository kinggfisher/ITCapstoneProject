def get_equipment_capacity_map():
    from .models import EquipmentCapacityMapping
    return {
        m.equipment_type: (m.capacity_alias.capacity_name, m.capacity_alias.alias)
        for m in EquipmentCapacityMapping.objects.select_related('capacity_alias').all()
    }