export async function showCharacterSelect() {
  if (window.app && typeof window.app.renderCharacterSelect === 'function') {
    return window.app.renderCharacterSelect();
  }
  throw new Error('renderCharacterSelect not available on window.app');
}
