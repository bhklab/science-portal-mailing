import pandas as pd
from datetime import datetime

authors = pd.read_csv("input_data/mcgill_staff.csv", encoding="utf-8")
authors.rename(
    columns={
        "Affiliations": "primaryResearchInstitute",
        "Email": "email",
    },
    inplace=True,
)

authors.index.name = "ENID"
authors[["lastName", "firstName"]] = authors["Researcher"].str.split(", ", expand=True)
authors.drop(columns=["Researcher"], inplace=True)
authors["primaryAppointment"] = "Scientist"

authors.to_csv(
    f"output_data/mcgill-authors-cleaned-{str(datetime.now())[:10]}.csv",
)
authors.reset_index().to_json(
    f"output_data/mcgill-authors-cleaned-{str(datetime.now())[:10]}.json",
    orient="records",
)
