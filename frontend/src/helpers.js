/**
 * Pick a display icon for an item based on slot, name, or stats.
 *
 * @param {Object} item - Item data from the API.
 * @returns {string} Emoji icon representing the item.
 */
export function makeIcon(i) {
  const slot = (i.slot || '').toLowerCase();
  if (slot === 'helmet') return '🪖';
  if (slot === 'armor') return '👕';
  if (slot === 'weapon') return '🗡️';
  if (slot === 'shield') return '🛡️';
  if (slot === 'ring') return '💍';
  if (slot === 'necklace') return '📿';

  return '💰';
}

/**
 * Infer the item category from its slot, name, or stat profile.
 *
 * @param {Object} item - Item data from the API.
 * @returns {string} Canonical item type string.
 */
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

/**
 * Format an item name with its level suffix when needed.
 *
 * @param {Object} item - Item data from the API.
 * @returns {string} Display name for the item.
 */
export function getItemDisplayName(item) {
  if (!item) return '';
  const name = String(item.name || 'Item').replace(/\s+\+\d+$/, '').trim() || 'Item';
  const level = item.level || 1;
  return level > 1 ? `${name} +${level}` : name;
}

/**
 * Convert loot counts into short human-readable summary lines.
 *
 * @param {Object<string, number>} lootCounts - Loot summary keyed by item name.
 * @returns {string[]} Human-readable loot summary lines.
 */
export function formatLootLines(lootCounts) {
  return Object.keys(lootCounts || {}).map(name => `${name}${lootCounts[name] > 1 ? ' x' + lootCounts[name] : ''}`);
}

/**
 * Escape text so it can be inserted into HTML safely.
 *
 * @param {*} value - Any value that should be rendered as text.
 * @returns {string} Escaped HTML string.
 */
export function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

/**
 * Render a combat log message into the styled dungeon message markup.
 *
 * @param {string} message - Raw combat log text from the API.
 * @returns {string} HTML markup for the formatted combat message.
 */
export function formatDungeonMessage(message) {
  const lines = String(message ?? '')
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean);

  const hasVictory = lines.some(line => /^Victory!?$/i.test(line));
  const hasSneak = lines.some(line => /^Sneaking!?$/i.test(line));
  const hasDefeat = lines.some(line => /defeated/i.test(line));
  const runSuccessLine = lines.find(line => /^You rolled a \d+! You successfully escaped and returned home!?$/i.test(line));
  const runFailLine = lines.find(line => /^You rolled a \d+ and failed to escape!?$/i.test(line));
  const hasRun = Boolean(runSuccessLine || runFailLine || lines.some(line => /escape/i.test(line)));
  const statusText = hasVictory ? 'Victory!' : (hasSneak ? 'Sneaking!' : (hasDefeat ? 'Defeat!' : (hasRun ? 'Run for your life!' : 'Fight!')));
  const statusClass = hasVictory ? 'dungeon-message-victory-text' : (hasSneak ? 'dungeon-message-sneak-text' : (hasDefeat ? 'dungeon-message-defeat-text' : (hasRun ? 'dungeon-message-run-text' : 'dungeon-message-fight-text')));

  let bodyLines = lines.filter(line => !/^Victory!?$/i.test(line) && !/^Sneaking!?$/i.test(line) && !/^Fight!?$/i.test(line) && !/^Defeat!?$/i.test(line) && !/^Run for your life!?$/i.test(line));
  if (runSuccessLine) {
    const rollMatch = runSuccessLine.match(/^You rolled a (\d+)! You successfully escaped and returned home!?$/i);
    bodyLines = [
      `You rolled a ${rollMatch ? rollMatch[1] : ''}!`,
      'You successfully escaped and returned home!',
    ];
  } else if (runFailLine) {
    const rollMatch = runFailLine.match(/^You rolled a (\d+) and failed to escape!?$/i);
    bodyLines = [
      `You rolled a ${rollMatch ? rollMatch[1] : ''}!`,
      'You failed to escape!',
    ];
  }

  const body = bodyLines.map(line => {
    const safeLine = escapeHtml(line);
    if (/leveled up/i.test(line)) {
      return `<div class="dungeon-message-line dungeon-message-levelup">${safeLine}</div>`;
    }
    if (/^You go deeper past the defeated/i.test(line)) {
      return `<div class="dungeon-message-line dungeon-message-sneak">${safeLine}</div>`;
    }
    if (/^You\s*:/.test(line) || /^You dealt/i.test(line)) {
      return `<div class="dungeon-message-line dungeon-message-player">${safeLine.replace(/^You\s*:/i, 'You')}</div>`;
    }
    if (/^You successfully escaped and returned home!?$/i.test(line)) {
      return `<div class="dungeon-message-line dungeon-message-run-success">${safeLine}</div>`;
    }
    if (/^You failed to escape!?$/i.test(line)) {
      return `<div class="dungeon-message-line dungeon-message-defeat">${safeLine}</div>`;
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

/**
 * Format a concise stat summary for inventory and equipment items.
 *
 * @param {Object} item - Item data from the API.
 * @returns {string} Short stat summary string.
 */
export function formatStats(i) {
  if (!i) return '';
  const ha = i.health ?? 0;
  const aa = i.damage ?? 0;
  if (ha > 0 && aa === 0) return `${ha} HP`;
  if (aa > 0 && ha === 0) return `${aa} ATK`;
  return `${ha} HP ${aa} ATK`;
}
