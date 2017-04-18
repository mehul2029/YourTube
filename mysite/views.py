from django.template import Template, Context
from django.http import HttpResponse  
import datetime
from django.shortcuts import render

def hello(request):
	return HttpResponse("Hello world")

def homepage(request):
	return HttpResponse("Homepage")

def current_datetime(request):
	date_time = datetime.datetime.now()

	# t = Template("<html><body>It is now {{ current_date }}.</body></html>")
	# html = t.render(Context({'current_date': date_time}))
	# return HttpResponse(html)

	return render(request, 'test.html', {'current_date': date_time})