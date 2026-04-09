export async function showHome() {
  if (window.app && typeof window.app.renderHome === 'function') {
    return window.app.renderHome();
  }
  throw new Error('renderHome not available on window.app');
}
