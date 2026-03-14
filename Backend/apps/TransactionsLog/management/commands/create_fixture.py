# management/commands/generate_transaction_fixtures.py
from django.core.management.base import BaseCommand
from django.core import serializers
from apps.TransactionsLog.models import TransactionsLog
from django.utils.timezone import now
from faker import Faker
import random
from datetime import timedelta
import json


class Command(BaseCommand):
    help = "Generate fixture data for TransactionsLog model"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=100, help="Number of records to create")
        parser.add_argument("--output", type=str, default="transactions_fixture.json", help="Output filename")

    def handle(self, *args, **options):
        fake = Faker()
        count = options["count"]
        output_file = options["output"]

        # Sample transaction types
        transactions_types = [
            "User login successful",
            "User created new order",
            "Payment processed",
            "Data export completed",
            "Report generated",
            "User profile updated",
            "Password changed",
            "Inventory updated",
            "Customer data modified",
            "System backup performed",
        ]

        # Sample usernames
        usernames = ["admin", "user1", "user2", "manager", "guest", "support", "auditor"]

        fixtures_data = []

        for i in range(count):
            # Create future data structure for fixture
            fixture_entry = {
                "model": "TransactionsLog.TransactionsLog",
                "fields": {
                    "username": random.choice(usernames),
                    "transaction": random.choice(transactions_types),
                    "created_date": (now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                },
            }
            fixtures_data.append(fixture_entry)

            if i % 50 == 0:
                self.stdout.write(f"Generated {i} fixture entries...")

        # Write to JSON file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(fixtures_data, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully generated {count} fixture entries in {output_file}")
        )
