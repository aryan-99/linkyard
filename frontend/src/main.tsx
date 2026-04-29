import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import { setAuthToken } from "./api/client";

// Bootstrap admin token from localStorage so it is applied from the very first request.
const storedToken = localStorage.getItem("linkyard_admin_token");
if (storedToken) {
  setAuthToken(storedToken);
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
