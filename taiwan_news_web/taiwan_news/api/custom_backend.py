from datetime import timedelta
from django.utils import timezone
from operator import attrgetter
from rest_framework import filters


class NewsFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        req_category = request.query_params.get('category')
        req_random = request.query_params.get('random')

        if req_category:
            queryset = queryset.filter(category=req_category)
        elif req_random:
            today = timezone.now()
            three_days_ago = today - timedelta(days=5)
            queryset = queryset.filter(dt_created__gte=three_days_ago).order_by('?')[:10]
            queryset = sorted(queryset, key=attrgetter('dt_created'))

        return queryset
