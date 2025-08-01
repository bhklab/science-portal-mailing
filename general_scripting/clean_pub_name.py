"""
Description: This script connects to a MongoDB database and cleans up publication names by removing <xyz> tags (modified clean_pdf_links for it to work with names)
Date: 2023-10-31
Author: Zéas Lupien (bhklab.zeaslupien@gmail.com, zaslup@gmail.com)
"""

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

# Find all publications with <.*?> tags in the name field 
#including <scp>, </scp>, <sup>, </sup>, <sub>, </sub>
query = {
    "name": {"$regex": "<.*?>"}
}
pubs = pub_collection.find(query)

changed_count = 0

for pub in pubs:
    original_name = pub.get("name", "")
    if original_name:
        # Remove all tags like <.*?> (xyz...), <scp>, </scp>, <sup>, </sup>, <sub>, </sub>
        cleaned_name = re.sub(r"<.*?>", "", original_name)
        if cleaned_name != original_name:
            pub_collection.update_one(
                {"_id": pub["_id"]},
                {"$set": {"name": cleaned_name}}
            )
            changed_count += 1

print(f"\nTotal names changed: {changed_count}")
