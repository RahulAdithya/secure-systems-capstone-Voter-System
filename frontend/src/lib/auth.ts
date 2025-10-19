export const auth = {
  get(): string | null {
    return localStorage.getItem("access_token");
  },
  set(token: string) {
    localStorage.setItem("access_token", token);
  },
  clear() {
    localStorage.removeItem("access_token");
  },
  isAuthed(): boolean {
    return !!localStorage.getItem("access_token");
  },
};
