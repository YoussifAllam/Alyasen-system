# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cacheops import invalidate_obj
from .models import TransactionsLog


@receiver(post_save, sender=TransactionsLog)
def invalidate_transaction_cache(sender, instance, **kwargs):
    """Invalidate cache when a transaction is saved"""
    invalidate_obj(instance)
    # Also invalidate any filtered caches that might include this transaction
    # Example: invalidate_dict(f'transactions_{instance.username}_{instance.created_date}')


@receiver(post_delete, sender=TransactionsLog)
def invalidate_transaction_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when a transaction is deleted"""
    invalidate_obj(instance)
