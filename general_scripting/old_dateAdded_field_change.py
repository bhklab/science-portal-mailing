"""
Description: This script connects to a MongoDB database and updates the `dateAdded` field in publications to ensure it is stored as a datetime object instead of a string. 2025-06-26T00:00:00.000+00:00 year-month-dayThour:minute:second.millisecond+ offset from UTC timezone.
Author: Zéas Lupien (bhklab.zeaslupien@gmail.com, zaslup@gmail.com)
Date: 2025-08-07
"""
#import all necessary libraries
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

#load environment variables
load_dotenv(override=True)

#connect to MongoDB
client = MongoClient(os.getenv("SP_DATABASE_STRING"))
db = client[os.getenv("DATABASE")]
pub_collection = db[os.getenv("PUBLICATION_COLLECTION")]

#query to find all publications
pubs = pub_collection.find()

#counter for changed documents
changed_count = 0

#iterate through each publication
for pub in pubs:
    if pub.get("dateAdded"):
        #convert string to datetime object
        date_obj = datetime.strptime(pub["dateAdded"], "%Y-%m-%d")
        #update with datetime object
        pub_collection.update_one(
            {"_id": pub["_id"]},
            {"$set": {"dateAdded": date_obj}}
        )
        #increases changed count
        changed_count += 1

#print total number of updated documents
print(f"\nTotal dateAdded fields updated: {changed_count}")
