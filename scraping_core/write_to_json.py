import json
import os

def write_to_json(filepath, doi, raw_links):
    data = []

    # Load existing data if file exists
    if os.path.exists(filepath):
        with open(filepath, mode='r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pass

    data.append({
        "doi": doi,
        "links": sorted(raw_links)
    })

    # Write updated data back to the file
    with open(filepath, mode='w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
