from fastapi import FastAPI, APIRouter, HTTPException, Body, Depends
import os
import time
from dotenv import load_dotenv
import pymongo
import nodriver as uc
from pyvirtualdisplay import Display
from scraping_core.scrape_body import scrape_body
from scraping_core.classify_links import classify_all
from scraping_core.write_to_csv import write_to_csv
from scraping_core.write_to_json import write_to_json


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

        
    browser = await uc.start(
        headless=False,
        # user_data_dir= os.getcwd() + "/profile", # by specifying it, it won't be automatically cleaned up when finished
        # browser_executable_path="/path/to/some/other/browser",
        # browser_args=['--some-browser-arg=true', '--some-other-option'],
        lang="en-US"   # this could set iso-language-code in navigator, not recommended to change
    )

    tab = await browser.get('https://doi.org/10.1177/17588359211072621')
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
            links.add(match.group(1))

    print(links)
        
    links.update(scrape_body(body_text))
        

    classified_links = classify_all(links)

    write_to_csv("output_data/output.csv", "10.1177/17588359211072621", classified_links)
    write_to_json("output_data/raw_links.json", "10.1177/17588359211072621", links)

    





