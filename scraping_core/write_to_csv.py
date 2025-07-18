import csv
from scraping_core.classify_links import SUPPLEMENTARY

# Write publication result to csv to show all obtained link results
def write_to_csv(filepath, doi, classified_links):
    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            existing_rows = list(reader)
    except FileNotFoundError:
        existing_rows = []

    headers = ["DOI"] + [subcat for group in SUPPLEMENTARY.values() for subcat in group]
    if not existing_rows:
        existing_rows.append(headers)

    row = [doi]
    for group in SUPPLEMENTARY:
        for sub in SUPPLEMENTARY[group]:
            row.append(", ".join(classified_links[group].get(sub, [])))

    existing_rows.append(row)

    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(existing_rows)
