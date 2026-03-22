# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cacheops import invalidate_obj
from .models import CompanyAssets


@receiver(post_save, sender=CompanyAssets)
def invalidate_CompanyAssets_cache(sender, instance, **kwargs):
    invalidate_obj(instance)


@receiver(post_delete, sender=CompanyAssets)
def invalidate_CompanyAssets_cache_on_delete(sender, instance, **kwargs):
    invalidate_obj(instance)
