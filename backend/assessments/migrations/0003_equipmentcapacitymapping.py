from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0002_assessment_created_by_alter_assessment_capacity_name'),
        ('assets', '0004_loadcapacityalias'),
    ]

    operations = [
        migrations.CreateModel(
            name='EquipmentCapacityMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('equipment_type', models.CharField(
                    choices=[
                        ('crane_with_outriggers', 'Crane with outriggers'),
                        ('mobile_crane', 'Mobile crane'),
                        ('heavy_vehicle', 'Heavy vehicle'),
                        ('elevated_work_platform', 'Elevated Work Platform'),
                        ('storage_load', 'Storage Load'),
                        ('vessel', 'Vessel'),
                    ],
                    max_length=64,
                    unique=True,
                )),
                ('capacity_alias', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='equipment_mappings',
                    to='assets.loadcapacityalias',
                )),
            ],
        ),
    ]
