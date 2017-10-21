# -*- coding: utf-8 -*-
## Author: Aziz Khan
## License: GPL v3
## Copyright © 2017 Aziz Khan <azez.khan__AT__gmail.com>
import os
from jaspar.settings import BASE_DIR
from portal.models import Matrix, MatrixAnnotation, MatrixProtein, MatrixSpecies, Tffm
from portal.views import _get_matrix_data, _print_matrix_data, _map_annotations
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.reverse import reverse
from utils import utils
from django.db.models import Q, Max
from django.shortcuts import render

from rest_framework.throttling import UserRateThrottle

from utils.motif_inferrer.inferrer import motif_infer

from rest_framework import renderers

from rest_framework_jsonp.renderers import JSONPRenderer
from rest_framework_yaml.renderers import YAMLRenderer

from rest_framework.response import Response
from .serializers import MatrixSerializer, MatrixAnnotationSerializer
import itertools

from rest_framework.pagination import (
    PageNumberPagination,
    )
from rest_framework.generics import (
    ListAPIView, 
    RetrieveAPIView, 
    )
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
    BaseFilterBackend,
    DjangoFilterBackend,
    )
import coreapi

class MatrixResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


def _get_sequence_logo(request, base_id, version):
    host_name = request.build_absolute_uri(location='/')
    return  str(host_name)+'static/logos/svg/'+base_id+'.'+str(version)+'.svg'

def _get_matrix_url(request, base_id, version):

    host_name = request.build_absolute_uri(location='/')
    return  str(host_name)+'api/v1/matrix/'+base_id+'.'+str(version)

def _get_versions_url(request, base_id):

    host_name = request.build_absolute_uri(location='/')
    return  str(host_name)+'api/v1/matrix/'+base_id+'/versions'

def _get_sites_fasta_url(request, base_id, version):

    if os.path.isfile(BASE_DIR+'/download/sites/'+base_id+'.'+str(version)+'.sites'):
        host_name = request.build_absolute_uri(location='/')
        return  str(host_name)+'download/sites/'+base_id+'.'+str(version)+'.sites'
    else:
        return None

def _get_sites_bed_url(request, base_id, version):

    if os.path.isfile(BASE_DIR+'/download/bed_files/'+base_id+'.'+str(version)+'.bed'):
        host_name = request.build_absolute_uri(location='/')
        return  str(host_name)+'download/bed_files/'+base_id+'.'+str(version)+'.bed'
    else:
        return None

class JASPARRenderer(renderers.BaseRenderer):
    '''
    Render the PFM in JASPAR format.
    '''
    media_type = 'text/jaspar'
    format = 'jaspar'

    def render(self, data, media_type=None, renderer_context=None):

        pfm = data['pfm']
       
        if not pfm:
            jaspar = '# No PFM data available'
            return jaspar
        else:
            jaspar = _print_matrix_data(pfm, matrix_id=data['matrix_id'], matrix_name=data['name'], format='jaspar')
            return jaspar

class TRANSFACRenderer(renderers.BaseRenderer):
    '''
    Render the PFM in TRASNFAC format.
    '''
    media_type = 'text/transfac'
    format = 'transfac'

    def render(self, data, media_type=None, renderer_context=None):
        
        pfm = data['pfm']
       
        if not pfm:
            transfac = '# No PFM data available'
            return transfac
        else:
            transfac = _print_matrix_data(pfm, matrix_id=data['matrix_id'], matrix_name=data['name'], format='transfac')
            
            return transfac

class MEMERenderer(renderers.BaseRenderer):
    '''
    Render the PFM in MEME format.
    '''
    media_type = 'text/meme'
    format = 'meme'

    def render(self, data, media_type=None, renderer_context=None):
        
        pfm = data['pfm']
       
        if not pfm:
            meme = '# No PFM data available'
            return meme
        else:
            lines = []
            line = "MEME version 4\n\n"
            lines.append(line)
            line = "ALPHABET= {0}\n\n".format('ACGT')
            lines.append(line)
            line = "strands: {0} {1}\n\n".format('+','-')
            lines.append(line)
            line = "Background letter frequencies\n"
            lines.append(line)
            line = "A {0} C {1} G {2} T {3}\n\n".format('0.25','0.25','0.25','0.25')
            lines.append(line)
            text = "".join(lines)
            meme = _print_matrix_data(pfm, matrix_id=data['matrix_id'], matrix_name=data['name'], format='meme')
            
            return text+meme

class PFMRenderer(renderers.BaseRenderer):
    '''
    Render the PFM in Raw PFM format.
    '''
    media_type = 'text/pfm'
    format = 'pfm'

    def render(self, data, media_type=None, renderer_context=None):

        pfm = data['pfm']
       
        if not pfm:
            pfm = '# No PFM data available'
            return pfm
        else:
            pfm = _print_matrix_data(pfm, matrix_id=data['matrix_id'], matrix_name=data['name'], format='pfm')
            
            return pfm

class JASPARListRenderer(renderers.BaseRenderer):
    '''
    Render a list of PFMs in JASPAR format.
    '''
    media_type = 'text/jaspar'
    format = 'jaspar'

    def render(self, data, media_type=None, renderer_context=None):

        jaspar = []
        for d in data['results']:
            pfm = _print_matrix_data(_get_matrix_data(utils.get_internal_id(d['matrix_id'])), 
                matrix_id=d['matrix_id'], 
                matrix_name=d['name'], 
                format='jaspar'
                )
            jaspar.append(pfm)
        
        if not jaspar:
            jaspar = 'No PFM data available'
            return jaspar
        else:
            return jaspar

class TRANSFACListRenderer(renderers.BaseRenderer):
    '''
    Render a list of PFMs in TRANSFAC format.
    '''
    media_type = 'text/transfac'
    format = 'transfac'

    def render(self, data, media_type=None, renderer_context=None):

        transfac = []
        for d in data['results']:
            pfm = _print_matrix_data(_get_matrix_data(utils.get_internal_id(d['matrix_id'])), 
                matrix_id=d['matrix_id'], 
                matrix_name=d['name'], 
                format='transfac'
                )
            transfac.append(pfm)
        
        if not transfac:
            transfac = 'No PFM data available'
            return transfac
        else:
            return transfac

class MEMEListRenderer(renderers.BaseRenderer):
    '''
    Render a list of PFMs in MEME format.
    '''
    media_type = 'text/meme'
    format = 'meme'

    def render(self, data, media_type=None, renderer_context=None):

        meme = []
        lines = []
        line = "MEME version 4\n\n"
        lines.append(line)
        line = "ALPHABET= {0}\n\n".format('ACGT')
        lines.append(line)
        line = "strands: {0} {1}\n\n".format('+','-')
        lines.append(line)
        line = "Background letter frequencies\n"
        lines.append(line)
        line = "A {0} C {1} G {2} T {3}\n\n".format('0.25','0.25','0.25','0.25')
        lines.append(line)
        text = "".join(lines)

        for d in data['results']:
            pfm = _print_matrix_data(_get_matrix_data(utils.get_internal_id(d['matrix_id'])), 
                matrix_id=d['matrix_id'], 
                matrix_name=d['name'], 
                format='meme'
                )
            meme.append(pfm)
        
        if not meme:
            meme = 'No PFM data available'
            return meme
        else:
            return text+"".join(meme)

class PFMListRenderer(renderers.BaseRenderer):
    '''
    Render a list of PFMs in Raw PFM format.
    '''
    media_type = 'text/pfm'
    format = 'pfm'

    def render(self, data, media_type=None, renderer_context=None):

        raw = []
        for d in data['results']:
            pfm = _print_matrix_data(_get_matrix_data(utils.get_internal_id(d['matrix_id'])), 
                matrix_id=d['matrix_id'], 
                matrix_name=d['name'], 
                format='pfm'
                )
            raw.append(pfm)
        
        if not raw:
            raw = 'No PFM data available'
            return raw
        else:
            return raw

class MatrixDetailsViewSet(APIView):
    """
    API endpoint that returns the matrix profile detail information.
    """
    #queryset = Matrix.objects.all()

    renderer_classes = [renderers.JSONRenderer, JSONPRenderer, YAMLRenderer, JASPARRenderer, TRANSFACRenderer, PFMRenderer, MEMERenderer, renderers.BrowsableAPIRenderer]

    def get(self, request, matrix_id, format=None):
        """
        Gets profile detail information
        """

        setattr(request, 'view', 'api-browsable')

        #split base_id and version
        (base_id, version) = utils.split_id(matrix_id)
        
        data_dict = {}

        #get matrix object
        matrix = Matrix.objects.get(base_id=base_id, version=version)

        data_dict = {
                'matrix_id': matrix.base_id+'.'+str(matrix.version),
                'name': matrix.name,
                'base_id': matrix.base_id,
                'version': matrix.version,
                'collection': matrix.collection,
                'sequence_logo': _get_sequence_logo(request, base_id, version),
                'versions_url': _get_versions_url(request, base_id),
                'sites_fasta': _get_sites_fasta_url(request, base_id, version),
                'sites_bed': _get_sites_bed_url(request, base_id, version),
            }
        
        #Get more details about matrix
        annotations_queryset = MatrixAnnotation.objects.all().filter(id=matrix.id)

        data_dict.update(_map_annotations(annotations_queryset))
        
        #get uniprot ids infp
        proteins = MatrixProtein.objects.filter(matrix_id=matrix.id)
        
        protein_list = []
        for protein in proteins:
            protein_list.append(protein.acc)
                    
        data_dict.update({'uniprot_ids': protein_list})

        #Get species
        species = MatrixSpecies.objects.filter(matrix_id=matrix.id)
        species_dict = []
        for specie in species:
            species_dict.append({
            'tax_id': specie.tax_id.tax_id,
            'name': specie.tax_id.species,
            })

        data_dict.update({'species': species_dict})
                
        
        #get tffm info
        try:
            tffm = Tffm.objects.get(matrix_base_id=base_id, matrix_version=version)
            tffm_dic = {
            'tffm': {
            'tffm_id': tffm.base_id+'.'+str(tffm.version),
            'base_id': tffm.base_id,
            'version': tffm.version,
            'log_p_1st_order': tffm.log_p_1st_order,
            'log_p_detailed': tffm.log_p_detailed,
            'experiment_name': tffm.experiment_name,
            }
            }
        except Tffm.DoesNotExist:
            tffm_dic = {
            'tffm': "No TFFM available for this model.",
            }

        data_dict.update(tffm_dic)

        #Get PFM 
        matrixdata = _get_matrix_data(matrix.id)

        data_dict.update({'pfm': matrixdata})

    	#serializer = MatrixSerializer(matrix, context={'request': request})
        
        return Response(data_dict)


class CollectionMatrixListViewSet(ListAPIView):
    """
    API endpoint that returns a list of all matrix profiles based on collection name.

    Collection names are: 'CORE', 'CNE', 'PHYLOFACTS', 'SPILCE', 'POLII', 'FAM','PBM','PBM_HOMEO','PBM_HLH'
    """
    
    serializer_class = MatrixSerializer
    pagination_class = MatrixResultsSetPagination
    throttle_classes = (UserRateThrottle,)
    filter_backends = [SearchFilter, OrderingFilter,]
    search_fileds = ['base_id', 'collection','name','version']
    filter_fileds = ['base_id', 'collection','name','version']
  
    renderer_classes = [renderers.JSONRenderer, JSONPRenderer, YAMLRenderer, JASPARListRenderer, TRANSFACListRenderer, PFMListRenderer, MEMEListRenderer, renderers.BrowsableAPIRenderer]

    def get_queryset(self):
        """
        List matrix profiles based on collection name
        """

        setattr(self.request, 'view', 'api-browsable')
        
        queryset = Matrix.objects.all()

        ##collection = self.request.GET.get('collection')
        collection = self.kwargs['collection']

        #if collection is set then filter queryset
        if collection.upper() in ['CORE', 'CNE', 'PHYLOFACTS', 'SPILCE', 'POLII', 'FAM','PBM','PBM_HOMEO','PBM_HLH']:
            queryset = queryset.filter(collection=collection.upper())
        else:
            queryset = None

        return queryset


class JASPARFilterBackend(BaseFilterBackend):
    def get_schema_fields(self, view):
        return [coreapi.Field(
            name='collection',
            location='query',
            description= 'JASPAR CORE or Collection name. For example: CNE',
            required=False,
            type='string'),
        coreapi.Field(
            name='tax_group',
            location='query',
            description= 'Taxonomic group. For example: Vertebrates',
            required=False,
            type='string'),
        coreapi.Field(
            name='class',
            location='query',
            description= 'Transcription factor class. For example: Zipper-Type',
            required=False,
            type='string'),
        coreapi.Field(
            name='family',
            location='query',
            description= 'Transcription factor family. For example: SMAD factors',
            required=False,
            type='string'),
        coreapi.Field(
            name='type',
            location='query',
            description= 'Type of data/experiment. For example: SELEX',
            required=False,
            type='string'),
        coreapi.Field(
            name='version',
            location='query',
            description= 'If set to latest, return latest version',
            required=False,
            type='string')
        ]

    def filter_queryset(self, request, queryset, view):

        query_string = request.GET.get('search', None)
        collection = request.GET.get('collection', None)
        tax_group = request.GET.get('tax_group', None)
        tf_class = request.GET.get('class', None)
        tf_family = request.GET.get('family', None)
        exp_type = request.GET.get('type', None)
        version = request.GET.get('version', None)

        #if collection is set then filter queryset
        if collection and collection !='':
            queryset = queryset.filter(collection=collection.upper())

        #if tax_group is set then filter queryset
        if tax_group and tax_group !='':
            matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(tag='tax_group',val=tax_group.lower())
            queryset = queryset.filter(id__in=matrix_ids)

        #if tf_class is set then filter queryset
        if tf_class and tf_class !='':
            matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(tag='class', val__icontains=tf_class)
            queryset = queryset.filter(id__in=matrix_ids)

        #if tf_family is set then filter queryset
        if tf_family and tf_family !='':
            matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(tag='family', val__icontains=tf_family)
            queryset = queryset.filter(id__in=matrix_ids)

        #if exp_type is set then filter queryset
        if exp_type and exp_type !='':
            matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(tag='type', val__icontains=exp_type)
            queryset = queryset.filter(id__in=matrix_ids)

        #if query string is set then filter queryset
        if query_string and query_string != '':
            queryset = queryset.filter(
            Q(name__icontains=query_string) | 
            Q(base_id__icontains=query_string) |
            Q(collection__icontains=query_string)).distinct()


        #if version is latest
        if version == 'latest':
            #latest_versions = queryset.values('base_id').annotate(Max('version'))
            #queryset = queryset.filter(version=latest_versions.values('version__max'))#.order_by('version')
            Q_statement = Q()
            latest_versions = queryset.values('base_id').annotate(latest_version=Max('version')).order_by()
            for version in latest_versions:
                Q_statement |=(Q(base_id__exact=version['base_id']) & Q(version=version['latest_version']))

            queryset = queryset.filter(Q_statement)

        return queryset

class MatrixListViewSet(ListAPIView):
    """
    REST API endpoint that returns a list of all matrix profiles.
    """
    
    #queryset = Matrix.objects.all()
    serializer_class = MatrixSerializer
    pagination_class = MatrixResultsSetPagination
    throttle_classes = (UserRateThrottle,)
    filter_backends = [SearchFilter, OrderingFilter, JASPARFilterBackend,]
    search_fileds = ['base_id', 'collection','name','version',]
    filter_fileds = ['base_id', 'collection','name', 'version',]
    renderer_classes = [ renderers.JSONRenderer, JSONPRenderer, YAMLRenderer, JASPARListRenderer, TRANSFACListRenderer, PFMListRenderer, MEMEListRenderer, renderers.BrowsableAPIRenderer]


    def get_queryset(self):
        """
        List all matrix profiles
        """

        setattr(self.request, 'view', 'api-browsable')
        
        queryset = Matrix.objects.all()

        #query_string = self.request.GET.get('q')
        # collection = self.request.GET.get('collection')
        # tax_group = self.request.GET.get('tax_group')
        # tf_class = self.request.GET.get('class')
        # tf_family = self.request.GET.get('family')
        # exp_type = self.request.GET.get('type')
        # version = self.request.GET.get('version')

        # query_string = self.request.query_params.get('search', None)
        # collection = self.request.query_params.get('collection', None)
        # tax_group = self.request.query_params.get('tax_group', None)
        # tf_class = self.request.query_params.get('tf_class', None)
        # tf_family = self.request.query_params.get('tf_family', None)
        # version = self.request.query_params.get('version', None)
        # exp_type = self.request.query_params.get('exp_type', None)


        # #if collection is set then filter queryset
        # if collection and collection !='':
        #     queryset = queryset.filter(collection=collection.upper())

        # #if tax_group is set then filter queryset
        # if tax_group and tax_group !='':
        #     matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(tag='tax_group',val=tax_group.lower())
        #     queryset = queryset.filter(id__in=matrix_ids)

        # #if tf_class is set then filter queryset
        # if tf_class and tf_class !='':
        #     matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(tag='class', val__icontains=tf_class)
        #     queryset = queryset.filter(id__in=matrix_ids)

        # #if tf_family is set then filter queryset
        # if tf_family and tf_family !='':
        #     matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(tag='family', val__icontains=tf_family)
        #     queryset = queryset.filter(id__in=matrix_ids)

        # #if exp_type is set then filter queryset
        # if exp_type and exp_type !='':
        #     matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(tag='type', val__icontains=exp_type)
        #     queryset = queryset.filter(id__in=matrix_ids)

        # #if query string is set then filter queryset
        # if query_string and query_string != '':
        #     queryset = queryset.filter(
        #     Q(name__icontains=query_string) | 
        #     Q(base_id__icontains=query_string) |
        #     Q(collection__icontains=query_string)).distinct()

        # #if version is latest
        # if version == 'latest':
        #     #latest_versions = queryset.values('base_id').annotate(Max('version'))
        #     #queryset = queryset.filter(version=latest_versions.values('version__max'))#.order_by('version')
        #     Q_statement = Q()
        #     latest_versions = queryset.values('base_id').annotate(latest_version=Max('version')).order_by()
        #     for version in latest_versions:
        #         Q_statement |=(Q(base_id__exact=version['base_id']) & Q(version=version['latest_version']))

        #     queryset = queryset.filter(Q_statement)

        return queryset

class MatrixVersionsViewSet(APIView):
    """
    API endpoint that returns matrix model versions based on base_id.
    """
    #queryset = Matrix.objects.all()
    serializer_class = MatrixSerializer
    throttle_classes = (UserRateThrottle,)
    #filter_backends = [OrderingFilter]
    #search_fileds = ['base_id', 'collection','name','version',]
    #filter_fileds = ['base_id', 'collection','name', 'version',]
    renderer_classes = [renderers.JSONRenderer, JSONPRenderer, YAMLRenderer, JASPARListRenderer, TRANSFACListRenderer, PFMListRenderer, MEMEListRenderer, renderers.BrowsableAPIRenderer]

    def get(self, request, base_id, format=None):
      """
      List matrix profile versions based on base_id
      """
      setattr(self.request, 'view', 'api-browsable')

      queryset = Matrix.objects.filter(base_id=base_id)
      
      data_dict = { 'count': queryset.count() }
      results = []
      for matrix in queryset:
        results.append({
        'matrix_id': matrix.base_id+'.'+str(matrix.version),
        'name': matrix.name,
        'base_id': matrix.base_id,
        'version': matrix.version,
        'collection': matrix.collection,
        'sequence_logo': _get_sequence_logo(request, matrix.base_id, matrix.version),
        'url': _get_matrix_url(request, matrix.base_id, matrix.version)
        })

      data_dict.update({'results': results})

      return Response(data_dict)

class MatrixInferenceViewSet(APIView):
    """
    API endpoint that infer matrix models based on protien sequence.
    """
    #queryset = Matrix.objects.all()
    #serializer_class = MatrixSerializer
    throttle_classes = (UserRateThrottle,)
    filter_backends = [SearchFilter, OrderingFilter]
    search_fileds = ['matrix_id', 'name','version']
    renderer_classes = [renderers.JSONRenderer, JSONPRenderer, YAMLRenderer, JASPARListRenderer, TRANSFACListRenderer, PFMListRenderer, MEMEListRenderer, renderers.BrowsableAPIRenderer]

    def get(self, request, sequence, format=None):
      """
      Infer matrix profiles, given protien sequence
      """
      setattr(self.request, 'view', 'api-browsable')
      #sequence = self.request.GET.get('sequence')
      #Call motif_infer function, to get inferred motifs for the sequence
      inferences = motif_infer(sequence)
      results = []
      for key, values in inferences.items():
        for value in values:
            data = {
            'matrix_id': value[1],
            'name': value[0],
            'evalue': value[2],
            'dbd': value[3],
            'url': request.build_absolute_uri(location='/')+'api/v1/matrix/'+value[1],
            'sequence_logo': request.build_absolute_uri(location='/')+'static/logos/svg/'+value[1]+'.svg'
            }
            results.append(data)
      
      
      data_dict = { 'count': len(results) }
      # for matrix in queryset:
      #   results.append({
      #   'matrix_id': matrix.base_id+'.'+str(matrix.version),
      #   'name': matrix.name,
      #   'base_id': matrix.base_id,
      #   'version': matrix.version,
      #   'collection': matrix.collection,
      #   'sequence_logo': _get_sequence_logo(request, matrix.base_id, matrix.version),
      #   'url': _get_matrix_url(request, matrix.base_id, matrix.version)
      #   })

      data_dict.update({'results': results})

      return Response(data_dict)


class MatrixAlignViewSet(APIView):
    """
    API endpoint that align an IUPAC string to matrix models in JaSPAR CORE by default of other collections if collection is set.
    """
    #queryset = Matrix.objects.all()
    #serializer_class = MatrixSerializer
    throttle_classes = (UserRateThrottle,)
    filter_backends = [SearchFilter, OrderingFilter]
    search_fileds = ['name','matrix_id']
    renderer_classes = [renderers.JSONRenderer, JSONPRenderer, YAMLRenderer, JASPARListRenderer, TRANSFACListRenderer, PFMListRenderer, MEMEListRenderer, renderers.BrowsableAPIRenderer]

    def get(self, request, sequence, format=None):
      """
      Align matrix profiles to IUPAC string.
      """
      setattr(self.request, 'view', 'api-browsable')
      
      collection = self.request.GET.get('collection')

      if collection.upper() not in ['CORE', 'CNE', 'PHYLOFACTS', 'SPILCE', 'POLII', 'FAM','PBM','PBM_HOMEO','PBM_HLH']:
        collection = 'CORE'

      #Call motif_infer function, to get inferred motifs for the sequence
      inferences = motif_infer(sequence)
      
      results = []
      for key, values in inferences.items():
        for value in values:
            data = {
            'matrix_id': value[1],
            'name': value[0],
            'evalue': value[2],
            'dbd': value[3],
            'url': request.build_absolute_uri(location='/')+'api/v1/matrix/'+value[1]
            }
            results.append(data)
      
      
      data_dict = { 'count': len(results) }
      # for matrix in queryset:
      #   results.append({
      #   'matrix_id': matrix.base_id+'.'+str(matrix.version),
      #   'name': matrix.name,
      #   'base_id': matrix.base_id,
      #   'version': matrix.version,
      #   'collection': matrix.collection,
      #   'sequence_logo': _get_sequence_logo(request, matrix.base_id, matrix.version),
      #   'url': _get_matrix_url(request, matrix.base_id, matrix.version)
      #   })

      data_dict.update({'results': results})

      return Response(data_dict)


class APIRoot(APIView):
    """
    This is the root of the JASPAR RESTful API v1. Please read the documentation for more details.
    """

    permission_classes = (AllowAny,)

    def get(self, request, format=format):
        setattr(request, 'view', 'api-browsable')
        return Response({
            'matrix': reverse('v1:matrix-list', request=request),
            'collection': reverse('v1:collection', args=['CORE'], request=request),
            'infer': reverse('v1:matrix-infer', args=['MSSILPFTPPIVKRLLGWKKGEQNGQEEKWCEKAVKSLVKKLKKTGQLDELEKAITTQNVNTKCITIPRSLDGRLQVSHRKGLPHVIYCRLWRWPDLHSHHELRAMELCEFAFNMKKDEVCVNPYHYQRVETPVLPPVLVPRHTEIPAEFPPLDDYSHSIPENTNFPAGIEPQSNIPETPPPGYLSEDGETSDHQMNHSMDAGSPNLSPNPMSPAHNNLDLQPVTYCEPAFWCSISYYELNQRVGETFHASQPSMTVDGFTDPSNSERFCLGLLSNVNRNAAVELTRRHIGRGVRLYYIGGEVFAECLSDSAIFVQSPNCNQRYGWHPATVCKIPPGCNLKIFNNQEFAALLAQSVNQGFEAVYQLTRMCTIRMSFVKGWGAEYRRQTVTSTPCWIELHLNGPLQWLDKVLTQMGSPSIRCSSVS'], request=request),
        })

def api_homepage(request):

    setattr(request, 'view', 'api-home')
    
    setattr(request, 'get_api_host', _get_api_root_url(request))
    setattr(request, 'get_host', _get_host_name(request))

    return render(request, 'rest_framework/api_home.html')

def api_docs(request):

    setattr(request, 'view', 'apidocs')
    setattr(request, 'get_api_host', _get_api_root_url(request))
    setattr(request, 'get_host', _get_host_name(request))

    return render(request, 'rest_framework/api_docs.html')

def api_overview(request):

    setattr(request, 'view', 'overview')
    setattr(request, 'get_api_host', _get_api_root_url(request))
    setattr(request, 'get_host', _get_host_name(request))

    return render(request, 'rest_framework/api_overview.html')

def api_clients(request):

    setattr(request, 'view', 'clients')
    setattr(request, 'get_api_host', _get_api_root_url(request))
    setattr(request, 'get_host', _get_host_name(request))

    return render(request, 'rest_framework/api_clients.html')


def _get_api_root_url(request):
    return request.build_absolute_uri(location='/')+'api/v1/'

def _get_host_name(request):
    return request.build_absolute_uri(location='/')


    

