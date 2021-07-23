from rest_framework.routers import DefaultRouter

from taiwan_news.api import apiview

router = DefaultRouter()

router.register(r'news', apiview.NewsViewset)
