from django.urls import path
from .views import UserProfileView, MyBookmarkView

app_name = 'accounts'

urlpatterns = [
    path('profile/<int:user_id>/', UserProfileView.as_view(), name='profile'),
    path('bookmarks/<int:user_id>/', MyBookmarkView.as_view(), name='my_bookmarks'),
]