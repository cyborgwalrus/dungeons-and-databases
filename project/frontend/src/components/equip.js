import { equipInventoryItem, getItemDragData, setItemDragData, unequipInventoryItem } from './item-actions.js';

/** Render the equipped-item panel and attach drag/drop handlers. */
export async function renderEquipPanel(opts) {
  const { equipped, fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull, makeIcon, formatStats, getItemDisplayName } = opts;
  const equipPanel = document.getElementById('equip-panel');
  if (!equipPanel) return;

  function inventoryCardHtml(i) {
    return `
      <button type="button" draggable="true" class="inventory-card equipped-card" data-item-id="${i.id}" data-item-source="equipped">
        <div class="item-icon">${makeIcon(i)}</div>
        <div class="card-details">
          <div class="item-name">${getItemDisplayName(i)}</div>
          <div class="item-type">${formatStats(i)}</div>
        </div>
      </button>`;
  }

  const SLOT_DEFS = [
    { type: 'helmet', label: 'Helmet' }, { type: 'armor', label: 'Armor' },
    { type: 'weapon', label: 'Weapon' }, { type: 'shield', label: 'Shield' },
    { type: 'ring', label: 'Ring' }, { type: 'necklace', label: 'Necklace' },
  ];

  const slotsHtml = SLOT_DEFS.map((slotDef, slotNum) => {
    const eq = (equipped || []).find(e => e.slot === slotDef.type);
    if (eq) {
      return `
        <div class="equip-slot" data-slot="${slotNum}" data-slot-type="${slotDef.type}">
          <span class="slot-label">${slotDef.label}</span>
          ${inventoryCardHtml(eq)}
        </div>`;
    }
    return `<div class="equip-slot empty" data-slot="${slotNum}" data-slot-type="${slotDef.type}"><span class="slot-label">${slotDef.label}</span><div class="empty-label">Empty</div></div>`;
  }).join('');

  equipPanel.innerHTML = `
    <div style="background:rgba(0,0,0,0.3);border:2px solid #4ecdc4;border-radius:10px;padding:0;margin-bottom:8px">
      <div style="margin:0">
        <div id="slots-grid" style="display:grid;grid-template-columns:repeat(2,1fr);gap:0;border-radius:10px;overflow:hidden">${slotsHtml}</div>
      </div>
    </div>`;

  document.querySelectorAll('.equip-slot').forEach(slotEl => {
    slotEl.ondragover = event => {
      const payload = getItemDragData(event);
      if (!payload || payload.source !== 'inventory') return;
      event.preventDefault();
      slotEl.classList.add('equip-slot--drop-active');
      if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
    };

    slotEl.ondragleave = () => {
      slotEl.classList.remove('equip-slot--drop-active');
    };

    slotEl.ondrop = async event => {
      slotEl.classList.remove('equip-slot--drop-active');
      const payload = getItemDragData(event);
      if (!payload || payload.source !== 'inventory') return;
      event.preventDefault();
      try {
        await equipInventoryItem({ fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull }, payload.itemId);
      } catch (error) {
        console.error('Failed to equip item from drag and drop', error);
      }
    };

    const equippedCard = slotEl.querySelector('.equipped-card');
    if (equippedCard) {
      equippedCard.addEventListener('dragstart', event => {
        setItemDragData(event, {
          itemId: Number(equippedCard.getAttribute('data-item-id')),
          source: equippedCard.getAttribute('data-item-source') || 'equipped',
        });
        equippedCard.classList.add('dragging');
      });

      equippedCard.addEventListener('dragend', () => {
        equippedCard.classList.remove('dragging');
      });

      equippedCard.addEventListener('dblclick', async event => {
        event.preventDefault();
        event.stopPropagation();
        const itemId = equippedCard.getAttribute('data-item-id');
        try {
          await unequipInventoryItem({ fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull }, itemId);
        } catch (error) {
          console.error('Failed to unequip item from double click', error);
        }
      });
    }
  });
}
