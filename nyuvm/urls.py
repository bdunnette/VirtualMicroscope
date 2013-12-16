# Uncomment the following line if using Django <= 1.5
#from django.conf.urls.defaults import *
# Uncomment the following line if using Django >= 1.6
from django.conf.urls import *

from nyuvm.views import *

urlpatterns = patterns('',
		#authoring
		(r'^u/(\d*)/(.*)/', ViewUncategorizedSlide),		
		(r'^masquerade/(.*)/', masquerade),		

		#Collections		
		(r'^collection/(\d*)/', ViewCollection),	
		(r'^editcollection/(\d*)/(.*)/(\d*)/', EditCollectionMembership),		
		(r'^editcollection/(\d*)/(.*)/', EditCollectionMembership),		
		(r'^editcollection/(\d*)/', EditCollection),		
		(r'^editcollectionslide/(\d*)/', EditCollectionSlide),				
		
		#Myslides - student personal slide boxes
		(r'^myslides/', ViewFavoriteSlides),	
		(r'^editmyslides/(.*)/(\d*)/', EditFavorites),		
		(r'^editmyslides/(.*)/', EditFavorites),		
		
		#Viewer - regular and minimalistic version for embedding and preview
		(r'^v/(\d*)/(.*)/', ViewSlide),		
		(r'^v/(\d*)/', ViewSlide),		
		(r'^m/(\d*)/(\d*)/', SlideMetaData),				
		(r'^m/(\d*)/', SlideMetaData),
		(r'^f/(\d*)/', SlideMetaData, {'view': True}),

		#Markers
		(r'^addmarker/(\d*)/', CreateMarker),		
		(r'^serializemarkers/(\d*)/', SerializeMarkers),		
		(r'^markercontent/(\d*)/', MarkerInfoWindow),		
		(r'^editmarkerform/(\d*)/', EditMarkerForm),		
		(r'^editmarkerposition/(\d*)/', EditMarkerPosition),		
		(r'^voteonmarker/(\d*)/(\d*)/', VoteOnMarker),
		(r'^editmarkersubmit/(\d*)/', EditMarkerSubmit),		
		(r'^deletemarker/(\d*)/', DeleteMarker),		
		(r'^adoptmarker/(\d*)/', AdoptMarker),		
		(r'^togglemarkerpublicity/(\d*)/', ToggleMarkerPublicity),		
	
		#Admin
		(r'^rebuildslidethumbnails/', RebuildSlideThumbnails),
		
		#search
		(r'^search/', Search),	
		(r'^authorsearch/(.*)/(\d*)/', AuthorSearch),	

		#home page
		(r'^$', MainPage),
	)
