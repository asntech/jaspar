# -*- coding: utf-8 -*-
## Author: Aziz Khan
## License: GPL v3
## Copyright © 2017 Aziz Khan <azez.khan__AT__gmail.com>

# Make sure the following:
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desidered behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from __future__ import unicode_literals

from django.db import models

from django.contrib.auth.models import User



#Model for MATRIX table in the database
class Matrix(models.Model):
    collection_choices = (
        ('CORE', 'CORE'),
        ('CNE', 'CNE'),
        ('PHYLOFACTS', 'PHYLOFACTS'),
        ('SPLICE', 'SPILCE'),
        ('POLII', 'POLII'),
        ('FAM','FAM'),
        ('PBM','PBM'),
        ('PBM_HOMEO','PBM_HOMEO'),
        ('PBM_HLH','PBM_HLH')
    )
    id = models.CharField(db_column='ID', primary_key=True, max_length=16)  
    collection = models.CharField(db_column='COLLECTION', max_length=16, blank=True, choices=collection_choices) 
    base_id = models.CharField(db_column='BASE_ID', max_length=16)  
    version = models.CharField(db_column='VERSION', max_length=16)  
    name = models.CharField(db_column='NAME', max_length=255)  

    class Meta:
        managed = False
        db_table = 'MATRIX'

    def __str__(self):
        return self.name+'_'+self.base_id+'_'+str(self.version)

#Model for MATRIX_ANNOTATION table in the database
class MatrixAnnotation(models.Model):

    tag_choices = (
        ('class','Class'),
        ('comment','Comment'),
        ('family','Family'),
        ('gc_content','GC Content'),
        ('medline','Medline'),
        ('tax_group','TAX Group'),
        ('tfbs_shape_id','TFBS Shape ID'),
        ('type','Type'),
        ('pazar_tf_id','PAZAR TF ID'),
        ('tfe_id','TFE ID'),
        ('alias','Alias'),
        ('description','Description'),
        ('symbol','Symbol'),
        ('centrality_logp','Centrality Logp'),
        ('source','Source'),
        ('consensus','Consensus'),
        ('jaspar','JASPAR'),
        ('mcs','MCS'),
        ('transfac','TRANSFAC'),
        ('end_relative_to_tss','End relative to TSS'),
        ('start_relative_to_tss','Start relative to TSS'),
        ('included_models','Included Models')
    )

    matrix_id = models.ForeignKey(Matrix, db_column='ID')  
    tag = models.CharField(db_column='TAG', max_length=150, choices=tag_choices)  
    val = models.CharField(db_column='VAL', max_length=255, blank=True, null=True)  

    class Meta:
        managed = False
        db_table = 'MATRIX_ANNOTATION'
        unique_together = (('matrix_id', 'tag',),)

    def __str__(self):
        return self.model._meta.unique_together

#Model for MATRIX_DATA table in the database
class MatrixData(models.Model):
    
    matrix_id = models.ForeignKey(Matrix, db_column='ID')  
    row = models.CharField(max_length=1)
    col = models.TextField()  
    val = models.TextField(blank=True, null=True) 
    
    class Meta:
        managed = False
        db_table = 'MATRIX_DATA'
        unique_together = (('matrix_id', 'row', 'col',),)

    def __str__(self):
        return 'Matrix Data: ' + str(self.matrix_id)


#Model for MATRIX_PROTEIN table in the database
class MatrixProtein(models.Model):
    matrix_id = models.ForeignKey(Matrix, db_column='ID')  
    acc = models.CharField(db_column='ACC', max_length=255, blank=True, null=True) 

    class Meta:
        managed = False
        db_table = 'MATRIX_PROTEIN'


#Model for TAX table in the database
class Tax(models.Model):
    tax_id = models.CharField(db_column='TAX_ID', primary_key=True, max_length=16)  
    species = models.CharField(db_column='SPECIES', max_length=250, blank=True, null=True)  

    class Meta:
        managed = False
        db_table = 'TAX'

#Model for TAX_EXT table in the database
class TaxExt(models.Model):
    tax_id = models.ForeignKey(Tax, unique=True, db_column='TAX_ID', primary_key=True, max_length=16)  
    name = models.CharField(db_column='NAME', max_length=255, blank=True, null=True)  

    class Meta:
        managed = False
        db_table = 'TAX_EXT'

#Model for MATRIX_SPECIES table in the database
class MatrixSpecies(models.Model):
    matrix_id = models.ForeignKey(Matrix, db_column='ID')  
    tax_id = models.ForeignKey(Tax, db_column='TAX_ID', max_length=255, blank=True, null=True)  

    class Meta:
        managed = False
        db_table = 'MATRIX_SPECIES'

#Model for TFFM table in the database
class Tffm(models.Model):
    id = models.CharField(db_column='ID', primary_key=True, max_length=8)  
    base_id = models.CharField(db_column='BASE_ID', max_length=16)  
    version = models.CharField(db_column='VERSION', max_length=2) 
    matrix_base_id = models.CharField(db_column='MATRIX_BASE_ID', max_length=16)  
    matrix_version = models.CharField(db_column='MATRIX_VERSION', max_length=2)  
    name = models.CharField(db_column='NAME', max_length=255) 
    log_p_1st_order = models.CharField(db_column='LOG_P_1ST_ORDER', max_length=16, blank=True, null=True)  
    log_p_detailed = models.CharField(db_column='LOG_P_DETAILED', max_length=16, blank=True, null=True) 
    experiment_name = models.TextField(db_column='EXPERIMENT_NAME', max_length=255, blank=True, null=True) 

    class Meta:
        managed = False
        db_table = 'TFFM'

#Model for Post table in the database
class Post(models.Model):
    category_choices = (
        ('Update', 'Update'),
        ('Bug fix', 'Bug fix'),
        ('Announcement', 'Announcement'),
        ('Other', 'Other'),    
    )
    title = models.CharField(max_length=100)  
    content = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=150, choices=category_choices)
    author = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)



