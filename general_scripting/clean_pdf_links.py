import pymongo
import os
from dotenv import load_dotenv
import re
from urllib.parse import urlparse, parse_qs

load_dotenv(override=True)

client = pymongo.MongoClient(os.getenv("SP_DATABASE_STRING"))
db = client[os.getenv("DATABASE")]
pub_collection = db[os.getenv("PUBLICATION_COLLECTION")]

# Clean journal and image fields from &amp; and replace them with &
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

# Clean name fields of <i> and </i> and removing them 
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

# Clean supplementary field of extra https if more than one exist
pubs = pub_collection.find()

changed_count = 0

for pub in pubs:
    updated_fields = {}
    original_supp = pub.get("supplementary", {})
    updated_supp = {}
    modified = False

    for category, subcategories in original_supp.items():
        updated_supp[category] = {}
        for subcat, links in subcategories.items():
            updated_links = []
            for link in links:
                if isinstance(link, str):
                    cleaned_link = link  # default
                    original_link = link

                    # Handle scholar/google redirects
                    if "url=" in link:
                        parsed = urlparse(link)
                        qs = parse_qs(parsed.query)
                        if "url" in qs:
                            cleaned_link = qs["url"][0]

                    # Fallback: if multiple https:// present
                    else:
                        matches = re.findall(r'https://[^\s"\']+', link)
                        if len(matches) > 1:
                            cleaned_link = matches[-1]

                    if cleaned_link != original_link:
                        print(f"Updated: {original_link} --> {cleaned_link}")
                        changed_count += 1
                        modified = True

                    updated_links.append(cleaned_link)
                else:
                    updated_links.append(link)
            updated_supp[category][subcat] = updated_links

    if modified:
        updated_fields["supplementary"] = updated_supp
        pub_collection.update_one(
            {"_id": pub["_id"]},
            {"$set": updated_fields}
        )

print(f"\nTotal links changed: {changed_count}")
