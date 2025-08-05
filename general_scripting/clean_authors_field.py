"""
Description: This script connects to a MongoDB database and cleans up authors field by removing "." from authors list when it is before ";" ex: ".;" . (modified clean_pub_names for it to work with authors)
Total authors_fields changed during test: 3885
Date: 2025-08-05
Author: Zéas Lupien (bhklab.zeaslupien@gmail.com, zaslup@gmail.com)
"""
#import all necessary libraries
import pymongo
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Connect to MongoDB
client = pymongo.MongoClient(os.getenv("SP_DATABASE_STRING"))
db = client[os.getenv("DATABASE")]
pub_collection = db[os.getenv("PUBLICATION_COLLECTION")]

# Query to find all publications
pubs = pub_collection.find()

# Counter for changed documents
changed_count = 0

# Iterate through each publication
for pub in pubs:
    if pub.get("authors"):
        if ".;" in pub.get("authors"):
            updated_authors_str = pub.get("authors").replace(".;", ";")
            pub_collection.update_one(
                {"_id": pub["_id"]},
                {"$set": {"authors": updated_authors_str}}
            )
            changed_count += 1
            print(f"changed: {changed_count}")

print(f"\nTotal authors_fields changed: {changed_count}")
