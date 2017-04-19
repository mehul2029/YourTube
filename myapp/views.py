from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from engine.spellcheck import *
from database.api import *
from engine.recommend import Recommendations
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
															'videos' : videos,
															'suggestion' : text})

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
	db_on_search_click(videoId, request.username)
	videos = recommendation(videoId, request.username)
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
	common_words = len(set(listify).intersection(set(reco)))
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
		
		video = {}
		video['thumbnail'] =  doc['videoInfo']['snippet']['thumbnails']['default']['url']
		video['title'] = doc['videoInfo']['snippet']['title']
		video['view'] = doc['videoInfo']['statistics']['viewCount']
		video['id'] = doc['videoInfo']['id']
		
		desc = doc['videoInfo']['snippet']['description'].split(' ')
		desc = desc[0:10]
		temp = ''
		for i in desc:
			temp = temp + i + ' '
		desc = temp[0:50]
		if (len(temp) > len(desc)):
			desc = desc + ' ...'

		video['desc'] = desc
		videos.append(video)

	return videos

def history(request):
	# Return the list of videos this user has seen.
	# If returns -1 then user hasn't yet seen any videos.
	result = UserInfoDB().get_user_info(request.username)
	videos = [row['videoid'] for row in result]
	return videos

def liked_videos(request):
	# Return the list of liked videos of the user.
	pass