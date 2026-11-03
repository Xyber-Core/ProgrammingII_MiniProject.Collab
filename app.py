
import json
from abc import ABC, abstractmethod
from datetime import date, datetime,timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve(). parent
INVENTORY_FILE_= BASE_DIR / "inventory.jason"


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