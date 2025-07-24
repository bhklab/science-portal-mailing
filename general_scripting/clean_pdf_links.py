import pymongo
import os
from dotenv import load_dotenv
import re

load_dotenv(override=True)

client = pymongo.MongoClient(os.getenv("SP_DATABASE_STRING"))
db = client[os.getenv("DATABASE")]
pub_collection = db[os.getenv("PUBLICATION_COLLECTION")]

query = {
    "journal": { "$regex": "&amp;" }
}

pubs = pub_collection.find(query)

for pub in pubs:
    updated_fields = {}

    if pub.get("journal"):
        if "&amp;" in pub["journal"]:
            updated_fields["journal"] = pub["journal"].replace("&amp;", "&")
        
    if pub.get("image"):
        if "&amp;" in pub["image"]:
            updated_fields["image"] = pub["image"].replace("&amp;", "&")

    if updated_fields:
        pub_collection.update_one(
            {"_id": pub["_id"]},
            {"$set": updated_fields}
        )

query = {
    "name": {"$regex": "<i>"}
}

pubs = pub_collection.find(query)

for pub in pubs:
    updated_fields = {}

    if pub.get("name"):
        if "<i>" in pub["name"]:
            updated_fields["name"] = pub["name"].replace("<i>", "").replace("</i>", "")

    if updated_fields:
        pub_collection.update_one(
            {"_id": pub["_id"]},
            {"$set": updated_fields}
        )

pubs = pub_collection.find(query)

for pub in pubs:
    updated_fields = {}

    for sect in pub["supplementary"]:
        for sub in sect:
            if len(sub) > 0:
                for link in sub:
                    matches = re.findall(r'https://[^https]+', link)
                    if matches:
                        link = matches[len(matches) - 1]

    if updated_fields:
        pub_collection.update_one(
            {"_id": pub["_id"]},
            {"$set": updated_fields}
        )

