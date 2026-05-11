"""Generate data/publications JSON with N sample records and rebuild SQLite + RDF."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.prototype import build_rdf, build_sqlite  # noqa: E402

AUTHORS = [
    {"id": "auth-001", "name": "Aigerim Nurgalieva", "affiliation": "Kazakh National University"},
    {"id": "auth-002", "name": "Daniyar Toleubay", "affiliation": "Astana IT University"},
    {"id": "auth-003", "name": "Madi Rysbek", "affiliation": "Nazarbayev University"},
    {"id": "auth-004", "name": "Saule Kenzhebek", "affiliation": "Al-Farabi KazNU"},
    {"id": "auth-005", "name": "Yerlan Akhmetov", "affiliation": "Satbayev University"},
    {"id": "auth-006", "name": "Ainur Omarova", "affiliation": "Eurasian National University"},
    {"id": "auth-007", "name": "Rustem Abdrakhmanov", "affiliation": "Kazakh-British Technical University"},
    {"id": "auth-008", "name": "Gulmira Mukhanova", "affiliation": "Karaganda Technical University"},
    {"id": "auth-009", "name": "Timur Suleimenov", "affiliation": "Nazarbayev University"},
    {"id": "auth-010", "name": "Zarina Bekturova", "affiliation": "Astana Medical University"},
]

VENUES = [
    {"name": "International Journal of Digital Libraries", "type": "journal"},
    {"name": "Workshop on Knowledge Graphs in Science", "type": "conference"},
    {"name": "Computational Linguistics and AI Review", "type": "journal"},
    {"name": "Central Asian Journal of Computer Science", "type": "journal"},
    {"name": "Proceedings of IEEE BigData", "type": "conference"},
    {"name": "Semantic Web Journal", "type": "journal"},
    {"name": "Journal of Machine Learning Research", "type": "journal"},
    {"name": "Information Systems Frontiers", "type": "journal"},
    {"name": "ACM Conference on Knowledge Discovery", "type": "conference"},
    {"name": "Data & Knowledge Engineering", "type": "journal"},
]

TOPIC_PREFIXES = [
    "Graph-based",
    "Neural",
    "Ontology-driven",
    "Scalable",
    "Federated",
    "Explainable",
    "Weakly supervised",
    "Cross-lingual",
    "Temporal",
    "Multi-modal",
]

TOPIC_CORES = [
    "metadata harmonization for research repositories",
    "entity linking in scholarly text",
    "citation network analysis",
    "topic modeling with domain ontologies",
    "knowledge graph construction from abstracts",
    "semantic search over publication corpora",
    "author disambiguation in bibliographic data",
    "dataset discovery via linked open data",
    "reproducibility tracking in ML papers",
    "survey summarization with LLMs",
]

KEYWORD_POOL = [
    "ontology",
    "knowledge graph",
    "metadata",
    "semantic web",
    "NLP",
    "machine learning",
    "information retrieval",
    "digital libraries",
    "bibliometrics",
    "linked data",
    "RDF",
    "SPARQL",
    "scientific publications",
    "Scopus",
    "OpenAlex",
]


def build_records(count: int) -> list[dict]:
    records: list[dict] = []
    for i in range(count):
        n = i + 1
        prefix = TOPIC_PREFIXES[i % len(TOPIC_PREFIXES)]
        core = TOPIC_CORES[i % len(TOPIC_CORES)]
        year = 2018 + (i % 9)
        venue = VENUES[i % len(VENUES)]
        a0 = i % len(AUTHORS)
        a1 = (i + 3 + (i % 4)) % len(AUTHORS)
        authors = [AUTHORS[a0]]
        if n % 3 != 0:
            authors.append(AUTHORS[a1])
        if n % 5 == 0:
            authors.append(AUTHORS[(a1 + 1) % len(AUTHORS)])

        k_start = i % max(1, len(KEYWORD_POOL) - 3)
        keywords = KEYWORD_POOL[k_start : k_start + 3]
        if len(keywords) < 3:
            keywords = KEYWORD_POOL[:3]

        records.append(
            {
                "id": f"pub-{n:03d}",
                "title": f"{prefix} approaches to {core}",
                "year": year,
                "doi": f"10.1000/kaz-scopus.{year}.{1000 + n}",
                "abstract": (
                    f"Study {n} examines methods for {core} in Central Asian and global "
                    "scholarly datasets, with evaluation on benchmark retrieval tasks."
                ),
                "user_id": "seeded",
                "venue": dict(venue),
                "authors": [dict(a) for a in authors],
                "keywords": list(keywords),
            }
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate seed publications JSON and rebuild artifacts.")
    parser.add_argument("--count", type=int, default=100, help="Number of publication records")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "publications",
        help="Path to JSON file (default: data/publications)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=ROOT / "science_publications.db",
        help="SQLite output path",
    )
    parser.add_argument(
        "--rdf",
        type=Path,
        default=ROOT / "science_publications.ttl",
        help="RDF Turtle output path",
    )
    parser.add_argument("--skip-db", action="store_true", help="Only write JSON")
    args = parser.parse_args()

    records = build_records(args.count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} records to {args.output}")

    if not args.skip_db:
        build_sqlite(records, args.db)
        build_rdf(records, args.rdf)
        print(f"SQLite: {args.db.resolve()}")
        print(f"Turtle: {args.rdf.resolve()}")


if __name__ == "__main__":
    main()
