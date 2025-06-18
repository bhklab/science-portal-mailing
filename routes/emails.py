from fastapi import FastAPI, APIRouter, HTTPException, Body, Depends
import os
import urllib.parse as urllp
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
from models.publication import Publication


load_dotenv(override=True)

router = APIRouter(prefix="/email") #Adding email part of route

@router.post("/director")
async def email_director(pub: Publication = Body(...)):
    
    message = Mail(
        from_email=os.getenv('FROM_EMAIL'),
        to_emails=os.getenv('DIRECTOR_EMAIL'),
        subject='Sendgrid Email',
        html_content='<strong>Publication Approval</strong>')
    
    split_email = pub.submitter.split(".")
    first_name = split_email[0]
    last_name = split_email[1].split("@")[0]

    totals = dict()

    for category in pub.supplementary:
        totals[category] = 0
        for subcategory in pub.supplementary[category]:
            totals[category] += len(pub.supplementary[category][subcategory])

    doi_encoding = urllp.quote(pub.doi, safe="~()*!.'")

    publication_breakdown = "The publication consists of "

    wording_map = {
        'code': 'code repositories',
        'data': 'datasets',
        'containers': 'containers',
        'trials': 'trials',
        'results': 'results',
        'protocols': 'protocols',
        'packages': 'packages',
        'miscellaneous': 'miscellaneous items'
    }

    index = 0
    for category in totals:
        if totals[category] > 0:
            publication_breakdown += f"{" and " if index == len(totals) - 1 else " "}{totals[category]} {wording_map[category]}{"," if index < len(totals) - 1 else "."}"
        index += 1

    message.dynamic_template_data = {  
        'name_of_user': f"{first_name.capitalize()} {last_name.capitalize()}",
        'email_of_user': pub.submitter,
        'publication_breakdown': publication_breakdown,

        'link_to_publication': f"{os.getenv('DOMAIN')}/publication/{doi_encoding}",
    }

    message.template_id = 'd-c684d53e767243d3be5481abd93b2510'

    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)

    return {"message": "Completed scraping and sent out director email."}

