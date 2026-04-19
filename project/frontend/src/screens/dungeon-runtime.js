import { formatDungeonMessage, formatLootLines } from '../helpers.js';
import { showDefeat } from './defeat.js';

export function buildDungeonMarkup(enemy, messageToShow) {
  // Keep the dungeon shell in one place so the combat handlers can update it in place.
  return `
    <div id="dungeon-wrap" style="display:flex;flex-direction:column;gap:12px;">
      <div id="dungeon-top" style="padding:0;margin:0">
        <div class="dungeon-message-panel">
          <div id="dungeon-message" class="dungeon-message">${formatDungeonMessage(messageToShow)}</div>
        </div>

        <div style="display:flex;gap:20;justify-content:center;flex-wrap:wrap;align-items:stretch;margin-top:12px;padding:8px">
          <div id="player-stats-container" style="flex:1;min-width:250px;max-width:400px"></div>
          <div class="player-stats" style="flex:1;min-width:250px;max-width:400px;border-color:#ff6b6b">
            <h2 id="enemy-name" style="color:#ff6b6b">Enemy: ${enemy.name || 'None'}</h2>
            <div class="stat"><span class="stat-label">Level:</span><span id="enemy-level" class="stat-value">${enemy.level || ''}</span></div>
            <div class="stat"><span class="stat-label">Health:</span><span id="enemy-health" class="stat-value">${enemy.health} / ${enemy.max_health} HP</span></div>
            <div class="stat"><span class="stat-label">Damage:</span><span id="enemy-damage" class="stat-value">${enemy.damage}</span></div>
              </div>
        </div>
      </div>

      <div id="dungeon-actions" style="margin-top:8px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
        <button type="button" class="dungeon-button" id="attack">Attack</button>
        <button type="button" class="dungeon-button" id="run" style="background:linear-gradient(135deg,#ff9f1c 0%,#ffb700 100%)">Run Away</button>
        <button type="button" class="dungeon-button" id="back">Back to Home</button>
      </div>

      <div id="loot" style="margin-top:6px;padding:8px"></div>
    </div>
  `;
}

export function renderLootPanel(lootEl, lootCounts) {
  if (!lootEl) return;
  const lines = formatLootLines(lootCounts);
  lootEl.innerHTML = `<div style="margin-top:10px;padding:10px;background:#2d3436;border-left:4px solid #fdcb6e;border-radius:4px"><strong style="color:#fdcb6e">🎁 Loot obtained:</strong><p>${lines.join(', ')}</p></div>`;
}

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

export async function showDungeonDefeatScreen({ message, lootCounts, onExit }) {
  await showDefeat({
    message: message || 'You were defeated and lost the loot from this dungeon run.',
    lootCounts,
    onExit
  });
}
