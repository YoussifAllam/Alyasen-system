# management/commands/generate_expenses_fixtures.py
import json
import random
from datetime import datetime


from django.core.management.base import BaseCommand
from django.utils.timezone import now
from faker import Faker


class Command(BaseCommand):
    help = "Generate fixture data for Expenses model"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=100, help="Number of records to create")
        parser.add_argument("--output", type=str, default="expenses_fixture.json", help="Output filename")
        parser.add_argument("--min-amount", type=float, default=10.0, help="Minimum amount value")
        parser.add_argument("--max-amount", type=float, default=10000.0, help="Maximum amount value")

    def handle(self, *args, **options):
        fake = Faker()
        count = options["count"]
        output_file = options["output"]
        min_amount = options["min_amount"]
        max_amount = options["max_amount"]

        # Sample expense transactions
        expense_types = [
            "Office Supplies Purchase",
            "Software Subscription Renewal",
            "Hardware Equipment",
            "Internet Bill Payment",
            "Electricity Bill",
            "Water Bill",
            "Rent Payment",
            "Employee Salary",
            "Transportation Costs",
            "Marketing Campaign",
            "Training and Development",
            "Maintenance and Repairs",
            "Travel Expenses",
            "Client Entertainment",
            "Insurance Premium",
            "Tax Payment",
            "Bank Charges",
            "Legal Fees",
            "Consulting Services",
            "Cleaning Services",
        ]

        # Sample permit numbers (format: PER-XXXXX)
        permit_numbers = [f"PER-{random.randint(10000, 99999)}" for _ in range(20)]
        permit_numbers.append(None)  # Some expenses might not have permit numbers
        permit_numbers.append("")  # Some might have empty strings

        # Sample notes
        notes_options = [
            "Urgent payment required",
            "Monthly recurring expense",
            "One-time purchase",
            "Approved by management",
            "Budget allocated",
            "Tax deductible",
            "Emergency expense",
            "Project related cost",
            "Department budget",
            "Quarterly expense",
            "",
            None,
        ]

        fixtures_data = []

        # Get current year for date generation
        current_year = now().year
        start_date = datetime(current_year, 1, 1)
        end_date = datetime(current_year, 12, 31)

        for i in range(count):
            transaction_type = random.choice(expense_types)
            permit_number = random.choice(permit_numbers)
            amount = round(random.uniform(min_amount, max_amount), 2)
            note = random.choice(notes_options)

            # Generate random date in current year
            random_date = fake.date_between_dates(date_start=start_date, date_end=end_date)

            # Create fixture entry
            fixture_entry = {
                "model": "Expenses.Expenses",  # Change 'your_app' to your actual app name
                "fields": {
                    "transaction": transaction_type,
                    "permit_number": permit_number,
                    "amount": amount,
                    "created_date": random_date.strftime("%Y-%m-%d"),
                    "notes": note,
                },
            }
            fixtures_data.append(fixture_entry)

            if i % 50 == 0:
                self.stdout.write(f"Generated {i} expense entries...")

        # Write to JSON file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(fixtures_data, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully generated {count} expense entries in {output_file}")
        )
