from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from taiwan_news.api import serializer
from taiwan_news.api.custom_backend import NewsFilterBackend
from taiwan_news.models import News


class NewsViewset(viewsets.ReadOnlyModelViewSet):
    queryset = News.objects.all()
    serializer_class = serializer.NewsSerializer
    filter_backends = [filters.OrderingFilter, NewsFilterBackend]
    ordering = ['id']
