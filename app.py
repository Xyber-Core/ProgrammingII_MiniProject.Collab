import json
import os
import tempfile
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from pathlib import Path

INVENTORY_FILE = Path(__file__).resolve().parent / "inventory.json"
# ============================================================
# DATE PARSING
# ============================================================


def parse_date(value):
    """convert an 150 date string into a date object."""
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ============================================================
# ABSTRACT INVENTORY ITEM CLASS
# ============================================================


class InventoryItem(ABC):
    """Base class for all inventory items."""

    def __init__(self, item_id, name, category, item_type):
        self.id = item_id
        self.name = name
        self.category = category
        self.type = item_type

    @abstractmethod
    def to_dict(self):
        """Convert the item into a dictionary."""
        pass


# ============================================================
# REAGENT CLASS
# ============================================================


class Reagent(InventoryItem):
    """Represent a chemical reagent."""

    def __init__(
        self,
        item_id,
        name,
        category,
        quantity,
        purchase_date,
        expiry_date,
        manufacturer,
    ):
        super().__init__(item_id, name, category, "reagent")

        self.quantity = quantity
        self.purchase_date = purchase_date
        self.expiry_date = expiry_date
        self.manufacturer = manufacturer

    def to_dict(self):
        """Return the reagent as a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "itemType": "reagent",
            "quantity": self.quantity,
            "purchaseDate": self.purchase_date,
            "expiryDate": self.expiry_date,
            "manufacturer": self.manufacturer,
        }


# ============================================================
# EQUIPMENT CLASS
# ============================================================


class Equipment(InventoryItem):
    """Represent laboratory equipment."""

    def __init__(
        self,
        item_id,
        name,
        category,
        location,
        status,
        maintenance,
    ):
        super().__init__(item_id, name, category, "equipment")

        self.location = location
        self.status = status
        self.maintenance = maintenance or []

    @property
    def last_maintenance_date(self):
        """Return the most recent recorded maintenance date"""
        dates = [
            parsed
            for record in self.maintenance
            if (parsed := parse_date(record.get("date"))) is not None
        ]

        return max(dates) if dates else None

    def to_dict(self):
        """Return the equipment as a dictionary."""
        return {
            "id": self.id,
            "itemType": "equipment",
            "name": self.name,
            "location": self.location,
            "statusLabel": self.status,
            "maintenance": self.maintenance,
        }


# ============================================================
# INVENTORY MANAGER
# ============================================================


class InventoryManager:
    """Manage, load, report on, and save inventory items."""

    def __init__(self, filename=INVENTORY_FILE):
        self.filename = Path(filename)
        self.items = {}
        self.equipment_categories = []
        self.material_categories = []

    def add_item(self, item):
        """Add an inventory item with a unique, non-empty ID."""
        if not isinstance(item, InventoryItem):
            raise TypeError("Expected an InventoryItem")
        if not item.id:
            raise ValueError("Item ID must not be empty")
        if item.id in self.items:
            raise ValueError(f"The ID {item.id} already exists")
        self.items[item.id] = item

    def find_item(self, item_id):
        """Return an item by ID, or None if it is absent."""
        return self.items.get(item_id)

    def update_item(self, item_id, **changes):
        """Update an item's fields while keeping its ID and type."""
        item = self.find_item(item_id)
        if item is None:
            raise KeyError(f"Unknown item ID: {item_id}")

        allowed = {"name", "category"}
        if isinstance(item, Reagent):
            allowed.update({"quantity", "purchase_date",
                            "expiry_date", "manufacturer"})
        else:
            allowed.update({"location", "status", "maintenance"})

        for field in changes:
            if field not in allowed:
                raise ValueError(f"Field cannot be updated: {field}")

        for field, value in changes.items():
            setattr(item, field, value)
        return item

    def remove_item(self, item_id):
        """Remove an item by ID, or None if it is absent."""
        return self.items.pop(item_id, None)

    def load(self):
        """load Json data and create python objects."""
        with self.filename.open("r", encoding="utf-8") as file:
            data = json.load(file)

        inventory = data.get("inventory", {})
        self.items = {}
        self.material_categories = list(inventory.get("materials", {}))
        self.equipment_categories = list(inventory.get("equipment", {}))

        # load materials grouped by category.
        materials = inventory.get("materials", {})

        for category, records in materials.items():
            for record in records.values():
                item = Reagent(
                    record.get("id"),
                    record.get("name"),
                    category,
                    record.get("quantity"),
                    record.get("purchaseDate"),
                    record.get("expiryDate"),
                    record.get("manufacturer"),
                )
                self.add_item(item)

        # load equipment grouped by category.
        equipment_groups = inventory.get("equipment", {})

        for category, records in equipment_groups.items():
            for record in records:
                item = Equipment(
                    record.get("id"),
                    record.get("name"),
                    category,
                    record.get("location"),
                    record.get("statusLabel"),
                    record.get("maintenance"),
                )
                self.add_item(item)

        return list(self.items.values())

    # ============================================================
    # SAVE INVENTORY DATA
    # ============================================================

    def save(self):
        """Save the inventory items to the JSON"""
        # Save a items using the same nested structure as migrate.py.
        inventory = {
            "equipment": {name: [] for name in self.equipment_categories},
            "materials": {name: {} for name in self.material_categories},
        }

        for item in self.items.values():
            if isinstance(item, Reagent):
                category = item.category
                inventory["materials"].setdefault(category, {})

                inventory["materials"][category][item.id] = item.to_dict()

            elif isinstance(item, Equipment):
                category = item.category
                inventory["equipment"].setdefault(category, [])

                inventory["equipment"][category].append(item.to_dict())

        data = {"inventory": inventory}

        temporary_name = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.filename.parent,
                prefix=".inventory-",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_name = file.name
                json.dump(data, file, indent=2, ensure_ascii=False)
                file.write("\n")
            os.replace(temporary_name, self.filename)
        finally:
            if temporary_name and os.path.exists(temporary_name):
                os.unlink(temporary_name)

    # ========================================================
    # INVENTORY REPORTING FUNCTIONS
    # ========================================================

    # Task 4

    # Method One: Expiring reagents filter with lambda
    def expiring_reagents(self, reference_date, days=90):
        """Find reagents expiring within the chosen date window"""
        end_date = reference_date + timedelta(days=days)

        # Select reagent items
        reagents = filter(
            lambda item: (
                isinstance(item, Reagent)
                and (expiry_date := parse_date(item.expiry_date)) is not None
                and reference_date <= expiry_date <= end_date
            ),
            self.items.values(),
        )

        return list(reagents)

    # Method Two: Equipment needing maintenance filter with lambda
    def equipment_needing_maintenance(self, reference_date, days=365):
        """Find equipment that is offline or needs maintenance."""
        cutoff_date = reference_date - timedelta(days=days)

        # Select equipment items
        equipment = filter(
            lambda item: (
                isinstance(item, Equipment)
                and (
                    item.status == "offline"
                    or item.last_maintenance_date is None
                    or item.last_maintenance_date < cutoff_date
                )
            ),
            self.items.values(),
        )

        return list(equipment)

    # Method Three: Inventory summary map with lambda
    def inventory_summary(self):
        """Return a short summary of every inventory item"""
        # Create a line of text for each item
        results = map(
            lambda item: f"{item.id}: {item.name} ({item.type})",
            self.items.values(),
        )

        return list(results)

    # End of Task 4

    def list_items(self):
        """Return a summery of all inventory items."""
        return [
            f"{item.id}: {item.name}({item.category} - {item.type})"
            for item in self.items.values()
        ]


# ============================================================
# MAIN PROGRAM EXECUTION
# ============================================================

if __name__ == "__main__":
    manager = InventoryManager()

    try:
        manager.load()

        print(f"loaded {len(manager.items)} inventory items.\n")
        # Run Method Three:
        for item in manager.inventory_summary():
            print(item)

        # Fixed reference date makes testing reproducible.
        reference_date = date(2026, 1, 1)

        expiring = manager.expiring_reagents(reference_date, days=90)

        print("\nReagents expiring within 90 days:")

        for item in expiring:
            print(f"-{item.name}: {item.expiry_date}")

        maintenance = manager.equipment_needing_maintenance(
            reference_date,
            days=365,
        )

        print("\nEquipment needing maintenance")

        for item in maintenance:
            print(f"- {item.name}: {item.status}")

        # Demonstrate saving and reloading a separate copy
        saved_file = INVENTORY_FILE.with_name("inventory_saved.json")
        saved_manager = InventoryManager(saved_file)
        for item in manager.items.values():
            saved_manager.add_item(item)
        saved_manager.save()
        saved_manager.load()
        print(f"\nSaved and reloaded {len(saved_manager.items)} items.")

    except FileNotFoundError:
        print(f"Inventory file not found: {INVENTORY_FILE}")

    except (json.JSONDecodeError, ValueError, KeyError, OSError) as error:
        print(f"Could not load inventory: {error}")
