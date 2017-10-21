## Author: Aziz Khan
## License: GPL v3
## Copyright 2017 Aziz Khan <azez.khan__AT__gmail.com>

from django.contrib import admin

from .models import Matrix, MatrixAnnotation, MatrixData, Tffm, Post


class MatrixAdmin(admin.ModelAdmin):
	list_display = ('base_id', 'id','name','collection','version',)
	search_fields = ['collection', 'id', 'name', 'base_id']
	list_filter = ('collection',)

admin.site.register(Matrix, MatrixAdmin)


class MatrixAnnotationAdmin(admin.ModelAdmin):
	list_display = ('matrix_id', 'tag','val',)
	search_fields = ['tag', 'val']
	list_filter = ('tag',)

#admin.site.register(MatrixAnnotation, MatrixAnnotationAdmin)


class MatrixDataAdmin(admin.ModelAdmin):
	list_display = ('matrix_id', 'row','col','val',)
	search_fields = ['row', 'col']


#admin.site.register(MatrixData, MatrixDataAdmin)

class TffmAdmin(admin.ModelAdmin):
	list_display = ('base_id', 'name','matrix_base_id','matrix_version',)
	search_fields = ['matrix_base_id', 'base_id','name']


admin.site.register(Tffm, TffmAdmin)


class NewsAndUpdateAdmin(admin.ModelAdmin):
	list_display = ('title', 'author','category','date')
	search_fields = ['title', 'author','category']
	list_filter = ('category','author',)

admin.site.register(Post, NewsAndUpdateAdmin)