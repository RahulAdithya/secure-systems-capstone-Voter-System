import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { auth } from "./lib/auth";
import Login from "./pages/Login";
import AdminLogin from "./pages/AdminLogin";
import MfaEnroll from "./pages/MfaEnroll";
import Signup from "./pages/Signup";
import AdminDashboard from "./pages/AdminDashboard";
import UserDashboard from "./pages/UserDashboard";
import AppChrome from "./components/layout/AppChrome";

type ProtectedProps = {
  children: React.ReactNode;
};

function Protected({ children }: ProtectedProps) {
  return auth.isAuthed() ? <>{children}</> : <Navigate to="/login" replace />;
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
          <Route
            path="/"
            element={
              <Protected>
                {auth.isAdmin() ? (
                  <AdminDashboard />
                ) : (
                  <UserDashboard />
                )}
              </Protected>
            }
          />
        </Routes>
      </AppChrome>
    </BrowserRouter>
  );
}
