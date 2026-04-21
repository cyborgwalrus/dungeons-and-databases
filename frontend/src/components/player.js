import { escapeHtml } from '../helpers.js';

/**
 * Derive the displayed combat stats from a player snapshot.
 * Keeps the same fallback logic in one place for all HUD panels.
 */
export function getPlayerStatValues(player) {
  const level = player?.level || 1;
  const bonusHealth = player?.bonus_health || 0;
  const bonusDamage = player?.bonus_damage || 0;
  const maxHealth = player?.max_health ?? ((100 + (Math.max(0, level - 1) * 10)) + bonusHealth);
  const totalDamage = (player?.damage || 0) + bonusDamage;
  const experience = player?.experience || 0;
  const experienceToNextLevel = player?.experience_to_next_level || (100 + (Math.max(0, level - 1) * 50));

  return {
    level,
    maxHealth,
    totalDamage,
    experience,
    experienceToNextLevel,
    bonusHealth,
    bonusDamage,
  };
}

/** Update a vertical health bar element to reflect current/max health. */
export function syncVerticalHealthBar(player, container = document, barId = 'player-health-bar') {
  if (!player) return;
  const stats = getPlayerStatValues(player);
  const bar = container.getElementById ? container.getElementById(barId) : container.querySelector(`#${barId}`);
  if (!bar) return;

  const currentHealth = Math.max(0, Number(player.health) || 0);
  const maxHealth = Math.max(1, Number(stats.maxHealth) || 1);
  const fillRatio = Math.max(0, Math.min(1, currentHealth / maxHealth));
  const fill = bar.querySelector('.vertical-health-bar-fill');
  if (fill) fill.style.height = `${fillRatio * 100}%`;
  bar.dataset.health = String(currentHealth);
  bar.dataset.maxHealth = String(maxHealth);
}

/** Update a vertical XP bar element to reflect current/max experience. */
export function syncVerticalXpBar(player, container = document, barId = 'player-xp-bar') {
  if (!player) return;
  const stats = getPlayerStatValues(player);
  const bar = container.getElementById ? container.getElementById(barId) : container.querySelector(`#${barId}`);
  if (!bar) return;

  const currentExperience = Math.max(0, Number(player.experience) || 0);
  const maxExperience = Math.max(1, Number(stats.experienceToNextLevel) || 1);
  const fillRatio = Math.max(0, Math.min(1, currentExperience / maxExperience));
  const fill = bar.querySelector('.vertical-health-bar-fill');
  if (fill) fill.style.height = `${fillRatio * 100}%`;
  bar.dataset.health = String(currentExperience);
  bar.dataset.maxHealth = String(maxExperience);
}

/**
 * Update the visible player stat nodes in place.
 * Shared by the dungeon HUD and the home screen.
 */
export function syncPlayerStatsInDom(player, container = document) {
  if (!player) return;
  const stats = getPlayerStatValues(player);
  const ph = container.getElementById ? container.getElementById('player-health') : container.querySelector('#player-health');
  const pd = container.getElementById ? container.getElementById('player-damage') : container.querySelector('#player-damage');
  const pl = container.getElementById ? container.getElementById('player-level') : container.querySelector('#player-level');
  const pxp = container.getElementById ? container.getElementById('player-xp') : container.querySelector('#player-xp');
  const pbh = container.getElementById ? container.getElementById('player-bonus-health') : container.querySelector('#player-bonus-health');
  const pbd = container.getElementById ? container.getElementById('player-bonus-damage') : container.querySelector('#player-bonus-damage');
  if (ph) ph.textContent = `${player.health}/${stats.maxHealth}`;
  if (pd) pd.textContent = `${stats.totalDamage}`;
  if (pl) pl.textContent = `${stats.level}`;
  if (pxp) pxp.textContent = `${stats.experience} / ${stats.experienceToNextLevel}`;
  if (pbh) pbh.textContent = `+${stats.bonusHealth}`;
  if (pbd) pbd.textContent = `+${stats.bonusDamage}`;
  syncVerticalHealthBar(player, container);
  syncVerticalXpBar(player, container);
}

/** Render the current player stats into the provided container. */
export function renderPlayerStatsInto(container, player) {
  if (!container) return;
  if (!player) {
    container.innerHTML = `<div class="player-stats"><p class="player-data-unavailable">Player data unavailable</p></div>`;
    return;
  }

  const stats = getPlayerStatValues(player);

  container.innerHTML = `
    <div class="dungeon-player-panel">
      <div class="vertical-health-bar" id="player-health-bar" aria-hidden="true"><div class="vertical-health-bar-fill"></div></div>
      <div class="player-stats">
        <h2>${escapeHtml(player.name)}</h2>
        <div class="player-stat-grid">
          <div class="player-stat-row">
            <div class="stat">
              <span class="stat-label">Level:</span>
              <span id="player-level" class="stat-value">${stats.level}</span>
            </div>
            <div class="stat">
              <span class="stat-label">XP:</span>
              <span id="player-xp" class="stat-value">${stats.experience} / ${stats.experienceToNextLevel}</span>
            </div>
          </div>
          <div class="player-stat-row">
            <div class="stat">
              <span class="stat-label">Health:</span>
              <span id="player-health" class="stat-value">${player.health}/${stats.maxHealth}</span>
            </div>
            <div class="stat">
              <span class="stat-label">+HP:</span>
              <span id="player-bonus-health" class="stat-value">${stats.bonusHealth}</span>
            </div>
          </div>
          <div class="player-stat-row">
            <div class="stat">
              <span class="stat-label">Damage:</span>
              <span id="player-damage" class="stat-value">${stats.totalDamage}</span>
            </div>
            <div class="stat">
              <span class="stat-label">+ATK:</span>
              <span id="player-bonus-damage" class="stat-value">${stats.bonusDamage}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="vertical-health-bar vertical-xp-bar" id="player-xp-bar" aria-hidden="true"><div class="vertical-health-bar-fill"></div></div>
    </div>`;

  syncVerticalHealthBar(player, container);
  syncVerticalXpBar(player, container);
}
