from celery import shared_task
from django.db import transaction

from apps.Mixtures.models import Mixtures, MixtureMaterial


@shared_task
def calculate_mixture_materials_cost(mixture_id):
    """
    Celery task to calculate and update materials_used_cost for a Mixture instance
    """
    try:
        # Get the mixture instance
        mixture = Mixtures.objects.get(id=mixture_id)

        # Calculate total materials cost
        total_cost = 0
        total_profit = 0

        # Get all related mixture materials
        mixture_materials = MixtureMaterial.objects.filter(mixture_fk=mixture)

        for mixture_material in mixture_materials:
            material_cost = mixture_material.quantity_used * mixture_material.material_fk.buy_price_per_kilo
            total_cost += material_cost

            material_profit = mixture_material.quantity_used * mixture_material.material_fk.proft
            total_profit += material_profit

        # Update the mixture instance with atomic transaction
        with transaction.atomic():
            mixture.materials_used_cost = total_cost
            mixture.profit = total_profit
            mixture.save()

    except Mixtures.DoesNotExist:
        print(f"Mixture with ID {mixture_id} not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
