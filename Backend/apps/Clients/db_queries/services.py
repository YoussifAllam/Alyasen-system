from ..models import ClientInvoice, InvoiceMaterials,Client,InvoicePayment
from django.utils.timezone import now

def increase_invoice_total_amount(invoice_instance: ClientInvoice, invoice_mixture_instance: InvoiceMaterials):
    invoice_instance.invoice_total_amount += (
        invoice_mixture_instance.mixture.selling_price * invoice_mixture_instance.quantity_in_kilo
    )
    invoice_instance.total_amount_payable = invoice_instance.invoice_total_amount
    invoice_instance.save()
    total_profit = invoice_mixture_instance.quantity_in_kilo * invoice_mixture_instance.mixture.profit
    return invoice_instance.invoice_total_amount, total_profit


def decrease_invoice_total_amount(invoice_instance: ClientInvoice, mixture_total_buy_price: float):
    invoice_instance.invoice_total_amount -= mixture_total_buy_price
    invoice_instance.total_amount_payable = invoice_instance.invoice_total_amount
    invoice_instance.save()
    return invoice_instance.invoice_total_amount


def update_client_balance_after_create_invoice(invoice_instance: ClientInvoice, payment_amount: float):
    invoice_instance.client.total_balance_owed_to_us += payment_amount
    invoice_instance.client.total_remaining_balance_owed_to_us += payment_amount
    invoice_instance.client.save()


def update_client_balance_after_payment(client_instance: Client, payment_amount: float):
    client_instance.total_paid_amount += payment_amount
    client_instance.total_remaining_balance_owed_to_us -= payment_amount
    client_instance.save()


def create_client_payment_invoice_record(client_instance: Client, payment_amount: float):
    InvoicePayment.objects.create(
        client_fk=client_instance,
        payment_amount=payment_amount,
        payment_date=now(),
    )
