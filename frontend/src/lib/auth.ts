export const auth = {
  get(): string | null {
    return localStorage.getItem("access_token");
  },
  set(token: string) {
    localStorage.setItem("access_token", token);
  },
  setRole(role: "admin" | "voter") {
    localStorage.setItem("role", role);
  },
  getRole(): "admin" | "voter" | null {
    const r = localStorage.getItem("role");
    return r === "admin" || r === "voter" ? r : null;
  },
  isAdmin(): boolean {
    return localStorage.getItem("role") === "admin";
  },
  clear() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("role");
  },
  isAuthed(): boolean {
    return !!localStorage.getItem("access_token");
  },
};
