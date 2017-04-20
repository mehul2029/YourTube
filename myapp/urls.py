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
    url(r'^history/$', views.history, name='history'),
    url(r'^liked_videos/$', views.liked_videos, name='liked_videos'),
    url(r'^ajax/like/$', views.like, name='ajax-like'),
    url(r'^ajax/dislike/$', views.dislike, name='ajax-dislike'),
    url(r'^ajax/follow/$', views.connect_users, name='ajax-follow'),
    url(r'^ajax/comment/$', views.comment, name='ajax-comment'),
    url(r'^find_user/$', views.find_user, name='find_user'),
    url(r'^found_user/$', views.is_user_present, name='found_user'),
    url(r'^db_update/(?P<newvideoId>.+)/(?P<oldvideoId>.+)/$', views.db_on_recommendation_click, name='db_update'),
	# url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/successfully_logged_out/'}, name='logout'),
]