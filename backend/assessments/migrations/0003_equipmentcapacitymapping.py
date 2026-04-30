from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0002_assessment_created_by_alter_assessment_capacity_name'),
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
                ('capacity_name', models.CharField(
                    choices=[
                        ('max_point_load', 'Max Point Load'),
                        ('max_axle_load', 'Max Axle Load'),
                        ('max_uniform_distributor_load', 'Max Uniform Distributor Load'),
                        ('max_displacement_size', 'Max Displacement Size'),
                    ],
                    max_length=64,
                )),
                ('load_label', models.CharField(max_length=100)),
            ],
        ),
    ]
