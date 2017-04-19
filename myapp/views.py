from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import authenticate as authen
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.decorators import login_required
import logging

#from django.forms import LoginForm

from engine.spellcheck import *
from database.api import *
from engine.recommend import Recommendations
import pandas as pd

# Get an instance of a logger
logger = logging.getLogger('')

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

@login_required
def home(request):
	return render(request, 'myapp/home.html')

def search(request):
	if 'q' in request.POST:
		if len(request.POST['q'])>0:
			# Check if suggestion is needed to be given
			q = request.POST['q']
			suggestion = suggest(q)
			text = ""
			if (suggestion != q):
				text = suggestion
			v = VideoInfo()
			result = v.search_text(q)
			videos = list()
			
			for doc in result:
				videos.append(helper_get_content(doc))
			count = len(videos)

			return render(request, 'myapp/result.html', {	'q' : q,
															'count' : count,
															'videos' : videos,
															'suggestion' : text})
	if request.META.get('HTTP_REFERER'):
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		return redirect('/home/')

def bootstrap(request):
	return render(request, 'myapp/bootstrap.html')

def signup(request):
	if request.method == "GET":
		return redirect('login')

	if request.method == "POST":
		#form = LoginForm(request.POST)
		if True: #form.is_valid():
			username = request.POST['username']
			password = request.POST['password']
			first_name = request.POST['first_name']
			last_name = request.POST['last_name']
			user = authen(username=username, password=password)
			if user is None:
				user = User.objects.create_user(username=username, email=username, password=password, first_name=first_name, last_name=last_name)
				login(request, user)
				return render(request, 'myapp/home.html')
			else:
				error = 'User already exists'
				return render(request, 'myapp/login.html', { 'error': 'Invalid username' })
		else:
			error = 'Something went wrong! Please try again.'
			return render(request, 'myapp/login.html', { 'error': 'Invalid username' })

def login_view(request):
	if request.method == "GET":
		return render(request, 'myapp/login.html')
	if request.method == "POST":
		#form = LoginForm(request.POST) # A form bound to the POST data
		if True:	#form.is_valid(): # All validation rules pass
			username = request.POST['username']
			password = request.POST['password']
			user = authen(username=username, password=password)
			if user is not None:
				# Redirect to a success page.
				login(request, user)
				return render(request, 'myapp/home.html')
			else:
				error = 'Invalid login'
				return render(request, 'myapp/login.html', { 'error': 'Invalid username' })
		else:
			error = 'Something went wrong! Please try again.'
			return render(request, 'myapp/login.html', { 'error': 'Invalid username' })

# def login_view(request):
# 	username = request.POST['username']
# 	password = request.POST['password']
# 	user = authen(user=username, password=password)
# 	if user is not None:
# 		if user.is_active:
# 			login(request, user)
# 			return render(request, 'home.html', {'firstname':user.first_name,
# 				'lastname':user.last_name, 'username':user.username})
# 		else:
# 			error = "Your account has been disabled. Use a different account. "
# 			return render (request, 'login.html', {'error':error})
# 	else:
# 		error = "Incorrect username or password provided."
# 		return render (request, 'login.html', {'error':error})

# Isn't really used. Using django.contrib.auth.views.logout instead.
def logout_view(request):
	logger.info('in logout')
	logout(request)
	return redirect('login')

def db_on_search_click(videoid, username):
	# Update historytags
	tag_list = VideoInfo().get_tags(videoid)
	obj = HistoryTags()
	for tag in tag_list:
		obj.upsert_tag(username, tag, count=1)

	# Update userinfo table
	UserInfoDB().upsert(username, videoid, likes=0,dislikes=0)

def db_on_recommendation_click(request):
	# Will increase the weight between the two videos. That is, the two videos watched
	# sequentially.
	g = VideosGraph()
	g.update_weight(vid1, vid2, weight=1.2)

def view(request, videoId):
	db_on_search_click(videoId, request.user.username)
	videos = recommendation(videoId, request.user.username)
	v = VideoInfo()
	currentvid = v.get_video(videoId)
	v = Comments()
	comment_list = v.get_comments(videoId)
	u = UserInfoDB()
	like = u.is_like()
	return render(request, 'myapp/view.html', { 'currentvid' : currentvid,
												'comment_list' : comment_list,
												'videos' : videos,
												'like' : like})

def suggest(query):
	# Will return the original query or the suggestion query accordingly.
	listify = [x for x in query.split(' ')]
	reco = [correction(x) for x in listify]
	common_words = set(listify).intersection(set(reco))
	if len(common_words)!=len(listify):
		# Aw, snap. You can't type it seems.
		new_query = " ".join(reco)
		return new_query
	return query

def recommendation(vid, username):
	# Give recommendation based on user and current video
	obj = Recommendations()
	v = VideoInfo()
	records = obj.nearest_neighbours(vid, k=7)
	refined_records = obj.userhistory(username,records)

	videos = list()

	for i in range(0, len(refined_records)):
		videoid = refined_records['Neighbor'][i]
		doc = v.get_video(videoid)
		videos.append(helper_get_content(doc))
	return videos

def history(request):
	# Return the list of videos this user has seen.
	# If returns -1 then user hasn't yet seen any videos.
	videos = list()
	result = UserInfoDB().get_user_info(request.user.username)
	if result == -1:
		return render(request, 'myapp/history.html', {'count':0, 'videos' : videos})	
	vid_list = [row['videoid'] for row in result]
	v = VideoInfo()

	for videoid in vid_list:
		doc = v.get_video(videoid);
		videos.append(helper_get_content(doc))
	count = len(videos)
	return render(request, 'myapp/history.html', {'count':count, 'videos' : videos})

def liked_videos(request, videoid):
	# Return the list of liked videos of the user.
	seen = history(request)
	obj = UserInfoDB()
	result = list()
	for vid in seen:
		if obj.is_like(request.user.username, videoid):
			result.append(videoid)
	return result


def helper_get_content(doc):
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
	return video
