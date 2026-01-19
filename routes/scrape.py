from fastapi import FastAPI, APIRouter, HTTPException, Body
import os
import re
import requests
from dotenv import load_dotenv
import pymongo
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio
from unidecode import unidecode
import nodriver as uc
from pyvirtualdisplay import Display
from scraping_core.scrape_body import scrape_body
from scraping_core.classify_links import classify_all
from scraping_core.write_to_csv import write_to_csv
from scraping_core.write_to_json import write_to_json
from models.publication import Publication
from llm_playground.LLM_scraping.publication_summary import summary_html
from bs4 import BeautifulSoup


load_dotenv(override=True)

router = APIRouter(prefix="/scrape")  # Adding email part of route

client = pymongo.MongoClient(os.getenv("SP_DATABASE_STRING"))
db = client[os.getenv("DATABASE")]
main_pub_collection = db[os.getenv("PUBLICATION_COLLECTION")]
scraping_pub_collection = db[os.getenv("SCRAPING_COLLECTION")]


@router.post("/publication/one")
async def scraping(pub: Publication = Body(...)):
    """
    Cross ref and supplementary scrape for newly submitted publication
    returns: Publication object with all scraped data
    """

    existing_doc = main_pub_collection.find_one({"doi": pub.doi})

    if existing_doc:
        print("DOI exists.")
        return "DOI exists."
    else:
        print("DOI does not exist yet.")

    publication = await crossref_scrape(pub)

    try:
        display = None
        browser = None

        if os.getenv("LINUX") == "yes":
            display = Display(visible=0, size=(1920, 1080))
            display.start()

        browser = await uc.start(
            headless=False,
            # user_data_dir=os.getcwd()
            # + "/profile",  # will be automatically cleaned up when finished if DNE
            # browser_args=['--some-browser-arg=true', '--some-other-option'],
            lang="en-US",  # this could set iso-language-code in navigator, it was not recommended to change according to docs
            no_sandbox=True,
        )
        tab = await browser.get(f"https://doi.org/{publication.doi}")

        await tab.wait(20)  # wait to ensure captcha can appear

        # Attempt to get past cloudflare verification
        try:
            await tab.verify_cf(
                (os.getcwd() + "/screenshots/verify/temp.png"), flash=False
            )
        except Exception as e:
            print("captcha cannot be solved:", e)

        await tab.wait(7)  # wait to ensure captcha can complete

        await tab.select("body")  # waits for page to render first
        await tab.scroll_down(200)

        body_text = await tab.get_content()

        # If the director fanout is requested, create 2 sentence summary
        if pub.fanout.get("request", False):
            publication.summary = await summary_html(body_text)

        elements = await tab.select_all("a[href]")

        await tab.save_screenshot(os.getcwd() + "/screenshots/test.jpeg", "jpeg")
        await tab.close()
        browser.stop()

        if display:
            display.stop()

    except Exception as e:
        if browser:
            browser.stop()
        if display:
            display.stop()
        raise HTTPException(
            status_code=500, detail=f"Error during supplementary scraping: {e}"
        )

    links = set()
    for ele in elements:
        match = re.search(r'href="([^"]+)"', str(ele))
        if match:
            if "https://" in match.group(1) or "http://" in match.group(1):
                links.add(match.group(1))

    if pub.supplementary:
        links.update(
            link
            for category in pub.supplementary.values()
            for subcategory in category.values()
            for link in subcategory
        )

    raw_body_links = re.findall(r"https?://[^\s\"'<>()]+", body_text)
    cleaned_body_links = {link.rstrip(".,;:!?)") for link in raw_body_links}
    links.update(cleaned_body_links)

    # Ensures lowercase set to ensure we can test for duplicates without affecting casing of original
    links_lower = {link.lower() for link in links}
    for new_link in scrape_body(body_text):
        if new_link.lower() not in links_lower:
            links.add(new_link)

    classified_links = classify_all(links)

    publication.supplementary = classified_links

    write_to_csv("output_data/output.csv", publication.doi, classified_links)
    write_to_json("output_data/raw_links.json", publication.doi, links)

    scraping_pub_collection.insert_one(publication.model_dump())

    return publication


async def crossref_scrape(pub: Publication) -> Publication:
    try:
        # Get publication metadata from Crossref
        r = requests.get(
            f"https://api.crossref.org/works/{pub.doi}",
            headers={
                "User-Agent": "Python-requests",
                "Mailto": "matthew.boccalon@uhn.ca",
            },
            timeout=60,
        )
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Error occured during crossref scrape {str(e)}",
        )

    try:
        if r.status_code == 200:  # Verify the api request was successful
            data = r.json()
            if data["status"] == "ok":
                author_string = ""
                affiliations = set()

                # Iterate author list, utilize unidecode to remove special characters, add them to string
                if data["message"].get("author"):
                    for i, author in enumerate(data["message"]["author"]):
                        author_string += f"{unidecode(author.get('family', ''))}, {unidecode(author.get('given', ''))}"
                        if (
                            i != len(data["message"]["author"]) - 1
                        ):  # Add ';' to separate author names
                            author_string += "; "
                        for affil in author["affiliation"]:
                            affiliations.add(affil["name"])

                    # Clean up authors field of unnecessary . when next to ;
                    author_string = author_string.replace(".;", ";")

                pub.PMID = (
                    pub.PMID
                    if (pub.PMID and (pub.PMID != "" or pub.PMID != -1))
                    else -1
                )
                pub.date = data["message"]["created"]["date-time"][:10]
                pub.name = re.sub(
                    r"\s{2,}",
                    " ",
                    re.sub(
                        r"<.*?>",
                        "",
                        re.sub(
                            r"&lt;.*?&gt;",
                            "",
                            data["message"]["title"][0].replace("&amp;", "&"),
                        ),
                    ),
                )
                # extract and clean the abstract (if it exists)
                pub.abstract = BeautifulSoup(
                    data["message"].get("abstract", ""), "html.parser"
                ).get_text()
                pub.abstract = pub.abstract.replace("Abstract", "").strip()
                pub.journal = (
                    data["message"]
                    .get("container-title")[0]
                    .replace("&amp;", "&")
                    .replace("<i>", "")
                    .replace("</i>", "")
                    if data["message"].get("container-title")
                    else data["message"]
                    .get("institution")[0]["name"]
                    .replace("&amp;", "&")
                    .replace("<i>", "")
                    .replace("</i>", "")
                )
                pub.type = data["message"].get("type")
                pub.authors = author_string if author_string != "" else pub.authors
                pub.filteredAuthors = ""
                pub.affiliations.extend(list(affiliations))
                pub.citations = data["message"].get("is-referenced-by-count", 0)
                pub.dateAdded = datetime.now(ZoneInfo("UTC"))
                pub.publisher = data["message"].get("publisher", "")
                pub.status = "published"
                pub.image = (
                    data["message"]
                    .get("container-title", [""])[0]
                    .lower()
                    .replace(" ", "_")
                    .replace("*", "")
                    .replace("#", "")
                    .replace("%", "")
                    .replace("$", "")
                    .replace("/", "")
                    .replace("\\", "")
                    .replace("<", "")
                    .replace(">", "")
                    .replace("!", "")
                    .replace(":", "")
                    .replace("&amp;", "&")
                    + ".jpg"
                    if data["message"].get("container-title")
                    else data["message"]
                    .get("institution")[0]["name"]
                    .lower()
                    .replace(" ", "_")
                    .replace("*", "")
                    .replace("#", "")
                    .replace("%", "")
                    .replace("$", "")
                    .replace("/", "")
                    .replace("\\", "")
                    .replace("<", "")
                    .replace(">", "")
                    .replace("!", "")
                    .replace(":", "")
                    .replace("&amp;", "&")
                    + ".jpg"
                )
                pub.scraped = True

                return pub
        else:
            raise HTTPException(status_code=404)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Crossref Error: {e}")
