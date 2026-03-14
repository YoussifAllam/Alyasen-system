from ..models import Mixtures, MixtureMaterial


def create_mixture_instance(name):
    Mixtures.objects.create(name=name)


def update_mixture_instance_name(mixture_instance: Mixtures, new_name: str):
    mixture_instance.name = new_name
    mixture_instance.save()


def update_mix_materials_used_cost(mix_material_instnace: MixtureMaterial):
    mix_material_instnace.mixture_fk.materials_used_cost += mix_material_instnace.total_price
    mix_material_instnace.mixture_fk.save()
    return mix_material_instnace.mixture_fk.materials_used_cost
