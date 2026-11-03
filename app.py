
import json
from abc import ABC, abstractmethod
from datetime import date, datetime,timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve(). parent
INVENTORY_FILE= BASE_DIR / "inventory.json"


class InventoryItem(ABC):
    """Base class for all inventory items."""

    def __init__(self, item_id, name, item_type):
        self.id = item_id
        self.name = name
        self.type = item_type

    @abstractmethod 
    def to_dict(self):
        """Convert the item into a dictionary.""" 
        pass


class Reagent(InventoryItem):
    """Represent a chemical reagent."""

    def __init__(
            self, item_id, name,quantity,
            purchase_date,expiry_date,manufacturer
    ):
        super().__init__(item_id, name, "regent")
        self.quantity = quantity
        self.purchase_date = purchase_date
        self. expiry_date = expiry_date
        self.manufacturer = manufacturer

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "quantity": self.quantity,
            "purchase_dat": self.purchase_date,
            "expiry_date": self.expiry_date,
            "manufacturer": self.manufacturer,
        }


class Equipment(InventoryItem):
    """Represent laboratory equipment."""

    def __init__(
            self,item_id, name, location, status,
            last_maintenance_date, notes
    ):
        super().__init__(item_id, name ,"equipment")
        self.location = location
        self.notes = notes
        self.last_maintenance_date = last_maintenance_date
        self.notes = notes

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "location": self.location,
            "status": self.status,
            "last_maintenance_date": self.last_maintenance_date,
            "notes": self.notes,

        }

    def parse_date(value):
        """convert an 150 date string in to a date object."""
        if not value:
            return None

        return datetime.strptime(value, "%y-%m-%d").date()


