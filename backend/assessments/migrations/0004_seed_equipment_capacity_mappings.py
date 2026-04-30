from django.db import migrations

INITIAL_MAPPINGS = [
    ('crane_with_outriggers',  'max_point_load',               'Max Outrigger Load'),
    ('mobile_crane',           'max_axle_load',                'Max Axle Load'),
    ('heavy_vehicle',          'max_axle_load',                'Max Axle Load'),
    ('elevated_work_platform', 'max_point_load',               'Max Wheel Load'),
    ('storage_load',           'max_uniform_distributor_load', 'Uniform Distributor Load'),
    ('vessel',                 'max_displacement_size',        'Displacement'),
]


def seed(apps, schema_editor):
    EquipmentCapacityMapping = apps.get_model('assessments', 'EquipmentCapacityMapping')
    for equipment_type, capacity_name, load_label in INITIAL_MAPPINGS:
        EquipmentCapacityMapping.objects.create(
            equipment_type=equipment_type,
            capacity_name=capacity_name,
            load_label=load_label,
        )


def unseed(apps, schema_editor):
    EquipmentCapacityMapping = apps.get_model('assessments', 'EquipmentCapacityMapping')
    EquipmentCapacityMapping.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0003_equipmentcapacitymapping'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
