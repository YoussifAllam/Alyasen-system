from rest_framework.exceptions import NotFound

from apps.Material_Warehouse.models import MaterialWarehouse


class WarehouseManager:
    """Handles the business logic for moving invoice materials to warehouse"""

    @staticmethod
    def create_new_material(invoice_material, material_name=None):
        """Create new warehouse material from invoice material"""
        if material_name is None:
            material_name = invoice_material.material_name

        return MaterialWarehouse.objects.create(
            material_name=material_name,
            quantity_in_kilo=invoice_material.quantity_in_kilo,
            buy_price_per_kilo=invoice_material.buy_price_per_kilo,
            price_per_kilo=invoice_material.sell_price_per_kilo,
            total_price=invoice_material.total_buy_price,
            proft=(invoice_material.sell_price_per_kilo - invoice_material.buy_price_per_kilo)
            * invoice_material.quantity_in_kilo,
        )


def validate_materials_exist(invoice_materials, invoice_number):
    """Validate that the invoice has materials to process"""
    if not invoice_materials.exists():
        raise NotFound(f"No materials found for invoice {invoice_number}")


def get_unique_material_name(base_name):
    """Generate a unique material name by appending a number if needed"""
    counter = 1
    new_name = base_name

    while MaterialWarehouse.objects.filter(material_name=new_name ).exists():
        counter += 1
        new_name = f"{base_name} {counter}"

    return new_name


def process_materials(invoice_materials):
    """Process all invoice materials and return results"""
    moved_materials = []

    for invoice_material in invoice_materials:
        original_name = invoice_material.material_name
        buy_price = invoice_material.buy_price_per_unit
        quantity = invoice_material.quantity_in_unit
        unit = invoice_material.unit

        data1 = {'material_name': original_name, 'quantity_in_unit': quantity, 'unit': unit, 'buy_price_per_unit': buy_price}
        material1, created1 = add_material_to_warehouse(data1)
        
        moved_materials.append(original_name)

    return moved_materials


#______________________________

def get_unique_material_name_for_price(base_name, price):
    """
    Generate a unique material name considering price differences.
    
    Rules:
    1. If material with same name AND same price exists: add quantity to existing
    2. If material with same name but different price exists: create new with counter
    3. If no material with same name exists: use base name
    
    Returns: tuple of (material_name, should_create_new)
    """
    # First, check if exact match exists (same name AND same price)
    exact_match = MaterialWarehouse.objects.filter(
        material_name=base_name,
        buy_price_per_unit=price
    ).first()
    
    if exact_match:
        # Return same name, don't create new
        return base_name, False
    
    # Check if any material with the same base name exists
    # We need to check patterns like "material", "material 1", "material 2", etc.
    existing_materials = MaterialWarehouse.objects.filter(
        material_name__startswith=base_name
    ).order_by('material_name')
    
    if not existing_materials.exists():
        # No material with this base name exists, use base name
        return base_name, True
    
    # Find materials with same base name pattern
    price_exists = False
    max_counter = 0
    
    for material in existing_materials:
        # Extract counter if exists
        if material.material_name == base_name:
            # Check if this exact name has same price
            if material.buy_price_per_unit == price:
                return base_name, False
            max_counter = max(max_counter, 1)
        elif material.material_name.startswith(f"{base_name} "):
            # Try to extract counter
            try:
                # Check if the rest is a number
                rest = material.material_name[len(base_name) + 1:]
                if rest.isdigit():
                    counter = int(rest)
                    max_counter = max(max_counter, counter)
                    
                    # Check if price matches
                    if material.buy_price_per_unit == price:
                        price_exists = True
                        matching_name = material.material_name
            except:
                pass
    
    # If price exists in numbered materials, use that name
    if price_exists:
        return matching_name, False
    
    # Price doesn't exist, create new with next counter
    new_counter = max_counter + 1
    new_name = f"{base_name} {new_counter}" if new_counter > 1 else base_name
    
    return new_name, True


# Example usage in your view or function:
def add_material_to_warehouse(material_data):
    """
    Add material to warehouse with proper name handling
    """
    base_name = material_data['material_name']
    price = material_data['buy_price_per_unit']
    quantity = material_data.get('quantity_in_unit', 0)
    
    # Get the appropriate name
    material_name, should_create_new = get_unique_material_name_for_price(base_name, price)
    
    if not should_create_new:
        # Update existing material
        material = MaterialWarehouse.objects.get(
            material_name=material_name,
            buy_price_per_unit=price
        )
        material.quantity_in_unit += quantity
        material.save()
        return material, False  # False = updated existing
    else:
        # Create new material
        material_data['material_name'] = material_name
        material = MaterialWarehouse.objects.create(**material_data)
        return material, True  # True = created new


# Alternative: Simpler version if you prefer more explicit logic
def get_material_name_with_price(base_name, price):
    """
    Simplified version that just returns the appropriate name
    """
    # Check for exact match
    if MaterialWarehouse.objects.filter(material_name=base_name, buy_price_per_unit=price).exists():
        return base_name
    
    # Check numbered versions
    counter = 1
    while True:
        # Check if "base_name counter" exists with same price
        check_name = f"{base_name} {counter}"
        if MaterialWarehouse.objects.filter(material_name=check_name, buy_price_per_unit=price).exists():
            return check_name
        
        # Check if "base_name counter" doesn't exist at all
        if not MaterialWarehouse.objects.filter(material_name=check_name).exists():
            # Found a gap or reached beyond existing counters
            return check_name
        
        counter += 1