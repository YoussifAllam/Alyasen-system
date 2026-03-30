# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cacheops import invalidate_obj
from .models import Quotations


@receiver(post_save, sender=Quotations)
def invalidate_quotation_cache(sender, instance, **kwargs):
    """Invalidate cache when a quotation is saved"""
    invalidate_obj(instance)


@receiver(post_delete, sender=Quotations)
def invalidate_quotation_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when a quotation is deleted"""
    invalidate_obj(instance)
