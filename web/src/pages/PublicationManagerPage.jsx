import { useState } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import { API_BASE } from "../config.js";
import { buildAuthHeaders } from "../auth.js";

const initialForm = {
  title: "",
  year: new Date().getFullYear(),
  doi: "",
  abstract: "",
  venueName: "",
  venueType: "journal",
  authors: "",
  keywords: "",
};

export function PublicationManagerPage() {
  const navigate = useNavigate();
  const { actor } = useOutletContext();
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  function onFieldChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function onSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    const authors = form.authors
      .split(",")
      .map((name) => name.trim())
      .filter(Boolean)
      .map((name) => ({ name }));

    const keywords = form.keywords
      .split(",")
      .map((keyword) => keyword.trim())
      .filter(Boolean);

    const payload = {
      title: form.title.trim(),
      year: Number(form.year),
      doi: form.doi.trim() || null,
      abstract: form.abstract.trim() || null,
      venue: {
        name: form.venueName.trim(),
        type: form.venueType.trim() || "unknown",
      },
      authors,
      keywords,
    };

    try {
      const response = await fetch(`${API_BASE}/publications`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...buildAuthHeaders(actor),
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const details = await response.json();
        throw new Error(details.detail || "Failed to create publication");
      }
      setForm(initialForm);
      navigate("/", { replace: false });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="container">
      <h1>Publication manager</h1>
      <p className="page-lede">
        Add new publications to the catalog as the selected actor. After saving you are taken back to
        the list.
      </p>

      <section className="card">
        <h2>Add publication</h2>
        {error ? <p className="error">{error}</p> : null}
        <form onSubmit={onSubmit} className="form-grid">
          <input
            required
            name="title"
            placeholder="Title"
            value={form.title}
            onChange={onFieldChange}
          />
          <input
            required
            name="year"
            type="number"
            placeholder="Year"
            value={form.year}
            onChange={onFieldChange}
          />
          <input name="doi" placeholder="DOI" value={form.doi} onChange={onFieldChange} />
          <input
            required
            name="venueName"
            placeholder="Venue name"
            value={form.venueName}
            onChange={onFieldChange}
          />
          <input
            name="venueType"
            placeholder="Venue type (journal/conference)"
            value={form.venueType}
            onChange={onFieldChange}
          />
          <input
            name="authors"
            placeholder="Authors, comma-separated"
            value={form.authors}
            onChange={onFieldChange}
          />
          <input
            name="keywords"
            placeholder="Keywords, comma-separated"
            value={form.keywords}
            onChange={onFieldChange}
          />
          <textarea
            name="abstract"
            placeholder="Abstract"
            value={form.abstract}
            onChange={onFieldChange}
          />
          <button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : "Add publication"}
          </button>
        </form>
      </section>
    </main>
  );
}

