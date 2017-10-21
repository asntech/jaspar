# -*- coding: utf-8 -*-
## Author: Aziz Khan
## License: GPL v3
## Copyright © 2017 Aziz Khan <azez.khan__AT__gmail.com>

from urllib import unquote
from portal.models import Matrix, MatrixAnnotation
import urllib2
import os
from jaspar.settings import BASE_DIR

def split_id(matrix_id):
    '''
    Split JASPAR ID into based_id and version
    '''

    id_split = unquote(matrix_id).split('.')

    base_id = None
    version = None
    if len(id_split) == 2:
        base_id = id_split[0]
        version = id_split[1]
    else:
        base_id = matrix_id

    return (base_id, version)

def get_base_id(matrix_id):
    """
    Return the base_id for the given matrix id
    """

    (bases_id,_) = split_id(matrix_id)

    return bases_id

def get_internal_id(matrix_id):
    """
    Return the internal_id for the given matrix_id
    """

    (base_id, version) = split_id(matrix_id)

    queryset = Matrix.objects.get(base_id=base_id, version=version)

    return queryset.id

def get_version(matrix_id):
    """
    Return the version for the given matrix id
    """

    (_,version) = split_id(matrix_id)

    return version

def get_latest_version(self, base_id):
    """
    Return the latest version number for the given base_id
    """

    queryset = Matrix.objects.filter(base_id=base_id).order_by('version')[0:1]

    return queryset.version

def get_matrix_id(id):
    """
    Return the matrix id for the given internal id
    """

    queryset = Matrix.objects.get(pk=id)

    matrix_id = queryset.base_id+'.'+str(queryset.version)

    return matrix_id

def tfbs_info_exist(base_id, version):
    '''
    Check if binding sites information does exist or not.
    return: dictionary object
    '''

    tfbs_info = {}
    url_fasta = BASE_DIR+'/download/sites/'+base_id+'.'+version+'.sites'
    url_bed = BASE_DIR+'/download/bed_files/'+base_id+'.'+version+'.bed'
    
    tfbs_info['tfbs_info_fasta'] = _path_exist(url_fasta)
    tfbs_info['tfbs_info_bed'] = _path_exist(url_bed)

    return tfbs_info

def _path_exist(file_path):
    if os.path.exists(file_path):
        return True
    else:
        return False

def _url_exist(url):
    '''
    URL exist or not
    '''       
    try:
        ret = urllib2.urlopen(url)
        if ret.code == 200:
            return True
        else:
            return False
    except:
        return False


