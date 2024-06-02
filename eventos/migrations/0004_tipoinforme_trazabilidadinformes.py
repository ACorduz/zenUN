# Generated by Django 5.0.3 on 2024-06-02 15:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0003_historicalevento_historicalevento_asistentes_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='tipoInforme',
            fields=[
                ('idTipoInforme', models.AutoField(primary_key=True, serialize=False)),
                ('tipo_informe', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='trazabilidadInformes',
            fields=[
                ('idInforme', models.AutoField(primary_key=True, serialize=False)),
                ('fechaGeneracionInforme', models.DateTimeField()),
                ('tipoInforme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='eventos.tipoinforme')),
            ],
        ),
    ]
