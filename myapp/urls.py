from django.conf.urls import url

from . import views

urlpatterns = [
<<<<<<< HEAD
    url(r'^$', views.index, name='index'),
    url(r'^test/', views.test_func, name='test'),
    url(r'^search/', views.search, name='search'),
=======
	url(r'^$', views.index, name='index'),
	url(r'^test/', views.test_func, name='test'),
	url(r'^bootstrap/', views.bootstrap, name='boot'),
	url(r'^login/$', views.login_view, name='login')
	url(r'^logout/$', 'django.contrib.auth.views.logout',
		{'next_page': '/successfully_logged_out/'}, name='logout'),
>>>>>>> 4ab62f24a639c5d0e7a9afa16c6471d47e88cde5
]