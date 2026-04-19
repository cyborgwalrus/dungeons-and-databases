export async function showLogin() {
  if (window.app && typeof window.app.renderLogin === 'function') {
    return window.app.renderLogin();
  }
  throw new Error('renderLogin not available on window.app');
}
