/** Pick a display icon for an item based on slot, name, or stats. */
export function makeIcon(i) {
  const slot = (i.slot || '').toLowerCase();
  if (slot === 'helmet') return '🪖';
  if (slot === 'armor') return '👕';
  if (slot === 'weapon') return '⚔️';
  if (slot === 'shield') return '🛡️';
  if (slot === 'ring') return '💍';
  if (slot === 'necklace') return '📿';

  const name = (i.name || '').toLowerCase();
  if (name.includes('helmet') || name.includes('helm') || name.includes('cap')) return '🪖';
  if (name.includes('ring')) return '💍';
  if (name.includes('necklace') || name.includes('amulet')) return '📿';
  if (name.includes('shield')) return '🛡️';
  const attack = i.damage ?? 0;
  const health = i.health ?? 0;
  if (attack > 0 && health === 0) return '⚔️';
  if (health > 0 && attack === 0) return '👕';
  if (health > 0 && attack > 0) return '💎';
  return '💰';
}

/** Infer the item category from its slot, name, or stat profile. */
export function getItemType(i) {
  const slot = (i.slot || '').toLowerCase();
  if (slot === 'shield') return 'shield';
  if (slot === 'helmet') return 'helmet';
  if (slot === 'necklace') return 'necklace';
  if (slot === 'ring') return 'ring';
  if (slot === 'weapon') return 'weapon';
  if (slot === 'armor') return 'armor';

  const name = (i.name || '').toLowerCase();
  if (name.includes('shield')) return 'shield';
  if (name.includes('helmet') || name.includes('helm') || name.includes('cap')) return 'helmet';
  if (name.includes('necklace') || name.includes('amulet')) return 'necklace';
  if (name.includes('ring')) return 'ring';
  const attack = i.damage ?? 0;
  const health = i.health ?? 0;
  if (attack > 0 && health === 0) return 'weapon';
  if (health > 0 && attack === 0) return 'armor';
  return 'misc';
}

/** Format an item name with its level suffix when needed. */
export function getItemDisplayName(item) {
  if (!item) return '';
  const name = String(item.name || 'Item').replace(/\s+\+\d+$/, '').trim() || 'Item';
  const level = item.level || 1;
  return level > 1 ? `${name} +${level}` : name;
}

/** Convert loot counts into short human-readable summary lines. */
export function formatLootLines(lootCounts) {
  return Object.keys(lootCounts || {}).map(name => `${name}${lootCounts[name] > 1 ? ' x' + lootCounts[name] : ''}`);
}

/** Escape text so it can be inserted into HTML safely. */
export function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

/** Render a combat log message into the styled dungeon message markup. */
export function formatDungeonMessage(message) {
  const lines = String(message ?? '')
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean);

  const hasVictory = lines.some(line => /^Victory!?$/i.test(line));
  const hasDefeat = lines.some(line => /defeated/i.test(line));
  const statusText = hasVictory ? 'Victory!' : (hasDefeat ? 'Defeat!' : 'Fight!');
  const statusClass = hasVictory ? 'dungeon-message-victory-text' : (hasDefeat ? 'dungeon-message-defeat-text' : 'dungeon-message-fight-text');

  const body = lines.filter(line => !/^Victory!?$/i.test(line) && !/^Fight!?$/i.test(line) && !/^Defeat!?$/i.test(line)).map(line => {
    const safeLine = escapeHtml(line);
    if (/leveled up/i.test(line)) {
      return `<div class="dungeon-message-line dungeon-message-levelup">${safeLine}</div>`;
    }
    if (/^You\s*:/.test(line) || /^You dealt/i.test(line)) {
      return `<div class="dungeon-message-line dungeon-message-player">${safeLine.replace(/^You\s*:/i, 'You')}</div>`;
    }
    if (/^[^:]+:\s*dealt/i.test(line)) {
      return `<div class="dungeon-message-line dungeon-message-enemy">${safeLine.replace(/^([^:]+):\s*/i, '$1 ')}</div>`;
    }
    if (/defeated/i.test(line)) {
      return `<div class="dungeon-message-line dungeon-message-defeat">${safeLine}</div>`;
    }
    return `<div class="dungeon-message-line">${safeLine}</div>`;
  }).join('');

  return `
    <div class="dungeon-message-frame">
      <div class="dungeon-message-status ${statusClass}">${escapeHtml(statusText)}</div>
      <div class="dungeon-message-body">${body || '<div class="dungeon-message-line">&nbsp;</div>'}</div>
    </div>
  `;
}

/** Format a concise stat summary for inventory and equipment items. */
export function formatStats(i) {
  if (!i) return '';
  const ha = i.health ?? 0;
  const aa = i.damage ?? 0;
  if (ha > 0 && aa === 0) return `${ha} HP`;
  if (aa > 0 && ha === 0) return `${aa} ATK`;
  return `+${ha} HP / +${aa} ATK`;
}
