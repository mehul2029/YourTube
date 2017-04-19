from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages

from database.api import VideoInfo

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
	if q in request.GET:
		if len(request.GET['q']):
			v = VideoInfo()
			result = v.search_text(request.GET['q'])
			
			thumbnail_list = list()
			title_list = list()
			desc_list = list()
			views_list = list()
			
			for doc in result:
				thumbnail_list.append(doc['videoInfo']['snippet']['thumbnails']['medium']['url'])
				title_list.append(doc['videoInfo']['snippet']['title'])
				views_list.append(doc['videoInfo']['snippet']['title']['statistics'])

				desc = doc['videoInfo']['snippet']['title'].split(' ')
				desc = desc[0:10]
				temp = ''
				for i in desc:
					temp = temp + i + ' '
				desc = temp[0:50]
				if (len(temp) > len(desc)):
					desc = desc + ' ...'

				desc_list.append(desc)

			return render(request, 'result.html', {'thumbnail_list' : thumbnail_list, 
													'title_list' : title_list,
													'desc_list' : desc_list
													'views_list' : views_list})

	return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
