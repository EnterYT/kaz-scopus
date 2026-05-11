# Prototype: Formation of a Scientific Publications Database (Ontological Approach)

This prototype demonstrates how to form a scientific publications database using an ontological model:

- **Relational storage** (SQLite) for structured querying and reporting.
- **Ontology graph** (RDF/Turtle) for semantic interoperability.

## What is included

- `data/publications` - publication metadata (JSON content).
- `docs/ontology.ttl` - core ontology classes and properties.
- `src/prototype.py` - ETL script that builds:
  - SQLite DB (`science_publications.db`)
  - RDF graph (`science_publications.ttl`)

## Quick start

1. Create environment and install Python dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Build DB + RDF once (optional but recommended):

```bash
python src/prototype.py
```

3. Start backend API:

```bash
uvicorn src.api:app --reload
```

4. In another terminal, start React frontend:

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) to view publications and add new ones.

## RBAC behavior

The app includes a simple two-role RBAC model:

- `user`: can upload publications and delete only publications they own.
- `admin`: can delete any publication.

In the web UI header, choose the current `User ID` and `Role`. These values are sent to the API as:

- `X-User-Id`
- `X-Role` (`user` or `admin`)

Each publication stores a `user_id`, set automatically to the current `X-User-Id` during creation.

Catalog page supports sorting by:

- Year: newest first
- Year: oldest first
- Title: A-Z
- Title: Z-A

5. Optional custom paths for ETL:

```bash
python src/prototype.py --input data/publications --db output.db --rdf output.ttl
```

## Ontological model used

Main concepts:

- `Publication`
- `Author`
- `Venue`
- `Keyword`
- `Affiliation`

Main relations:

- `hasAuthor` (Publication -> Author)
- `publishedIn` (Publication -> Venue)
- `hasKeyword` (Publication -> Keyword)
- `hasAffiliation` (Author -> Affiliation)

## Typical extension points

- Add ORCID, Scopus ID, WoS ID as author identifiers.
- Add citation links (Publication -> cites -> Publication).
- Add topic hierarchy as a SKOS concept scheme.
- Add ingestion from APIs (Crossref, OpenAlex, Scopus export).
#
