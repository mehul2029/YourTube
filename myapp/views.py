from django.shortcuts import render
from database.api import *
from django.http import HttpResponse


def index(request):
	return render(request, 'myapp/index.html')	

def test_func(request):
	v = VideoInfo()
	res = v.search_text("birth")
	s = ''
	for d in res:
		s += d['videoInfo']['snippet']['title']
		s += '$$'
	return HttpResponse("%s." % s)

def bootstrap(request):
	return render(request, 'myapp/bootstrap.html')	

def search(request):
	return render(request, 'myapp/search.html')	