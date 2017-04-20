from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import authenticate as authen
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.decorators import login_required
import logging
import json
from django.shortcuts import render_to_response
from pandas import DataFrame

#from django.forms import LoginForm

from engine.spellcheck import *
from database.api import *
from engine.recommend import Recommendations
import pandas as pd

from operator import itemgetter
import random
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
	videos = global_recommendation(request)
	logger.info(videos)
	return render(request, 'myapp/home.html', videos)

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
			score = list()

			for doc in result:
				video = helper_get_content(doc)
				video['score'] = str(doc['score'])
				videos.append(video)

			count = len(videos)

			return render(request, 'myapp/result.html', {	'q' : q,
															'count' : count,
															'videos' : videos,
															'suggestion' : text,})
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
	# If you get -1 in comment_list, it means there are no comments yet.
	comment_list = v.get_comments(videoId)
	comment_count = 0
	if comment_list != -1:
		comment_count = len(comment_list)
	u = UserInfoDB()
	like = u.is_like(request.user.username,videoId)
	src = 'https://www.youtube.com/embed/' + currentvid['videoInfo']['id']
	return render(request, 'myapp/view.html', { 'currentvid' : currentvid,
												'src' : src,
												'comment_list' : comment_list,
												'comment_count' : comment_count,
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
	refined_records = obj.user_history(username,records)
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
	# vid_list = [row['videoid'] for row in result]
	vid_list = result
	v = VideoInfo()

	for videoid in vid_list:
		doc = v.get_video(videoid);
		videos.append(helper_get_content(doc))
	count = len(videos)
	return render(request, 'myapp/history.html', {'count':count, 'videos' : videos})

def liked_videos(request):
	# Return the list of liked videos of the user.
	count = 0
	vids = UserInfoDB().get_user_info(request.user.username)
	if vids == -1:
		vids = []
	obj = UserInfoDB()
	result = list()
	for vid in vids:
		if obj.is_like(request.user.username, vid):
			result.append(vid)
	count = len(result)
	v = VideoInfo()
	videos = list()
	for videoid in result:
		doc = v.get_video(videoid);
		videos.append(helper_get_content(doc))
	return render(request, 'myapp/liked_videos.html', {'count':count, 'videos' : videos})


def helper_get_content(doc):
	video = {}
	video['thumbnail'] =  { 'medium': doc['videoInfo']['snippet']['thumbnails']['medium']['url'], 
							'default': doc['videoInfo']['snippet']['thumbnails']['default']['url'] }
	video['title'] = doc['videoInfo']['snippet']['title']
	video['view'] = doc['videoInfo']['statistics']['viewCount']
	video['likes'] = doc['videoInfo']['statistics']['likeCount']
	video['id'] = doc['videoInfo']['id']

	desc = doc['videoInfo']['snippet']['description'].split(' ')
	desc = desc[0:60]
	temp = ''
	for i in desc:
		temp = temp + i + ' '
	desc = temp[0:200]
	if (len(temp) > len(desc)):
		desc = desc + ' ...'

	video['desc'] = desc
	return video

def global_recommendation(request):
	obj = UserInfoDB()
	liked_vid_list_org, count_of_liked_vid_list = obj.get_users_liked_video(request.user.username)
	liked_vid_list = liked_vid_list_org[0:10]
	vid_list = set()
	for c in liked_vid_list:
		vid_list.add(c)

	viewed_vid_list = obj.get_user_info(request.user.username)
	viewed_vid_list = viewed_vid_list[0:5]
	for c in viewed_vid_list:
		vid_list.add(c)

	recommend_list = set()
	obj = Recommendations()
	for v in vid_list:
		reco = obj.nearest_neighbours(v, 1)
		recommend_list.add(reco['Neighbor'].ix[0])
	recommend_list.difference_update(vid_list)

	v = VideoInfo()
	recommends = list()
	for vid in recommend_list:
		doc = v.get_video(vid)
		recommends.append(helper_get_content(doc))

		recommends = recommends[0:5]

	watch_it_again_list = list()

	for vid, count in zip(liked_vid_list_org, count_of_liked_vid_list):
		temp = (vid, count)
		watch_it_again_list.append(temp)
	sorted(watch_it_again_list, key=itemgetter(1), reverse=True)

	watch_it_again_list = watch_it_again_list[0:2]

	watch_again = list()
	for tup in watch_it_again_list:
		doc = v.get_video(tup[0])
		watch_again.append(helper_get_content(doc))

	recos = set()

	f = UserGraph()
	following_list = DataFrame(f.get_following_list(request.user.username).data())
	obj = UserInfoDB()
	for i in range(0, len(following_list)):
		uid = following_list['follows'][i]
		vid_list = obj.get_users_liked_video(uid)
		if vid_list != -1:
			recos.add(vid_list[0])

	recos = list(recos)
	result = list()
	if len(recos) >= 6:
		ran = random.sample(range(0, len(recos)), 6)
		for i in ran:
			result.append(recos[i])

	follow_recos = list()
	for vid in result:
		doc = v.get_video(vid)
		follow_recos.append(helper_get_content(doc))

	return {	'watch_again' : watch_again,
				'recommends' : recommends,
				'follow_recos' : follow_recos,};

def is_user_present(request):
	count = 0
	obj = UserGraph()
	if 'q' in request.POST:
		if len(request.POST['q'])>0:
			count = obj.find_user(request.POST['q'])
			return render(request, 'myapp/found_user.html', {'count' : count,
															'user' : request.POST['q']})
	if request.META.get('HTTP_REFERER'):
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
	else:
		return redirect('/home/')

def like(request):
	if request.method == "POST" and request.is_ajax():
		vid = request.POST.get('vid')
		u = UserInfoDB()
		if u.is_like(request.user.username,vid) == 1:
			u.upsert(request.user.username, vid, likes=0, dislikes=0)
			return HttpResponse(json.dumps({'resp': 0 }), content_type="application/json")
		else:
			u.upsert(request.user.username, vid, likes=1, dislikes=0)
			return HttpResponse(json.dumps({'resp': 1 }), content_type="application/json")

def dislike(request):
	if request.method == "POST" and request.is_ajax():
		vid = request.POST.get('vid')
		u = UserInfoDB()
		if u.is_like(request.user.username,vid) == -1:
			u.upsert(request.user.username, vid, likes=0, dislikes=0)
			return HttpResponse(json.dumps({'resp': 0 }), content_type="application/json")
		else:
			u.upsert(request.user.username, vid, likes=0, dislikes=1)
			return HttpResponse(json.dumps({'resp': -1 }), content_type="application/json")

def connect_users(request, username):
	obj = UserGraph()
	obj.follow_user(request.user.username, username)
	return redirect('/home/')
