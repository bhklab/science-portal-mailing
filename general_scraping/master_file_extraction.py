import pandas as pd
import re


# Split authors by comma or semicolon, strip whitespace, convert to lowercase
def has_matching_author(pub_authors_str):
    pub_authors = []
    for raw_name in str(pub_authors_str).split(';'):
        name = raw_name.strip()
        if ',' in name:
            last, first = [part.strip() for part in name.split(',', 1)]
            full_name = f"{first} {last}".lower()
        else:
            full_name = name.lower()
        pub_authors.append(full_name)
    return any(author in author_names_set for author in pub_authors)




# Read the CSV files with UTF-8 encoding
pubs_df = pd.read_csv('input_data/all-uhn-pubs-utf-8.csv', encoding='utf-8')
authors_df = pd.read_csv('input_data/sp-authors.csv', encoding='utf-8')

# Select and rename columns
selected_columns = [
    'Year of Pub', 'Author Names', 'DOI Identifier', 'PMID', 'InCites Doc Type'
]
df_selected = pubs_df[selected_columns].rename(columns={
    'Year of Pub': 'year',
    'Author Names': 'authors',
    'DOI Identifier': 'doi',
    'InCites Doc Type': 'type'
})

# Remove publications that don't have doi's
df_selected = df_selected[df_selected['doi'].notna() & (df_selected['doi'].str.strip() != '')]

# Remove 'MEDLINE:' from PMID field
df_selected['PMID'] = df_selected['PMID'].astype(str).str.replace(r'^MEDLINE:', '', regex=True)
# Ensure PMID is a numeric value, replace NaNs or invalid values with -1, and convert to int
df_selected['PMID'] = pd.to_numeric(df_selected['PMID'], errors='coerce').fillna(-1).astype(int)

# Remove duplicate DOIs
df_selected = df_selected.drop_duplicates(subset='doi', keep='first')

# Type cast year to string
df_selected['year'] = df_selected['year'].astype(str)

# authors df setup
authors_df['full_name'] = authors_df['firstName'].str.strip() + ' ' + authors_df['lastName'].str.strip()
author_names_set = set(authors_df['full_name'].str.lower())

# Filter out early review/access and non-PM affiliated publications
filtered_selected_df = df_selected[
    (~df_selected['type'].str.contains('Proceedings Paper', case=False, na=False)) &
	(df_selected['year'].str.contains('2022|2021|2020|2019|2018|2017|2016|2015', case=False, na=False)) &
    (df_selected['authors'].apply(has_matching_author))
]

# Export the filtered results
filtered_selected_df.to_csv('output_data/pubs-pre-2022-utf-8.csv', index=False)
