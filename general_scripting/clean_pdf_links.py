import pymongo
import os
from dotenv import load_dotenv

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
