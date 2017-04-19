from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^test/', views.test_func, name='test'),
    url(r'^search/', views.search, name='search'),
]