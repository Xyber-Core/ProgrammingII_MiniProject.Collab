import csv
import json
import logging
from datetime import datetime

# ---------------------------------------------------------------
# Settings
# ---------------------------------------------------------------

csv_file = "legacy_inventory.csv"
json_file = "legacy_equipment.json"
output_file = "inventory"
date_formats = ["%Y-%m-%d", "%d/%m/%Y"]
units = {"g": "g", "kg": "kg", "ml": "mL", "l": "L"}
ID_keys = ["ID", "item_id", "equipment_id"]
maintenance_keys = ["last_maintenance", "last_maintenance_date"]

status_values = {
    "online": "online",
    "offline": "offline",
    True: "online",
    False: "offline",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("migrate")

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

    for date_format in date_formats:
        try:
            return datetime.strptime(
                value, date_format
                ).strftime("%Y-%m-%d")
        except ValueError:
            continue

    logger.warning("Could not read the date %r, saved as null", value)
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
    except ValueError:
        logger.warning("Could not read the quantity %r", value)
        return None

    if number.is_integer():
        number = int(number)

    unit = units.get(unit_part, unit_part)
    return {"value": number, "unit": unit}


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

    if value in status_values:
        return status_values[value]

    logger.warning("Unknown status %r, saved as null", value)
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
    return {
        "name": fix_name(row.get("item_name")),
        "itemType": "reagent",
        "quantity": split_quantity(row.get("quantity")),
        "purchaseDate": fix_date(row.get("purchase_date")) or "",
        "expiryDate": fix_date(row.get("expiry_date")) or "",
        "manufacturer": clean_text(row.get("manufacturer")) or "",
    }


def merge_duplicates(reagents):
    materials = {}

    for reagent in reagents:
        name = reagent["name"]

        if not name:
            logger.warning("Skipping material with no name.")
            continue

        slug = make_slug(name)
        quantity = reagent["quantity"]

        if slug not in materials:
            materials[slug] = {
                "name": name,
                "itemType": reagent["itemType"],
                "purchaseDate": reagent["purchaseDate"],
                "expiryDate": reagent["expiryDate"],
                "manufacturer": reagent["manufacturer"],
                "quantity": quantity,
            }
            continue
        existing = materials[slug]
        existing_quantity = existing["quantity"]

        if quantity is None:
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

        logger.info(
            "Merged duplicate%s: %s %s",
            name,
            existing_quantity["value"],
            existing_quantity["unit"],
        )

    return materials


def add_material_ids(materials):
    for number, material in enumerate(materials.values(), start=1):
        material["itemID"] = f"MT-{number:03d}"

    return materials


def format_materials(materials):
    result = {}

    for slug, material in materials.items():
        quantity = material["quantity"]

        result[slug] = [{
            "itemID": material["itemID"],
            "itemType": material["itemType"],
            "purchaseDate": material["purchaseDate"],
            "expiryDate": material["expiryDate"],
            "manufacturer": material["manufacturer"],
            "quantity": [quantity] if quantity is not None else [],
        }]

    return result


# ---------------------------------------------------------------
# Phase IV: Rebuild the JSON equipment.
# ---------------------------------------------------------------

def clean_equipment(record, index):
    equip_id = clean_text(get_first_key(record, ID_keys))

    if not equip_id:
        equip_id = f"EQ-{index:03d}"

    equipment_type = clean_text(record.get("type")) or "Unknown"

    maintenance_date = fix_date(
        get_first_key(record, maintenance_keys)
    ) or ""

    maintenance_note = clean_text(record.get("notes")) or ""

    return {
        "equipID": equip_id,
        "equipmentType": equipment_type,
        "statusLabel": fix_date(record.get("status")) or "",
        "maintenance": [{
            "date": maintenance_date,
            "note": maintenance_note,
        }],
    }


def group_equipment(records):
    grouped = {}

    for index, record in enumerate(records, start=1):
        equipment = clean_equipment(record, index)

        group_name = (
            clean_text(record.get("category"))
            or "Laboratory"
        )

        grouped.setdefault(group_name, []).append(equipment)

    return grouped
