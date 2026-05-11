import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import XSD


BASE = Namespace("http://example.org/science-onto#")
RES = Namespace("http://example.org/resource/")


def create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS publications (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            year INTEGER NOT NULL,
            doi TEXT UNIQUE,
            abstract TEXT,
            owner_user_id TEXT NOT NULL DEFAULT 'seed-admin'
        );

        CREATE TABLE IF NOT EXISTS authors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            affiliation TEXT
        );

        CREATE TABLE IF NOT EXISTS venues (
            name TEXT PRIMARY KEY,
            type TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS keywords (
            keyword TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS publication_authors (
            publication_id TEXT NOT NULL,
            author_id TEXT NOT NULL,
            PRIMARY KEY (publication_id, author_id),
            FOREIGN KEY (publication_id) REFERENCES publications (id),
            FOREIGN KEY (author_id) REFERENCES authors (id)
        );

        CREATE TABLE IF NOT EXISTS publication_keywords (
            publication_id TEXT NOT NULL,
            keyword TEXT NOT NULL,
            PRIMARY KEY (publication_id, keyword),
            FOREIGN KEY (publication_id) REFERENCES publications (id),
            FOREIGN KEY (keyword) REFERENCES keywords (keyword)
        );

        CREATE TABLE IF NOT EXISTS publication_venues (
            publication_id TEXT PRIMARY KEY,
            venue_name TEXT NOT NULL,
            FOREIGN KEY (publication_id) REFERENCES publications (id),
            FOREIGN KEY (venue_name) REFERENCES venues (name)
        );
        """
    )
    conn.commit()


def load_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of publication objects.")
    return data


def normalize_token(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-")


def build_sqlite(records: list[dict[str, Any]], db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    create_schema(conn)
    cur = conn.cursor()

    for rec in records:
        cur.execute(
            """
            INSERT OR REPLACE INTO publications (id, title, year, doi, abstract, owner_user_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                rec["id"],
                rec["title"],
                rec["year"],
                rec.get("doi"),
                rec.get("abstract"),
                rec.get("owner_user_id", "seed-admin"),
            ),
        )

        venue = rec.get("venue", {})
        venue_name = venue.get("name", "Unknown Venue")
        venue_type = venue.get("type", "unknown")
        cur.execute(
            "INSERT OR REPLACE INTO venues (name, type) VALUES (?, ?)",
            (venue_name, venue_type),
        )
        cur.execute(
            "INSERT OR REPLACE INTO publication_venues (publication_id, venue_name) VALUES (?, ?)",
            (rec["id"], venue_name),
        )

        for author in rec.get("authors", []):
            cur.execute(
                "INSERT OR REPLACE INTO authors (id, name, affiliation) VALUES (?, ?, ?)",
                (author["id"], author["name"], author.get("affiliation")),
            )
            cur.execute(
                "INSERT OR REPLACE INTO publication_authors (publication_id, author_id) VALUES (?, ?)",
                (rec["id"], author["id"]),
            )

        for keyword in rec.get("keywords", []):
            cur.execute("INSERT OR IGNORE INTO keywords (keyword) VALUES (?)", (keyword,))
            cur.execute(
                "INSERT OR REPLACE INTO publication_keywords (publication_id, keyword) VALUES (?, ?)",
                (rec["id"], keyword),
            )

    conn.commit()
    conn.close()


def build_rdf(records: list[dict[str, Any]], rdf_path: Path) -> None:
    graph = Graph()
    graph.bind("onto", BASE)
    graph.bind("res", RES)

    for rec in records:
        pub_uri = URIRef(RES[f"publication/{rec['id']}"])
        graph.add((pub_uri, RDF.type, BASE.Publication))
        graph.add((pub_uri, BASE.title, Literal(rec["title"], datatype=XSD.string)))
        graph.add((pub_uri, BASE.year, Literal(rec["year"], datatype=XSD.gYear)))
        if rec.get("doi"):
            graph.add((pub_uri, BASE.doi, Literal(rec["doi"], datatype=XSD.string)))

        venue = rec.get("venue", {})
        venue_name = venue.get("name", "Unknown Venue")
        venue_uri = URIRef(RES[f"venue/{normalize_token(venue_name)}"])
        graph.add((venue_uri, RDF.type, BASE.Venue))
        graph.add((venue_uri, BASE.title, Literal(venue_name, datatype=XSD.string)))
        graph.add((pub_uri, BASE.publishedIn, venue_uri))

        for author in rec.get("authors", []):
            author_uri = URIRef(RES[f"author/{author['id']}"])
            graph.add((author_uri, RDF.type, BASE.Author))
            graph.add((author_uri, BASE.title, Literal(author["name"], datatype=XSD.string)))
            if author.get("affiliation"):
                aff_token = normalize_token(author["affiliation"])
                aff_uri = URIRef(RES[f"affiliation/{aff_token}"])
                graph.add((aff_uri, RDF.type, BASE.Affiliation))
                graph.add(
                    (aff_uri, BASE.title, Literal(author["affiliation"], datatype=XSD.string))
                )
                graph.add((author_uri, BASE.hasAffiliation, aff_uri))
            graph.add((pub_uri, BASE.hasAuthor, author_uri))

        for keyword in rec.get("keywords", []):
            key_uri = URIRef(RES[f"keyword/{normalize_token(keyword)}"])
            graph.add((key_uri, RDF.type, BASE.Keyword))
            graph.add((key_uri, BASE.title, Literal(keyword, datatype=XSD.string)))
            graph.add((pub_uri, BASE.hasKeyword, key_uri))

    graph.serialize(destination=rdf_path, format="turtle")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prototype: ontology-based scientific publication database formation"
    )
    parser.add_argument(
        "--input",
        default="data/publications",
        help="Path to publication JSON file",
    )
    parser.add_argument("--db", default="science_publications.db", help="SQLite DB output path")
    parser.add_argument("--rdf", default="science_publications.ttl", help="RDF Turtle output path")
    args = parser.parse_args()

    input_path = Path(args.input)
    db_path = Path(args.db)
    rdf_path = Path(args.rdf)

    records = load_records(input_path)
    build_sqlite(records, db_path)
    build_rdf(records, rdf_path)

    print(f"Loaded records: {len(records)}")
    print(f"SQLite database written to: {db_path.resolve()}")
    print(f"RDF Turtle written to: {rdf_path.resolve()}")


if __name__ == "__main__":
    main()
