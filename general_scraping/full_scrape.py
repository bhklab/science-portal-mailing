import pandas as pd
from models.publication import Publication


df = pd.read_csv('output_data/pubs-2022-to-2025-utf-8.csv', encoding='utf-8')

dicts = df.to_dict(orient='records')

pubs = []
for dict in dicts:
	pubs.append(Publication(PMID=dict['pmid'], doi=dict['doi'],))








