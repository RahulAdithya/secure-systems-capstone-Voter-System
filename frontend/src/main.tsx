import React from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./index.css";
import { ThemeProvider } from "./theme/ThemeProvider";

const container = document.getElementById("root");

if (!container) {
  throw new Error("Root container not found");
}

createRoot(container).render(
  <React.StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </React.StrictMode>,
);
