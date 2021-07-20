from django.db import models


class News(models.Model):
    token = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50)
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=500, blank=True)
    date = models.CharField(max_length=50)
    abstract = models.CharField(max_length=1500)
    content = models.CharField(max_length=25000, blank=True)
    image_url = models.CharField(max_length=1500, blank=True)
    page_url = models.CharField(max_length=1500)
    dt_created = models.DateTimeField(auto_now_add=True)
