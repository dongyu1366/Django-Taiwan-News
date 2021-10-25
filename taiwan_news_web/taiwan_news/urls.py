from django.urls import path
from taiwan_news import views


urlpatterns = [
    path('index/', views.index, name='index'),
]
