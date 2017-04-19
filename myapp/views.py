from django.shortcuts import render
from database.api import *
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout


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
	