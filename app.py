import json
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
        return {
            "id": self.id,
            "item type": "equipment",
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
        self.item = []

    def load(self):
        """load Json data and create python objects."""
        with self.filename.open("r", encoding="utf-8") as file:
            data = json.load(file)

        inventory = data.get("inventory", {})
        self.items = []

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
                self.items.append(item)

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
            self.items.append(item)

        return self.items

    # ============================================================
    # SAVE INVENTORY DATA
    # ============================================================

    def save(self):
        # Save a items using the same nested structure as migrate.py.
        inventory = {
            "equipment": {},
            "materials": {},
        }

        for item in self.items:
            if isinstance(item, Reagent):
                category = item.category
                inventory["materials"].setdefault(category, {})

                inventory["materials"][category][item.id] = item.to_dict()

            elif isinstance(item, Equipment):
                category = item.category
                inventory["equipment"].setdefault(category, [])

                inventory["equipment"][category].append(item.to_dict())

        data = {"inventory": inventory}

        with self.filename.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.write("\n")

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
                lambda item: isinstance(item, Reagent),
                self.items,
        )

        results = []

# Check each reagent's expiry date
        for reagent in reagents:
            expiry_date = parse_date(reagent.expiry_date)

# Skip missing 
            if expiry_date is None:
                continue

# Keep reagents expiring inside the window
            if reference_date <= expiry_date <= end_date:
                results.append(reagent)

        return results
    
# Method Two: Equipment needing maintenance filter with lambda

# Method Three: Inventory summary map with lambda

# End of Task 4

    def list_items(self):
        """Return a summery of all inventory items."""
        return [
            f"{item.id}: {item.name}({item.category} - {item.type})"
            for item in self.items
        ]


# ============================================================
# MAIN PROGRAM EXECUTION
# ============================================================

if __name__ == "__main__":
    manager = InventoryManager()

    try:
        manager.load()

        print(f"loaded {len(manager.items)} inventory items.\n")

        for item in manager.list_items():
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

    except FileNotFoundError:
        print(f"Inventory file not found: {INVENTORY_FILE}")

    except (json.JSONDecodeError, ValueError) as error:
        print(f"Could not load inventory: {error}")
