from rest_framework import serializers

from taiwan_news.models import News


class NewsSerializer(serializers.ModelSerializer):

    class Meta:
        model = News
        fields = '__all__'
