import csv
import json
import logging
import math
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------
# Settings
# ---------------------------------------------------------------

BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "legacy_inventory.csv"
JSON_FILE = BASE_DIR / "legacy_equipment.json"
OUTPUT_FILE = BASE_DIR / "inventory.json"
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y")
UNITS = {"g": "g", "kg": "kg", "ml": "mL", "l": "L"}
ID_KEYS = ["ID", "item_id", "equipment_id"]
MAINTENANCE_KEYS = ["last_maintenance", "last_maintenance_date"]

MATERIALS_CATEGORIES = {
    "sodium chloride": "Chemicals",
    "hydrochloric acid": "Acids",
    "distilled water": "Liquids",
    "ethanol": "Liquids",
    "acetic acid": "Acids",
    "potassium permanganate": "Chemicals",
    "silver nitrate": "Chemicals",
    "copper sulfate": "Chemicals",
}

EQUIPMENT_CATEGORIES = {
    "centrifuge": "Laboratory Equipment",
    "microscope": "Optical Equipment",
    "spectrophotometer": "Optical Equipment",
    "magnetic stirrer": "Laboratory Equipment",
    "ph meter": "Laboratory Equipment",
    "autoclave": "Sterilization Equipment",
}
STATUS_VALUES = {
    "online": "online",
    "offline": "offline",
    True: "online",
    False: "offline",
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger("migrate")

# ---------------------------------------------------------------
# Phase I: Read the two outdated files.
# ---------------------------------------------------------------


def read_csv(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def read_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# ---------------------------------------------------------------
# Phase II: Small helper functions, one for each cleaning rule.
# ---------------------------------------------------------------


def clean_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def fix_name(name):
    name = clean_text(name)
    return name.title() if name else None


def fix_date(value):
    value = clean_text(value)
    if not value:
        return None
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).strftime("%Y-%m-%d")
        except ValueError:
            continue
    LOGGER.warning("Could not read the date %r, saved as null", value)
    return None


def split_quantity(value):
    value = clean_text(value)
    if not value:
        return None

    position = 0
    while position < len(value) and (
        value[position].isdigit() or value[position] == "."
    ):
        position += 1

    number_part = value[:position]
    unit_part = value[position:].strip().lower()
    try:
        number = float(number_part)
        if not math.isfinite(number) or number < 0:
            raise ValueError("Quantity must be finite and non-negative")
    except ValueError:
        LOGGER.warning("Invalid Quantity %r saved as null", value)
        return None

    if not unit_part:
        LOGGER.warning("Missing unit in quantity %r, saved as null", value)
        return None
    if unit_part not in UNITS:
        LOGGER.warning("Unknown unit %r in quantity %r", unit_part, value)
        return None

    if number.is_integer():
        number = int(number)
    return {"value": number, "unit": UNITS[unit_part]}


def make_slug(name):
    slug = ""
    for character in name.lower():
        if character.isalnum():
            slug += character
        elif slug and not slug.endswith("-"):
            slug += "-"
    return slug.strip("-")


def fix_status(value):
    if isinstance(value, str):
        value = value.strip().lower()
    if isinstance(value, (bool, str)) and value in STATUS_VALUES:
        return STATUS_VALUES[value]
    LOGGER.warning("Unknown status %r, saved as null", value)
    return None


def get_first_key(record, keys):
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


# ---------------------------------------------------------------
# Phase III: Rebuild the CSV materials.
# ---------------------------------------------------------------


def clean_reagent(row):
    name = fix_name(row.get("item_name"))
    category = MATERIALS_CATEGORIES.get(
        name.casefold() if name else "", "Uncategorized"
    )
    return {
        "name": name,
        "category": category,
        "itemType": "reagent",
        "quantity": split_quantity(row.get("quantity")),
        "purchaseDate": fix_date(row.get("purchase_date")),
        "expiryDate": fix_date(row.get("expiry_date")),
        "manufacturer": clean_text(row.get("manufacturer")),
    }


def merge_duplicates(reagents):
    materials = {}
    for reagent in reagents:
        name = reagent["name"]
        if not name:
            LOGGER.warning("Skipping material with no name.")
            continue

        normalized_name = name.casefold()
        quantity = reagent["quantity"]
        if normalized_name not in materials:
            materials[normalized_name] = dict(reagent)
            continue

        existing = materials[normalized_name]
        existing_quantity = existing["quantity"]
        if quantity is None:
            LOGGER.warning("Skipping missing quantity for duplicate %s", name)
            continue
        if existing_quantity is None:
            existing["quantity"] = quantity
            continue
        if existing_quantity["unit"] != quantity["unit"]:
            raise ValueError(
                f"Cannot merge {name}: units differ "
                f"({existing_quantity['unit']} and {quantity['unit']})"
            )

        existing_quantity["value"] += quantity["value"]
        LOGGER.info(
            "Merged duplicate: %s (%s %s)",
            name,
            existing_quantity["value"],
            existing_quantity["unit"],
        )
    return materials


def add_material_ids(materials):
    used_ids = set()
    for material in materials.values():
        base_id = make_slug(material["name"])
        material_id = base_id
        suffix = 2
        while material_id in used_ids:
            material_id = f"{base_id}-{suffix}"
            suffix += 1
        material["id"] = material_id
        used_ids.add(material_id)
    return materials


def format_materials(materials):
    result = {}
    for material in materials.values():
        material_id = material["id"]
        category = material["category"]
        result.setdefault(category, {})
        result[category][material_id] = {
            "id": material_id,
            "name": material["name"],
            "itemType": material["itemType"],
            "purchaseDate": material["purchaseDate"],
            "expiryDate": material["expiryDate"],
            "manufacturer": material["manufacturer"],
            "quantity": material["quantity"],
        }
    return result


# ---------------------------------------------------------------
# Phase IV: Rebuild the JSON equipment.
# ---------------------------------------------------------------


def clean_equipment(record, index):
    equip_id = clean_text(get_first_key(record, ID_KEYS))
    if not equip_id:
        equip_id = f"EQ-{index:03d}"
    equipment_type = clean_text(record.get("type"))
    maintenance_date = fix_date(get_first_key(record, MAINTENANCE_KEYS))
    maintenance_note = clean_text(record.get("notes"))

    return {
        "id": equip_id,
        "itemType": "equipment",
        "name": equipment_type,
        "location": clean_text(record.get("location")),
        "statusLabel": fix_status(record.get("status")),
        "maintenance": [{"date": maintenance_date, "note": maintenance_note}],
    }


def group_equipment(records):
    grouped = {}
    used_ids = set()
    for index, record in enumerate(records, start=1):
        equipment = clean_equipment(record, index)
        base_id = equipment["id"]
        equip_id = base_id
        suffix = 2
        while equip_id in used_ids:
            equip_id = f"{base_id}-{suffix}"
            suffix += 1
        equipment["id"] = equip_id
        used_ids.add(equip_id)

        name = equipment["name"]
        group_name = EQUIPMENT_CATEGORIES.get(
            name.casefold() if name else "", "Uncategorized"
        )
        grouped.setdefault(group_name, []).append(equipment)
    return grouped


# ---------------------------------------------------------------
# Phase V: Build and save the final inventory
# ---------------------------------------------------------------


def main():
    try:
        rows = read_csv(CSV_FILE)
        equipment_records = read_json(JSON_FILE)
        if not isinstance(equipment_records, list):
            raise ValueError("Equipment must be a JSON format")

        reagents = [clean_reagent(row) for row in rows]
        materials = merge_duplicates(reagents)
        add_material_ids(materials)
        equipment = group_equipment(equipment_records)

        inventory = {
            "inventory": {
                "equipment": equipment,
                "materials": format_materials(materials),
            }
        }

        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            json.dump(inventory, file, indent=2, ensure_ascii=False)
            file.write("\n")

    except (
        ValueError, FileNotFoundError, json.JSONDecodeError, OSError
    ) as error:
        LOGGER.error("Migration stopped: %s", error)
        return False

    LOGGER.info(
        "Saved %d material groups and %d equipment groups to %s",
        len(materials), sum(len(group) for group in equipment.values()),
        OUTPUT_FILE,
    )
    return True


if __name__ == "__main__":
    main()
