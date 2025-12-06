# CT Synthetic Free Text Reports Generator

This repository generates **synthetic Hebrew CT radiology reports** for:

- Instruction–response datasets (e.g. for instruction-tuned models)
- NER (Named Entity Recognition) training

It uses hand-crafted templates, fills anonymized placeholders with randomized but realistic values, and exports:

- An **Excel** file with `instruction` and `response` columns
- A **JSON** file with NER-style entity annotations (character offsets + labels)

---

## Table of Contents

1. [Overview](#overview)
2. [Repository Structure](#repository-structure)
3. [Installation](#installation)
4. [Usage](#usage)
   - [Command-line Usage](#command-line-usage)
   - [Python API Usage](#python-api-usage)
5. [Generated Data Format](#generated-data-format)
   - [Excel File](#excel-file)
   - [NER JSON File](#ner-json-file)
6. [Templates Module](#templates-module)
7. [Configuration & Extension](#configuration--extension)
8. [Notes](#notes)
9. [License](#license)

---

## Overview

The generator creates synthetic CT reports in Hebrew by:

1. Sampling a template from a list of CT report templates.
2. Identifying anonymized tags such as:
   - `<תאריך_קודם_>`
   - `<ממצא_>`, `<ממצאים_>`
   - `<גודל_>`
   - `<המלצה_>`
3. Replacing these tags with:
   - Realistic dates using `Faker('he_IL')`
   - Random clinical entities (like: findings, sizes, and recommendations) from predefined lists
4. Recording the **character spans** and **labels** of these inserted values for NER training.
5. Saving the result to:
   - An Excel file (`instruction`, `response`)
   - A JSON file (NER annotations), while preserving previous runs.

---

## Repository Structure

Typical layout:

```text
.
├── main_script.py
├── templates
│       └── CTAbdomenAndPelvis_template.py
├── data
│   ├── train_synthetic_data.xlsx      # created/updated by the script
│   └── ner_train_data.json            # created/updated by the script
└── README.md
```

### `main_script.py`

Main entry point. Responsibilities:

- Generate synthetic CT records.
- Replace anonymized tags in templates with concrete values.
- Collect NER entities (start, end, label).
- Append to/initialize:
  - Excel file with instruction/response pairs.
  - JSON file with NER annotations.
- Expose CLI parameters via `argparse`:
  - `--num-records`
  - `--excel-output-path`
  - `--json-output-path`

### `templates/CTAbdomenAndPelvis_template.py`

Template module, imported as:

```python
from templates.CTAbdomenAndPelvis_template import (
    CTAbdomenAndPelvis,
    individual_finding,
    many_findings,
    recommendations,
    prev_date_options,
)
```

Contains:

- `CTAbdomenAndPelvis`: list of base CT abdomen & pelvis report templates (with placeholders).
- `individual_finding`, `many_findings`: text snippets for single/multiple findings.
- `recommendations`: possible recommendation sentences.
- `prev_date_options`: patterns for previous-study statements containing `<תאריך_>`.

---

## Installation

### Python Version

- Python **3.8+** (3.9+ recommended)

### Dependencies

Install requirements (you can put these in a `requirements.txt` if you like):

- `faker`
- `pandas`
- `tqdm`
- `openpyxl` (Excel writer engine used by `pandas.to_excel`)

Install via:

```bash
pip install faker pandas tqdm openpyxl
```

If you’re using a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install faker pandas tqdm openpyxl
```

---

## Usage

### Command-line Usage

From the repository root:

```bash
python main_script.py
```

This runs with the **default behavior**:

- Generates **100** synthetic records.
- Appends them to:

  - `./data/train_synthetic_data.xlsx`

- Merges NER annotations into:

  - `./data/ner_train_data.json`

#### CLI Arguments

`main_script.py` uses `argparse` and supports:

- `--num-records`  
  Number of synthetic records to generate.  
  **Default:** `100`

- `--excel-output-path`  
  Path to the Excel file for instruction/response pairs.  
  **Default:** `./data/train_synthetic_data.xlsx`

- `--json-output-path`  
  Path to the JSON file for NER annotations.  
  **Default:** `./data/ner_train_data.json`

#### Examples

Generate 500 records (default output locations):

```bash
python main_script.py --num-records 500
```

Custom Excel and JSON paths:

```bash
python main_script.py \
  --num-records 250 \
  --excel-output-path ./data/ct_train_250.xlsx \
  --json-output-path ./data/ct_ner_250.json
```

### Python API Usage

You can import and call the generator directly in Python:

```python
from main_script import run_generation

run_generation(
    additional_records=200,
    excel_output_path="./data/custom_train_synthetic_data.xlsx",
    json_output_path="./data/custom_ner_train_data.json",
)
```

This reuses the exact same generation logic as the CLI.

---

## Generated Data Format

### Excel File

Default path: `./data/train_synthetic_data.xlsx`

Columns:

- `instruction`  
  The **de-anonymized text** (all placeholders replaced with concrete values).

- `response`  
  The **original template text** used as the “target” / reference.

Each row corresponds to one generated record.

### NER JSON File

Default path: `./data/ner_train_data.json`

Structure (simplified):

```json
{
  "0": [
    { "start": 10, "end": 25, "label": "prev_date" },
    { "start": 40, "end": 55, "label": "finding" }
  ],
  "1": [
    { "start": 5, "end": 12, "label": "size" }
  ]
}
```

- **Keys**: numeric strings (`"0"`, `"1"`, …) identifying each record.
- **Values**: lists of entities, where each entity has:
  - `start`: character offset in the de-anonymized text (inclusive)
  - `end`: character offset in the de-anonymized text (exclusive)
  - `label`: e.g. `"prev_date"`, `"finding"`, `"size"`, `"recommendations"`

Multiple runs:

- If the JSON file already exists, the script:
  - Reads existing keys.
  - Computes the max key.
  - Offsets new keys by `max_key + 1` so previous entries are preserved.
  - Merges and writes back.

---

## Templates Module

The template file `CTAbdomenAndPelvis_for_thesis.py` defines:

- Template texts for CT abdomen & pelvis, including placeholders like:
  - `<תאריך_קודם_>`
  - `<ממצא_>`
  - `<ממצאים_>`
  - `<גודל_>`
  - `<המלצה_>`
- Lists of candidate replacements for each placeholder.

The main script:

1. Samples a template from `CTAbdomenAndPelvis`.
2. Calls `get_non_anonymized_record(response)`:
   - Finds all tags matching `(<[א-ת_]+>)`.
   - Replaces each tag according to its type:
     - `<תאריך_קודם_>` → a text from `prev_date_options` with a replaced `<תאריך_>` date.
     - `<ממצא_>` → a single random finding from `individual_finding`.
     - `<ממצאים_>` → a composite finding from `many_findings`.
     - `<גודל_>` → random size + units (cm/mm).
     - `<המלצה_>` → a random element from `recommendations`.
   - Records the character spans and labels in `entities`.

This core flow has **not** been changed; only parameterization and CLI parsing have been added.

---

## Configuration & Extension

To extend the generator:

- **New record types**  
  Add additional template lists (e.g. `CTChest`, `CTHead`) to the templates module and extend:

  ```python
  def generate_medical_records(record_type):
      if record_type == "CT בטן ואגן":
          ...
      elif record_type == "CT חזה":
          ...
  ```

- **Additional placeholder types**  
  Add new tag patterns (e.g. `<מיקום_>`) and extend the `get_non_anonymized_record` function with another `elif` block that:
  - Chooses a replacement string.
  - Updates `new_res`.
  - Appends an entity with the appropriate label.

---

## Notes

- Generated reports are **synthetic**, written in **Hebrew**, and are intended for **research/experimentation** only.
- No random seed is set by default, so each run produces different data.
  - For reproducibility, you can manually set:

    ```python
    import random
    from faker import Faker

    random.seed(42)
    fake = Faker('he_IL')
    fake.seed_instance(42)
    ```

---

## License

MIT
