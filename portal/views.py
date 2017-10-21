## Author: Aziz Khan
## License: GPL v3
## Copyright 2017 Aziz Khan <azez.khan__AT__gmail.com>

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Max
from .models import Matrix, MatrixAnnotation, MatrixSpecies, Tax, TaxExt, MatrixData, MatrixProtein, Tffm, Post
from utils import utils
from itertools import chain
from operator import attrgetter
from sets import Set as set
from .forms import InferenceForm, ContactForm, AlignForm, SearchForm
import os, sys, re
from django.core.mail import send_mail, BadHeaderError
from django.urls import reverse

from utils.motif_inferrer.inferrer import motif_infer, write
from jaspar.settings import BASE_DIR, BIN_DIR, TEMP_DIR, TEMP_LIFE, SEND_TO_EMAIL

def index(request):
	'''
	This loads the homepage
	'''

	setattr(request, 'view', 'index')

	exp_type = MatrixAnnotation.objects.filter(tag='type').values('val').distinct().order_by('val')
	tf_family = MatrixAnnotation.objects.filter(tag='family').values('val').distinct().order_by('val')
	tf_class = MatrixAnnotation.objects.filter(tag='class').values('val').distinct().order_by('val')

	search_form = SearchForm()

	context ={
	'exp_type': exp_type,
	'tf_family': tf_family,
	'tf_class': tf_class,
	'search_form': search_form,
	}

	home_version = request.GET.get('home', None)

	if home_version == 'v1':
		return render(request, 'portal/index_v1.html', context)
	else:
		return render(request, 'portal/index.html', context)


def search(request):
	'''
	This function returns the results based the on the search query
	'''
	
	query_string = request.GET.get('q', None)
	tax_group = request.GET.get('tax_group', None)
	collection = request.GET.get('collection', None)
	exp_type = request.GET.get('type', None)
	tf_class = request.GET.get('class', None)
	tf_family = request.GET.get('family', None)
	version = request.GET.get('version', None)

	#has_tffm = request.GET.get('has_tffm', None)

	setattr(request, 'view', 'search')

	#Pagination
	page = request.GET.get('page', 1)
	page_size = request.GET.get('page_size', 10)
	if page_size =='' or int(page_size) > 1000:
		page_size = 10

	queryset = None

	if query_string is not None:
		
		#check if user is searching with matrix id, then return to detail page else pass
		id_query = query_string.split('.')
		if len(id_query) == 2:
			if len(Matrix.objects.filter(base_id=id_query[0], version=id_query[1])) > 0:
				return redirect('/matrix/'+query_string)
			else:
				pass

		#If collection is not set, set it to CORE
		if collection is None or collection =='':
			collection = 'CORE'

		#Get matrix ids by searching from different models
		if collection == 'all':
			queryset = Matrix.objects.all().order_by('base_id')
		else:
			queryset = Matrix.objects.filter(collection=collection.upper()).order_by('base_id')

		#if has_tffm:
		#	base_ids = Tffm.objects.values_list('matrix_base_id',flat=True)
		#	queryset = queryset.filter(base_id__in=base_ids)

		#get matrix ids
		matrix_ids = queryset.values_list('id', flat=True)
		
		#filter based on tax group
		if tax_group and tax_group !='' and tax_group !='all':
			matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(
				tag='tax_group', val=tax_group.lower(), matrix_id__in=matrix_ids)

		#filter based on experiment type
		if exp_type and exp_type !='' and exp_type !='all':
			matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(
				tag='type', val=exp_type, matrix_id__in=matrix_ids)

		#filter based on tf class
		if tf_class and tf_class !='' and tf_class !='all':
			matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(
				tag='class', val=tf_class, matrix_id__in=matrix_ids)

		#filter based on tf family
		if tf_family and tf_family !='' and tf_family !='all':
			matrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(
				tag='family', val=tf_family, matrix_id__in=matrix_ids)
		
		#filter based on query_sting
		if query_string !='':
			
			#filter based on matrix model
			if collection !='all':
				matrix_matrix_ids = list(queryset.values_list('id', flat=True).filter(
				Q(name__icontains=query_string) | 
				Q(base_id__icontains=query_string), 
				collection=collection, id__in=matrix_ids)
				)
			else:
				matrix_matrix_ids = list(queryset.values_list('id', flat=True).filter(
				Q(name__icontains=query_string) | 
				Q(base_id__icontains=query_string), id__in=matrix_ids))

			#filter based of MatrixAnnotation model
			matrix_annotation_ids = list(MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(
				val__icontains=query_string, 
				matrix_id__in=matrix_ids))

			#filter based of MatrixProtein model
			matrix_protein_ids = list(MatrixProtein.objects.values_list('matrix_id', flat=True).filter(
				acc=query_string, matrix_id__in=matrix_ids))

			#filter based of MatrixSpecies model
			matrix_species_ids = list(MatrixSpecies.objects.values_list('matrix_id', flat=True).filter(
				Q(tax_id=query_string) | 
				Q(tax_id__species__icontains=query_string), 
				matrix_id__in=matrix_ids)
			)

			#Make a union of all the matrix ids
			matrix_ids = list(
				set(matrix_matrix_ids) | 
				set(matrix_annotation_ids) | 
				set(matrix_protein_ids) | 
				set(matrix_species_ids)
				)
			
		#filter matrix query based on ids
		queryset = queryset.filter(id__in=matrix_ids).distinct()

		#If version is set to latest, then get the latest version
		if version == 'latest':
			
			Q_statement = Q()
			latest_versions = queryset.values('base_id').annotate(latest_version=Max('version')).order_by()
			for version in latest_versions:
				Q_statement |=(Q(base_id__exact=version['base_id']) & Q(version=version['latest_version']))
			queryset = queryset.filter(Q_statement).distinct()

		##paginate the queryset

		paginator = Paginator(queryset, page_size)
		try:
			queryset = paginator.page(page)
		except PageNotAnInteger:
			queryset = paginator.page(1)
		except EmptyPage:
			queryset = paginator.page(paginator.num_pages)
			
		##create a data dictionary with more information from other tables by looping through the matrix ids 
		results = _get_matrix_detail_info(queryset)
	else:
		results = None

	#exp_type for the search form drop-down
	exp_type  = MatrixAnnotation.objects.filter(tag='type').values('val').distinct().order_by('val')
	tf_family = MatrixAnnotation.objects.filter(tag='family').values('val').distinct().order_by('val')
	tf_class = MatrixAnnotation.objects.filter(tag='class').values('val').distinct().order_by('val')

	
	#import json
	#results = json.dumps(list(results))
	
	context = {
	'matrices': results,
	'exp_type': exp_type,
	'pages': queryset,
	'tf_family': tf_family,
	'tf_class': tf_class,
	
	}
	
	#return render(request, 'portal/search.html', context)
	return render(request, 'portal/search_paginator.html', context)


def browse_collection(request, collection):
	'''
	Browse Collection
	'''

	setattr(request, 'view', 'collection')
	
	page = request.GET.get('page', 1)

	page_size = request.GET.get('page_size', 10)
	if page_size =='':
		page_size = 10

	setattr(request, 'collection', collection.upper())

	queryset = Matrix.objects.filter(collection=collection.upper()).order_by('base_id')

	paginator = Paginator(queryset, page_size)

	try:
		queryset = paginator.page(page)
	except PageNotAnInteger:
		queryset = paginator.page(1)
	except EmptyPage:
		queryset = paginator.page(paginator.num_pages)

	results = _get_matrix_detail_info(queryset)

	context = {
	'matrices': results,
	'pages': queryset,
	'collection': collection,
	}

	return render(request, 'portal/browse_collection.html', context)

def _get_matrix_detail_info(queryset):
    '''
    Get detail matrix info based on queryset

    @input:
    queryset {QuerySet}
    @return:
    results {dictionary}
    '''
    results = []
    
    for matrix in queryset:
        data_dict = {}
        data_dict['id'] = matrix.id
        data_dict['matrix_id'] = matrix.base_id+'.'+str(matrix.version)
        data_dict['base_id'] = matrix.base_id
        data_dict['version'] = matrix.version
        data_dict['collection'] = matrix.collection
        data_dict['name'] = matrix.name

        data_dict['logo'] = _get_sequence_logo(matrix.base_id+'.'+str(matrix.version))
        
        #Get annotations for each matrix id
        annotation_queryset = MatrixAnnotation.objects.filter(matrix_id=matrix.id)

        data_dict.update(_map_annotations(annotation_queryset))
        
        #Get species for each matrix id
        species = MatrixSpecies.objects.filter(matrix_id=matrix.id)
    
        #loop through species and get specie details
        species_dict = []
        if species:
        	for specie in species:
        		try:
        			species_dict.append([
        				specie.tax_id.tax_id,
        				specie.tax_id.species,
        				])
        		except:
        			pass
        data_dict.update({'species': species_dict})
        
        results.append(data_dict)

    return results

def _map_annotations(queryset):
	'''
	Internal method to map annotations in a structured data

	@input:
	queryset {QuerySet}

	@output:
	annotations {dictionary}
	'''
	annotations = {}

	tf_class = []
	tf_family = [] 
	tfe_ids = []
	pubmed_ids = []
	pazar_tf_ids =[]      
	#loop through annotations and get what needed
	for annotation in queryset:

		if annotation.tag == 'tax_group':
			annotations['tax_group'] = annotation.val
		elif annotation.tag == 'type':
			annotations['type'] = annotation.val
		elif annotation.tag == 'class':
			tf_class.append(annotation.val)
		elif annotation.tag == 'family':
			tf_family.append(annotation.val)
		elif annotation.tag == 'tfe_id':
			tfe_ids.append(annotation.val)
		elif annotation.tag == 'included_models':
			annotations['included_models'] = annotation.val.replace(',', ' ')
		elif annotation.tag == 'medline':
			pubmed_ids.append(annotation.val)
		elif annotation.tag == 'pazar_tf_id':
			pazar_tf_ids.append(annotation.val)
		else:
			annotations[annotation.tag] = annotation.val
		
		annotations['class'] = tf_class
		annotations['family'] = tf_family
		annotations['tfe_ids'] = tfe_ids
		annotations['pubmed_ids'] = pubmed_ids
		annotations['pazar_tf_ids'] = pazar_tf_ids

	return annotations


def _get_sequence_logo(matrix_id, input_type='sites', output_type='png', size='medium'):
	'''
	Takes matrix ID and returns URL for sequence logo
	'''
	
	from Bio import motifs

	logo_name = matrix_id+'.'+output_type

	#get absolute path
	input_file =  BASE_DIR+'/download/'+input_type+'/'+matrix_id+'.'+input_type
	output_logo = BASE_DIR+'/static/logos/'+logo_name

	
	if os.path.exists(output_logo):
		return logo_name
	else:
		try:
			with open(input_file) as handle:
				motif = motifs.read(handle, input_type)
			motif.weblogo(output_logo, format=output_type, show_errorbars=False, size='large', xaxis_label='Position', yaxis_label=' ')
			#By using WebLogo
			#cmd = "weblogo -f "+input_file+" -o "+output_logo+" --resolution 300 -x ' ' -y 'position' --format "+output_type+" --show_errorbars False --size "+size
			#os.system(cmd)
		except:
			pass

		return logo_name

## This function is not used
def svg_logo(request, matrix_id):

	from Bio import motifs
	output_type = 'jpg'
	input_type = 'pfm'

	logo_name = matrix_id+'.'+output_type

	#get absolute path
	input_file =  BASE_DIR+'/download/'+input_type+'/'+matrix_id+'.'+input_type
	output_logo = BASE_DIR+'/static/logos/svg/'+logo_name

	
	if os.path.exists(output_logo):
		return logo_name
	else:
		try:
			#with open(input_file) as handle:
			#	motif = motifs.read(handle, input_type)
			#motif.weblogo(output_logo, format=output_type, show_errorbars=False, size='large', xaxis_label='Position', yaxis_label=' ')
			#By using WebLogo
			cmd = "weblogo -f "+input_file+" -o "+output_logo+" --resolution 300 -x ' ' -y 'position' --format "+output_type+" --show_errorbars False --size large"
			os.system(cmd)
		except:
			pass

	return HttpResponse(output_logo)


def html_binding_sites(request, matrix_id):


	sites_file = BASE_DIR+'/download/sites/'+matrix_id+'.sites'
	
	sites = _get_html_binding_sties(sites_file)

	context = {
	'sites': sites,
	'matrix_id': matrix_id,
	}

	return render(request, 'portal/html_binding_sites_external.html', context)


def _get_html_binding_sties(sites):

	from Bio import SeqIO

	split_sites = []

	fasta_sequences = SeqIO.parse(open(sites),'fasta')

	for fasta in fasta_sequences:
		sequence = str(fasta.seq)
		site = re.sub('[^A-Z]', '', sequence)
		split_site = sequence.split(site)
		split_site.append(site)
		split_sites.append(split_site)

	return split_sites


def matrix_detail(request, matrix_id):
	'''
	This will show the details of a matrix based on base_id and version
	'''
	(base_id, version) = utils.split_id(matrix_id)

	matrix = Matrix.objects.get(base_id=base_id, version=version)
	#annotation = MatrixAnnotation.objects.values_list('tag','val').filter(id=matrix.id)
	annotation_queryset = MatrixAnnotation.objects.filter(id=matrix.id)

	#map annotations
	annotation = _map_annotations(annotation_queryset)
	#matrixdata = MatrixData.objects.all().filter(id=matrix.id)
	proteins = MatrixProtein.objects.filter(matrix_id=matrix.id)
	
	species = MatrixSpecies.objects.filter(matrix_id=matrix.id)

	try:
		tffm = Tffm.objects.get(matrix_base_id=base_id, matrix_version=version)
	except Tffm.DoesNotExist:
		tffm = None

	if request.method == 'GET' and 'revcomp' in request.GET:
		revcomp_value = request.GET['revcomp']
		if revcomp_value is not None and revcomp_value != '':
			if revcomp_value == '1':
				revcomp = True
			else:
				revcomp = False
	else:
		revcomp = False
	
	tfbs_info = utils.tfbs_info_exist(base_id=base_id, version=version)

	matrixdata = _get_matrix_data(matrix.id, revcomp=revcomp)

	versions = _get_versions_data(base_id)

	#Check if cart and remove the current profile if it's in the cart
	cart = request.session.get('imatrix_ids', None)
	removed = False
	if cart:
		matrix_id = request.GET.get('remove')
		if matrix_id and matrix_id in cart:
			cart.remove(matrix_id)
			request.session['imatrix_ids'] = cart
			removed = matrix_id
		queryset = Matrix.objects.filter(id__in=cart)
		results = _get_matrix_detail_info(queryset)
		request.session['cart'] = results[:5]

	context = {
		'matrix': matrix,
		'proteins': proteins,
		'species': species,
		'versions': versions,
		'tffm': tffm,
	}

	context.update(tfbs_info)
	context.update(matrixdata)
	context.update(annotation)

	return render(request, 'portal/matrix_detail.html', context)


def profile_inference(request):
	'''
	This will inference a profile based on a protein sequence
	'''

	setattr(request, 'view', 'inference')

	form_class = InferenceForm
	# if request is not post, initialize an empty form
	form = form_class(request.POST or None)

	if request.method == 'POST':
		#create a form instance and populate it with data from the request:
		form = InferenceForm(request.POST)
		# check whether it's valid:
        if form.is_valid():
        	
        	#process the data in form.cleaned_data as required
        	sequence = form.cleaned_data['sequence']

        	#Call motif_infer function, to get inferred motifs for the sequence
        	inferences = motif_infer(sequence)

        	matrices = []
        	for key, values in inferences.items():
        		for value in values:
	        		data = {
	        		'matrix_id': value[1],
	        		'name': value[0],
	        		'evalue': value[2],
	        		'dbd': value[3]
	        		}
	        		if value[1] != '':
	        			internal_id  = utils.get_internal_id(value[1])
	        			#values.append(internal_id)
	        			data['id'] = internal_id
        			
        			matrices.append(data)
        	
           	#Create context to pass it to the profile_inference_results template
        	context = {
        	'matrices': matrices,
        	}

        	return render(request, 'portal/profile_inference_results.html', context)
	#if it's not a POST request, show the form
	else:
		#create form object
		form = InferenceForm()
		#Create context to pass it to the profile_inference template
		context = {
		"form": form,
		}	
		return render(request, 'portal/profile_inference.html', context)

def matrix_align(request):
	'''
	This will take a custom matrix or IUPAC string and align it to CORE (default) or to a selected collection 
	'''

	form_class = AlignForm
	# if request is not post, initialize an empty form
	form = form_class(request.POST or None)
	
	setattr(request, 'view', 'align')

	if request.method == 'POST':
		pfm1_input = request.POST.get('matrix')
		matrix_type = request.POST.get('matrix_type')
		form = AlignForm(request.POST)
		# check whether it's valid:
        if form.is_valid():
      	
        	# process the data in form as required
            pfm1 = TEMP_DIR+'/'+_get_current_date()+'_matrix_align_'+str(os.getpid())+'.pfm'

            #import re
            #pattern = re.compile("^([\[\]][ACGT]+)+$")
            #if pattern.match(pfm1_input):
            if matrix_type == 'jaspar':
            	pfm1_input = pfm1_input.replace('[',"")
            	pfm1_input = pfm1_input.replace(']',"")
            	pfm1_input = pfm1_input.replace('A',"")
            	pfm1_input = pfm1_input.replace('C',"")
            	pfm1_input = pfm1_input.replace('G',"")
            	pfm1_input = pfm1_input.replace('T',"")
            
            elif matrix_type == 'iupac':
            	#need to be implemented
            	pfm1_input = pfm1_input
            else:
            	pass

            width = float(len(pfm1_input.split('\n')[0].split(' ')))

            pfm1_file = open(pfm1, 'w')
            pfm1_file.write(pfm1_input)
            pfm1_file.close()
       
            collection = form.cleaned_data['collection']
            #get matrix data
            queryset = Matrix.objects.filter(collection=collection)

            version = 'latest'
            #If version is set to latest, then get the latest version
            if version == 'latest':
            	Q_statement = Q()
            	latest_versions = queryset.values('base_id').annotate(latest_version=Max('version')).order_by()
            	for version in latest_versions:
            		Q_statement |=(Q(base_id__exact=version['base_id']) & Q(version=version['latest_version']))
            	queryset = queryset.filter(Q_statement).distinct()
            matrices = []
            import subprocess

            for query in queryset:

            	#pfm2 = _print_matrix_data(_get_matrix_data(query.id), format='pfm')
            	pfm2 = BASE_DIR+'/download/all_data/FlatFileDir/'+query.base_id+'.'+str(query.version)+'.pfm'
            	cmd = BIN_DIR+'/matrixaligner/matrix_aligner '+pfm1+' '+pfm2
            	#cmd = 'matrix_aligner '+pfm1+' '+pfm2
            	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            	
            	score = 1
            	try:
            		line = None
            		#for line in iter(proc.stdout.readline, ""):
            		for line in proc.stdout:
            			pass
            		if line is not None:
						results = line.split('\t')
						score = float(results[3])
            	except:
            		pass
            	
            	pfm2_length = MatrixData.objects.filter(id=query.id, row='A').order_by('-col')[0]

            	if(pfm2_length.col < width):
            		width = pfm2_length.col
            	
            	rel_score = 100.0*score/float(width*2)

            	data = {
            	'id': query.id,
            	'matrix_id': query.base_id+'.'+str(query.version),
            	'name': query.name,
            	'collection': query.collection,
            	'score': score,
            	'percent_score': rel_score
            	}
            	matrices.append(data)

            context = {
            'matrices': matrices,
            'matrix': request.POST.get('matrix'),

            }
            return render(request, 'portal/align_results.html', context)
	else:
	
		context = {
		"form": form,
		}
		
		return render(request, 'portal/align.html', context)


def analysis(request):
	'''
	This will perform analyis on the selected profiles or profiles in the cart
	'''

	#delete older temp files
	_delete_temp_files(path=TEMP_DIR, days=TEMP_LIFE)
	
	if request.method == 'POST':
		#populate data from the request:
		
		cart = request.POST.get('cart_data', None)

		if cart:
			##Internal matrix ids in cart
			imatrix_ids = request.session.get('imatrix_ids')
		else:
			#Internal matrix ids
			imatrix_ids = request.POST.getlist('matrix_id')
		
		#Check the analysis type
		if request.POST.get('scan'):

			analysis_type = 'Scan'
			(results, matrix_ids) = _scan_matrix(imatrix_ids, 
				request.POST.get('scan_sequence'), 
				request.POST.get('threshold_score')
				)

		elif request.POST.get('cart'):

			analysis_type = 'Add to cart'
			#call the add to cart function
			profiles_added =_add_to_cart(request, imatrix_ids)
			request.session['message'] = "You have added "+str(profiles_added)+" profile(s) to the cart."
			collection_data = request.POST.get('collection_data')
			page_number = request.POST.get('page_number')
			page_size = request.POST.get('page_size')
			inference_data = request.POST.get('inference_data')
			profile_data = request.POST.get('profile_data')
			if profile_data:
				redirect_url = request.META.get('HTTP_REFERER')+'?cart=1'
			elif collection_data and not page_number and not page_size:
				redirect_url = request.META.get('HTTP_REFERER')+'?cart=1'
			elif inference_data:
				return redirect('view_cart')
			else:
				redirect_url = request.META.get('HTTP_REFERER')+"&cart=1"
			return HttpResponseRedirect(redirect_url)

		elif request.POST.get('permute'):

			analysis_type = 'Permute'
			#call the permute function
			(results, matrix_ids) = _permute_matrix(imatrix_ids, 
				request.POST.get('permute_type'),  
				request.POST.get('permute_format')
				)

		elif request.POST.get('cluster'):

			analysis_type = 'Cluster'

			(results, matrix_ids) = _cluster_matrix(imatrix_ids, 
				request.POST.get('tree'), 
				request.POST.get('align'),
				request.POST.get('ma'),
				request.POST.get('cc')

				)

		elif request.POST.get('randomize'):

			analysis_type = 'Randomize'
			(results, matrix_ids) = _randomize_matrix(imatrix_ids, 
				request.POST.get('randomize_format'), 
				request.POST.get('randomize_count')
				)

		elif request.POST.get('download'):

			analysis_type = 'Download'
			(results, matrix_ids) = _download_matrix(imatrix_ids, 
				request.POST.get('download_type','individual'), 
				request.POST.get('download_format', 'jaspar')
				)

		else:
			results = 'Something went wrong!'

		context = {
		"results": results,
		'matrix_ids': matrix_ids,
		'analysis_type': analysis_type,
		'temp_life': TEMP_LIFE,
		}

		return render(request, 'portal/analysis_results.html', context)
	
	else:
		results = "Please select models to perform analysis."
	
		context = {
		"results": results,
		}
		
		return render(request, 'portal/analysis.html', context)

def _add_to_cart(request, imatrix_ids):
	'''
	Add profiles to card using ajax to download together
	'''

	#imatrix_ids = request.POST.getlist('matrix_id')
	cart = request.session.get('imatrix_ids')

	profiles_added = len(imatrix_ids)

	if cart:
		
		imatrix_ids.extend(request.session['imatrix_ids'])

		request.session['imatrix_ids'] = list(set(imatrix_ids))

		queryset = Matrix.objects.filter(id__in=request.session['imatrix_ids']).order_by('name')[:5]
		results = _get_matrix_detail_info(queryset)
		request.session['cart'] = results

		profiles_added = abs(len(request.session['imatrix_ids']) - len(cart))
	else:
		request.session['imatrix_ids'] = imatrix_ids
		queryset = Matrix.objects.filter(id__in=imatrix_ids).order_by('name')[:5]
		results = _get_matrix_detail_info(queryset)
		request.session['cart'] = results

   	data ={
   	'imatrix_ids': request.session['imatrix_ids']
   	}

   	return profiles_added


def _scan_matrix(imatrix_ids, fasta_sequence, threshold_score=80):
	'''
	Scan the matrix models for a fasta sequence

    @input:
    matrix_ids {list}, fasta_sequence {string}, threshold_score {float}
    @return:
    results {list}, matrix_ids {list}
    '''

	from Bio import motifs
	import math
	from operator import itemgetter
	import Bio.SeqIO
	from Bio.Alphabet import generic_dna
	from Bio.Alphabet.IUPAC import IUPACUnambiguousDNA as unambiguousDNA

	threshold_score = float(threshold_score)/100
	
	matrix_ids = []
	results = []

	fasta_file = _get_current_date()+'_scan_fasta_file_'+str(os.getpid())+'.txt'
	
	input_file = open(TEMP_DIR+'/'+fasta_file, 'w+')
	input_file.write(fasta_sequence)
	input_file.close()

	for imatrix_id in imatrix_ids:
		(matrix_id, matrix_name) = _get_matrix_id_name(imatrix_id)
		matrix_ids.append(matrix_id)
	
		with open(BASE_DIR+'/download/all_data/FlatFileDir/'+matrix_id+'.pfm') as handle:
			motif = motifs.read(handle, "pfm")

		motif.pseudocounts = motifs.jaspar.calculate_pseudocounts(motif)
		pssm = motif.pssm
		max_score = pssm.max
		min_score = pssm.min
		abs_score_threshold = (max_score - min_score) * threshold_score + min_score

		for record in Bio.SeqIO.parse(TEMP_DIR+'/'+fasta_file, "fasta", generic_dna):
			record.seq.alphabet = unambiguousDNA()
			
			for position, score in pssm.search(record.seq, threshold=abs_score_threshold):
				if not math.isnan(score):
					rel_score = (score - min_score) / (max_score - min_score)
					if rel_score:
						position_max = position
						strand = "+"
						if position_max < 0:
							strand = "-"
							position_max = position + len(record.seq)
						start_position = position_max + 1
						end_position = position_max + pssm.length

						sequence = record.seq[start_position-1:end_position]
						if strand == "-":
							sequence = record.seq[start_position-1:end_position].reverse_complement()

						results.append({
							'matrix_id': matrix_id,
							'name': matrix_name,
							'position': position,
							'seq_id': record.id,
							'start': start_position,
							'end': end_position,
							'strand': strand,
							'score': score,
							'rel_score': rel_score,
							'sequence': sequence
							})			
	
	return results, matrix_ids

def _permute_matrix(imatrix_ids, permute_type='intra', permute_format='pfm'):
	'''
	Permute the selected matrix models's columns inter or intra matrcies

    @input:
    matrix_ids {list}, permute_type{string}, permute_format {string}
    @return:
    permuted_file_name {string}, matrix_ids {list}
    '''
   
	permuted_file_name = _get_current_date()+'_permuted_matrices_'+str(os.getpid())+'.txt'

	matrix_ids = []

	input_file = open(TEMP_DIR+'/'+permuted_file_name, 'w')

	if permute_type  == "intra":
		for imatrix_id in imatrix_ids:
			(matrix_id, matrix_name) = _get_matrix_id_name(imatrix_id)
			input_file.write(_print_matrix_data(_get_matrix_data(imatrix_id, permute=True), matrix_id, matrix_name, format=permute_format))
			matrix_ids.append(matrix_id)
		input_file.close()

		return permuted_file_name, matrix_ids

	elif permute_type  == "inter":
		list_A, list_C, list_G, list_T  = [], [], [], []
		sizes = []
		matrix_names = []
		for imatrix_id in imatrix_ids:
			(matrix_id, matrix_name) = _get_matrix_id_name(imatrix_id)

			data_dic = _get_matrix_data(imatrix_id)

			list_A.extend(data_dic['A'])
			list_C.extend(data_dic['C'])
			list_G.extend(data_dic['G'])
			list_T.extend(data_dic['T'])
				
			sizes.append(len(data_dic['A']))
			matrix_names.append(matrix_name)
			
			matrix_ids.append(matrix_id)

		#Permute columns between matrices
		import numpy as np 
		pfm_array = np.array([ list_A, list_C, list_G, list_T ])
		pfm_array = pfm_array[:, np.random.permutation(pfm_array.shape[1])]

		#update data_dic with permuted columns
		i, j, k  = 0, 0, 0
		for matrix_id in matrix_ids:
			k = k+sizes[i]-1

			data_dic = {
			'A': pfm_array[0][j:k],
			'C': pfm_array[1][j:k],
			'G': pfm_array[2][j:k],
			'T': pfm_array[3][j:k],
			}
			input_file.write(_print_matrix_data(data_dic, matrix_id, matrix_names[i], format=permute_format))
			
			j = k+1
			i = i+1

		input_file.close()

		return permuted_file_name, matrix_ids	

	else:
		raise ValueError("Unknown Permute Type %s" % permute_type)


def _randomize_matrix(imatrix_ids, randomize_format='raw', randomize_count=200):
	'''
	Randomize the matrix models

    @input:
    matrix_ids {list}
    @return:
    randomized_file_name {string}, matrix_ids {list}
    '''
    
	randomized_file_name = _get_current_date()+'_randomized_matrices_'+str(os.getpid())+'.txt'

	matrix_file = _get_current_date()+'_randomized_matrixfile_'+str(os.getpid())+'.txt'
	
	matrix_ids = []

	input_file = open(TEMP_DIR+'/'+matrix_file, 'w+')

	for imatrix_id in imatrix_ids:
		(matrix_id, matrix_name) = _get_matrix_id_name(imatrix_id)
		input_file.write(_print_matrix_data(_get_matrix_data(imatrix_id), matrix_id, matrix_name, 'jaspar'))
		matrix_ids.append(matrix_id)

	input_file.close()
	#Run PWMrandom
	#PWMrandom <inputmatrix> <outputmatrix> <nmatrix> <width>
	pwm_path = BIN_DIR+'/PWMrandomization/'
	cmd = 'cd '+pwm_path+' && ./PWMrandom '+matrix_file+' '+TEMP_DIR+'/'+randomized_file_name+' '+str(randomize_count)
	#cmd = 'cd '+pwm_path+' && ./PWMrandom '+matrix_file+' '+randomized_file_name+' '+str(randomize_count)+' > '+randomized_file_name
	#cmd = 'PWMrandom '+matrix_file+' '+randomized_file_name+' '+str(randomize_count)+' > '+randomized_file_name
	os.system(cmd)

	try:
		os.remove(matrix_file)
	except:
		pass
	
	return randomized_file_name, matrix_ids


def _cluster_matrix(imatrix_ids, tree="UPGMA", align="SWA", ma="PPA", cc="PCC"):
	'''
	Cluster the matrix models using STAMP

	cc: Column comparison metric
	ma: Multiple alignment method
	tree: Tree-building method
	align: Alignment method 
	
	@input:
    matrix_ids {list}, cc
    @return:
    results {string}
    '''

	matrix_file = _get_current_date()+'_clustered_matrixfile_'+str(os.getpid())+'.txt'
	
	matrix_ids = []

	input_file = open(TEMP_DIR+'/'+matrix_file, 'w')

	for imatrix_id in imatrix_ids:
		(matrix_id, matrix_name) = _get_matrix_id_name(imatrix_id)
		input_file.write(_print_matrix_data(_get_matrix_data(imatrix_id), matrix_id, matrix_name, 'transfac'))
		matrix_ids.append(matrix_id)

	input_file.close()

	score_file = BIN_DIR+'/stamp/ScoreDists/JaspRand_'+cc+'_'+align+'.scores'
	stamp_output = 'stamp_output_'+str(os.getpid())

	#Prepare STAMP srguments
	#-tf [input file] - Input dataset of motifs in TRANSFAC format [required!]
	#-sd [score file] - Input file with random score distributions [required!]
	#-cc: Column comparison metric
	#-ma - Multiple alignment method
	#-tree - Tree-building method
	#-align - Alignment method 
	arguments = '-tf '+TEMP_DIR+'/'+matrix_file+' -sd '+score_file+' -tree '+tree+' -align '+align+' -ma '+ma+' -cc '+cc+' -out '+TEMP_DIR+'/'+stamp_output
	cmd = BIN_DIR+'/stamp/stamp '+arguments+' > '+TEMP_DIR+'/'+stamp_output+'.txt'
	#cmd = 'stamp '+arguments+' > '+TEMP_DIR+'/'+stamp_output+'.txt'
	
	#Run STAMP
	try:
		os.system(cmd)
	except:
		pass

	#delete the temp input file
	try:
		os.remove(matrix_file)
	except:
		pass

	import zipfile
	from os.path import basename
	#Create a zip file of STAMP output files or play with the STAMP output files.
	file_name = _get_current_date()+'_STAMP_output_'+str(os.getpid())+'.zip'
	stampzip = zipfile.ZipFile(TEMP_DIR+'/'+file_name, 'w', zipfile.ZIP_DEFLATED)

	try:
		input_file = TEMP_DIR+'/'+stamp_output+'.txt'
		stampzip.write(input_file, basename(input_file))

		input_file = TEMP_DIR+'/'+stamp_output+'.tree'
		stampzip.write(input_file, basename(input_file))

		input_file = TEMP_DIR+'/'+stamp_output+'FBP.txt'
		stampzip.write(input_file, basename(input_file))

		#input_file = TEMP_DIR+'/'+stamp_output+'_match_pairs.txt'
		#stampzip.write(input_file, basename(input_file))

		#input_file = TEMP_DIR+'/'+stamp_output+'_matched.transfac'
		#stampzip.write(input_file, basename(input_file))
	except:
		pass
	
	stampzip.close()

	
	return file_name, matrix_ids

def _download_matrix(imatrix_ids, download_type='individual', download_format='pfm'):
	'''
	Download the matrix models

    @input:
    matrix_ids {list}
    @return:
    file_name {string}, matrix_ids {list}
    '''
 
	results = []
	matrix_ids = []
	
	if download_type  == "individual":
		
		import zipfile
		from os.path import basename

		#Create a zip file
		file_name = _get_current_date()+'_JASPAR2018_individual_matrices_'+str(os.getpid())+'_'+download_format+'.zip'
		matriceszip = zipfile.ZipFile(TEMP_DIR+'/'+file_name, 'w', zipfile.ZIP_DEFLATED)
		
		for imatrix_id in imatrix_ids:
			(matrix_id, matrix_name) = _get_matrix_id_name(imatrix_id)
			matrix_ids.append(matrix_id)
			input_file_path = TEMP_DIR+'/'+matrix_id+'.'+download_format
			input_file = open(input_file_path, 'w')
			
			if download_format == 'meme':
				input_file.write(_write_meme_header())
			
			input_file.write(_print_matrix_data(_get_matrix_data(imatrix_id), matrix_id, matrix_name, format=download_format))
			input_file.close()
			matriceszip.write(input_file_path, basename(input_file_path))
		
		matriceszip.close()

		return file_name, matrix_ids

	elif download_type  == "combined":

		file_name = _get_current_date()+'_JASPAR2018_combined_matrices_'+str(os.getpid())+'_'+download_format+'.txt'
		download_file = open(TEMP_DIR+'/'+file_name, 'w')

		if download_format == 'meme':
			download_file.write(_write_meme_header())

		for imatrix_id in imatrix_ids:
			(matrix_id, matrix_name) = _get_matrix_id_name(imatrix_id)
			matrix_ids.append(matrix_id)
			#with open(BASE_DIR+'/download/'+download_format+'/'+matrix_id+'.'+download_format) as input_file:
			download_file.write(_print_matrix_data(_get_matrix_data(imatrix_id), matrix_id, matrix_name, format=download_format))
		
		download_file.close()
		
		return file_name, matrix_ids
	
	else:
		raise ValueError("Unknown Download Type %s" % download_type)

def _write_meme_header(version='4'):

	letters = "ACGT"
	lines = []
	line = "MEME version "+version+"\n\n"
	lines.append(line)
	line = "ALPHABET= {0}\n\n".format(letters)
	lines.append(line)
	line = "strands: {0} {1}\n\n".format('+','-')
	lines.append(line)
	line = "Background letter frequencies\n"
	lines.append(line)
	line = "A {0} C {1} G {2} T {3}\n\n".format('0.25','0.25','0.25','0.25')
	lines.append(line)

	return "".join(lines)

def _delete_temp_files(path=TEMP_DIR, days=TEMP_LIFE):
	'''
	Delete older temp files based on TEMP_DIR and TEMP_LIFE.
	Please change the number of days in the jaspar.settings files

	@input
	path{string}, days{integer}
	'''
	import time

	current_time = time.time()

	for f in os.listdir(path):
		f = os.path.join(path, f)
		if os.stat(f).st_mtime < current_time - days * 86400:
			os.remove(f)
					

def _get_current_date():
	
	import datetime
	
	now = datetime.datetime.now()

	return str(str(now.year)+str(now.month).zfill(2)+str(now.day).zfill(2))

def _get_versions_data(base_id):
	'''
	Return all the versions for a given base_id
	'''

	queryset = Matrix.objects.filter(base_id=base_id)

	results = _get_matrix_detail_info(queryset)

	return results

def _get_matrix_id_name(id):
	'''
	Get matrix id and named from internal matrix id
	'''

	queryset = Matrix.objects.get(pk=id)

	return (queryset.base_id+'.'+str(queryset.version), queryset.name)

def _get_matrix_data(id, revcomp=False, permute=False):
	'''
	Takes internal matrix id and returns matrix data as a dictionary object
	'''
	data_dic = {}
	
	for base in ('A','C','G','T'):
		data_dic[base] = MatrixData.objects.values_list('val', flat=True).filter(id=id, row=base).order_by('col')

	#If reverse complement is true, compute revcomp
	if revcomp == True:
		revcomp_data_dic = {}
		
		revcomp_data_dic['A'] = data_dic['T'].reverse()
		revcomp_data_dic['C'] = data_dic['G'].reverse()
		revcomp_data_dic['G'] = data_dic['C'].reverse()
		revcomp_data_dic['T'] = data_dic['A'].reverse()

		data_dic = revcomp_data_dic
	#If permute is true, permute the matrix
	if permute == True:
		import numpy as np 
		pfm_array = np.array([ data_dic['A'], data_dic['C'], data_dic['G'], data_dic['T'] ])
		pfm_array = pfm_array[:, np.random.permutation(pfm_array.shape[1])]

		#update data_dic with permuted columns
		(data_dic['A'], data_dic['C'], data_dic['G'], data_dic['T']) = (pfm_array[0], pfm_array[1], pfm_array[2], pfm_array[3])

	return data_dic


def _print_matrix_data(matrix_data, matrix_id=None, matrix_name=None, format='pfm'):
    """
    Return the representation of motifs in "pfm" "jaspar" or trnasfac format.

    Addopted from BioPython jaspar module.

    """
    letters = "ACGT"
    length = len(matrix_data[letters[0]])
    lines = []
    if format == 'pfm':
    	if matrix_id and matrix_name:
    		line = ">{0} {1}\n".format(matrix_id, matrix_name)
    		lines.append(line)
    	for letter in letters:
    		terms = ["{0:6.2f}".format(float(value)) for value in matrix_data[letter]]
    		line = "{0}\n".format(" ".join(terms))
    		lines.append(line)

    elif format == 'flate_pfm':
    	
    	for letter in letters:
    		terms = ["{0:6.2f}".format(float(value)) for value in matrix_data[letter]]
    		line = "{0}\n".format(" ".join(terms))
    		lines.append(line)
    
    elif format == 'jaspar':
    	line = ">{0}\t{1}\n".format(matrix_id, matrix_name)
    	lines.append(line)
    	for letter in letters:
    		terms = ["{0:6.0f}".format(float(value)) for value in matrix_data[letter]]
    		line = "{0}  [{1} ]\n".format(letter, " ".join(terms))
    		lines.append(line)
    
    elif format == 'transfac':
    	line = "AC {0}\n".format(matrix_id)
    	lines.append(line)
    	line = "XX\n"
    	lines.append(line)
    	line = "ID {0}\n".format(matrix_name)
    	lines.append(line)
    	line = "XX\n"
    	lines.append(line)
    	line = "DE {0} {1} {2}\n".format(matrix_id, matrix_name, '; From JASPAR 2018')
    	lines.append(line)
    	line = "PO\t{0}\t{1}\t{2}\t{3}\n".format('A','C','G','T')
    	lines.append(line)
    	for i in range(len(matrix_data[letters[0]])):
    		line = "{0}\t{1}\t{2}\t{3}\t{4}\n".format(str(i+1).zfill(2), matrix_data['A'][i], matrix_data['C'][i], matrix_data['G'][i], matrix_data['T'][i])
    		lines.append(line)
    	line = "XX\n"
    	lines.append(line)

    elif format == 'meme':
    	
    	line = "MOTIF {0} {1}\n".format(matrix_id, matrix_name)
    	lines.append(line)
    	nsites = float(matrix_data['A'][0]) + float(matrix_data['C'][0]) + float(matrix_data['G'][0]) + float(matrix_data['T'][0])
    	line = "letter-probability matrix: alength= {0} w= {1} nsites= {2} E= {3}\n".format(4,length,int(nsites),'0')
    	lines.append(line)
    	for i in range(len(matrix_data[letters[0]])):
    		
    		line = " {0:6.6f}  {1:6.6f}  {2:6.6f}  {3:6.6f}\n".format(float(matrix_data['A'][i])/nsites, float(matrix_data['C'][i])/nsites, float(matrix_data['G'][i])/nsites, float(matrix_data['T'][i])/nsites)
    		lines.append(line)
    	line = "URL {0}\n\n".format('http://jaspar.genereg.net/matrix/'+matrix_id)
    	lines.append(line)

    else:
        raise ValueError("Unknown matrix format %s" % format)

    # Finished; glue the lines together
    text = "".join(lines)

    return text

def _get_latest_version(based_id):
	'''
	Get latest version of a matrix model
	'''
	matrix = Matrix.objects.order_by('version')[0:1].get(base_id=base_id)

	return matrix.version


def _get_pssm(matrix_id):

	from Bio import motifs

	with open(BASE_DIR+'/download/all_data/FlatFileDir/'+matrix_id+'.pfm') as handle:
		motif = motifs.read(handle, "pfm")

	motif.pseudocounts = motifs.jaspar.calculate_pseudocounts(motif)
	pssm = motif.pssm

	return pssm

def _parse_pubmed_id(pubmed_id):
	'''
	It takes pubmed_id and returns citation as string
	'''
	import requests
	url = "https://www.ncbi.nlm.nih.gov/pmc/utils/ctxp?ids="+str(pubmed_id)+"&report=citeproc"
	r = requests.get(url)
	data = r.json()
	citation = data['author'][0]['family']+" "+data['author'][0]['given'][0]+". et al. "+str(data['issued']['date-parts'][0][0])+", "+data['container-title-short']

	return citation

def view_cart(request):
	'''
	This will show the cart page with list of profiles
	'''
	setattr(request, 'view', 'cart')

	cart = request.session.get('imatrix_ids')
	removed = False
	if cart:
		matrix_id = request.GET.get('remove')
		if matrix_id and matrix_id in cart:
			cart.remove(matrix_id)
			request.session['imatrix_ids'] = cart
			removed = matrix_id
		queryset = Matrix.objects.filter(id__in=cart)
		results = _get_matrix_detail_info(queryset)
		request.session['cart'] = results[:5]
	else:
		results = None
	
	return render(request, 'portal/cart.html', {'matrices': results, 'removed': removed})

def empty_cart(request):
	'''
	This will empty the cart
	'''
	setattr(request, 'view', 'cart')

	if request.session['imatrix_ids']:
		del request.session['imatrix_ids']
	if request.session['cart']:
		del request.session['cart']
	
	return render(request, 'portal/cart.html', {'matrices': None})


def matrix_clustering(request):

	setattr(request, 'view', 'cluster')

	return render(request, 'portal/clustering_home.html')


def radial_tree(request, tax_group):

	setattr(request, 'view', 'cluster')
	return render(request, 'portal/clustering_detail.html', {'tax_group': tax_group})

def genome_tracks(request):

	setattr(request, 'view', 'tracks')

	return render(request, 'portal/genome_tracks.html')



def documentation(request):
	'''
	This will show the documentation page
	'''
	setattr(request, 'view', 'docs')

	return render(request, 'portal/documentation.html')

def download_data(request):
	'''
	This will show the downloads page
	'''
	setattr(request, 'view', 'downloads')

	tax_groups = ['Vertebrates', 'Plants','Insects','Nematodes','Fungi','Urochordates']

	collections = ['CORE', 'CNE', 'PHYLOFACTS','SPLICE','POLII','FAM','PBM','PBM_HOMEO','PBM_HLH']

	return render(request, 'portal/downloads.html', {'tax_groups': tax_groups, 'collections':collections})


def internal_download_data(request):
	'''
	This function prepares the data for downloads page
	
	To run this function enable the below line in urls.py and open the ROOT/downloads-internal/ URL in the browser.
    #url(r'^downloads-internal/$', views.internal_download_data, name='internal_download_data'),
    '''
 
	results = []
	matrix_ids = []

	matrix_version = request.GET.get('version', 'all')

	#download_format = request.GET.get('format', 'jaspar')


	download_formats = ['jaspar','meme','transfac']
	#download_formats = ['meme']

	collections = ['CORE', 'CNE', 'PHYLOFACTS','SPLICE','POLII','FAM','PBM','PBM_HOMEO','PBM_HLH']

	#collections = ['CORE']
	
	if matrix_version == 'latest':
		redundancy = 'non-redundant'
	else:
		redundancy = 'redundant'

	for collection in collections:

		queryset = Matrix.objects.filter(collection=collection.upper())

		#If version is set to latest, then get the latest version
		if matrix_version == 'latest':
				
			Q_statement = Q()
			latest_versions = queryset.values('base_id').annotate(latest_version=Max('version')).order_by()
			for version in latest_versions:
				Q_statement |=(Q(base_id__exact=version['base_id']) & Q(version=version['latest_version']))
			queryset = queryset.filter(Q_statement).distinct()
		
		
		imatrix_ids = queryset.values_list('id', flat=True)

		import zipfile
		from os.path import basename

		#Create a zip file
		for download_format in download_formats:
			zip_file_name = 'JASPAR2018_'+str(collection)+'_'+redundancy+'_pfms_'+str(download_format)+'.zip'
			txt_file_name = 'JASPAR2018_'+str(collection)+'_'+redundancy+'_pfms_'+str(download_format)+'.txt'
		
			matriceszip = zipfile.ZipFile(TEMP_DIR+'/'+zip_file_name, 'w', zipfile.ZIP_DEFLATED)

			download_file = open(TEMP_DIR+'/'+txt_file_name, 'w')

			if download_format == 'meme':
				download_file.write(_write_meme_header())
			
			for imatrix_id in imatrix_ids:
				(matrix_id, matrix_name) = _get_matrix_id_name(imatrix_id)
				matrix_ids.append(matrix_id)
				input_file_path = TEMP_DIR+'/'+matrix_id+'.'+download_format
				input_file = open(input_file_path, 'w')

				if download_format == 'meme':
					input_file.write(_write_meme_header())

				input_file.write(_print_matrix_data(_get_matrix_data(imatrix_id), matrix_id, matrix_name, format=download_format))
				input_file.close()
				matriceszip.write(input_file_path, basename(input_file_path))

				download_file.write(_print_matrix_data(_get_matrix_data(imatrix_id), matrix_id, matrix_name, format=download_format))
				
			matriceszip.close()
			download_file.close()

	tax_groups = ['vertebrates', 'plants','insects','nematodes','fungi','urochordates']
	#tax_groups = ['plants']

	for tax_group in tax_groups:
		#collections = ['CORE']
		queryset = Matrix.objects.filter(collection='CORE')

		#get matrix ids
		imatrix_ids = queryset.values_list('id', flat=True)
		
		#filter based on tax group
		if tax_group and tax_group !='' and tax_group !='all':
			imatrix_ids = MatrixAnnotation.objects.values_list('matrix_id', flat=True).filter(
				tag='tax_group', val=tax_group.lower(), matrix_id__in=imatrix_ids)

		#filter matrix query based on ids
		queryset = queryset.filter(id__in=imatrix_ids).distinct()

		#If version is set to latest, then get the latest version
		if matrix_version == 'latest':
			Q_statement = Q()
			latest_versions = queryset.values('base_id').annotate(latest_version=Max('version')).order_by()
			for version in latest_versions:
				Q_statement |=(Q(base_id__exact=version['base_id']) & Q(version=version['latest_version']))
			queryset = queryset.filter(Q_statement).distinct()
		
		
		imatrix_ids = queryset.values_list('id', flat=True)

		import zipfile
		from os.path import basename


		#Create a zip file
		for download_format in download_formats:
			
			zip_file_name = 'JASPAR2018_'+collection+'_'+tax_group+'_'+redundancy+'_pfms_'+download_format+'.zip'
			txt_file_name = 'JASPAR2018_'+collection+'_'+tax_group+'_'+redundancy+'_pfms_'+download_format+'.txt'

			matriceszip = zipfile.ZipFile(TEMP_DIR+'/'+zip_file_name, 'w', zipfile.ZIP_DEFLATED)

			download_file = open(TEMP_DIR+'/'+txt_file_name, 'w')
			if download_format == 'meme':
				download_file.write(_write_meme_header())
				
			for imatrix_id in imatrix_ids:
				(matrix_id, matrix_name) = _get_matrix_id_name(imatrix_id)
				matrix_ids.append(matrix_id)
				input_file_path = TEMP_DIR+'/'+matrix_id+'.'+download_format
				input_file = open(input_file_path, 'w')

				if download_format == 'meme':
					input_file.write(_write_meme_header())

				input_file.write(_print_matrix_data(_get_matrix_data(imatrix_id), matrix_id, matrix_name, format=download_format))
				input_file.close()
				matriceszip.write(input_file_path, basename(input_file_path))

				download_file.write(_print_matrix_data(_get_matrix_data(imatrix_id), matrix_id, matrix_name, format=download_format))
				
			matriceszip.close()
			download_file.close()

	return render(request, 'portal/index.html')


def api_documentation(request):
	'''
	This will show the api documentation page
	'''
	setattr(request, 'view', 'api-home')
	#setattr(request, 'view', 'apidocs')

	#return render(request, 'portal/api_documentation.html')
	return render(request, 'rest_framework/api_home.html')

def tools(request):
	'''
	This will show the tools page
	'''
	setattr(request, 'view', 'tools')

	return render(request, 'portal/tools.html')

def contact_us(request):
	'''
	Contact us and feednback page to send email
	'''
	setattr(request, 'view', 'contact_us')

	from django.core.mail import EmailMessage

	if request.method == 'GET':
		form = ContactForm()
	else:
		form = ContactForm(request.POST)
		if form.is_valid():
			subject = form.cleaned_data['subject']
			from_email = form.cleaned_data['from_email']
			#from_name = form.cleaned_data['from_name']
			message = form.cleaned_data['message']

			email = EmailMessage(
			    subject,
			    'From: '+from_email+'\n\nMessage: '+message,
			    from_email,
			    SEND_TO_EMAIL,
			    reply_to=[from_email],
			)
			try:
				#send_mail(subject, message, from_email, SEND_TO_EMAIL)
				email.send()
			except BadHeaderError:
				context ={'message': 'Invalid header found. Your message did not went through.', 'message_type': 'error', }
				return render(request, 'portal/contact_us.html', context)

			context = {'message': 'Thank you! Your message has been sent successfully. We will get back to you shortly.', 'message_type': 'success'}

			return render(request, 'portal/contact_us.html', context)
	return render(request, 'portal/contact_us.html', {'form': form})


def faq(request):
	'''
	This will show the FAQ page
	'''

	setattr(request, 'view', 'faq')


	return render(request, 'portal/faq.html')

def changelog(request):
	'''
	This will show the changelog page
	'''

	setattr(request, 'view', 'changelog')


	return render(request, 'portal/changelog.html')

def tour_video(request):
	'''
	This will show the tour video page
	'''

	setattr(request, 'view', 'tour')


	return render(request, 'portal/tour_video.html')

def about(request):
	'''
	This will show the about page
	'''
	setattr(request, 'view', 'about')

	matrix_ids = Matrix.objects.filter(collection="CORE").values_list('id', flat=True).distinct()

	#count the number of profiles in each taxonomic group
	vertibrates = MatrixAnnotation.objects.filter(tag='tax_group', val='vertebrates', matrix_id__in=matrix_ids).values_list('matrix_id', flat=True).distinct().count()
	plants = MatrixAnnotation.objects.filter(tag='tax_group', val='plants', matrix_id__in=matrix_ids).values_list('matrix_id', flat=True).distinct().count()
	insects = MatrixAnnotation.objects.filter(tag='tax_group', val='insects', matrix_id__in=matrix_ids).values_list('matrix_id', flat=True).distinct().count()
	nematodes = MatrixAnnotation.objects.filter(tag='tax_group', val='nematodes', matrix_id__in=matrix_ids).values_list('matrix_id', flat=True).distinct().count()
	fungi = MatrixAnnotation.objects.filter(tag='tax_group', val='fungi', matrix_id__in=matrix_ids).values_list('matrix_id', flat=True).distinct().count()
	urochordates = MatrixAnnotation.objects.filter(tag='tax_group', val='urochordates', matrix_id__in=matrix_ids).values_list('matrix_id', flat=True).distinct().count()

	context = {
	'vertibrates': vertibrates,
	'plants': plants,
	'insects': insects,
	'nematodes': nematodes,
	'fungi': fungi,
	'urochordates': urochordates,
	}

	return render(request, 'portal/about.html', context)


def post_details(request, year, month, day, slug):
	'''
	Show individual news/update
	'''
	post = get_object_or_404(Post, slug=slug)

	posts = Post.objects.all().order_by('-date')[:5]

	return render(request, 'portal/blog_single.html', {
        'post': post,
        'posts': posts,
    })

def post_list(request):
	'''
	List all news/updates
	'''
	posts = Post.objects.all().order_by('-date')

	return render(request, 'portal/blog.html', {
        'posts': posts,
    })


def matrix_versions(request, base_id):
	'''
	This will show the details of a matrix versions on base_id
	'''
	setattr(request, 'view', 'versions')

	queryset = Matrix.objects.filter(base_id=base_id)

	results = _get_matrix_detail_info(queryset)
	
	return render(request, 'portal/search.html', {'matrices': results})


def profile_versions(request):
	'''
	This will show the profile versions page
	'''

	setattr(request, 'view', 'profile-versions')


	return render(request, 'portal/profile_versions.html')

def url_redirection(request):
	'''
	Redirect the old URL request to new URL structure
	'''
	matrix_id = request.GET.get('ID', None)

	collection = request.GET.get('db', None)
	tax_group = request.GET.get('tax_group', None)

	url_path = request.get_full_path()

	if matrix_id:
		return redirect('/matrix/'+matrix_id)
	elif collection and tax_group:
		return redirect('/search/?q=&collection='+collection.upper()+'&tax_group='+tax_group)
	elif url_path == '/html/DOWNLOAD':
		return redirect('/downloads')
	else:
		#return render(request, '404.html', status=404)
		return redirect('index')

def page_not_found(request):
	'''
	Return custome 404 error page
	'''

	return render(request, '404.html', status=404)


def server_error(request):
	'''
	Return custome 500 error page
	'''
	return render(request, '500.html', status=500)

