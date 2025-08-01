"""
Description: This script connects to a MongoDB database and cleans up authors field by removing "." from authors list. (modified clean_pub_names for it to work with authors)
Total authors_fields changed: 3885
Date: 2025-07-31
Author: Zéas Lupien (bhklab.zeaslupien@gmail.com, zaslup@gmail.com)
"""
# import necessary libraries
import pymongo
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv(override=True)

# Connect to MongoDB
client = pymongo.MongoClient(os.getenv("SP_DATABASE_STRING"))
db = client[os.getenv("DATABASE")]
pub_collection = db[os.getenv("PUBLICATION_COLLECTION")]

# Find all publications where any author name contains a period
query = {
    "authors": {"$elemMatch": {"$regex": "\\."}}
}
pubs = pub_collection.find(query)

#keep count of authors amount changed
changed_count = 0

# Iterate through each publication and clean the authors field
for pub in pubs:
    authors_list = pub.get("authors", [])
    
    if isinstance(authors_list, list):
        updated_authors = [name.replace(".", "") for name in authors_list]
        if updated_authors != authors_list:
            pub_collection.update_one(
                {"_id": pub["_id"]},
                {"$set": {"authors": updated_authors}}
            )
            changed_count += 1
#print out the total number of authors fields changed
print(f"\nTotal authors_fields changed: {changed_count}")