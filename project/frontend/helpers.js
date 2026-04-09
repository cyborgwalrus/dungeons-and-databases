export function makeIcon(i) {
  const name = (i.name || '').toLowerCase();
  if (name.includes('helmet') || name.includes('helm') || name.includes('cap')) return '🪖';
  if (name.includes('ring')) return '💍';
  if (name.includes('necklace') || name.includes('amulet')) return '📿';
  if (name.includes('shield')) return '🛡️';
  if (i.bonus_attack > 0 && i.bonus_health === 0) return '⚔️';
  if (i.bonus_health > 0 && i.bonus_attack === 0) return '👕';
  if (i.bonus_health > 0 && i.bonus_attack > 0) return '💎';
  return '💰';
}

export function getItemType(i) {
  const name = (i.name || '').toLowerCase();
  if (name.includes('shield')) return 'shield';
  if (name.includes('helmet') || name.includes('helm') || name.includes('cap')) return 'helmet';
  if (name.includes('necklace') || name.includes('amulet')) return 'necklace';
  if (name.includes('ring')) return 'ring';
  if (i.bonus_attack > 0 && i.bonus_health === 0) return 'weapon';
  if (i.bonus_health > 0 && i.bonus_attack === 0) return 'armor';
  return 'misc';
}

export function formatStats(i) {
  if (!i) return '';
  const ha = i.bonus_health || 0;
  const aa = i.bonus_attack || 0;
  if (ha > 0 && aa === 0) return `${ha} HP`;
  if (aa > 0 && ha === 0) return `${aa} ATK`;
  return `+${ha} HP / +${aa} ATK`;
}
