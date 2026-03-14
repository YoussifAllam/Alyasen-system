import random
from django.core.management.base import BaseCommand
from faker import Faker
from apps.Clients.models import ClientInvoice, Client  # Replace 'your_app' with your actual app name


class Command(BaseCommand):
    help = "Create 10,000 fake client invoices"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10000,
            help="Number of invoices to create (default: 10000)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing invoices before creating new ones",
        )

    def handle(self, *args, **options):
        count = options["count"]
        clear = options["clear"]
        fake = Faker()

        # Get available client IDs (1 to 6)
        client_ids = list(range(1, 7))

        if not Client.objects.filter(id__in=client_ids).exists():
            self.stdout.write(
                self.style.ERROR("Clients with IDs 1-6 do not exist. Please create them first.")
            )
            return

        if clear:
            self.stdout.write("Clearing all existing invoices...")
            ClientInvoice.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("All existing invoices cleared."))

        self.stdout.write(f"Creating {count} fake invoices...")

        invoices = []
        existing_invoice_numbers = set(ClientInvoice.objects.values_list("invoice_number", flat=True))

        for i in range(count):
            # Generate unique invoice number
            while True:
                invoice_number = f"INV{fake.unique.random_number(digits=6)}"
                if invoice_number not in existing_invoice_numbers:
                    existing_invoice_numbers.add(invoice_number)
                    break

            # Generate random dates within the last 2 years
            invoice_date = fake.date_between(start_date="-2y", end_date="today")

            # Generate random amounts
            invoice_total_amount = round(random.uniform(10000, 100000), 2)
            total_paid_amount = round(random.uniform(0, invoice_total_amount), 2)
            total_amount_payable = round(invoice_total_amount - total_paid_amount, 2)

            # Random client from IDs 1-6
            client_id = random.choice(client_ids)

            # Random notes (50% chance of having notes)
            notes = fake.text(max_nb_chars=200) if random.random() > 0.5 else ""

            # Random is_moved_to_warehouse (70% chance of True)
            is_moved_to_warehouse = random.random() > 0.3

            invoice = ClientInvoice(
                client_id=client_id,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                invoice_total_amount=invoice_total_amount,
                total_amount_payable=total_amount_payable,
                total_paid_amount=total_paid_amount,
                notes=notes,
                is_moved_to_warehouse=is_moved_to_warehouse,
            )

            invoices.append(invoice)

            # Show progress
            if (i + 1) % 1000 == 0:
                self.stdout.write(f"Created {i + 1} invoices...")

        # Bulk create all invoices
        ClientInvoice.objects.bulk_create(invoices, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {count} fake invoices!"))
