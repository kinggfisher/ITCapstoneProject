from django.db import migrations, models

LABELS = {
    'crane_with_outriggers':  'Crane with outriggers',
    'mobile_crane':           'Mobile crane',
    'heavy_vehicle':          'Heavy vehicle',
    'elevated_work_platform': 'Elevated Work Platform',
    'storage_load':           'Storage Load',
    'vessel':                 'Vessel',
}


def populate_labels(apps, schema_editor):
    EquipmentCapacityMapping = apps.get_model('assessments', 'EquipmentCapacityMapping')
    for mapping in EquipmentCapacityMapping.objects.all():
        mapping.equipment_label = LABELS.get(mapping.equipment_type, mapping.equipment_type)
        mapping.save()


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0004_seed_equipment_capacity_mappings'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentcapacitymapping',
            name='equipment_label',
            field=models.CharField(max_length=100, default=''),
            preserve_default=False,
        ),
        migrations.RunPython(populate_labels, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='equipmentcapacitymapping',
            name='equipment_type',
            field=models.CharField(max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name='assessment',
            name='equipment_type',
            field=models.CharField(max_length=64),
        ),
    ]
