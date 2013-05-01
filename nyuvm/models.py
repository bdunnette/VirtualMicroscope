from django.db import models
from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.core.files import File

import os
import urllib

CACHED_THUMBNAILS=getattr(settings, 'CACHED_THUMBNAILS', False)

#core metadata options for collectionslide - customize these for your local faculty
SCANLEVELLIST = (((5, 5), (10, 10), (20, 20), (40, 40), (100, 100), (120, 120)))
STAINLIST=(('AFB', 'AFB'), ('Alcian Blue', 'Alcian Blue'), ('Bielschowsky Silver Stain', 'Bielschowsky Silver Stain'), ('Cajal', 'Cajal'), ('Diff-Quik', 'Diff-Quik'), ('Elastic Fiber Stain', 'Elastic Fiber Stain'), ('EVG', 'EVG'), ('Fontana Masson', 'Fontana Masson'), ('Foot-Hortegas silver technique', 'Foot-Hortegas silver technique'), ('Gallocyanin', 'Gallocyanin'), ('Giemsa', 'Giemsa'), ('GMS', 'GMS'), ('Golgis Silver Method', 'Golgis Silver Method'), ('Gomoris silver technique', 'Gomoris silver technique'), ('Gram Stain', 'Gram Stain'), ('H and E', 'H and E'), ('Helly fixation', 'Helly fixation'), ('Immunohistochemical Stain ', 'Immunohistochemical Stain '), ('Iron Hematoxylin', 'Iron Hematoxylin'), ('Iron Stain', 'Iron Stain'), ('Jones Silver Stain', 'Jones Silver Stain'), ('Mallorys PTAH', 'Mallorys PTAH'), ('Mallorys trichrome', 'Mallorys trichrome'), ('Masson Trichrome', 'Masson Trichrome'), ('Mucicarmine', 'Mucicarmine'), ('Myeloperoxidase', 'Myeloperoxidase'), ('Osmic acid', 'Osmic acid'), ('Papanicolau', 'Papanicolau'), ('PAS', 'PAS'), ('PAS+D', 'PAS+D'), ('Reticulin Stain', 'Reticulin Stain'), ('Rhodamine/Copper Stain', 'Rhodamine/Copper Stain'), ('Romanes silver technique', 'Romanes silver technique'), ('Romanovsky-type', 'Romanovsky-type'), ('Silver technique', 'Silver technique'), ('Steiner Stain', 'Steiner Stain'), ('Trypan Blue Vital Stain', 'Trypan Blue Vital Stain'), ('Von Kossa', 'Von Kossa'))
TISSUESOURCELIST = (('Cat', 'Cat'), ('Cow', 'Cow'), ('Dog', 'Dog'), ('Guinea Pig', 'Guinea Pig'), ('Human', 'Human'), ('Mammal', 'Mammal'), ('Monkey', 'Monkey'), ('Mouse', 'Mouse'), ('Pig', 'Pig'), ('Rabbit', 'Rabbit'), ('Rat', 'Rat'))
DEVELOPMENTALSTAGELIST = (('Fetal', 'Fetal'), ('Pre-pubescent', 'Pre-pubescent'), ('Adult', 'Adult'), ('Senescent', 'Senescent'))
PREPARATIONLIST=(('Dry ground', 'Dry ground'), ('Paraffin embedded', 'Paraffin embedded'), ('Plastic embedded', 'Plastic embedded'), ('Smear', 'Smear'), ('Whole-mount', 'Whole-mount'))
SECTIONTYPELIST=(('Coronal', 'Coronal'), ('Longtitudinal', 'Longtitudinal'), ('Sagittal', 'Sagittal'), ('Transverse', 'Transverse'))

def get_upload_path(instance, filename):
	return os.path.join("thumbs/", filename)

class Slide(models.Model):
	url = models.URLField( verbose_name="URL to slide directory", max_length=500)
	label = models.CharField( verbose_name="Label", max_length=500)
	institution = models.CharField(  verbose_name="Source Institution", max_length=500,blank=True, null=True)
	scanlevel = models.CharField( verbose_name="Magnification at which slide was scanned", max_length=500,blank=True, null=True,choices=SCANLEVELLIST)
	maxzoomlevel = models.IntegerField( verbose_name="Maximum Google Zoom Level")
	viewcount = models.IntegerField(blank=True, null=True)
	adddate = models.DateTimeField(auto_now_add=True)
	thumbnail = models.ImageField(upload_to=get_upload_path,null=True, blank=True)
	
	def __str__(self):
		if self.label: return self.label
		return self.url

	def natural_key(self):
			return (self.url)
					
	def thumbnail_path(self):
		if hasattr(settings, 'CACHED_THUMBNAILS'):
			if CACHED_THUMBNAILS:
				if self.url and not self.thumbnail:
					result = urllib.urlretrieve(self.url+"/tile_0_0_0.jpg")
					self.thumbnail.save(os.path.basename(str(self.id)+".jpg"),File(open(result[0])))
					self.save()
				return	self.thumbnail.url	
		return	self.url+"/tile_0_0_0.jpg"						

class Collection(models.Model):
	label = models.CharField(max_length=500,blank=True, null=True)
	authors =  models.ManyToManyField(User)
	slides =  models.ManyToManyField(Slide, through='CollectionSlide', related_name="collection_slides",)
	public =  models.NullBooleanField(default=True, null=True) 
	description = models.TextField(blank=True, null=True)
	category = models.CharField(max_length=500,blank=True, null=True)
	
	
	def __str__(self):
		return self.label	

class CollectionSlide(models.Model):
	slide = models.ForeignKey('Slide', on_delete=models.DO_NOTHING)
	collection = models.ForeignKey('Collection', on_delete=models.DO_NOTHING)
	label = models.CharField( verbose_name="Label", max_length=500)
	sequence = models.IntegerField(blank=True, null=True)
	author = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)
	adddate = models.DateTimeField(auto_now_add=True)
	tissue = models.CharField( verbose_name="Tissue Type",max_length=500,blank=True, null=True)
	diagnosis = models.CharField( verbose_name="Diagnosis",max_length=500,blank=True, null=True)
	stain = models.CharField( verbose_name="Stain used",max_length=500,blank=True, null=True, choices=STAINLIST)
	slidebox = models.CharField( verbose_name="Box",max_length=500,blank=True, null=True)
	slidenumber = models.CharField( verbose_name="Number",max_length=500,blank=True, null=True)
	tissuesource = models.CharField( verbose_name="Source organism",max_length=500,blank=True, null=True, choices = TISSUESOURCELIST)
	developmentalstage = models.CharField( verbose_name="Developmental Stage",max_length=500,blank=True, null=True, choices = DEVELOPMENTALSTAGELIST)
	preparation = models.CharField( verbose_name="Preparation",max_length=500,blank=True, null=True, choices = PREPARATIONLIST)
	sectiontype = models.CharField( verbose_name="Section Type",max_length=500,blank=True, null=True, choices = SECTIONTYPELIST)
# 	notes = models.ManyToManyField(Note,blank=True,  null=True)
	markers = models.ManyToManyField('SlideMarker',blank=True,  null=True, related_name='slide_markers')
	relatedslides = models.ManyToManyField('self',blank=True,  null=True)
	viewcount = models.IntegerField(blank=True, null=True)
	
	def __str__(self):
		if self.label and (self.label != ""):
			return self.label
		return self.slide.label
		
	def metadata(self):	
		return {'Tissue':self.tissue,'Diagnosis':self.diagnosis, 'Stain':self.stain, 'Box':self.slidebox, 'Number':self.slidenumber, 'Source':self.tissuesource, 'Developmental Stage':self.developmentalstage, 'Preparation':self.preparation}
	
class FavoriteSlide(models.Model):
	user = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)
	slide = models.ForeignKey('CollectionSlide', on_delete=models.DO_NOTHING)
	sequence = models.IntegerField(blank=True, null=True)
	adddate = models.DateTimeField(auto_now_add=True)
# 	notes = models.ManyToManyField("Note", null=True)
	lat = models.FloatField(blank=True, null=True)
	lng = models.FloatField(blank=True, null=True)
	zoom = models.IntegerField(blank=True, null=True)
	tile = models.CharField( verbose_name="Tile Path", max_length=500, blank=True, null=True)
	title = models.TextField(null=True)
	
	def urlparams(self):
		try:
			if self.lat:
				return "?lat="+str(self.lat)+"&lng="+str(self.lng)+"&zoom="+str(self.zoom)
		except Exception, e:
			if settings.DEBUG: print e
			return ''
		return ''

class FavoriteMarker(models.Model):
	user = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)
	marker = models.ForeignKey('SlideMarker', on_delete=models.DO_NOTHING)
	adddate = models.DateTimeField(auto_now_add=True)

class SlideMarker(models.Model):
	author = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)
	type = models.IntegerField(blank=True, null=True) 
	label = models.CharField(max_length=500,blank=True, null=True)
	html = models.TextField(null=True)
	public =  models.NullBooleanField(default=True, null=True) 
	lat = models.FloatField()
	lng = models.FloatField()
	zoom = models.IntegerField(blank=True, null=True)
	timestamp = models.DateTimeField(auto_now_add=True)
	score = models.IntegerField(default=0, null=True)
	voters =  models.ManyToManyField(User,blank=True,  null=True, related_name='marker_voters')
	original_author =  models.ForeignKey(User, null=True, related_name="orginal_user", on_delete=models.DO_NOTHING)
	deleted_by =  models.ForeignKey(User, null=True, related_name="deletor_user", on_delete=models.DO_NOTHING)