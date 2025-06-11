from fastapi import FastAPI, APIRouter, HTTPException, Body, Depends
import os
import time
import re
import requests
from dotenv import load_dotenv
import pymongo
import datetime
from unidecode import unidecode
import nodriver as uc
from pyvirtualdisplay import Display
from scraping_core.scrape_body import scrape_body
from scraping_core.classify_links import classify_all
from scraping_core.write_to_csv import write_to_csv
from scraping_core.write_to_json import write_to_json
from models.publication import Publication


load_dotenv(override=True)

router = APIRouter(prefix="/scrape") #Adding email part of route

client = pymongo.MongoClient(os.getenv('SP_DATABASE_STRING'))
db = client[os.getenv("DATABASE")]
main_pub_collection = db[os.getenv("PUBLICATION_COLLECTION")]
scraping_pub_collection = db[os.getenv("SCRAPING_COLLECTION")]
  
@router.post("/publication")
async def scraping(doi: str = Body(..., embed=True)):
    '''
        Cross ref and supplementary scrape for newly submitted publication
        returns: boolean (true if success, false if unsuccessful)
    '''
    
    existing_doc = main_pub_collection.find_one({"doi": doi})

    if existing_doc:
        print("DOI exists.")
        return "DOI exists."
    else:
        print("DOI does not exist yet.")

    publication =  await crossref_scrape(doi)

    browser = await uc.start(
        headless=False,
        # user_data_dir= os.getcwd() + "/profile", # by specifying it, it won't be automatically cleaned up when finished
        # browser_executable_path="/path/to/some/other/browser",
        # browser_args=['--some-browser-arg=true', '--some-other-option'],
        lang="en-US",   # this could set iso-language-code in navigator, not recommended to change
        no_sandbox=True
    )

    tab = await browser.get(f'https://doi.org/{doi}')
    await tab.select('body') # waits for page to render first

    time.sleep(1)

    body_text = await tab.get_content()
    print(body_text)

    await tab.scroll_down(100)
    await tab.scroll_down(100)
    await tab.scroll_down(200)

    elements = await tab.select_all("a[href]")
    await tab.save_screenshot(os.getcwd() + '/screenshots/test.jpeg', 'jpeg')

    links = set ()
    for ele in elements:
        match = re.search(r'href="([^"]+)"', str(ele))
        if match:
            if "http" in match:
                links.add(match.group(1))

    print(links)
        
    links.update(scrape_body(body_text))
        

    classified_links = classify_all(links)

    publication.supplementary = classified_links


    write_to_csv("output_data/output.csv", doi, classified_links)
    write_to_json("output_data/raw_links.json", doi, links)

    await tab.close()
    browser.stop()

    return publication

    

async def crossref_scrape(doi: str) -> Publication:

    try:
        # Get Crossref data for publication
        r = requests.get(
            f'https://api.crossref.org/works/{doi}',
            headers = {
                'User-Agent': f'Python-requests',
                'Mailto': "matthew.boccalon@uhn.ca"
            }
        )
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=f"Error occured during crossref scrape {str(e)}")

    
    try:
        if (r.status_code == 200): # Verify the api request was successful
            data = r.json()
            if data['status'] == "ok":

                author_string = ""
                affiliations = set()

                # Iterate author list, utilize unidecode to remove special characters, add them to string
                for i, pub in enumerate(data['message']['author']):
                    author_string += f"{unidecode(pub.get('family', ''))}, {unidecode(pub.get('given', ''))}"
                    if i != len(data['message']['author']) - 1: # Add ';' to separate author names 
                        author_string += "; "
                    for affil in pub['affiliation']:
                        affiliations.add(affil['name'])        

                publication = Publication(  
                    PMID = -1,
                    doi = doi,
                    date = data['message']['created']['date-time'][:10],
                    name = data['message']['title'][0],
                    journal = data['message'].get('container-title', [""])[0],
                    type = data['message'].get('type'),
                    authors = author_string,
                    filteredAuthors = "",
                    affiliations = affiliations,
                    citations = data['message'].get('is-referenced-by-count', 0),
                    dateAdded = str(datetime.datetime.now())[0:10],
                    publisher = data['message']['publisher'],
                    status = "published",
                    image = data['message'].get('container-title', [""])[0].lower().replace(' ', '_').replace('*', '').replace('#', '')
                            .replace('%', '').replace('$', '').replace('/', '').replace('\\', '' )
                            .replace('<', '').replace('>', '').replace('!', '').replace(':', '') + '.jpg',
                    fanout = {
                        "request": False,
                        "completed": False
                    },
                    scraped = True
                )
                return publication
        else:
            raise HTTPException(status_code=404)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"DOI does not exist in crossref {e}")


