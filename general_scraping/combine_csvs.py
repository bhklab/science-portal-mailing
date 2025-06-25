import pandas as pd

# Read the CSV files with UTF-8 encoding
df1 = pd.read_csv('input_data/pubs-2022-utf-8.csv', encoding='utf-8')
df2 = pd.read_csv('input_data/pubs-2023-utf-8.csv', encoding='utf-8')
df3 = pd.read_csv('input_data/pubs-2024-utf-8.csv', encoding='utf-8')
df4 = pd.read_csv('input_data/pubs-2025-utf-8.csv', encoding='utf-8')

# Combine the DataFrames
combined_df = pd.concat([df1, df2, df3, df4], ignore_index=True, sort=False)

# Select and rename columns
selected_columns = [
    'PMID', 'doi', 'Date', 'Title', 'Journal', 'Article Type',
    'Author List', 'Filtered Author List', 'All Affiliations', 'Filtered Affiliations'
]
df_selected = combined_df[selected_columns].rename(columns={
    'Date': 'date',
    'Title': 'name',
    'Journal': 'journal',
    'Article Type': 'type',
    'Author List': 'authors',
    'Filtered Author List': 'filteredAuthors',
    'All Affiliations': 'affiliations',
    'Filtered Affiliations': 'filteredAffiliations',
})

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
    )
]

# Export the filtered results
filtered_selected_df.to_csv('output_data/pubs-2022-to-2025-utf-8-2.csv', index=False)
