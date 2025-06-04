from fastapi import FastAPI, APIRouter, HTTPException, Body, Depends
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import pymongo

load_dotenv(override=True)

router = APIRouter(prefix="/scrape") #Adding email part of route

client = pymongo.MongoClient(os.getenv('SP_DATABASE_STRING'))
db = client[os.getenv("DATABASE")]
collection = db[os.getenv("COLLECTION")]
  
@router.get("/publication")
async def scraping():
    '''
        Cross ref and supplementary scrape for newly submitted publication
        returns: boolean (true if success, false if unsuccessful)
    '''

    for doc in collection.find():
        doc.get('doi', '')
