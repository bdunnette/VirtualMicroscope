from django.contrib import admin
from models import Slide,Collection,CollectionSlide

class SlideAdmin(admin.ModelAdmin):
    exclude = ('viewcount',)
admin.site.register(Slide, SlideAdmin)

class CollectionSlideAdmin(admin.ModelAdmin):
    exclude = ('viewcount',)
admin.site.register(CollectionSlide, CollectionSlideAdmin)

class CollectionAdmin(admin.ModelAdmin):
	filter_horizontal = ('authors',)
admin.site.register(Collection, CollectionAdmin)
