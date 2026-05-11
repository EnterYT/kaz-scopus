const ACTOR_STORAGE_KEY = "kaz_scopus_actor";

const DEFAULT_ACTOR = {
  userId: "user-1",
  role: "user",
};

export function normalizeActor(actor) {
  const userId = String(actor?.userId ?? "").trim() || DEFAULT_ACTOR.userId;
  const roleValue = String(actor?.role ?? "").trim().toLowerCase();
  const role = roleValue === "admin" ? "admin" : "user";
  return { userId, role };
}

export function loadActor() {
  try {
    const raw = localStorage.getItem(ACTOR_STORAGE_KEY);
    if (!raw) {
      return DEFAULT_ACTOR;
    }
    return normalizeActor(JSON.parse(raw));
  } catch {
    return DEFAULT_ACTOR;
  }
}

export function persistActor(actor) {
  const normalized = normalizeActor(actor);
  localStorage.setItem(ACTOR_STORAGE_KEY, JSON.stringify(normalized));
  return normalized;
}

export function buildAuthHeaders(actor) {
  const normalized = normalizeActor(actor);
  return {
    "X-User-Id": normalized.userId,
    "X-Role": normalized.role,
  };
}

export function canDeletePublication(publication, actor) {
  const normalized = normalizeActor(actor);
  if (normalized.role === "admin") {
    return true;
  }
  return publication.user_id === normalized.userId;
}
