from django.template import Library
from django.template.defaultfilters import stringfilter
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from nyuvm.models import SlideMarker

register = Library()

@register.filter
@stringfilter
def customrange(value, arg):
	return_list =[]
	if value:
		f=0.0
		while f <= int(float(value)):
			return_list.append(float(f))
			f = f + 0.5
	return return_list
	
