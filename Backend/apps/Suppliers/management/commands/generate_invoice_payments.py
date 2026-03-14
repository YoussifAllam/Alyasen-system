from django.core.management.base import BaseCommand
from faker import Faker
from apps.Suppliers.models import InvoicePayment, SupplierInvoice
from datetime import datetime
import random


class Command(BaseCommand):
    help = "Generate fake data for InvoicePayment model using bulk creation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="Number of invoice payments to create (default: 50)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Batch size for bulk creation (default: 100)",
        )

    def handle(self, *args, **options):
        fake = Faker()
        count = options["count"]
        batch_size = options["batch_size"]

        # Available invoice IDs (26 to 33)
        available_invoice_ids = list(range(26, 34))

        # Verify invoices exist
        existing_invoices = SupplierInvoice.objects.filter(id__in=available_invoice_ids).values_list(
            "id", flat=True
        )

        if not existing_invoices:
            self.stdout.write(
                self.style.ERROR(
                    "No invoices found with IDs 26-33. Please create SupplierInvoice instances first."
                )
            )
            return

        valid_invoice_ids = list(existing_invoices)

        invoice_payments = []
        created_count = 0

        for i in range(count):
            try:
                invoice_id = random.choice(valid_invoice_ids)
                invoice = SupplierInvoice.objects.get(id=invoice_id)

                payment_amount = round(random.uniform(100, 5000), 2)
                payment_date = fake.date_between_dates(
                    date_start=datetime(2023, 1, 1).date(), date_end=datetime.now().date()
                )
                notes = fake.text(max_nb_chars=200) if random.choice([True, False]) else ""

                invoice_payment = InvoicePayment(
                    invoice=invoice, payment_amount=payment_amount, payment_date=payment_date, notes=notes
                )

                invoice_payments.append(invoice_payment)
                created_count += 1

                # Bulk create in batches
                if len(invoice_payments) >= batch_size:
                    InvoicePayment.objects.bulk_create(invoice_payments)
                    self.stdout.write(
                        self.style.SUCCESS(f"Created batch of {len(invoice_payments)} invoice payments")
                    )
                    invoice_payments = []

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating invoice payment: {str(e)}"))
                continue

        # Create any remaining invoice payments
        if invoice_payments:
            InvoicePayment.objects.bulk_create(invoice_payments)
            self.stdout.write(
                self.style.SUCCESS(f"Created final batch of {len(invoice_payments)} invoice payments")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_count} invoice payments for invoice IDs {valid_invoice_ids}"
            )
        )
