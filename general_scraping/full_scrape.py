# TO RUN: pixi run python general_scraping/full_scrape.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from models.publication import Publication
from routes.scrape import scraping
import pymongo
import json
import asyncio
import requests
from dotenv import load_dotenv


load_dotenv(override=True)

client = pymongo.MongoClient(os.getenv('SP_DATABASE_STRING'))
db = client[os.getenv("DATABASE")]
main_pub_collection = db[os.getenv("PUBLICATION_COLLECTION")]

async def publication_scraping():
	df = pd.read_csv(f'{os.getcwd()}/general_scraping/output_data/pubs-2022-to-2025-utf-8.csv', encoding='utf-8')

	dicts = df.to_dict(orient='records')

	with open(f'{os.getcwd()}/general_scraping/errors/testing-format.json', mode='w', encoding='utf-8') as f:
		json.dump(dicts, f, indent=2)

	pubs = []
	errors = []

	for dict in dicts:
		pubs.append(Publication(PMID=dict['PMID'], doi=dict['doi'], authors=dict['authors']))

	for pub in pubs:
		if not main_pub_collection.find_one({"doi": pub.doi}):
			try:
				pub_dump = pub.model_dump()
				r = requests.post(
					'http://localhost:8000/scrape/publication/one',
					json=pub_dump,
					headers = {
						'User-Agent': 'Python-requests'
					}
				)
				if r.status_code == 200:
					print(r._content)
					full_pub = r.json()
					main_pub_collection.insert_one(full_pub)
				else: 
					errors.append({"doi": pub.doi, "error": r.json()})
			except Exception as e:
				errors.append({"doi": pub.doi, "error": e})
				print(e)
		else:
			print(f"DOI already exists: {pub.doi}")

	with open(f'{os.getcwd()}/general_scraping/errors/dois-of-errors.json', mode='w', encoding='utf-8') as f:
		json.dump(errors, f, indent=2)

async def main():
	await publication_scraping()


if __name__ == "__main__":
    asyncio.run(main())








