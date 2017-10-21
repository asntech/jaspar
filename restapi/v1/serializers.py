# -*- coding: utf-8 -*-
## Author: Aziz Khan
## License: GPL v3
## Copyright © 2017 Aziz Khan <azez.khan__AT__gmail.com>

from rest_framework import serializers
from portal.models import Matrix, MatrixAnnotation

from django.http import HttpRequest


class MatrixAnnotationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MatrixAnnotation
        fields = ('id', 'tag','val')

class MatrixSerializer(serializers.HyperlinkedModelSerializer):

	#matrixannotations = MatrixAnnotationSerializer(many=True, read_only=True)
		
	matrix_id = serializers.SerializerMethodField()
	url = serializers.SerializerMethodField()
	sequence_logo = serializers.SerializerMethodField()

	#url = serializers.HyperlinkedIdentityField(view_name='matrix-detail', lookup_field='id')
  	
	class Meta:
		model = Matrix
		#fields = ('__all__')
		fields = ('matrix_id', 'name','collection', 'base_id', 'version','sequence_logo','url')

	def get_matrix_id(self, obj):

		return obj.base_id+'.'+str(obj.version)

	def get_sequence_logo(self, obj):

		host_name = self.context['request'].build_absolute_uri(location='/')
	
		return  str(host_name)+'static/logos/svg/'+obj.base_id+'.'+str(obj.version)+'.svg'

	def get_url(self, obj):

		host_name = self.context['request'].build_absolute_uri(location='/')
		
		return  str(host_name)+'api/v1/matrix/'+obj.base_id+'.'+str(obj.version)+'/'

