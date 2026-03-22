from rest_framework.request import Request
from cacheops import cached_as
from django.db.models import Q
from rest_framework.exceptions import NotFound

from ..models import Safe, SafeLogs


def get_safe_balance():
    safe_instnace, created = Safe.objects.get_or_create(id=1)
    return safe_instnace.balance


def get_safe_logs():
    return SafeLogs.objects.all()
