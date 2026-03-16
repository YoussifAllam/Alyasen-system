# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from cacheops import invalidate_obj
from .models import Client


@receiver(post_save, sender=Client)
def invalidate_ClientInvoice_cache(sender, instance: Client, **kwargs):
    invalidate_obj(instance)


@receiver(post_delete, sender=Client)
def invalidate_ClientInvoice_cache_on_delete(sender, instance: Client, **kwargs):
    invalidate_obj(instance)


# # !-----


# @receiver(post_save, sender=SupplierInvoice)
# def invalidate_SupplierInvoice_cache(sender, instance: SupplierInvoice, **kwargs):
#     calc_invoice_remaining_amount(instance)
#     invalidate_obj(instance)


# @receiver(post_delete, sender=SupplierInvoice)
# def invalidate_SupplierInvoice_cache_on_delete(sender, instance: SupplierInvoice, **kwargs):
#     invalidate_obj(instance)


# def calc_invoice_remaining_amount(instance: SupplierInvoice):
#     new_total_amount_payable = instance.invoice_total_amount - instance.total_paid_amount

#     SupplierInvoice.objects.filter(pk=instance.pk).update(total_amount_payable=new_total_amount_payable)
#     instance.refresh_from_db()


# # !-----


# @receiver(post_save, sender=InvoiceMaterial)
# def invalidate_invoice_material_cache_on_save(sender, instance: InvoiceMaterial, **kwargs):
#     # clac_total_price_and_profit(instance)
#     invalidate_obj(instance)


# @receiver(post_delete, sender=InvoiceMaterial)
# def invalidate_invoice_material_cache_on_delete(sender, instance: InvoiceMaterial, **kwargs):
#     invalidate_obj(instance)


# def clac_total_price_and_profit(instance: InvoiceMaterial):
#     new_total_buy_price = instance.quantity_in_kilo * instance.buy_price_per_kilo
#     InvoiceMaterial.objects.filter(pk=instance.pk).update(total_buy_price=new_total_buy_price)
#     instance.refresh_from_db()


# # !-----


# @receiver(post_save, sender=InvoicePayment)
# def invalidate_invoice_payment_cache_on_save(sender, instance: InvoicePayment, **kwargs):
#     invalidate_obj(instance)


# @receiver(post_delete, sender=InvoicePayment)
# def invalidate_invoice_payment_cache_on_delete(sender, instance: InvoicePayment, **kwargs):
#     invalidate_obj(instance)
