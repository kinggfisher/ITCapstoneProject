from django.db import migrations

# (equipment_type, capacity_name, alias)
INITIAL_DATA = [
    ('crane_with_outriggers',  'max_point_load',               'Max Outrigger Load'),
    ('mobile_crane',           'max_axle_load',                'Max Axle Load'),
    ('heavy_vehicle',          'max_axle_load',                'Max Axle Load'),
    ('elevated_work_platform', 'max_point_load',               'Max Wheel Load'),
    ('storage_load',           'max_uniform_distributor_load', 'Uniform Distributor Load'),
    ('vessel',                 'max_displacement_size',        'Displacement'),
]


def seed(apps, schema_editor):
    LoadCapacityAlias = apps.get_model('assets', 'LoadCapacityAlias')
    EquipmentCapacityMapping = apps.get_model('assessments', 'EquipmentCapacityMapping')

    alias_cache = {}
    for equipment_type, capacity_name, alias_text in INITIAL_DATA:
        if alias_text not in alias_cache:
            obj, _ = LoadCapacityAlias.objects.get_or_create(
                alias=alias_text,
                defaults={'capacity_name': capacity_name},
            )
            alias_cache[alias_text] = obj
        EquipmentCapacityMapping.objects.create(
            equipment_type=equipment_type,
            capacity_alias=alias_cache[alias_text],
        )


def unseed(apps, schema_editor):
    EquipmentCapacityMapping = apps.get_model('assessments', 'EquipmentCapacityMapping')
    LoadCapacityAlias = apps.get_model('assets', 'LoadCapacityAlias')
    EquipmentCapacityMapping.objects.all().delete()
    LoadCapacityAlias.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0003_equipmentcapacitymapping'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
