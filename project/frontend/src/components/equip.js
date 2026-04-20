import { isSlotCompatible } from '../helpers.js';
import { bindDragSource, bindDropZone } from '../drag-drop.js';

async function unequipItemFromDoubleClick(opts, itemId) {
  const { fetchJson, inventoryPath, loadStateAndRenderPartial, syncPlayerHealthToFull, setCurrentDrag, updateSlotHighlights } = opts;
  if (!inventoryPath || !itemId) return;

  await fetchJson(inventoryPath, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_id: Number(itemId), is_equipped: false })
  });

  await loadStateAndRenderPartial();
  if (syncPlayerHealthToFull) await syncPlayerHealthToFull();
  setCurrentDrag(null);
  updateSlotHighlights();
}

export async function renderEquipPanel(opts) {
  const { equipped, inventory, allItems, getCharacterId, getCurrentDrag, setCurrentDrag, updateSlotHighlights, fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull, getItemType, makeIcon, formatStats, getItemDisplayName } = opts;
  const equipPanel = document.getElementById('equip-panel');
  if (!equipPanel) return;

  const characterId = getCharacterId ? getCharacterId() : null;
  const inventoryPath = characterId ? `/characters/${characterId}/inventory/` : null;

  function inventoryCardHtml(i) {
    return `
      <div class="inventory-card equipped-card" draggable="false" data-item-id="${i.id}">
        <div class="item-icon">${makeIcon(i)}</div>
        <div class="card-details">
          <div class="item-name">${getItemDisplayName(i)}</div>
          <div class="item-type">${formatStats(i)}</div>
        </div>
      </div>`;
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
        <div class="equip-slot" data-slot="${slotNum}" data-slot-type="${slotDef.type}" draggable="true" data-from="equipped" data-item-id="${eq.id}" data-slot-index="${slotNum}">
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
    const equippedCard = slotEl.querySelector('.equipped-card');
    if (equippedCard) {
      equippedCard.addEventListener('dblclick', async event => {
        event.preventDefault();
        event.stopPropagation();
        const itemId = equippedCard.getAttribute('data-item-id');
        try {
          await unequipItemFromDoubleClick({ fetchJson, inventoryPath, loadStateAndRenderPartial, syncPlayerHealthToFull, setCurrentDrag, updateSlotHighlights }, itemId);
        } catch (error) {
          console.error('Failed to unequip item from double click', error);
        }
      });
    }

    bindDragSource(slotEl, {
      createPayload: () => {
      const itemId = slotEl.getAttribute('data-item-id');
      const slotIndex = slotEl.getAttribute('data-slot-index');
      const itemObj = (allItems || []).find(a => a.id == itemId) || (inventory || []).find(i => i.id == itemId) || null;
      const itemType = itemObj ? getItemType(itemObj) : null;
        return { itemId: itemId ? Number(itemId) : null, itemType, from: 'equipped', slot: slotIndex ? Number(slotIndex) : null, source_slot: slotIndex ? Number(slotIndex) : null };
      },
      onDragStart: (ev, payload) => {
        setCurrentDrag(payload);
        updateSlotHighlights();
      },
      onDragEnd: () => {
        setCurrentDrag(null);
        updateSlotHighlights();
      }
    });

    bindDropZone(slotEl, {
      onDrop: async ev => {
        slotEl.classList.remove('slot-allowed'); slotEl.classList.remove('slot-denied');
        const raw = ev.dataTransfer.getData('text/plain');
        const payload = raw ? JSON.parse(raw) : getCurrentDrag();
        if (!payload) return;
        const slotType = slotEl.getAttribute('data-slot-type') || 'misc';
        const itemId = Number(payload.itemId);

        const itemObj = (allItems || []).find(a => a.id === itemId) || (inventory || []).find(i => i.id === itemId) || null;
        const itemType = itemObj ? getItemType(itemObj) : 'misc';
        if (!isSlotCompatible(slotType, itemType)) return;

        if (!inventoryPath) return;

        const payloadBody = { item_id: itemId };
        if (payload.from === 'equipped') {
          payloadBody.is_equipped = true;
        }

        await fetchJson(inventoryPath, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payloadBody) });
        await loadStateAndRenderPartial();
        if (syncPlayerHealthToFull) await syncPlayerHealthToFull();
        setCurrentDrag(null);
        updateSlotHighlights();
      }
    });
  });
}
