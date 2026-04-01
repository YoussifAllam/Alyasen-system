# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cacheops import invalidate_obj
from .models import Supplier, ProjectPayment


@receiver(post_save, sender=Supplier)
def invalidate_Supplier_cache(sender, instance: Supplier, **kwargs):
    invalidate_obj(instance)


@receiver(post_delete, sender=Supplier)
def invalidate_Supplier_cache_on_delete(sender, instance: Supplier, **kwargs):
    invalidate_obj(instance)


@receiver(post_save, sender=ProjectPayment)
def invalidate_invoice_payment_cache_on_save(
    sender, instance: ProjectPayment, **kwargs
):
    invalidate_obj(instance)


@receiver(post_delete, sender=ProjectPayment)
def invalidate_invoice_payment_cache_on_delete(
    sender, instance: ProjectPayment, **kwargs
):
    invalidate_obj(instance)
