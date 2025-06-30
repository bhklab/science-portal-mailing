import pandas as pd

# Read the CSV files with UTF-8 encoding
pubs_df = pd.read_csv('input_data/all-uhn-pubs-utf-8.csv', encoding='utf-8')
authors_df = pd.read_csv('input_data/sp-authors.csv', encoding='utf-8')

# Select and rename columns
selected_columns = [
    'Year of Pub', 'Author Names', 'DOI Identifier', 'PMID'
]
df_selected = pubs_df[selected_columns].rename(columns={
    'Year of Pub': 'year',
    'Author Names': 'authors',
    'DOI Identifier': 'doi',
})

# Ensure PMID is a numeric value, replace NaNs or invalid values with -1, and convert to int
df_selected['PMID'] = pd.to_numeric(df_selected['PMID'], errors='coerce').fillna(-1).astype(int)

# Remove duplicate DOIs
df_selected = df_selected.drop_duplicates(subset='doi', keep='first')

# Filter out early review/access and non-PM affiliated publications
filtered_selected_df = df_selected[
    (~df_selected['type'].str.contains('early-review', case=False, na=False)) &
    (~df_selected['type'].str.contains('Early Access', case=False, na=False)) &
    (
        df_selected['affiliations'].str.contains('Princess Margaret', case=False, na=False) |
        df_selected['affiliations'].str.contains('PMC', case=False, na=False) |
        df_selected['filteredAffiliations'].str.contains('Princess Margaret', case=False, na=False) |
        df_selected['filteredAffiliations'].str.contains('PMC', case=False, na=False)
    ) & 
	(df_selected['year'].str.contains('2022|2021|2020|2019|2018', case=False, na=False))
]

# Export the filtered results
filtered_selected_df.to_csv('output_data/pubs-pre-2022-utf-8.csv', index=False)
