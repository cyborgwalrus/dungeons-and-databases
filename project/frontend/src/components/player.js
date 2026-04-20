export function renderPlayerStatsInto(container, player) {
  if (!container) return;
  if (!player) {
    container.innerHTML = `<div class="player-stats"><p style="color:#999">Player data unavailable</p></div>`;
    return;
  }

  const level = player.level || 1;
  const maxHealth = (100 + (Math.max(0, level - 1) * 10)) + (player.bonus_health || 0);
  const totalDamage = (player.damage || 0) + (player.bonus_damage || 0);

  container.innerHTML = `
    <div class="player-stats">
      <h2>${player.name}</h2>
      <div class="player-stat-lines">
        <div class="stat"><span class="stat-label">Health:</span><span id="player-health" class="stat-value">${player.health} / ${maxHealth} HP</span></div>
        <div class="stat"><span class="stat-label">Damage:</span><span id="player-damage" class="stat-value">${totalDamage}</span></div>
        <div class="stat"><span class="stat-label">Level:</span><span id="player-level" class="stat-value">${player.level}</span></div>
        <div class="stat" style="color:#4ecdc4"><span class="stat-label">+Health Bonus:</span><span id="player-bonus-health" class="stat-value">${player.bonus_health || 0}</span></div>
        <div class="stat" style="color:#4ecdc4"><span class="stat-label">+Attack Bonus:</span><span id="player-bonus-damage" class="stat-value">${player.bonus_damage || 0}</span></div>
      </div>
    </div>`;
}
