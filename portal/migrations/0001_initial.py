# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-21 22:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Matrix',
            fields=[
                ('id', models.CharField(db_column='ID', max_length=16, primary_key=True, serialize=False)),
                ('collection', models.CharField(blank=True, choices=[('CORE', 'CORE'), ('CNE', 'CNE'), ('PHYLOFACTS', 'PHYLOFACTS'), ('SPLICE', 'SPILCE'), ('POLII', 'POLII'), ('FAM', 'FAM'), ('PBM', 'PBM'), ('PBM_HOMEO', 'PBM_HOMEO'), ('PBM_HLH', 'PBM_HLH')], db_column='COLLECTION', max_length=16)),
                ('base_id', models.CharField(db_column='BASE_ID', max_length=16)),
                ('version', models.CharField(db_column='VERSION', max_length=16)),
                ('name', models.CharField(db_column='NAME', max_length=255)),
            ],
            options={
                'db_table': 'MATRIX',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MatrixData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('row', models.CharField(max_length=1)),
                ('col', models.TextField()),
                ('val', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'MATRIX_DATA',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Tax',
            fields=[
                ('tax_id', models.TextField(db_column='TAX_ID', primary_key=True, serialize=False)),
                ('species', models.CharField(blank=True, db_column='SPECIES', max_length=250, null=True)),
            ],
            options={
                'db_table': 'TAX',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TaxExt',
            fields=[
                ('tax_id', models.TextField(db_column='TAX_ID', primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, db_column='NAME', max_length=255, null=True)),
            ],
            options={
                'db_table': 'TAX_EXT',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Tffm',
            fields=[
                ('id', models.TextField(db_column='ID', primary_key=True, serialize=False)),
                ('base_id', models.CharField(db_column='BASE_ID', max_length=16)),
                ('version', models.TextField(db_column='VERSION')),
                ('matrix_base_id', models.CharField(db_column='MATRIX_BASE_ID', max_length=16)),
                ('matrix_version', models.TextField(db_column='MATRIX_VERSION')),
                ('name', models.CharField(db_column='NAME', max_length=255)),
                ('log_p_1st_order', models.TextField(blank=True, db_column='LOG_P_1ST_ORDER', null=True)),
                ('log_p_detailed', models.TextField(blank=True, db_column='LOG_P_DETAILED', null=True)),
                ('experiment_name', models.CharField(blank=True, db_column='EXPERIMENT_NAME', max_length=255, null=True)),
            ],
            options={
                'db_table': 'TFFM',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MatrixAnnotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(choices=[('class', 'class'), ('comment', 'comment'), ('family', 'family'), ('gc_content', 'gc_content'), ('medline', 'medline'), ('tax_group', 'tax_group'), ('tfbs_shape_id', 'tfbs_shape_id'), ('type', 'type'), ('pazar_tf_id', 'pazar_tf_id'), ('tfe_id', 'tfe_id'), ('alias', 'alias'), ('description', 'description'), ('symbol', 'symbol'), ('centrality_logp', 'centrality_logp'), ('source', 'source'), ('consensus', 'consensus'), ('jaspar', 'jaspar'), ('mcs', 'mcs'), ('transfac', 'transfac'), ('end_relative_to_tss', 'end_relative_to_tss'), ('start_relative_to_tss', 'start_relative_to_tss'), ('included_models', 'included_models')], db_column='TAG', max_length=150)),
                ('val', models.CharField(blank=True, db_column='VAL', max_length=255, null=True)),
                ('matrix_id', models.ForeignKey(db_column='ID', on_delete=django.db.models.deletion.CASCADE, to='portal.Matrix')),
            ],
            options={
                'db_table': 'MATRIX_ANNOTATION',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MatrixProtein',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acc', models.CharField(blank=True, db_column='ACC', max_length=255, null=True)),
                ('matrix_id', models.ForeignKey(db_column='ID', on_delete=django.db.models.deletion.CASCADE, to='portal.Matrix')),
            ],
            options={
                'db_table': 'MATRIX_PROTEIN',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MatrixSpecies',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('matrix_id', models.ForeignKey(db_column='ID', on_delete=django.db.models.deletion.CASCADE, to='portal.Matrix')),
                ('tax_id', models.ForeignKey(blank=True, db_column='TAX_ID', max_length=255, null=True, on_delete=django.db.models.deletion.CASCADE, to='portal.Tax')),
            ],
            options={
                'db_table': 'MATRIX_SPECIES',
                'managed': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='matrixannotation',
            unique_together=set([('matrix_id', 'tag')]),
        ),
    ]
