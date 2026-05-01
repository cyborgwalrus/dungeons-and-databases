import { equipInventoryItem, getItemDragData, unequipInventoryItem } from './item-actions.js';
import { setupDragDropZone, setupDraggableItem } from '../utils/drag-drop.js';
import { renderItemCardHtml } from './item-card.js';

/**
 * Render the equipped-item panel and attach drag/drop handlers.
 * Uses standardized drag/drop utilities to reduce code duplication.
 */
export function renderEquipPanel(opts) {
  const { equipped, fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull, makeIcon, formatStats, getItemDisplayName } = opts;
  const equipPanel = document.getElementById('equip-panel');
  if (!equipPanel) return;

  const SLOT_DEFS = [
    { type: 'helmet', label: 'Helmet' }, { type: 'armor', label: 'Armor' },
    { type: 'weapon', label: 'Weapon' }, { type: 'shield', label: 'Shield' },
    { type: 'ring', label: 'Ring' }, { type: 'necklace', label: 'Necklace' },
  ];

  const slotsHtml = SLOT_DEFS.map((slotDef, slotNum) => {
    const eq = (equipped || []).find(e => e.slot_type === slotDef.type);
    if (eq) {
      return `
        <div class="equip-slot" data-slot="${slotNum}" data-slot-type="${slotDef.type}">
          ${renderItemCardHtml(eq, {
            className: 'equipped-card',
            source: 'equipped',
            icon: makeIcon(eq),
            name: getItemDisplayName(eq),
            stats: formatStats(eq),
          })}
        </div>`;
    }
    return `<div class="equip-slot empty" data-slot="${slotNum}" data-slot-type="${slotDef.type}"><span class="slot-label">${slotDef.label}</span><div class="empty-label">Empty</div></div>`;
  }).join('');

  equipPanel.innerHTML = `
    <div class="equipment-panel">
      <div class="equipment-panel-inner">
        <div id="slots-grid" class="slots-grid">${slotsHtml}</div>
      </div>
    </div>`;

  // Setup each equipment slot as a drop zone for inventory items
  document.querySelectorAll('.equip-slot').forEach(slotEl => {
    const slotType = slotEl.getAttribute('data-slot-type') || '';
    setupDragDropZone(slotEl, {
      isEligibleDrag: (event) => {
        const payload = getItemDragData(event);
        return Boolean(payload && payload.source === 'inventory');
      },
      validatePayload: (event) => {
        const payload = getItemDragData(event);
        if (!payload || payload.source !== 'inventory') return null;
        return payload.slot_type && payload.slot_type === slotType ? payload : null;
      },
      onDrop: async (payload) => {
        try {
          await equipInventoryItem({ fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull }, payload.itemId);
        } catch (error) {
          console.error('Failed to equip item from drag and drop', error);
        }
      },
      activeClass: 'equip-slot--drop-active',
      invalidClass: 'equip-slot--drop-invalid'
    });

    // Setup equipped item cards as draggable and unequippable
    const equippedCard = slotEl.querySelector('.equipped-card');
    if (equippedCard) {
      setupDraggableItem(equippedCard, {
        dragData: {
          itemId: Number(equippedCard.getAttribute('data-item-id')),
          source: equippedCard.getAttribute('data-item-source') || 'equipped',
          unequipHref: equippedCard.getAttribute('data-item-unequip-href') || '',
        }
      });

      equippedCard.addEventListener('dblclick', async event => {
        event.preventDefault();
        event.stopPropagation();
        const itemId = equippedCard.getAttribute('data-item-id');
        try {
          await unequipInventoryItem({ fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull }, {
            itemId,
            unequipHref: equippedCard.getAttribute('data-item-unequip-href') || '',
          });
        } catch (error) {
          console.error('Failed to unequip item from double click', error);
        }
      });
    }
  });

  // Show equipment slot glow whenever any item is being dragged
  document.addEventListener('dragstart', (event) => {
    const draggedElement = event.target;
    const cardElement = draggedElement.closest('.inventory-card') || draggedElement.closest('.equipped-card');
    if (!cardElement) return;

    const draggedSlotType = cardElement.getAttribute('data-item-slot-type') || '';
    document.querySelectorAll('.equip-slot').forEach(slot => {
      const slotType = slot.getAttribute('data-slot-type') || '';
      if (slotType === draggedSlotType) {
        slot.classList.add('equip-slot--item-dragging');
        slot.classList.remove('equip-slot--item-dragging-mismatch');
      } else {
        slot.classList.add('equip-slot--item-dragging-mismatch');
        slot.classList.remove('equip-slot--item-dragging');
      }
    });
  });

  document.addEventListener('dragend', () => {
    document.querySelectorAll('.equip-slot').forEach(slot => {
      slot.classList.remove('equip-slot--item-dragging');
      slot.classList.remove('equip-slot--item-dragging-mismatch');
    });
  });
}

