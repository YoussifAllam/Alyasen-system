# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cacheops import invalidate_obj

from .tasks import celery_tasks
from .models import MaterialWarehouse


@receiver(post_save, sender=MaterialWarehouse)
def invalidate_transaction_cache(sender, instance: MaterialWarehouse, **kwargs):
    notify_admin_if_low_stock(instance)
    invalidate_obj(instance)


def notify_admin_if_low_stock(material_instance: MaterialWarehouse):
    if material_instance.quantity_in_unit <= 25:
        celery_tasks.send_email_to_all_users_task.delay(
            subject="منتج علي وشك النفاذ ",
            message="المنتج : "
            + material_instance.material_name
            + " علي وشك النفاذ الكميه الحاليه : "
            + str(material_instance.quantity_in_unit)
            + " "
            + material_instance.unit,
        )


@receiver(post_delete, sender=MaterialWarehouse)
def invalidate_transaction_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when a transaction is deleted"""
    invalidate_obj(instance)
