from django.contrib import admin
from models import Slide,Collection,CollectionSlide, SlideMarker

class SlideAdmin(admin.ModelAdmin):
    exclude = ('viewcount',)
    list_display = ('label', 'url',)
admin.site.register(Slide, SlideAdmin)

class CollectionSlideAdmin(admin.ModelAdmin):
    exclude = ('viewcount',)
    list_display = ('label', 'slide', 'collection',)
admin.site.register(CollectionSlide, CollectionSlideAdmin)

class CollectionAdmin(admin.ModelAdmin):
	filter_horizontal = ('authors',)
admin.site.register(Collection, CollectionAdmin)

class SlideMarkerAdmin(admin.ModelAdmin):
    exclude = ('score', 'voters',)
admin.site.register(SlideMarker, SlideMarkerAdmin)
