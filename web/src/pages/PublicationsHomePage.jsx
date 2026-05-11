import { useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { API_BASE, PAGE_SIZE_OPTIONS } from "../config.js";
import { buildAuthHeaders, canDeletePublication } from "../auth.js";

export function PublicationsHomePage() {
  const { actor } = useOutletContext();
  const [publications, setPublications] = useState([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingPublicationId, setDeletingPublicationId] = useState("");

  const total = publications.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1);

  const visiblePublications = useMemo(() => {
    const start = (page - 1) * pageSize;
    return publications.slice(start, start + pageSize);
  }, [publications, page, pageSize]);

  useEffect(() => {
    setPage((p) => Math.min(Math.max(1, p), totalPages));
  }, [totalPages]);

  async function loadPublications() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/publications`);
      if (!response.ok) {
        throw new Error("Failed to load publications");
      }
      const data = await response.json();
      setPublications(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPublications();
  }, []);

  async function onDeletePublication(publicationId) {
    setDeletingPublicationId(publicationId);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/publications/${publicationId}`, {
        method: "DELETE",
        headers: buildAuthHeaders(actor),
      });
      if (!response.ok) {
        const details = await response.json();
        throw new Error(details.detail || "Failed to delete publication");
      }
      setPublications((current) => current.filter((pub) => pub.id !== publicationId));
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingPublicationId("");
    }
  }

  return (
    <main className="container">
      <h1>Publications</h1>
      <p className="page-lede">Browse publications from the catalog. Use the manager to add new entries.</p>

      <section className="card">
        <h2>Catalog</h2>
        {error ? <p className="error">{error}</p> : null}
        {loading ? <p>Loading...</p> : null}
        {!loading && publications.length === 0 ? <p>No publications yet.</p> : null}
        {!loading && total > 0 ? (
          <div className="pagination-bar" aria-label="Publication list pagination">
            <p className="pagination-meta">
              Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}
            </p>
            <div className="pagination-row">
              <label className="pagination-page-size">
                Per page{" "}
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                >
                  {PAGE_SIZE_OPTIONS.map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
              </label>
              <div className="pagination-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={page <= 1}
                  onClick={() => setPage(1)}
                >
                  First
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </button>
                <span className="pagination-page-indicator">
                  Page {page} of {totalPages}
                </span>
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={page >= totalPages}
                  onClick={() => setPage(totalPages)}
                >
                  Last
                </button>
              </div>
            </div>
          </div>
        ) : null}
        <ul className="pub-list">
          {visiblePublications.map((pub) => (
            <li key={pub.id}>
              <h3>
                {pub.title} ({pub.year})
              </h3>
              <p>
                <strong>ID:</strong> {pub.id}
              </p>
              <p>
                <strong>Venue:</strong> {pub.venue?.name || "N/A"} ({pub.venue?.type || "N/A"})
              </p>
              <p>
                <strong>Authors:</strong>{" "}
                {pub.authors?.length
                  ? pub.authors.map((author) => author.name).join(", ")
                  : "N/A"}
              </p>
              <p>
                <strong>Keywords:</strong> {pub.keywords?.length ? pub.keywords.join(", ") : "N/A"}
              </p>
              {pub.doi ? (
                <p>
                  <strong>DOI:</strong> {pub.doi}
                </p>
              ) : null}
              <p>
                <strong>Owner:</strong> {pub.owner_user_id}
              </p>
              {canDeletePublication(pub, actor) ? (
                <button
                  type="button"
                  className="btn-danger"
                  onClick={() => onDeletePublication(pub.id)}
                  disabled={deletingPublicationId === pub.id}
                >
                  {deletingPublicationId === pub.id ? "Deleting..." : "Delete publication"}
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

