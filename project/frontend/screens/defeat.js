export async function showDefeat({ message = 'You were defeated', lootCounts = {}, onExit = null } = {}) {
  if (!(window.app && typeof window.app.renderDungeon === 'function')) {
    // fallback: render a minimal defeat screen into root
    const root = document.getElementById('root');
    root.innerHTML = `<div class="game-container"><h1>${message}</h1></div>`;
    return;
  }
  // render into the existing dungeon content area if present
  const content = document.getElementById('dungeon-content') || document.getElementById('main-content') || document.getElementById('root');
  const lines = Object.keys(lootCounts).map(name => `${name}${lootCounts[name] > 1 ? ' x' + lootCounts[name] : ''}`);
  content.innerHTML = `
    <div style="display:flex;flex-direction:column;align-items:center;gap:12px;padding:20px">
      <h1 style="color:#ff6b6b">${message}</h1>
      <div style="margin-top:10px;padding:10px;background:#2d3436;border-left:4px solid #fdcb6e;border-radius:4px;width:100%;max-width:700px">
        <strong style="color:#fdcb6e">🎁 Loot obtained:</strong>
        <p>${lines.length ? lines.join(', ') : 'No loot obtained.'}</p>
      </div>
      <div style="margin-top:8px"><button id="exit-dungeon" class="dungeon-button">Exit dungeon</button></div>
    </div>
  `;
  const exitBtn = document.getElementById('exit-dungeon');
  if (exitBtn) exitBtn.addEventListener('click', () => {
    if (typeof onExit === 'function') onExit(); else window.location.hash = '#/';
  });
}
