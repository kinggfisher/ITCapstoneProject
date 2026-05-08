from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0003_asset_drawing_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoadCapacityAlias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('capacity_name', models.CharField(
                    choices=[
                        ('max_point_load', 'Max Point Load'),
                        ('max_axle_load', 'Max Axle Load'),
                        ('max_uniform_distributor_load', 'Max Uniform Distributor Load'),
                        ('max_displacement_size', 'Max Displacement Size'),
                    ],
                    max_length=64,
                )),
                ('alias', models.CharField(max_length=100, unique=True)),
            ],
        ),
    ]
