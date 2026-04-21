import { escapeHtml, formatDungeonMessage, formatLootLines } from '../helpers.js';
import { showDefeat } from './defeat.js';

/** Build the static dungeon layout used by the live combat screen. */
export function buildDungeonMarkup(enemy, messageToShow) {
  // Keep the dungeon shell in one place so the combat handlers can update it in place.
  return `
    <div id="dungeon-wrap" class="dungeon-wrap">
      <div id="dungeon-top" class="dungeon-top">
        <div class="dungeon-message-panel">
          <div id="dungeon-message" class="dungeon-message">${formatDungeonMessage(messageToShow)}</div>
        </div>

        <div class="dungeon-stats-row">
          <div id="player-stats-container" class="dungeon-player-stats"></div>
          <div class="player-stats dungeon-enemy-stats">
            <h2 id="enemy-name" class="dungeon-enemy-name">Enemy: ${escapeHtml(enemy.name || 'None')}</h2>
            <div class="stat"><span class="stat-label">Level:</span><span id="enemy-level" class="stat-value">${enemy.level || ''}</span></div>
            <div class="stat"><span class="stat-label">Health:</span><span id="enemy-health" class="stat-value">${enemy.health} / ${enemy.max_health} HP</span></div>
            <div class="stat"><span class="stat-label">Damage:</span><span id="enemy-damage" class="stat-value">${enemy.damage}</span></div>
          </div>
        </div>
      </div>

      <div id="dungeon-actions" class="dungeon-actions-row">
        <button type="button" class="dungeon-button dungeon-button-primary" id="attack">Attack</button>
        <button type="button" class="dungeon-button dungeon-button-escape" id="run">Run Away</button>
        <button type="button" class="dungeon-button dungeon-button-secondary" id="back">Back to Home</button>
      </div>

      <div id="loot" class="dungeon-loot-section"></div>
    </div>
  `;
}

/** Render the loot summary panel inside the dungeon screen. */
export function renderLootPanel(lootEl, lootCounts) {
  if (!lootEl) return;
  const lines = formatLootLines(lootCounts);
  lootEl.innerHTML = `<div class="dungeon-loot-panel"><strong class="dungeon-loot-title">🎁 Loot obtained:</strong><p>${escapeHtml(lines.join(', '))}</p></div>`;
}

/** Apply the latest combat response to the active dungeon UI. */
export function applyDungeonCombatUpdate(d, { lootCounts, onLootDropped, setLastDungeonMessage, lootEl }) {
  // The server returns the latest enemy/player state after each attack; mirror it into the live panel.
  const nextMessage = d.message || 'You attacked the monster!';
  if (typeof setLastDungeonMessage === 'function') setLastDungeonMessage(nextMessage);
  const dungeonMessage = document.getElementById('dungeon-message');
  if (dungeonMessage) dungeonMessage.innerHTML = formatDungeonMessage(nextMessage);

  if (d.items_dropped && d.items_dropped.length) {
    d.items_dropped.forEach(it => {
      const n = it.name || 'Unknown';
      lootCounts[n] = (lootCounts[n] || 0) + 1;
    });
    if (typeof onLootDropped === 'function') onLootDropped(d.items_dropped);
    renderLootPanel(lootEl, lootCounts);
  }
}

/** Show the defeat overlay and let the caller restore navigation state. */
export async function showDungeonDefeatScreen({ message, lootCounts, onExit }) {
  await showDefeat({
    message: message || 'You were defeated and lost the loot from this dungeon run.',
    lootCounts,
    onExit
  });
}
