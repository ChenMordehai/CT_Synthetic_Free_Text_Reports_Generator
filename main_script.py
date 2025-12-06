# coding utf-8
import os
import random
import re
import secrets
import time
from tqdm import tqdm
from faker import Faker
import pandas as pd
import json
import argparse

from templates.CTAbdomenAndPelvis_template import (
    CTAbdomenAndPelvis,
    individual_finding,
    many_findings,
    recommendations,
    prev_date_options,
)


def get_non_anonymized_record(response):
    new_res = response
    entities = []

    anonymized_pattern = r"(<[א-ת_]+>)"
    all_tags = [
        {"start": match.start(), "end": match.end(), "tag": match.group()}
        for match in re.finditer(anonymized_pattern, new_res)
    ]

    for tag_dict in all_tags:
        # replace prev_date
        if tag_dict['tag'] == "<תאריך_קודם_>":
            date = fake.date_time_this_century()
            date_time_patterns_with_day = ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y"]
            the_date = date.strftime(random.choice(date_time_patterns_with_day))
            prev_date = random.choice(prev_date_options)
            if prev_date.count("<תאריך_>") > 0:
                prev_date = prev_date.replace("<תאריך_>", the_date, 1)
                start_idx = new_res.find("<תאריך_קודם_>")
                end_idx = start_idx + len(prev_date)
                new_res = new_res.replace("<תאריך_קודם_>", prev_date, 1)
                entities.append({"start": start_idx, "end": end_idx, "label": "prev_date"})
            else:
                new_res = new_res.replace("<תאריך_קודם_>", prev_date, 1)

        # replace individual finding
        elif tag_dict['tag'] == "<ממצא_>":
            finding = random.choice(individual_finding)
            start_idx = new_res.find("<ממצא_>")
            end_idx = start_idx + len(finding)
            new_res = new_res.replace("<ממצא_>", finding, 1)
            entities.append({"start": start_idx, "end": end_idx, "label": "finding"})

        # replace many findings
        elif tag_dict['tag'] == "<ממצאים_>":
            m_finding = random.choice(many_findings)
            start_idx = new_res.find("<ממצאים_>")
            end_idx = start_idx + len(m_finding)
            new_res = new_res.replace("<ממצאים_>", m_finding, 1)
            entities.append({"start": start_idx, "end": end_idx, "label": "finding"})

        # replace size
        elif tag_dict['tag'] == "<גודל_>":
            size_uint = ["""סמ""", """ס"מ""", """ממ""", """מ"מ"""]
            size = [f"{random.randrange(1, 12)}", f"{round(random.uniform(0.1, 11.5), 1)}"]
            size_ = f"{random.choice(size)} {random.choice(size_uint)}"
            start_idx = new_res.find("<גודל_>")
            end_idx = start_idx + len(size_)
            new_res = new_res.replace("<גודל_>", size_, 1)
            entities.append({"start": start_idx, "end": end_idx, "label": "size"})

        # replace recommendations
        elif tag_dict['tag'] == "<המלצה_>":
            rec = random.choice(recommendations)
            start_idx = new_res.find("<המלצה_>")
            end_idx = start_idx + len(rec)
            new_res = new_res.replace("<המלצה_>", rec, 1)
            entities.append({"start": start_idx, "end": end_idx, "label": "recommendations"})

    return new_res, entities


def generate_medical_records(record_type):
    if record_type == "CT בטן ואגן":
        response = random.choice(CTAbdomenAndPelvis)
        inst, entities_ = get_non_anonymized_record(response)
        return inst, response, entities_


def main(additional_records, excel_output_path, json_output_path):
    new_records = []
    ner_data = {}

    for i in tqdm(range(additional_records), desc="Processing Records"):
        rec_type = random.choice(["CT בטן ואגן"])
        instruction_generation, response_generation, entities = generate_medical_records(rec_type)
        instruction = instruction_generation
        new_records.append([instruction, response_generation])
        ner_data[i] = entities

    # Creating a DataFrame for new records
    new_records_df = pd.DataFrame(new_records, columns=['instruction', 'response'])

    # Saving to Excel
    output_path = excel_output_path
    if os.path.exists(output_path):
        # Read existing data
        existing_df = pd.read_excel(output_path)
        # Append new records
        updated_df = pd.concat([existing_df, new_records_df], ignore_index=True)
    else:
        # If the file doesn't exist, just use the new records
        updated_df = new_records_df

    # Save the updated DataFrame
    updated_df.to_excel(output_path, index=False)

    # Saving the NER data to JSON
    if os.path.exists(json_output_path):
        # Load existing JSON data
        with open(json_output_path, 'r', encoding='utf-8') as f:
            existing_ner_data = json.load(f)
    else:
        # If the file doesn't exist, start with an empty dictionary
        existing_ner_data = {}

    # Merge new data with existing data
    if len(existing_ner_data) > 0:
        max_existing_key = max(map(int, existing_ner_data.keys()))
        adjusted_ner_data = {str(k + max_existing_key + 1): v for k, v in ner_data.items()}
    else:
        adjusted_ner_data = {str(k): v for k, v in ner_data.items()}

    # Merge new data with existing data
    existing_ner_data.update(adjusted_ner_data)

    # Save the updated JSON data
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(existing_ner_data, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    # global Faker instance
    fake = Faker('he_IL')

    parser = argparse.ArgumentParser(
        description='Generate synthetic CT Abdomen & Pelvis reports and NER annotations.'
    )
    parser.add_argument(
        '--num-records',
        type=int,
        default=100,
        help='Number of additional records to generate (default: 100).',
    )
    parser.add_argument(
        '--excel-output-path',
        type=str,
        default='./data/train_synthetic_data.xlsx',
        help='Path to the Excel file for synthetic data (default: ./data/train_synthetic_data.xlsx).',
    )
    parser.add_argument(
        '--json-output-path',
        type=str,
        default='./data/ner_train_data.json',
        help='Path to the JSON file for NER annotations (default: ./data/ner_train_data.json).',
    )

    args = parser.parse_args()

    main(
        additional_records=args.num_records,
        excel_output_path=args.excel_output_path,
        json_output_path=args.json_output_path,
    )
