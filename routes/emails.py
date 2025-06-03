from fastapi import FastAPI, APIRouter, HTTPException, Body, Depends
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv(override=True)

router = APIRouter(prefix="/email") #Adding email

@router.post("/director")
async def email_director(pub):

    scraping(pub)

    message = Mail(
        from_email=os.getenv('FROM_EMAIL'),
        to_emails=os.getenv('DIRECTOR_EMAIL'),
        subject='Sendgrid Email',
        html_content='<strong>Publication Approval</strong>')
    
    data = {}

    message.dynamic_template_data = {  
        'name_of_user': data.name,
        'email_of_user': data.email,
        'code_total': data.code,
        'dataset_total': data.dataset,
        'container_total': data.container,
        'trial_total': data.trial,
        'protocol_total': data.protocol,
        'package_total': data.package,

        'link_to_publication': data.publication_link,

        'acceptance_url': data.accept_url,
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



    return {"message": "Hello World"}

async def scraping(pub):
    '''
        Cross ref and supplementary scrape for newly submitted publication
        returns: boolean (true if success, false if unsuccessful)
    '''

    ### E2E scraping ###
