from ..models import SegmentalInvoicePayment


# def increase_invoice_total_amount(
#     invoice_instance: Invoice, invoice_mixture_instance: SegmentalInvoiceMixtures
# ):
#     invoice_instance.invoice_total_amount += (
#         invoice_mixture_instance.mixture.selling_price * invoice_mixture_instance.quantity_in_kilo
#     )
#     invoice_instance.save()
#     total_profit = invoice_mixture_instance.quantity_in_kilo * invoice_mixture_instance.mixture.profit
#     return invoice_instance.invoice_total_amount, total_profit


# def decrease_invoice_total_amount(invoice_instance: Invoice, mixture_total_buy_price: float):
#     invoice_instance.invoice_total_amount -= mixture_total_buy_price
#     invoice_instance.save()
#     return invoice_instance.invoice_total_amount


def create_payment_record(amount: float):
    SegmentalInvoicePayment.objects.create(payment_amount=amount)
