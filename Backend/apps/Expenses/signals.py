# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cacheops import invalidate_obj
from .models import Expenses


@receiver(post_save, sender=Expenses)
def invalidate_Expenses_cache(sender, instance, **kwargs):
    invalidate_obj(instance)


@receiver(post_delete, sender=Expenses)
def invalidate_Expenses_cache_on_delete(sender, instance, **kwargs):
    invalidate_obj(instance)
