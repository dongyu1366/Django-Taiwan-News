from django.urls import path
from taiwan_news import views


urlpatterns = [
    path('update-news', views.update_news)
]
