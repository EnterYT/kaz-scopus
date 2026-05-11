import { NavLink, Outlet } from "react-router-dom";

function navClass({ isActive }) {
  return isActive ? "nav-link nav-link-active" : "nav-link";
}

export function MainLayout({ actor, onActorChange }) {
  function onUserChange(event) {
    onActorChange({ ...actor, userId: event.target.value });
  }

  function onRoleChange(event) {
    onActorChange({ ...actor, role: event.target.value });
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="site-header-inner container">
          <span className="site-brand">Kaz Scopus</span>
          <nav className="site-nav" aria-label="Primary">
            <NavLink to="/" className={navClass} end>
              Publications
            </NavLink>
            <NavLink to="/manage" className={navClass}>
              Publication manager
            </NavLink>
          </nav>
          <div className="actor-controls" aria-label="Current actor context">
            <label>
              User ID
              <input value={actor.userId} onChange={onUserChange} placeholder="user-1" />
            </label>
            <label>
              Role
              <select value={actor.role} onChange={onRoleChange}>
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
            </label>
          </div>
        </div>
      </header>
      <Outlet context={{ actor }} />
    </div>
  );
}

