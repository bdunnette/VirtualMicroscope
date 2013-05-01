from django.template.loader import get_template
from django.template import Context, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q, Sum, Avg, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.core import serializers
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404,render_to_response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.cache import cache_page
 
import re
import datetime

try:
	import json as json
except:	
	import simplejson as json

from string import replace
from models import *
from forms import *

#test for variables from settings.py and provide defaults if they are missing
FOLLOWS_ACTIVE=getattr(settings, 'FOLLOWS_ACTIVE', False)
FOLLOW_EXPIRE=getattr(settings, 'FOLLOW_EXPIRE', 180) #Minutes
EXAMS_ACTIVE=getattr(settings, 'EXAMS_ACTIVE', False)
COMM_MARKER_EXPIRE=getattr(settings, 'COMM_MARKER_EXPIRE', 300) #Days
SLIDES_PER_PAGE=getattr(settings, 'SLIDES_PER_PAGE', 10)
API_KEY=getattr(settings, 'API_KEY', None)
URL_ROOT=getattr(settings, 'URL_ROOT', '')
GAKEY=getattr(settings, 'GAKEY', None)
REQ_LOGIN=getattr(settings, 'REQ_LOGIN', False)

if FOLLOWS_ACTIVE:
	from nyuvmfollows.models import Follow

##For debugging purposes
def masquerade(request,username):
	if (settings.DEBUG) or request.user.is_superuser:
		"""
		Log in a user without requiring credentials (using ``login`` from``django.contrib.auth``, first finding a matching backend). 
		THIS IS FOR DEBUGGING ONLY
		"""
		from django.contrib.auth import load_backend, login
		try:
			#user = User.objects.get(username=request.POST['userid'])
			user = User.objects.get(username=username)
		
			if not hasattr(user, 'backend'):
				for backend in settings.AUTHENTICATION_BACKENDS:				
					if user == load_backend(backend).get_user(user.pk):
						user.backend = backend
						break
			
			if hasattr(user, 'backend'):
				login(request, user)
				request.session['_auth_user_backend'] = 'django_cas.backends.CASBackend'
		except:
			messages.error(request, 'That user does not exist')
			return HttpResponseRedirect(URL_ROOT+"/")		  
	return HttpResponseRedirect(URL_ROOT+"/")		

#Utility
def generate(request,template_name,template_values={}):
	#the base template generator function with some default data
	follows = None
	followtemplate = None
	if request.user.is_authenticated():
		if FOLLOWS_ACTIVE:
			follows = Follow.objects.filter(active=True,starttime__gt=datetime.datetime.now()- datetime.timedelta(minutes=FOLLOW_EXPIRE))
			followtemplate = "follow/follow_menu.html"
		collections = Collection.objects.all().order_by('category','label')
	else:
		collections = Collection.objects.filter(public=True).order_by('category','label')

	collections = collections.values('category','label','id')


	values = {
			'URL_ROOT':URL_ROOT,
			'user': request.user,
			'login_url':settings.LOGIN_URL,
			'logout_url':settings.LOGOUT_URL,		
			'collections':collections,
			'GAKEY':GAKEY,
			'follows':follows,
			'FOLLOWS_ACTIVE':FOLLOWS_ACTIVE,
			'followtemplate':followtemplate,
			'EXAMS_ACTIVE':EXAMS_ACTIVE,
			
			}	
			
	values.update(template_values)
	t = get_template(template_name)
	return HttpResponse(t.render(RequestContext(request, values)))

def MainPage(request): 
	return generate(request,'index.html', {})   

#Viewing Views
@cache_page(30)
def ViewCollection(request, collectionid): 
	#Check for heavy system load mode - require authentication
	if (request.user.is_authenticated()==False) and REQ_LOGIN:
		messages.info(request, 'The system is currently experiencing heavy traffic.<br>Log in with your NYULMC account to view slides.')
		return HttpResponseRedirect(URL_ROOT+"/")	

	collection = get_object_or_404(Collection, pk=collectionid)
	slides = CollectionSlide.objects.filter(collection=collection).order_by('sequence')
	paginator = Paginator(slides, SLIDES_PER_PAGE) # Show XX slides per page
	
	page = request.GET.get('page')
	try:
		slidepage = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		slidepage = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		slidepage = paginator.page(paginator.num_pages)	
	return generate(request,'collection.html', {"collection":collection,'slides':slidepage})   

def ViewSlide(request,collectionslideid,compact = False,transcriptid=None): 

	if compact=='compact': compact=True

	#url variables, if any
	m = request.GET.get('m', '0')
	lat  = request.GET.get('lat', '0')
	lng  = request.GET.get('lng', '0')
	zoom  = request.GET.get('zoom', '2')
	page = request.GET.get('p', '1')	

	related_slides = None
	if collectionslideid: 
		collectionslide = get_object_or_404(CollectionSlide, pk=collectionslideid)

		try:
			collectionslide.collection
		except:
			messages.info(request, 'That slide has been removed.')
			return HttpResponseRedirect(URL_ROOT+"/")	


		#Check for heavy system load mode - require authentication
		if (request.user.is_authenticated()==False) and REQ_LOGIN:
			messages.info(request, 'The system is currently experiencing heavy traffic.<br>Log in with your NYULMC account to view slides.')
			return HttpResponseRedirect(URL_ROOT+"/")	

		#security check for collection publicity
		if ((request.user.is_authenticated()==False) and (collectionslide.collection.public == False)):
			messages.error(request, 'Log in with your NYULMC account to access that slide.')
			return HttpResponseRedirect(URL_ROOT+"/")	

		if collectionslide.viewcount:
			collectionslide.viewcount = collectionslide.viewcount + 1
		else:
			collectionslide.viewcount = 1
		collectionslide.save()
		# As per RS, matching should be across collections
		related_slides = CollectionSlide.objects.filter(slidenumber=collectionslide.slidenumber, slidenumber__isnull=False).exclude(slidenumber="").order_by("id")
	if 'follow_id' in request.session:
		try:
			follow = Follow.objects.filter(id=request.session['follow_id'], active=True)[0]
		except:
			follow = None
	else:
		follow = None	

	if FOLLOWS_ACTIVE:
		container_template = "follow/follow_container.html" 
		transcript_template = "follow/transcript_container.html"
	else:
		container_template = None
		transcript_template = None	
		
	transcript = None
	if transcriptid:
		transcript = Follow.objects.get(id=transcriptid)

	return generate(request,'viewer.html', {
		"slide":collectionslide.slide,
		"collectionslide":collectionslide,
		'related_slides':related_slides,
		'compact':compact, 
		'follow':follow,
		'transcript':transcript,
		'lat':lat,
		'lng':lng,		
		'zoom':zoom,
		'm':m,
		'page':page,
		'API_KEY':API_KEY,
		'container_template':container_template,
		'transcript_template':transcript_template
		})  

def SlideMetaData(request,collectionslideid,currentslideid=None,view=None):
	if view:
		view = get_object_or_404(FavoriteSlide, pk=collectionslideid)
		collectionslide = view.slide
	else:
		collectionslide = get_object_or_404(CollectionSlide, pk=collectionslideid)

	if request.user.is_authenticated():
		try:
			myslide = FavoriteSlide.objects.filter(user=request.user, lat__isnull=True,slide=collectionslide)[0]	
		except:
			myslide = None	
	else:
		myslide = None

	favspage = getattr(request.GET, 'f', None)
	t = get_template("includes/slide_metadata.html")	
	c = Context({"s":collectionslide,'myslide':myslide,'URL_ROOT':URL_ROOT,'user': request.user,'currentslide':currentslideid,'view':view,'favspage':favspage})
	return HttpResponse(t.render(c))	
	
@login_required
def ViewUncategorizedSlide(request,slideid,compact = False): 
	if compact=='compact': compact=True

	#url variables, if any
	m = request.GET.get('m', '0')
	lat  = request.GET.get('lat', '0')
	lng  = request.GET.get('lng', '0')
	zoom  = request.GET.get('zoom', '2')	
	
	return generate(request,'viewer.html', {
		"slide":Slide.objects.get(id=slideid),
		"collectionslide":None,
		'compact':compact, 
		'follow':None,
		'lat':lat,
		'lng':lng,		
		'zoom':zoom,
		'm':m,
		'API_KEY':API_KEY		
		})  

#Markers
@login_required
def CreateMarker(request, collectionslideid):
	collectionslide = CollectionSlide.objects.get(id=collectionslideid)		
	try:
		if request.method == 'POST':
			newmarker = SlideMarker()
			newmarker.author = request.user
			newmarker.lat = request.POST["lat"]
			newmarker.lng = request.POST["lng"]
			newmarker.zoom = request.POST["zoom"]
			
			#community markers are private by default
			if (request.user not in collectionslide.collection.authors.all()):
				newmarker.public = False
			
			newmarker.save()
			#add this newly crated marker to the slide object
			collectionslide.markers.add(newmarker)
	except Exception, e:
		if settings.DEBUG: print e

	return HttpResponse(newmarker.id)   

@login_required
def DeleteMarker(request, slidemarkerid):
	slidemarker = SlideMarker.objects.get(id = slidemarkerid)
	if (request.user in slidemarker.slide_markers.all()[0].collection.authors.all()) or request.user.is_superuser or (request.user == slidemarker.author):
		#delete all related favorites of this marker
		FavoriteMarker.objects.filter(marker=slidemarker).delete()
		slidemarker.delete()		
		
	return HttpResponse()

@login_required
def AdoptMarker(request, slidemarkerid):
	slidemarker = SlideMarker.objects.get(id = slidemarkerid)
	if (request.user in slidemarker.slide_markers.all()[0].collection.authors.all()) or request.user.is_superuser:
		slidemarker.original_author = slidemarker.author
		slidemarker.author = request.user
		slidemarker.save()
	return HttpResponse()

@login_required
def EditMarkerForm(request, slidemarkerid):
	slidemarker = SlideMarker.objects.get(id = slidemarkerid)
	return generate(request,'includes/markereditor.html', {"slidemarker":slidemarker})   

@require_POST
def EditMarkerSubmit(request, slidemarkerid):
	
	
	print request.POST
	
	slidemarker = SlideMarker.objects.get(id = slidemarkerid)
	if (request.user in slidemarker.slide_markers.all()[0].collection.authors.all()) or request.user.is_superuser or (request.user == slidemarker.author):	
		slidemarker.type = request.POST["markertypeinput"]
		slidemarker.label = request.POST["markerlabelinput"]
		slidemarker.html = request.POST["markerhtmlinput"]
	slidemarker.save()
	return HttpResponse()

@login_required
@require_POST
def EditMarkerPosition(request, slidemarkerid):
	slidemarker = SlideMarker.objects.get(id = slidemarkerid)
	if (request.user in slidemarker.slide_markers.all()[0].collection.authors.all()) or request.user.is_superuser or (request.user == slidemarker.author):
		slidemarker.lat = request.POST["lat"]
		slidemarker.lng = request.POST["lng"]
		slidemarker.zoom = request.POST["zoom"]
		slidemarker.save()
	return HttpResponse()

def ToggleMarkerPublicity(request, slidemarkerid):
	slidemarker = SlideMarker.objects.get(id = slidemarkerid)
	if (request.user in slidemarker.slide_markers.all()[0].collection.authors.all()) or request.user.is_superuser or (request.user == slidemarker.author):	
		if slidemarker.public:
			slidemarker.public = False
		else:
			slidemarker.public = True
		slidemarker.save()		
	return HttpResponse(slidemarker.public)  

@login_required
@require_POST
def VoteOnMarker(request, slidemarkerid,vote):
	slidemarker = SlideMarker.objects.get(id = slidemarkerid)
	#existing vote?
	if request.user not in slidemarker.voters.all():
		if int(vote) == 1:
			slidemarker.score = slidemarker.score+1
		else:
			slidemarker.score-=1
		slidemarker.voters.add(request.user)
		slidemarker.save()		
	return HttpResponse()

def SerializeMarkers(request, collectionslideid):
	collectionslide = CollectionSlide.objects.get(id=collectionslideid)
	try:
		collectionslide.collection
	except:
		return HttpResponse()
	
	themarkers = collectionslide.markers.all().filter(deleted_by__isnull=True)	
	if request.user.is_authenticated(): 
		themarkers = themarkers.exclude(~Q(author = request.user),public=False) #exclude markers marked private
		themarkers = themarkers.exclude(~Q(author = request.user),~Q(author__in=collectionslide.collection.authors.all()), timestamp__lt=datetime.datetime.now()- datetime.timedelta(days=COMM_MARKER_EXPIRE)) #exclude community markers that are over COMM_MARKER_EXPIRE threshhold
		themarkers = themarkers.exclude(~Q(author = request.user),score__lt=-4) #exclude markers that have a score of less than -4
		themarkers = themarkers.exclude(~Q(author = request.user),label__isnull=True)
	else:
		themarkers = themarkers.exclude(public=False)
		themarkers = themarkers.exclude(label__isnull=True)
		themarkers = themarkers.exclude(~Q(author__in=collectionslide.collection.authors.all())) #exclude ALL community markers
		
	return HttpResponse(serializers.serialize("json", themarkers))

def MarkerInfoWindow(request, slidemarkerid):
	slidemarker = get_object_or_404(SlideMarker, pk=slidemarkerid)

	alreadyfavorite=False
	expired=False
	editable = False
	votable = False
	facultymarker = False
	deletable = False
	adoptable = False
	
	if request.user.is_authenticated():
		
		authors = slidemarker.slide_markers.all()[0].collection.authors.all()
		
	
		if FavoriteMarker.objects.filter(user=request.user,marker=slidemarker):
			alreadyfavorite=True
		#if its a student marker and is expired	
		if (slidemarker.timestamp < (datetime.datetime.now()- datetime.timedelta(days=COMM_MARKER_EXPIRE))) and (request.user not in authors):
			expired=True

		#if its score is too low
		if slidemarker.score <-4:
			expired=True
			
		if (request.user == slidemarker.author):
			editable=True
		
		#if its a faculty marker, its not votable
		if (slidemarker.author not in authors):
			# and if user didnt already vote
			if request.user not in slidemarker.voters.all():
				votable=True
		else:
			facultymarker = True
			
		#collection faculty and superusers can edit any faculty markers, but not student markers
		if (slidemarker.author in authors) and ((request.user in authors) or (request.user.is_superuser)):
			editable=True
			
		if (request.user in authors) or request.user.is_superuser or (request.user == slidemarker.author):
			deletable=True			

		#collection faculty and superusers can adopt student markers
		if ((request.user in authors) or request.user.is_superuser) and (slidemarker.author not in authors):
			adoptable=True						
			
	return generate(request,'includes/infowindow.html', {"slidemarker":slidemarker,"alreadyfavorite":alreadyfavorite,"expired":expired,"editable":editable,"deletable":deletable,"votable":votable,"facultymarker":facultymarker,"adoptable":adoptable})   

#Authoring Views
@login_required
def EditCollection(request, collectionid): 
	collection = Collection.objects.get(id=collectionid)
	if (request.user in collection.authors.all()) or request.user.is_superuser:
		slides = CollectionSlide.objects.filter(collection=collection).order_by('sequence')
		#availableslides = Slide.objects.all().exclude(id__in=slides.values_list('slide', flat=True)).order_by('label')
		
	else:
		raise PermissionDenied	
	#return generate(request,'author/editcollection.html', {"collection":collection,'slides':slides,'availableslides':availableslides})   
	return generate(request,'author/editcollection.html', {"collection":collection,'slides':slides})   

@login_required	
def EditCollectionMembership(request,collectionid,action,slideid=None):
	collection = Collection.objects.get(id=collectionid)
	if (request.user in collection.authors.all()) or request.user.is_superuser:
		if slideid: slide = Slide.objects.get(id=slideid)
		if action == "add":
			#by default, if a slide is already in another collection, we will copy its metadata over too. 
			otherinstances = CollectionSlide.objects.filter(slide=slide).order_by('-pk')
			newcollectionslide = CollectionSlide(slide=slide, collection=collection, label = slide.label, sequence = CollectionSlide.objects.filter(collection=collection).count()+1,author=request.user)
			if otherinstances:
				#copy metadata
				newcollectionslide.label = otherinstances[0].label
				newcollectionslide.tissue = otherinstances[0].tissue
				newcollectionslide.diagnosis = otherinstances[0].diagnosis
				newcollectionslide.stain = otherinstances[0].stain
				newcollectionslide.slidebox = otherinstances[0].slidebox
				newcollectionslide.slidenumber = otherinstances[0].slidenumber
				newcollectionslide.tissuesource = otherinstances[0].tissuesource
				newcollectionslide.developmentalstage = otherinstances[0].developmentalstage
				newcollectionslide.preparation = otherinstances[0].preparation
				newcollectionslide.sectiontype = otherinstances[0].sectiontype
			newcollectionslide.save()
		elif action == "del":
			#Since this slide will no longer exist within this program, we will need to also remove it from everyone's favorites list
			FavoriteSlide.objects.filter(slide=CollectionSlide.objects.filter(collection=collection,slide=slide)).delete()		
			CollectionSlide.objects.filter(collection=collection,slide=slide).delete()
		elif action == "reorder":	
			if request.method == 'POST': 
				counter = 0
				for item in request.POST['data'].split("&"):
					try:
						thiscollectionslide = CollectionSlide.objects.get(id=int(item.split("=")[1]))
						thiscollectionslide.sequence=counter
						thiscollectionslide.save()
					except:
						thiscollectionslide = None
						if settings.DEBUG: print 'slide not found while reordering.  ID was: ' + str(item)
					counter += 1
	else:
		raise PermissionDenied					
	return HttpResponseRedirect(URL_ROOT+'/editcollection/'+str(collection.id)+'/')

@login_required
def EditCollectionSlide(request, collectionslideid): 
	collectionslide = CollectionSlide.objects.get(id=collectionslideid)		
	if (request.user in collectionslide.collection.authors.all()) or request.user.is_superuser:
		if request.method == 'POST':
			formset = CollectionSlideForm(request.POST, instance=collectionslide)
			if formset.is_valid():
				formset.save()
				return HttpResponseRedirect(URL_ROOT+'/editcollection/'+str(collectionslide.collection.id)+'/')
				
		else:
			formset = CollectionSlideForm(instance=collectionslide)
	else:
		raise PermissionDenied	
		    	
	return generate(request,'author/editcollectionslide.html', {
		"formset": formset,	
		"collectionslide":collectionslide
	})   
	
#FavoriteSlides
@login_required
def ViewFavoriteSlides(request):
	slides = FavoriteSlide.objects.filter(user = request.user, lat__isnull=True).order_by('adddate')
	views = FavoriteSlide.objects.filter(user = request.user, lat__isnull=False).order_by('adddate')
 	marker_slides = CollectionSlide.objects.filter(markers__author= request.user,markers__deleted_by__isnull=True).distinct()
 	marker_favorites = FavoriteMarker.objects.filter(user= request.user,marker__deleted_by__isnull=True)

	if FOLLOWS_ACTIVE:
		member =  request.user.follow_members.all()
		leader =  Follow.objects.filter(author = request.user)
		follows = member | leader
	else:
		follows = None

	return generate(request,'myslides.html', {
		"favspage":True,
		"slides":slides,
		"views":views,
		"myfollows":follows,
		"marker_slides":marker_slides,
		"marker_favorites":marker_favorites,
	})   

@login_required
def EditFavorites(request,action,selectedid=None):
	if action == "add":
		collectionslide = CollectionSlide.objects.get(id=selectedid)
		#only if not already there
		try:
			newmyslide = FavoriteSlide.objects.filter(user=request.user, lat__isnull=True,slide=collectionslide)[0]
		except:	
			newmyslide = FavoriteSlide(user=request.user, slide=collectionslide, sequence = FavoriteSlide.objects.filter(user=request.user).count()+1)
		newmyslide.save()
		return HttpResponse('<div class="alert alert-success">Added to favorites!</div>')
		#return HttpResponseRedirect(URL_ROOT+'/myslides/')
	elif action == "addview":
		collectionslide = CollectionSlide.objects.get(id=selectedid)
		newmyslide = FavoriteSlide(user=request.user, slide=collectionslide, sequence = FavoriteSlide.objects.filter(user=request.user).count()+1)
		newmyslide.lat=request.POST["lat"]
		newmyslide.lng = request.POST["lng"]
		newmyslide.zoom = request.POST["zoom"]
		newmyslide.tile = collectionslide.slide.url + "/" + request.POST["tile"]
		newmyslide.title = request.POST["title"]	
		newmyslide.save()
		return HttpResponse()
		
	elif action == "addmarker":
		newmarker = FavoriteMarker(user=request.user, marker = SlideMarker.objects.get(id=request.POST["markerid"]))
		newmarker.save()
		return HttpResponse()	
		
	elif action == "del":
		fav = FavoriteSlide.objects.get(id=int(selectedid))
		if request.user == fav.user:
			fav.delete()
		return HttpResponse('<div class="alert alert-success">Removed from favorites!</div>')
		#return HttpResponseRedirect(URL_ROOT+'/myslides/')
	elif action == "delmarker":
		fav = FavoriteMarker.objects.get(user=request.user,id=selectedid)
		if request.user == fav.user:
			fav.delete()
		return HttpResponseRedirect(URL_ROOT+'/myslides/')
	return HttpResponse()	
	

#Search
def normalize_query(query_string,findterms=re.compile(r'"([^"]+)"|(\S+)').findall,normspace=re.compile(r'\s{2,}').sub):
    ''' Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example:
        
        >>> normalize_query('  some random  words "with   quotes  " and   spaces')
        ['some', 'random', 'words', 'with quotes', 'and', 'spaces']
    
    '''
    return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)] 

def get_query(query_string, search_fields):
    ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    
    '''
    query = None # Query to search for every search term        
    terms = normalize_query(query_string)
    for term in terms:
        or_query = None # Query to search for a given term in each field
        for field_name in search_fields:
            q = Q(**{"%s__icontains" % field_name: term})
            if or_query is None:
                or_query = q
            else:
                or_query = or_query | q
        if query is None:
            query = or_query
        else:
            query = query & or_query
    return query	

def Search(request):
    query_string = ''
    found_slides = None
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        entry_query = get_query(query_string, ['label','tissue','diagnosis','stain','slidebox','slidenumber','tissuesource','developmentalstage','preparation','sectiontype'])
        found_slides = CollectionSlide.objects.filter(entry_query)
    return generate(request, 'searchresults.html',{ 'query_string': query_string, 'found_slides': found_slides })	

@login_required    
def AuthorSearch(request,addtotype,addtoid):
    query_string = ''
    found_entries = None
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        entry_query = get_query(query_string, ['label','tissue','diagnosis','stain','slidebox','slidenumber','tissuesource','developmentalstage','preparation','sectiontype'])
        found_slides1 = CollectionSlide.objects.filter(entry_query).values_list('slide', flat=True)
        entry_query = get_query(query_string, ['label','url','institution'])
        found_slides2 =  Slide.objects.filter(entry_query).values_list('id', flat=True)
        found_slides = Slide.objects.filter(id__in = list(found_slides1)+list(found_slides2))
        
        exam = None
        
        if addtotype=="collection": 
        	thecollection = Collection.objects.get(id=int(addtoid))       
        	found_slides = found_slides.exclude(id__in=thecollection.slides.all().values_list('id', flat=True)).order_by('label')

        if addtotype=="exam": 
        	if EXAMS_ACTIVE:
				exam = ExamQuestion.objects.get(id=int(addtoid)).examquestions.all()[0]     
				found_slides = found_slides.exclude(id__in=ExamQuestion.objects.get(id=int(addtoid)).slides.all().values_list('id', flat=True)).order_by('label')


        return generate(request, 'includes/slide_list_search.html',{ 'query_string': query_string, 'found_slides': found_slides, 'addtoid':addtoid,'addtotype':addtotype,'exam':exam })
    else:
    	return HttpResponse()
          
#ADMIN
def RebuildSlideThumbnails(request):
	if (request.user.is_authenticated() and request.user.is_superuser):
		slides = Slide.objects.all()
		for s in slides:
			if s.url:
				file = os.path.join(settings.MEDIA_ROOT,"thumbs",str(s.id)+".jpg")
				if not os.path.exists(file):
					#print 'not found, retrieving'
					result = urllib.urlretrieve(s.url+"/tile_0_0_0.jpg")
					s.thumbnail.save(os.path.basename(str(s.id)+".jpg"),File(open(result[0])))
					s.save()
				else:
					#use the file path found
					s.thumbnail= os.path.join("thumbs",str(s.id)+".jpg")
					s.save()
	return HttpResponse("process complete")