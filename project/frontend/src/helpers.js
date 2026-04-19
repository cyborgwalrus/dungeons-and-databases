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
  const attack = i.damage_bonus ?? i.bonus_attack ?? 0;
  const health = i.health_bonus ?? i.bonus_health ?? 0;
  if (attack > 0 && health === 0) return '⚔️';
  if (health > 0 && attack === 0) return '👕';
  if (health > 0 && attack > 0) return '💎';
  return '💰';
}

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
  const attack = i.damage_bonus ?? i.bonus_attack ?? 0;
  const health = i.health_bonus ?? i.bonus_health ?? 0;
  if (attack > 0 && health === 0) return 'weapon';
  if (health > 0 && attack === 0) return 'armor';
  return 'misc';
}

export function isSlotCompatible(slotType, itemType) {
  const normalizedSlotType = slotType || 'misc';
  const normalizedItemType = itemType || 'misc';
  return normalizedSlotType === 'misc'
    ? !['weapon', 'armor', 'shield'].includes(normalizedItemType)
    : normalizedSlotType === normalizedItemType;
}

export function getEquipScore(item, slotType) {
  if (!item) return -Infinity;
  const attack = item.damage_bonus ?? item.bonus_attack ?? 0;
  const health = item.health_bonus ?? item.bonus_health ?? 0;
  return slotType === 'weapon' ? (attack * 10 + health) : (health * 10 + attack);
}

export function getItemDisplayName(item) {
  if (!item) return '';
  const name = String(item.name || 'Item').replace(/\s+\+\d+$/, '').trim() || 'Item';
  const level = item.level || 1;
  return level > 1 ? `${name} +${level}` : name;
}

export function formatLootLines(lootCounts) {
  return Object.keys(lootCounts || {}).map(name => `${name}${lootCounts[name] > 1 ? ' x' + lootCounts[name] : ''}`);
}

export function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

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

export function formatStats(i) {
  if (!i) return '';
  const ha = i.health_bonus ?? i.bonus_health ?? 0;
  const aa = i.damage_bonus ?? i.bonus_attack ?? 0;
  if (ha > 0 && aa === 0) return `${ha} HP`;
  if (aa > 0 && ha === 0) return `${aa} ATK`;
  return `+${ha} HP / +${aa} ATK`;
}
