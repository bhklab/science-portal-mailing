from fastapi import FastAPI, APIRouter, HTTPException, Body, Depends
import os
import urllib.parse as urllp
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from models.publication import Publication
import pymongo

load_dotenv(override=True)

client = pymongo.MongoClient(os.getenv("SP_DATABASE_STRING"))
db = client[os.getenv("DATABASE")]
authors_collection = db[os.getenv("AUTHOR_COLLECTION")]

router = APIRouter(prefix="/email")  # Adding email part of route

wording_map = {
    "code": "code repo",
    "data": "dataset",
    "containers": "container",
    "trials": "trial",
    "results": "result",
    "protocols": "protocol",
    "packages": "package",
    "miscellaneous": "unclassified resource",
}


@router.post("/director")
async def email_director(pub: Publication = Body(...)):
    message = Mail(
        from_email=os.getenv("FROM_EMAIL"),
        to_emails=os.getenv("DIRECTOR_EMAIL"),
        subject="Sendgrid Email",
        html_content="<strong>Publication Approval</strong>",
    )

    split_email = pub.submitter.split(".")
    first_name = split_email[0]
    last_name = split_email[1].split("@")[0]

    totals = dict()

    # Count total links in each supplementary category
    for category in pub.supplementary:
        totals[category] = 0
        for subcategory in pub.supplementary[category]:
            totals[category] += len(pub.supplementary[category][subcategory])

    doi_encoding = urllp.quote(pub.doi, safe="~()*!.'")

    publication_breakdown = "The publication consists of "

    index = 0
    total_categories = 0
    for category in totals:
        if totals[category] > 0:
            publication_breakdown += f"{' and ' if index == len(totals) - 1 and total_categories > 0 else ' '}{totals[category]} {wording_map[category]}{'s' if totals[category] > 1 else ''}{'.' if index == len(totals) - 1 else ','}"
            total_categories += 1
        index += 1

    message.dynamic_template_data = {
        "name_of_user": f"{first_name.capitalize()} {last_name.capitalize()}",
        "email_of_user": pub.submitter,
        "publication_breakdown": publication_breakdown,
        "link_to_publication": f"{os.getenv('DOMAIN')}/publication/{doi_encoding}",
    }

    message.template_id = "d-c684d53e767243d3be5481abd93b2510"

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        await sg.send(message)
    except Exception as e:
        HTTPException(status_code=500, detail=f"Error sending director email {str(e)}")

    return {"message": "Completed scraping and sent out director email."}


@router.post("/fanout")
async def email_fanout(pub: Publication = Body(...)):
    message = Mail(
        from_email=os.getenv("FROM_EMAIL"),
        to_emails=os.getenv("DIRECTOR_EMAIL"),
        subject="Sendgrid Email",
        html_content="<strong>Publication Approval</strong>",
    )

    totals = dict()

    # Count total links in each supplementary category
    for category in pub.supplementary:
        totals[category] = 0
        for subcategory in pub.supplementary[category]:
            totals[category] += len(pub.supplementary[category][subcategory])

    doi_encoding = urllp.quote(pub.doi, safe="~()*!.'")

    publication_breakdown = "The publication consists of "

    index = 0
    total_categories = 0
    for category in totals:
        if totals[category] > 0:
            publication_breakdown += f"{' and ' if index == len(totals) - 1 and total_categories > 0 else ' '}{totals[category]} {wording_map[category]}{'s' if totals[category] > 1 else ''}{'.' if index == len(totals) - 1 else ','}"
            total_categories += 1
        index += 1

    authors = pub.authors.split(";")

    submitter = pub.submitter.split(".")  # To extract first and last name

    message.dynamic_template_data = {
        "main_author": f"{submitter[1].split('@')[0].capitalize()}, {submitter[0].capitalize()}",
        "publication_title": pub.name,
        "publication_journal": pub.journal,
        "other_authors": f"{authors[0]}; {authors[1]}; {authors[2]}; {authors[len(authors) - 3]}; {authors[len(authors) - 2]}; {authors[len(authors) - 1]}"
        if len(authors) > 5
        else pub.authors,
        "publication_breakdown": publication_breakdown,
        "link_to_publication": f"{os.getenv('DOMAIN')}/publication/{doi_encoding}",
    }

    message.template_id = "d-6ddf5ce280b545bebc6e210da785fd65"

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        await sg.send(message)
    except Exception as e:
        HTTPException(status_code=500, detail=f"Error sending fanout email {str(e)}")
