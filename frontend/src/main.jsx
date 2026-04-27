// React entry point — the first JS that runs in the browser.
//
// Order of wrappers matters:
//   StrictMode  — turns on dev-only checks for unsafe lifecycle patterns
//   BrowserRouter — provides URL-based routing context
//   AuthProvider  — provides the "current user" context
//   App           — the actual route table and pages
//
// Each provider that comes later can use the context from the providers
// before it.

import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { AuthProvider } from "./auth.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
