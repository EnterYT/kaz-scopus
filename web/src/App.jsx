import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useState } from "react";

import { MainLayout } from "./layouts/MainLayout.jsx";

import { PublicationManagerPage } from "./pages/PublicationManagerPage.jsx";

import { PublicationsHomePage } from "./pages/PublicationsHomePage.jsx";
import { loadActor, persistActor } from "./auth.js";



export default function App() {
  const [actor, setActor] = useState(() => loadActor());
  const onActorChange = (nextActor) => {
    setActor(persistActor(nextActor));
  };

  return (

    <BrowserRouter>

      <Routes>

        <Route element={<MainLayout actor={actor} onActorChange={onActorChange} />}>

          <Route path="/" element={<PublicationsHomePage />} />

          <Route path="/manage" element={<PublicationManagerPage />} />

          <Route path="*" element={<Navigate to="/" replace />} />

        </Route>

      </Routes>

    </BrowserRouter>

  );

}


