# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cacheops import invalidate_obj
from .models import MixtureMaterial, Mixtures


@receiver(post_save, sender=Mixtures)
def invalidate_Mixtures_cache(sender, instance, **kwargs):
    invalidate_obj(instance)


@receiver(post_delete, sender=Mixtures)
def invalidate_Mixtures_cache_on_delete(sender, instance, **kwargs):
    invalidate_obj(instance)


@receiver(post_save, sender=MixtureMaterial)
def invalidate_mixture_material_cache_on_save(sender, instance, **kwargs):
    invalidate_obj(instance)


@receiver(post_delete, sender=MixtureMaterial)
def invalidate_mixture_material_cache_on_delete(sender, instance, **kwargs):
    invalidate_obj(instance)
