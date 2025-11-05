# science-portal-mailing

This repository serves as the data processing portion of https://pmscience.ca. The `/publication/one` route expects a publication doi as an arugment and extracts publication information/sources directly from the publication page and Crossref. The `/director` route expects the data extracted from `/publication/one` in dictionary format and pulls out pieces to form an email to send to the director at the institution about the publication. The `/fanout` route expects the data extracted from `/publication/route` in dictionary format and extracts pieces to form an email to circulate to the institution. 

## Environment Variables

```bash
SENDGRID_API_KEY=
FROM_EMAIL=

DIRECTOR_EMAIL=

SP_DATABASE_STRING=
DATABASE=
PUBLICATION_COLLECTION=publications
SCRAPING_COLLECTION=scrapes
AUTHOR_COLLECTION=authors

LINUX=yes/no

DOMAIN=http://localhost:3000

GEMINI_API_KEY=
```