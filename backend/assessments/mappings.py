def get_equipment_capacity_map():
    from .models import EquipmentCapacityMapping
    return {
        m.equipment_type: (m.capacity_name, m.load_label)
        for m in EquipmentCapacityMapping.objects.all()
    }