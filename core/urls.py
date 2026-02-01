from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
	    path('', views.main_view, name='main'),
		path('logout/', LogoutView.as_view(next_page='main'), name='logout'),
		path('login/', LogoutView.as_view(next_page='main'), name='login'),
]