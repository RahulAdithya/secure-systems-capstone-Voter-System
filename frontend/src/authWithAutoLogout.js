// authWithAutoLogout.js
import { apiLogin } from './api.js';

let logoutTimer;
let warningTimer;
const INACTIVITY_LIMIT = 30 * 1000; // 30 sec logout for testing
const WARNING_TIME = 15 * 1000; // 15 sec warning
let loggedOut = false; 

export function startAutoLogout(updateMessage) {
  clearTimeout(logoutTimer);
  clearTimeout(warningTimer);
  loggedOut = false;

  warningTimer = setTimeout(() => {
    
    if (!loggedOut && updateMessage){
      updateMessage("⚠️ You will be logged out soon!");
    }
  }, WARNING_TIME);

  logoutTimer = setTimeout(() => {
    clearTimeout(logoutTimer);
    clearTimeout(warningTimer);
    loggedOut = true;
    localStorage.removeItem("token");
    updateMessage("You have been logged out.");
    window.location.href = "/login";
    
  }, INACTIVITY_LIMIT);
}

export function resetAutoLogout(updateMessage) {
 if (!loggedOut){
  if (updateMessage) updateMessage("");
  startAutoLogout(updateMessage);
 } 
}

export async function loginWithAutoLogout(username, password, updateMessage) {
  const data = await apiLogin(username, password);
  localStorage.setItem("token", data.access_token);
  startAutoLogout(updateMessage);
  return data;
}
