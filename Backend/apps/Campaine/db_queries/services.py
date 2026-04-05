from django.db import transaction
from apps.Campaine.models import Campaine, CampaineItem

from apps.Clients.models import Client, ClientProjectBalance
from apps.Suppliers.models import Supplier
from apps.Projects.models import BaseProject

from celery import shared_task


def create_campaign_service(*, name, client_id, items_data):
    """
    Creates a Campaign and its items, updates total cost,
    and updates each supplier's balance.
    """
    with transaction.atomic():
        client = Client.objects.get(id=client_id)
        campaign = Campaine.objects.create(name=name, client=client, total_cost=0)

        total_cost = 0
        for item in items_data:
            supplier = Supplier.objects.get(id=item["supplier_id"])
            project = BaseProject.objects.get(id=item["project_id"])
            amount = item["amount"]

            CampaineItem.objects.create(
                campaine=campaign, supplier=supplier, project=project, amount=amount
            )

            # Update Supplier balance
            # Based on Supplier model: total_amount_due and total_amount_payable
            supplier.total_amount_due += amount
            supplier.total_amount_payable += amount
            supplier.save()

            total_cost += amount

        campaign.total_cost = total_cost
        campaign.save()

        return campaign


@shared_task(name="create_client_project_balance_profile")
def create_client_project_balance_profile(campaine_id, client_id):
    client_instnace = Client.objects.get(id=client_id)
    campaine_instance = Campaine.objects.get(id=campaine_id)

    ClientProjectBalance.objects.create(
        project_type="campaine",
        campaine_fk=campaine_instance,
        client_fk=client_instnace,
        total=campaine_instance.total_cost,
        remining=campaine_instance.total_cost,
        paid=0,
    )
