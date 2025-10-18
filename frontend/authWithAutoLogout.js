import { apiLogin } from './api.js'; // your existing apiLogin

// --- Auto logout setup ---
let logoutTimer;
const INACTIVITY_LIMIT = 15 * 60 * 1000; // 15 minutes

function startLogoutTimer() {
  clearTimeout(logoutTimer);
  logoutTimer = setTimeout(() => {
    // Remove token and redirect
    localStorage.removeItem("token");
    alert("You have been logged out due to inactivity.");
    window.location.href = "/login"; // change to your login page route
  }, INACTIVITY_LIMIT);
}

function resetLogoutTimer() {
  startLogoutTimer();
}

// Listen for user activity
window.addEventListener("mousemove", resetLogoutTimer);
window.addEventListener("keydown", resetLogoutTimer);
window.addEventListener("click", resetLogoutTimer);
window.addEventListener("scroll", resetLogoutTimer);

// --- Login function wrapper ---
export async function loginWithAutoLogout(username, password) {
  try {
    const data = await apiLogin(username, password);
    // Store token in localStorage
    localStorage.setItem("token", data.access_token);

    // Start inactivity timer
    startLogoutTimer();

    alert("Login successful!");
    return data;
  } catch (err) {
    alert(err.message);
    throw err;
  }
}