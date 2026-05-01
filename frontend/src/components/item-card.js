import { escapeHtml } from '../helpers.js';

/**
 * Render a reusable inventory/equipment item card.
 * Keeps the markup consistent across inventory and equipped slots.
 */
export function renderItemCardHtml(item, { className = '', source = 'inventory', icon = '', name = '', stats = '', better = false } = {}) {
  const classes = ['inventory-card', className, better ? 'inventory-card--better' : ''].filter(Boolean).join(' ');
  const equipHref = item?._links?.equip?.href || '';
  const unequipHref = item?._links?.unequip?.href || '';
  return `
    <button type="button" draggable="true" class="${classes}" data-item-id="${item.id}" data-item-source="${escapeHtml(source)}" data-item-slot-type="${escapeHtml(item?.slot_type || '')}" data-item-equip-href="${escapeHtml(equipHref)}" data-item-unequip-href="${escapeHtml(unequipHref)}">
      <div class="item-icon">${icon}</div>
      <div class="card-details">
        <div class="item-name">${escapeHtml(name)}</div>
        <div class="item-type${better ? ' item-type--better' : ''}">${escapeHtml(stats)}</div>
      </div>
    </button>`;
}