from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^test/', views.test_func, name='test'),
    url(r'^home/',views.home, name='home'),
    url(r'^search/', views.search, name='search'),
    url(r'^view/(?P<videoId>.+)$', views.view, name='view'),
	url(r'^login/$', views.login_view, name='login')
	# url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/successfully_logged_out/'}, name='logout'),
]