import pandas as pd
from models.publication import Publication
from routes.scrape import scraping
import pymongo
import os
import json
from dotenv import load_dotenv


load_dotenv(override=True)

client = pymongo.MongoClient(os.getenv('SP_DATABASE_STRING'))
db = client[os.getenv("DATABASE")]
main_pub_collection = db[os.getenv("PUBLICATION_COLLECTION")]


df = pd.read_csv('output_data/pubs-2022-to-2025-utf-8.csv', encoding='utf-8')

dicts = df.to_dict(orient='records')

pubs = []
errors = []

for dict in dicts:
	pubs.append(Publication(PMID=dict['pmid'], doi=dict['doi'],))

for pub in pubs:
	try:
		full_pub = scraping(pub)
		main_pub_collection.insert_one(full_pub)
	except Exception as e:
		errors.append(pub.doi)

with open('errors/dois-of-errors.json', mode='w', encoding='utf-8') as f:
    json.dump(errors, f, indent=2)








