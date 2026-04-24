import { escapeHtml, formatDungeonMessage, formatLootLines } from '../helpers.js';
import { showDefeat } from './defeat.js';

/** Build the static dungeon layout used by the live combat screen. */
export function buildDungeonMarkup(enemy, messageToShow) {
  // Keep the dungeon shell in one place so the combat handlers can update it in place.
  return `
    <div id="dungeon-wrap" class="dungeon-wrap screen-stack">
      <div class="screen-panel screen-panel--nested dungeon-enemy-panel">
        <div class="vertical-health-bar" id="enemy-health-bar" aria-hidden="true"><div class="vertical-health-bar-fill"></div></div>
        <div class="player-stats dungeon-enemy-stats">
          <h2 id="enemy-name" class="dungeon-enemy-name">Enemy: ${escapeHtml(enemy.name || 'None')}</h2>
          <div class="stat"><span class="stat-label">Level:</span><span id="enemy-level" class="stat-value">${enemy.level || ''}</span></div>
          <div class="stat"><span class="stat-label">Health:</span><span id="enemy-health" class="stat-value">${enemy.health} / ${enemy.max_health} HP</span></div>
          <div class="stat"><span class="stat-label">Damage:</span><span id="enemy-damage" class="stat-value">${enemy.damage}</span></div>
        </div>
      </div>

      <div id="player-stats-container" class="screen-panel screen-panel--nested dungeon-player-stats">
        <div class="vertical-health-bar" id="player-health-bar" aria-hidden="true"><div class="vertical-health-bar-fill"></div></div>
      </div>

      <div class="screen-panel screen-panel--dark dungeon-message-panel">
        <div id="dungeon-message" class="dungeon-message">${formatDungeonMessage(messageToShow)}</div>
      </div>

      <div id="dungeon-actions" class="screen-panel screen-panel--dark dungeon-actions-row">
        <div class="screen-button-stack">
          <button type="button" class="dungeon-button dungeon-button-primary" id="attack">⚔️ATTACK</button>
          <button type="button" class="dungeon-button dungeon-button-escape" id="run" data-action="run">4/6🎲RUN AWAY</button>
        </div>
      </div>

      <div id="loot" class="screen-panel screen-panel--dark dungeon-loot-section"></div>
    </div>
  `;
}

/** Update the dungeon action labels without rebuilding the screen. */
export function updateDungeonActionLabels({ attackLabel, runLabel } = {}) {
  const attackButton = document.getElementById('attack');
  const runButton = document.getElementById('run');
  if (attackButton && attackLabel) attackButton.textContent = attackLabel;
  if (runButton && runLabel) runButton.textContent = runLabel;
  if (runButton && runLabel === '🏠GO HOME') runButton.dataset.action = 'home';
  if (runButton && runLabel === '4/6🎲RUN AWAY') runButton.dataset.action = 'run';
}

/** Render the loot summary panel inside the dungeon screen. */
export function renderLootPanel(lootEl, lootCounts) {
  if (!lootEl) return;
  const lines = formatLootLines(lootCounts);
  const totalLoot = Object.values(lootCounts || {}).reduce((sum, count) => sum + Math.max(0, Number(count) || 0), 0);
  const lootList = lines.length ? `<p class="dungeon-loot-list">${escapeHtml(lines.join(', '))}</p>` : '<div class="dungeon-loot-empty"></div>';
  lootEl.innerHTML = `<div class="dungeon-loot-panel"><strong class="dungeon-loot-title">🎁 Loot obtained: ${totalLoot}</strong>${lootList}</div>`;
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
  }

  renderLootPanel(lootEl, lootCounts);
}

/** Show the defeat overlay and let the caller restore navigation state. */
export function showDungeonDefeatScreen({ message, onExit }) {
  return showDefeat({
    message: message || 'You were defeated and lost the loot from this dungeon run.',
    onExit
  });
}
