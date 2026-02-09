from django.urls import path
from . import views

urlpatterns = [
     path('terms/', views.terms_view, name='terms'),
     path('terms/bookmark/', views.bookmark_term, name='bookmark_term'),
     path('terms/unbookmark/', views.unbookmark_term, name='unbookmark_term'),
     path('bookmarks/json/', views.bookmarks_json, name='bookmarks_json'),
]