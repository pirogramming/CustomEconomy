from django.urls import path
from .views import TermSearchView

app_name = 'terms'

urlpatterns = [
    path('search/', TermSearchView.as_view(), name='term_search'),
]