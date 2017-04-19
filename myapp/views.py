from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from database.api import *
from engine import Recommendations
import pandas as pd


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

def home(request):
	return render(request, 'myapp/home.html')	

def search(request):
	if 'q' in request.POST:
		if len(request.POST['q']):
			v = VideoInfo()
			result = v.search_text(request.POST['q'])
			q = request.POST['q']

			videos = list()
			
			for doc in result:
				video = {}
				video['thumbnail'] =  doc['videoInfo']['snippet']['thumbnails']['default']['url']
				video['title'] = doc['videoInfo']['snippet']['title']
				video['view'] = doc['videoInfo']['statistics']['viewCount']
				video['id'] = doc['videoInfo']['id']

				desc = doc['videoInfo']['snippet']['description'].split(' ')
				desc = desc[0:25]
				temp = ''
				for i in desc:
					temp = temp + i + ' '
				desc = temp[0:120]
				if (len(temp) > len(desc)):
					desc = desc + ' ...'

				video['desc'] = desc
				videos.append(video)			
			count = len(videos)

			return render(request, 'myapp/result.html', {	'q' : q,
															'count' : count,
															'videos' : videos})

	return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def login_view(request):
	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=username, password=password)
	if user is not None:
		if user.is_active:
			login(request, user)
			return render(request, 'home.html', {'firstname':user.first_name,
				'lastname':user.last_name, 'username':user.username})
		else:
			error = "Your account has been disabled. Use a different account. "
			return render (request, 'login.html', {'error':error})
	else:
		error = "Incorrect username or password provided."
		return render (request, 'login.html', {'error':error})

# Isn't really used. Using django.contrib.auth.views.logout instead.
def logout_view(request):
	logout(request)
	return redirect('/login/')

def on_search_click(request):
	# Will update userinfo table, historytags.
	a = 0

def view(request, videoId):
	a=0
