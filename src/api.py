import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.prototype import create_schema


DB_PATH = Path("science_publications.db")


class AuthorInput(BaseModel):
    name: str = Field(min_length=1)
    affiliation: str | None = None


class VenueInput(BaseModel):
    name: str = Field(min_length=1)
    type: str = "unknown"


class PublicationInput(BaseModel):
    title: str = Field(min_length=1)
    year: int
    doi: str | None = None
    abstract: str | None = None
    venue: VenueInput
    authors: list[AuthorInput] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


def normalize_token(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    create_schema(conn)
    ensure_rbac_schema(conn)
    return conn


app = FastAPI(title="Publications API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_rbac_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(publications)")
    columns = {row["name"] for row in cur.fetchall()}
    if "owner_user_id" not in columns:
        cur.execute(
            "ALTER TABLE publications ADD COLUMN owner_user_id TEXT NOT NULL DEFAULT 'legacy-user'"
        )
        conn.commit()


def get_actor(
    x_user_id: str | None = Header(default=None),
    x_role: str | None = Header(default=None),
) -> tuple[str, str]:
    user_id = (x_user_id or "").strip()
    role = (x_role or "").strip().lower()

    if not user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    if role not in {"user", "admin"}:
        raise HTTPException(status_code=403, detail="X-Role must be either 'user' or 'admin'")
    return user_id, role


@app.get("/api/publications")
def list_publications() -> list[dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, title, year, doi, abstract, owner_user_id
        FROM publications
        ORDER BY year DESC, title
        """
    )
    publications = [dict(row) for row in cur.fetchall()]

    for pub in publications:
        pub_id = pub["id"]
        cur.execute(
            """
            SELECT a.id, a.name, a.affiliation
            FROM authors a
            JOIN publication_authors pa ON pa.author_id = a.id
            WHERE pa.publication_id = ?
            ORDER BY a.name
            """,
            (pub_id,),
        )
        pub["authors"] = [dict(row) for row in cur.fetchall()]

        cur.execute(
            """
            SELECT v.name, v.type
            FROM venues v
            JOIN publication_venues pv ON pv.venue_name = v.name
            WHERE pv.publication_id = ?
            """,
            (pub_id,),
        )
        venue_row = cur.fetchone()
        pub["venue"] = dict(venue_row) if venue_row else None

        cur.execute(
            """
            SELECT k.keyword
            FROM keywords k
            JOIN publication_keywords pk ON pk.keyword = k.keyword
            WHERE pk.publication_id = ?
            ORDER BY k.keyword
            """,
            (pub_id,),
        )
        pub["keywords"] = [row["keyword"] for row in cur.fetchall()]

    conn.close()
    return publications


@app.post("/api/publications")
def create_publication(
    payload: PublicationInput,
    x_user_id: str | None = Header(default=None),
    x_role: str | None = Header(default=None),
) -> dict[str, str]:
    user_id, _role = get_actor(x_user_id, x_role)
    pub_id = f"pub-{uuid4().hex[:8]}"
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO publications (id, title, year, doi, abstract, owner_user_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (pub_id, payload.title, payload.year, payload.doi, payload.abstract, user_id),
        )

        cur.execute(
            "INSERT OR IGNORE INTO venues (name, type) VALUES (?, ?)",
            (payload.venue.name, payload.venue.type),
        )
        cur.execute(
            "INSERT OR REPLACE INTO publication_venues (publication_id, venue_name) VALUES (?, ?)",
            (pub_id, payload.venue.name),
        )

        for author in payload.authors:
            author_id = f"auth-{normalize_token(author.name) or uuid4().hex[:6]}"
            cur.execute(
                "INSERT OR IGNORE INTO authors (id, name, affiliation) VALUES (?, ?, ?)",
                (author_id, author.name, author.affiliation),
            )
            cur.execute(
                "INSERT OR REPLACE INTO publication_authors (publication_id, author_id) VALUES (?, ?)",
                (pub_id, author_id),
            )

        for keyword in payload.keywords:
            cleaned = keyword.strip()
            if not cleaned:
                continue
            cur.execute("INSERT OR IGNORE INTO keywords (keyword) VALUES (?)", (cleaned,))
            cur.execute(
                "INSERT OR REPLACE INTO publication_keywords (publication_id, keyword) VALUES (?, ?)",
                (pub_id, cleaned),
            )

        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Database constraint error: {exc}") from exc
    finally:
        conn.close()

    return {"id": pub_id}


@app.delete("/api/publications/{publication_id}")
def delete_publication(
    publication_id: str,
    x_user_id: str | None = Header(default=None),
    x_role: str | None = Header(default=None),
) -> dict[str, str]:
    user_id, role = get_actor(x_user_id, x_role)
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT owner_user_id FROM publications WHERE id = ?", (publication_id,))
    publication = cur.fetchone()
    if publication is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Publication not found")

    owner_user_id = publication["owner_user_id"]
    if role != "admin" and owner_user_id != user_id:
        conn.close()
        raise HTTPException(status_code=403, detail="You can only delete your own publications")

    try:
        cur.execute("DELETE FROM publication_authors WHERE publication_id = ?", (publication_id,))
        cur.execute("DELETE FROM publication_keywords WHERE publication_id = ?", (publication_id,))
        cur.execute("DELETE FROM publication_venues WHERE publication_id = ?", (publication_id,))
        cur.execute("DELETE FROM publications WHERE id = ?", (publication_id,))
        conn.commit()
    finally:
        conn.close()

    return {"status": "deleted"}
