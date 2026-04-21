import { formatDungeonMessage } from '../helpers.js';

/** Show the dungeon defeat screen and optionally hand control back to the caller. */
export function showDefeat({ message = 'Defeat!\nYou have been defeated by the enemy!\nYou lost the loot from this dungeon run...', onExit = null } = {}) {
  // render into the existing dungeon content area if present
  const content = document.getElementById('dungeon-content') || document.getElementById('main-content') || document.getElementById('root');
  if (!content) {
    return;
  }
  content.innerHTML = `
    <div class="dungeon-defeat-screen screen-stack">
      <div class="screen-panel screen-panel--dark dungeon-defeat-message">${formatDungeonMessage(message)}</div>
      <div class="screen-panel screen-panel--dark dungeon-exit-section">
        <div class="screen-button-stack"><button id="exit-dungeon" class="dungeon-button">Exit dungeon</button></div>
      </div>
    </div>
  `;
  const exitBtn = document.getElementById('exit-dungeon');
  if (exitBtn) exitBtn.addEventListener('click', () => {
    if (typeof onExit === 'function') onExit(); else window.location.hash = '#/';
  });
}
