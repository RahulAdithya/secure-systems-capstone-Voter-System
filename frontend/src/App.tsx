import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { auth } from "./lib/auth";
import Login from "./pages/Login";
import AdminLogin from "./pages/AdminLogin";
import MfaEnroll from "./pages/MfaEnroll";
import Signup from "./pages/Signup";
import AdminDashboard from "./pages/AdminDashboard";
import UserDashboard from "./pages/UserDashboard";
import Forbidden from "./pages/Forbidden";
import AppChrome from "./components/layout/AppChrome";

type ProtectedProps = {
  children: React.ReactNode;
};

function RequireAuth({ children }: ProtectedProps) {
  return auth.isAuthed() ? <>{children}</> : <Navigate to="/login" replace />;
}

function RequireAdmin({ children }: ProtectedProps) {
  if (!auth.isAuthed()) {
    return <Navigate to="/admin-login" replace />;
  }
  if (!auth.isAdmin()) {
    return <Navigate to="/403" replace />;
  }
  return <>{children}</>;
}

export default function App(): React.ReactElement {
  return (
    <BrowserRouter>
      <AppChrome>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/admin-login" element={<AdminLogin />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/mfa-enroll" element={<MfaEnroll />} />
          <Route path="/403" element={<Forbidden />} />
          <Route
            path="/"
            element={
              <RequireAuth>
                {auth.isAdmin() ? <Navigate to="/admin" replace /> : <UserDashboard />}
              </RequireAuth>
            }
          />
          <Route
            path="/admin"
            element={
              <RequireAdmin>
                <AdminDashboard />
              </RequireAdmin>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppChrome>
    </BrowserRouter>
  );
}
