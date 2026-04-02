from .. import models
from rest_framework.request import Request
from cacheops import cached_as


def get_all_campaigns():
    return models.Campaine.objects.all()
