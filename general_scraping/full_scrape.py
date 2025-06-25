# TO RUN: pixi run python -m general_scraping.full_scrape
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
		print(dict['doi'])
		pubs.append(Publication(PMID=dict['PMID'], doi=dict['doi']))

	for pub in pubs:
		try:
			print(pub.model_dump())
			full_pub = requests.post(
				f'http://localhost:8000/scrape/publication/one',
				json=pub.model_dump(),
				headers = {
					'User-Agent': f'Python-requests',
				}
			)
			print(full_pub)
			main_pub_collection.insert_one(full_pub.model_dump())
		except Exception as e:
			errors.append(pub.doi)
			# print(e)

	with open(f'{os.getcwd()}/general_scraping/errors/dois-of-errors.json', mode='w', encoding='utf-8') as f:
		json.dump(errors, f, indent=2)

async def main():
	await publication_scraping()


if __name__ == "__main__":
    asyncio.run(main())








