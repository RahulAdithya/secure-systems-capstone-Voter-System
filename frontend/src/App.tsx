import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { auth } from "./lib/auth";
import Login from "./pages/Login";
import MfaEnroll from "./pages/MfaEnroll";

type ProtectedProps = {
  children: React.ReactNode;
};

function Protected({ children }: ProtectedProps) {
  return auth.isAuthed() ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App(): React.ReactElement {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/mfa-enroll" element={<MfaEnroll />} />
        <Route
          path="/"
          element={
            <Protected>
              <div style={{ padding: 24, fontFamily: "system-ui" }}>
                <h2>Dashboard (Protected)</h2>
                <p>You are authenticated with MFA.</p>
                <button
                  onClick={() => {
                    auth.clear();
                    window.location.href = "/login";
                  }}
                >
                  Sign out
                </button>
              </div>
            </Protected>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
