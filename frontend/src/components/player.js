import { escapeHtml } from '../helpers.js';

/** Render the current player stats into the provided container. */
export function renderPlayerStatsInto(container, player) {
  if (!container) return;
  if (!player) {
    container.innerHTML = `<div class="player-stats"><p class="player-data-unavailable">Player data unavailable</p></div>`;
    return;
  }

  const level = player.level || 1;
  const maxHealth = player.max_health ?? ((100 + (Math.max(0, level - 1) * 10)) + (player.bonus_health || 0));
  const totalDamage = (player.damage || 0) + (player.bonus_damage || 0);
  const experience = player.experience || 0;
  const experienceToNextLevel = player.experience_to_next_level || (100 + (Math.max(0, level - 1) * 50));

  container.innerHTML = `
    <div class="player-stats">
      <h2>${escapeHtml(player.name)}</h2>
      <div class="player-stat-lines">
        <div class="stat"><span class="stat-label">Health:</span><span id="player-health" class="stat-value">${player.health} / ${maxHealth} HP</span></div>
        <div class="stat"><span class="stat-label">Damage:</span><span id="player-damage" class="stat-value">${totalDamage}</span></div>
        <div class="stat"><span class="stat-label">Level:</span><span id="player-level" class="stat-value">${player.level}</span></div>
        <div class="stat"><span class="stat-label">XP:</span><span id="player-xp" class="stat-value">${experience} / ${experienceToNextLevel}</span></div>
        <div class="stat stat-bonus"><span class="stat-label">+Health Bonus:</span><span id="player-bonus-health" class="stat-value">${player.bonus_health || 0}</span></div>
        <div class="stat stat-bonus"><span class="stat-label">+Attack Bonus:</span><span id="player-bonus-damage" class="stat-value">${player.bonus_damage || 0}</span></div>
      </div>
    </div>`;
}
