# 🧪 Chemistry Inventory Management System

**BACT 7601 — Programming II | Assessment 2: “Legacy Lab” Overhaul**  
*A collaborative Python project for modernising laboratory inventory data.*

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
![Data](https://img.shields.io/badge/Data-CSV%20%2B%20JSON-333333)
![Project](https://img.shields.io/badge/Project-Academic%20Assessment-7856C5)
![Status](https://img.shields.io/badge/Status-Completed-238636)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **From inconsistent legacy records to one structured inventory.** The system cleans and merges chemical-reagent data, normalises laboratory equipment, and provides an object-oriented application with persistent storage and functional reports.

**Repository:** [Xyber-Core / ProgrammingII_MiniProject.Collab](https://github.com/Xyber-Core/ProgrammingII_MiniProject.Collab) · **Development history:** [View commits](https://github.com/Xyber-Core/ProgrammingII_MiniProject.Collab/commits/main)

---

## 📑 Contents

- [🔎 Overview](#overview)
- [📁 Repository structure](#repository-structure)
- [🧾 1. Analysis of legacy data](#legacy-data)
- [🗂️ 2. Unified JSON schema](#schema)
- [🔄 3. Data migration](#migration)
- [🏗️ 4. Object-oriented application](#oop)
- [📊 5. Functional reporting](#reports)
- [✅ 6. Code quality and verification](#quality)
- [👥 7. Team and contributions](#team)
- [🎓 Assessment information](#assessment)
- [🔐 Security and license](#license)

---

<a id="overview"></a>

## 🔎 Overview

The university chemistry laboratory had two separate legacy data sources: a CSV file containing chemical reagents and a JSON file containing laboratory equipment. The records had inconsistent identifiers, date formats, capitalisation, status values and missing fields. Some reagent entries also represented the same material more than once.

This project provides two complementary Python programs:

- **`migrate.py`** reads the legacy files, validates and standardises their values, merges duplicate reagents, assigns consistent identifiers and creates **`inventory.json`**.
- **`app.py`** loads that JSON into an object-oriented inventory manager, supports item lookup and changes, produces reports, and demonstrates saving and reloading the inventory.

### ✨ Verified results with the supplied sample data

| Result | Value |
| :--- | ---: |
| Legacy reagent rows | **10** |
| Unique reagents after migration | **8** |
| Equipment records | **6** |
| Total inventory items loaded | **14** |
| Sodium Chloride after merging | **700 g** |
| Ethanol after merging | **3,500 mL** |
| Items saved and reloaded by `app.py` | **14** |

The application uses only the **Python standard library** at runtime. Flake8 is an optional development tool.

<a id="repository-structure"></a>

## 📁 Repository structure

```text
ProgrammingII_MiniProject.Collab/
├── .gitattributes          # Git file-type classification
├── LICENSE                 # MIT license
├── README.md               # Project overview and assessment documentation
├── SECURITY.md             # Security reporting guidance
├── app.py                  # OOP model, inventory manager and reports
├── inventory.json          # Unified inventory dataset
├── inventory_saved.json    # Example save/reload output
├── legacy_equipment.json   # Original laboratory equipment records
├── legacy_inventory.csv    # Original chemical-reagent records
└── migrate.py              # Legacy-data migration and cleaning
```

No external Python package is required to run the two application scripts.

---

<a id="legacy-data"></a>

## 🧾 1. Analysis of legacy data

### `legacy_inventory.csv` — chemical reagents

| Original problem | Example from the source data | How it is handled |
| :--- | :--- | :--- |
| Mixed letter case | `sodium chloride` / `SODIUM CHLORIDE`; `Ethanol` / `ethanol` | Names are normalised before comparison. |
| Duplicate materials | Sodium Chloride appears as `500g` and `200g`; Ethanol appears as `2500ml` and `1000ml` | Records are merged by normalised name and same-unit quantities are summed. |
| Mixed date formats | `2023-01-15` and `15/05/2023` | Supported dates become `YYYY-MM-DD`. |
| Missing values | Distilled Water and Silver Nitrate have no expiry date; Acetic Acid has no manufacturer | Missing information is represented as JSON `null`. |
| Quantity stored as text | `500g`, `1L`, `2500ml` | Quantity is split into a number and a standardised unit label. |
| No reagent IDs | The CSV has no identifier column | Unique slug-style IDs are generated from reagent names. |
| Conflicting duplicate metadata | Duplicate rows can have different purchase or expiry dates | The first record's descriptive fields are retained while quantities are combined. |

### `legacy_equipment.json` — laboratory equipment

| Original problem | How it is handled |
| :--- | :--- |
| Identifiers appear under `ID`, `item_id` and `equipment_id` | All equipment uses the `id` field in the new schema. |
| Statuses mix strings and booleans | `online`, `offline`, `true` and `false` are normalised to consistent string labels. |
| Maintenance dates use `last_maintenance` or `last_maintenance_date` | Both forms are read and stored in the same `maintenance` structure. |
| Optional notes are missing from some records | Missing notes are retained as `null`. |
| Equipment needs consistent grouping | Equipment is organised into descriptive categories. |

<a id="schema"></a>

## 🗂️ 2. Unified JSON schema

The migration creates **one JSON file** containing two category-based branches under `inventory`. All items use common fields — `id`, `name` and `itemType` — with additional fields appropriate to reagents or equipment.

### Example of the resulting structure

```json
{
  "inventory": {
    "equipment": {
      "Optical Equipment": [
        {
          "id": "EQ-001",
          "itemType": "equipment",
          "name": "Microscope",
          "location": "Lab A, Bench 3",
          "statusLabel": "online",
          "maintenance": [
            { "date": "2024-02-18", "note": null }
          ]
        }
      ]
    },
    "materials": {
      "Chemicals": {
        "sodium-chloride": {
          "id": "sodium-chloride",
          "name": "Sodium Chloride",
          "itemType": "reagent",
          "purchaseDate": "2023-01-15",
          "expiryDate": "2028-01-15",
          "manufacturer": "Sigma-Aldrich",
          "quantity": { "value": 700, "unit": "g" }
        }
      }
    }
  }
}
```

This is an **illustrative subset**, not the entire generated `inventory.json`.

### 🆔 Identifier and data rules

- **Reagents:** Normalised names become lowercase hyphenated IDs (for example, `sodium-chloride`). A numeric suffix is added if needed to avoid a reused reagent ID.
- **Equipment:** Existing equipment IDs are preserved when supplied. A synthetic `EQ-###` ID is generated when absent, and suffixes handle repeated equipment IDs.
- **Dates:** Supported input formats are converted to ISO-style `YYYY-MM-DD`; missing or unreadable dates become `null` during migration.
- **Quantities:** Stored as `{"value": number, "unit": string}`. The script recognises `g`, `kg`, `mL` and `L`.
- **Categories:** Unknown reagent or equipment types can be grouped under `Uncategorized`.
- **Missing values:** `null` is used rather than inconsistent empty strings.

### ⚖️ Why this design?

We considered a **single flat list** containing every reagent and equipment item. That would make general iteration straightforward, but our chosen **category-based hierarchy** preserves useful grouping by laboratory item type and supports direct reagent lookup by ID within a material category. Equipment remains a list within each equipment category, while reagents are dictionaries keyed by their generated IDs.

The branches are structurally different, but `app.py` converts both into subclasses of the shared `InventoryItem` base class. This gives the application a consistent object model without requiring identical JSON layouts for every type. Additional categories can be introduced without changing the top-level structure.

<a id="migration"></a>

## 🔄 3. Data migration

`migrate.py` separates the migration into small functions with single, understandable responsibilities:

| Function | Responsibility |
| :--- | :--- |
| `read_csv()`, `read_json()` | Load the original files. |
| `clean_text()`, `fix_name()` | Strip whitespace and standardise names. |
| `fix_date()` | Convert supported date formats. |
| `split_quantity()` | Validate and separate quantities and units. |
| `make_slug()`, `add_material_ids()` | Generate unique reagent IDs. |
| `merge_duplicates()` | Merge same-name reagents by adding compatible quantities. |
| `fix_status()`, `get_first_key()` | Normalise equipment statuses and inconsistent field names. |
| `clean_equipment()`, `group_equipment()` | Rebuild and categorise equipment records. |
| `format_materials()`, `main()` | Assemble and save the unified JSON inventory. |

The migration logs invalid data and file-level errors. If duplicate reagent quantities use different units, the current script **stops rather than silently combining incompatible values**; automatic conversion between `kg`/`g` or `L`/`mL` is not implemented.

<a id="oop"></a>

## 🏗️ 4. Object-oriented application

The application separates item-specific data from inventory management.

| Component | Responsibility |
| :--- | :--- |
| `InventoryItem` | Abstract base class with shared `id`, `name`, category and item type; requires `to_dict()`. |
| `Reagent` | Represents chemicals, quantities, purchase/expiry dates and manufacturers. |
| `Equipment` | Represents instruments, location, status and maintenance history. |
| `InventoryManager` | Loads, stores, changes, reports on and saves inventory items. |

### 🧰 InventoryManager operations

| Method | Behaviour |
| :--- | :--- |
| `load()` | Reads `inventory.json` and creates `Reagent` and `Equipment` objects. |
| `add_item()` | Adds an item; rejects missing or duplicate IDs. |
| `find_item()` | Looks up an item by ID. |
| `update_item()` | Updates permitted fields without changing an item's ID or type. |
| `remove_item()` | Removes an item by ID. |
| `save()` | Serialises objects back into the nested schema. |
| `list_items()` | Returns readable item descriptions. |

For reliability, `save()` writes a temporary JSON file in the destination directory and then replaces the destination file with `os.replace()`. The main program demonstrates persistence using a separate `inventory_saved.json` rather than overwriting the original inventory during its save/reload example.

<a id="reports"></a>

## 📊 5. Functional reporting

Three reporting methods use functional-programming constructs:

| Method | Construct | Result |
| :--- | :--- | :--- |
| `expiring_reagents(reference_date, days=90)` | `filter()` with `lambda` | Reagents whose valid expiry dates fall within the specified date window. |
| `equipment_needing_maintenance(reference_date, days=365)` | `filter()` with `lambda` | Equipment that is offline, has no usable maintenance date, or is overdue. |
| `inventory_summary()` | `map()` with `lambda` | Readable `ID: name (type)` strings for every item. |

The first two methods accept a **reference date**, so tests and demonstrations do not depend on the system clock. Using the sample inventory and **1 January 2026** as the reference date, the 90-day expiry report identifies **Acetic Acid**, and the maintenance report flags **all six equipment records** under its stated rules.

<a id="quality"></a>

## ✅ 6. Code quality and verification

The code is organised into named functions and classes, uses docstrings and logging, and separates migration, modelling, persistence and reporting. Git commit history records the team's changes and reviews.

### Run the checks

```bash
# Optional: install the development-only style checker
python -m pip install flake8

# Check the two Python files
python -m flake8 migrate.py app.py

# Compile and execute the project
python -m compileall -q migrate.py app.py
python migrate.py
python app.py
```

Flake8 normally prints **no output when it detects no violations**. Successful compilation does not replace the functional execution checks.

### Verified sample-data checks

- ✅ Migration creates **8 unique reagent records** and **6 equipment records**.
- ✅ Sodium Chloride merges to **700 g**; Ethanol merges to **3,500 mL**.
- ✅ The inventory manager loads **14 items**.
- ✅ The application reports the expected expiry and maintenance results for its fixed reference date.
- ✅ Saving to `inventory_saved.json` and reloading succeeds with **14 items**.

These are checks of the supplied sample dataset, not a claim of exhaustive automated test coverage.

<a id="team"></a>

## 👥 7. Team and contributions

This is a collaborative assessment. Responsibilities below reflect the team's project report; the repository's [commit history](https://github.com/Xyber-Core/ProgrammingII_MiniProject.Collab/commits/main) provides evidence of individual code changes.

| Team member | Student ID | Main responsibilities | GitHub |
| :--- | :--- | :--- | :--- |
| **Riker Hoch** | 20241490 | Migration implementation, schema organisation, repository coordination and Git management | [@RikerHoch](https://github.com/RikerHoch) |
| **Shatha Abid Ali** | 20251597 | Object-oriented item classes and `app.py` development | [@abidalishatha-wq](https://github.com/abidalishatha-wq) |
| **Caleb Lambert** | 20240970 | Functional reporting features and related documentation in `app.py` | [@caleb444c](https://github.com/caleb444c) |
| **Fatimah Almukhtar** | 20251554 | Data-migration documentation, code readability, commentary and formatting | [@fatimahAlmukhtar](https://github.com/fatimahAlmukhtar) |

### 🔗 Selected Git contribution evidence

| Contributor | Relevant commit example |
| :--- | :--- |
| Riker | [Migration and schema implementation](https://github.com/Xyber-Core/ProgrammingII_MiniProject.Collab/commit/67be8031c386465593c432d7caabf99d5b28e145) |
| Shatha | [Object-oriented model](https://github.com/Xyber-Core/ProgrammingII_MiniProject.Collab/commit/e689c08ba0e1c96cd02b830b93776a857a858693) |
| Caleb | [Functional reporting](https://github.com/Xyber-Core/ProgrammingII_MiniProject.Collab/commit/3d22dbdfdc590cbdf446f490ec1f34898db3495f) |
| Fatimah | [Formatting and readability](https://github.com/Xyber-Core/ProgrammingII_MiniProject.Collab/commit/5e03d3c4e6580ff3d8c6a8116279d2655f155f57) |

The team also collaborated on analysing the original files, discussing the schema, reviewing code and preparing the report. For detailed individual evidence, see the Git history and the submission's contribution statements.

<a id="assessment"></a>

## 🎓 Assessment information

| Detail | Information |
| :--- | :--- |
| Course | **BACT 7601 — Programming II** |
| Assessment | **Assessment 2: “Legacy Lab” Overhaul** |
| Semester | **Semester 2, 2026** |
| Domain | Chemistry laboratory inventory management |
| Main language | Python |
| Data formats | CSV and JSON |

### Learning outcomes demonstrated

1. **Object-oriented programming:** Abstract base classes, inheritance, subclasses and encapsulated responsibilities.
2. **Data structures:** Dictionaries, lists, structured JSON and unique identifiers.
3. **Functional programming:** `filter()`, `map()`, lambdas and comprehensions.
4. **Persistence:** Reading, migrating, serialising and safely saving JSON data.
5. **Collaborative development:** Git commits, clear task allocation, documentation and code-quality checks.

### 📦 Key deliverables

The repository includes `migrate.py`, `app.py`, `inventory.json`, the two original legacy datasets, and supporting documentation. The full assessment report contains the extended analysis, schema justification and individual statements of contribution.

<a id="license"></a>

## 🔐 Security and license

- For security-related issues, follow [SECURITY.md](SECURITY.md).
- This repository includes an **[MIT License](LICENSE)**. See that file for the applicable permissions and conditions.
- This is an **educational project** intended to demonstrate inventory migration, OOP and reporting; it is not presented as a production laboratory information-management system.

---

<p align="center">
  <strong>🧪 Clean data · 🏗️ Maintainable design · 📊 Useful reports</strong><br>
  <sub>Developed collaboratively for BACT 7601 Programming II — Assessment 2, 2026.</sub>
</p>
