from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.home, name='index'),
    url(r'^test/', views.test_func, name='test'),
    url(r'^home/',views.home, name='home'),
    url(r'^signup/',views.signup, name='signup'),
    url(r'^bootstrap/',views.bootstrap, name='bootstrap'),
    url(r'^search/', views.search, name='search'),
    url(r'^view/(?P<videoId>.+)$', views.view, name='view'),
    url(r'^login/$', views.login_view, name='login'),
    url(r'^logout/$',views.logout_view, name='logout'),
    url(r'^history/$', views.history, name='history')
	# url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/successfully_logged_out/'}, name='logout'),
]