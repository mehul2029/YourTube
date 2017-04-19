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
			videoid_list = list()
			
			for doc in result:
				thumbnail_list.append(doc['videoInfo']['snippet']['thumbnails']['medium']['url'])
				title_list.append(doc['videoInfo']['snippet']['title'])
				views_list.append(doc['videoInfo']['snippet']['title']['statistics'])
				videoid_list.append(doc['videoInfo']['id'])

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
													'desc_list' : desc_list,
													'views_list' : views_list,
													'videoid_list' : videoid_list})

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

def recommendation(vid, username):
	# Give recommendation based on user and current video
	obj = Recommendations()
	v = VideoInfo()
	records = obj.nearest_neighbours(vid, k=7)
	refined_records = obj.userhistory(username,records)

	thumbnail_list = list()
	title_list = list()
	desc_list = list()
	views_list = list()
	videoid_list = list()

	for i in range(0, len(refined_records)):
		videoid = refined_records['Neighbor'][i]
		doc = v.get_video(videoid)
		
		thumbnail_list.append(doc['videoInfo']['snippet']['thumbnails']['medium']['url'])
		title_list.append(doc['videoInfo']['snippet']['title'])
		views_list.append(doc['videoInfo']['statistics']['viewCount'])
		videoid_list.append(doc['videoInfo']['id'])

		desc = doc['videoInfo']['snippet']['description'].split(' ')
		desc = desc[0:10]
		temp = ''
		for i in desc:
			temp = temp + i + ' '
		desc = temp[0:50]
		if (len(temp) > len(desc)):
			desc = desc + ' ...'

		desc_list.append(desc)

	return (thumbnail_list, title_list, desc_list, views_list, videoid_list)