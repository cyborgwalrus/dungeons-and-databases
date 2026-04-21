import { formatDungeonMessage, formatLootLines } from '../helpers.js';

/** Show the dungeon defeat screen and optionally hand control back to the caller. */
export async function showDefeat({ message = 'You were defeated and lost the loot from this dungeon run.', lootCounts = {}, onExit = null } = {}) {
  // render into the existing dungeon content area if present
  const content = document.getElementById('dungeon-content') || document.getElementById('main-content') || document.getElementById('root');
  if (!content) {
    return;
  }
  const lines = formatLootLines(lootCounts);
  content.innerHTML = `
    <div class="dungeon-defeat-screen">
      <div class="dungeon-defeat-message">${formatDungeonMessage(message)}</div>
      <div class="dungeon-loot-panel">
        <strong class="dungeon-loot-title">🎁 Loot obtained:</strong>
        <p class="dungeon-loot-list">${lines.length ? lines.join(', ') : 'No loot obtained.'}</p>
      </div>
      <div style="margin-top:8px"><button id="exit-dungeon" class="dungeon-button">Exit dungeon</button></div>
    </div>
  `;
  const exitBtn = document.getElementById('exit-dungeon');
  if (exitBtn) exitBtn.addEventListener('click', () => {
    if (typeof onExit === 'function') onExit(); else window.location.hash = '#/';
  });
}
