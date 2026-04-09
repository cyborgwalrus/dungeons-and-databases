export async function showDungeon() {
  if (window.app && typeof window.app.renderDungeon === 'function') {
    return window.app.renderDungeon();
  }
  throw new Error('renderDungeon not available on window.app');
}
