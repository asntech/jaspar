# -*- coding: utf-8 -*-
## Author: Aziz Khan
## License: GPL v3
## Copyright © 2017 Aziz Khan <azez.khan__AT__gmail.com>

from django import forms
from .models import Matrix, MatrixAnnotation

class ContactForm(forms.Form):
    '''
	Form for contact us page
    '''
    #from_name = forms.CharField(label='Your name', required=True, max_length=100)
    from_email = forms.EmailField(required=True, label='Your email')
    subject = forms.CharField(label='Subject', required=False, max_length=100)
    message = forms.CharField(label='Your message/feedback', required=True, widget=forms.Textarea)


class InferenceForm(forms.Form):
	'''
	Form for profile inference page 
    '''
	sequence = forms.CharField(label='Paste a protein sequence below', required=True, widget=forms.Textarea)

class AlignForm(forms.Form):
	'''
	Form for matrix align page
    '''
	#matrix = forms.CharField(label='Paste custom matrix or IUPAC string', required=True, widget=forms.Textarea)
	collection = forms.CharField(label='Select collection', widget=forms.Select(
    	choices=Matrix.objects.values('collection').distinct().values_list('collection', 'collection')
    	))

class SearchForm(forms.Form):
	
	'''
	Form for advanced search options
    '''
    #Experiment type
	tf_type = forms.CharField(widget=forms.Select(
    	choices=MatrixAnnotation.objects.filter(tag='type').values('val').distinct().values_list('val', 'val')
    	))

	#TF Class
	tf_class = forms.CharField(
    	widget=forms.Select(
    		choices = MatrixAnnotation.objects.filter(tag='class').values('val').distinct().values_list('val', 'val')
			)
		)

	#Family
	tf_family = forms.CharField(
		widget=forms.Select(
			choices = MatrixAnnotation.objects.filter(tag='family').values('val').distinct().values_list('val', 'val')
			)
		)