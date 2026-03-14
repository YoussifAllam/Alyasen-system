from apps.Material_Warehouse.models import MaterialWarehouse
from django.core.cache import cache
from cacheops import cached_as


class MaterialInventoryService:
    """Service class for material inventory analysis"""

    @classmethod
    def _fetch_lowest_quantity_materials(cls, limit=2):
        """
        Fetch materials with lowest quantity from warehouse
        """
        lowest_materials = (
            MaterialWarehouse.objects.only("material_name", "quantity_in_unit")
            .filter(quantity_in_unit__gt=0)  # Only materials with quantity > 0
            .order_by("quantity_in_unit")
            .values("material_name", "quantity_in_unit")
        )[:limit]

        return list(lowest_materials)

    @classmethod
    def get_lowest_quantity_materials(cls, limit=2):
        """
        Get the lowest quantity materials with caching
        """

        @cached_as(MaterialWarehouse, extra=("lowest_materials", limit))
        def _get_cached_lowest_materials():
            materials_data = cls._fetch_lowest_quantity_materials(limit)

            if not materials_data:
                return []

            # Format the lowest materials data
            lowest_materials = []
            for item in materials_data:
                lowest_materials.append(
                    {
                        "name": item["material_name"],
                        "quantity_in_unit": float(item["quantity_in_unit"]),
                        "total": float(item["quantity_in_unit"]) + 10,
                    }
                )

            return lowest_materials

        return _get_cached_lowest_materials()

    @classmethod
    def invalidate_material_cache(cls):
        """
        Invalidate material inventory cache
        """
        from cacheops import invalidate_dict

        # Invalidate for MaterialWarehouse model
        invalidate_dict(MaterialWarehouse)

        # Delete specific cache keys
        cache_keys = [
            "lowest_quantity_materials",
            "lowest_quantity_materials_profit",
            "low_stock_alert",
        ]

        for cache_key in cache_keys:
            cache.delete(cache_key)

        print("Material inventory cache invalidated")

    @classmethod
    def force_refresh_material_analysis(cls):
        """
        Force refresh material analysis data
        """
        cls.invalidate_material_cache()
        return {
            "lowest_quantity": cls.get_lowest_quantity_materials(2),
            "low_stock_alert": cls.get_low_stock_alert(10.0),
        }
