"""
Description: This script connects to a MongoDB database and cleans up publication names by removing <xyz...> tags (modified clean_pdf_links for it to work with names)
Date: 2025-08-01
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

# Find all publications with <.*?> tags in the name field including <scp>, </scp>, <sup>, </sup>, <sub>, </sub>
query = {
    "name": {"$regex": "<.*?>"}
}
pubs = pub_collection.find(query)

#count of names changed before cleaning
changed_count = 0

# Iterate through each publication and clean the name field
for pub in pubs:
    original_name = pub.get("name", "")
    if original_name:
        # Remove all tags like <.*?> (xyz...), <scp>, </scp>, <sup>, </sup>, <sub>, </sub> re.sub allows for more complex patterns such as non specific patterns
        cleaned_name = re.sub(r"<.*?>", "", original_name)
        if cleaned_name != original_name:
            pub_collection.update_one(
                {"_id": pub["_id"]},
                {"$set": {"name": cleaned_name}}
            )
            changed_count += 1

# Print out the total number of names changed
print(f"\nTotal names changed: {changed_count}")
