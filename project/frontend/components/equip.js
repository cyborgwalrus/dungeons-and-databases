import { isSlotCompatible } from '../helpers.js';
import { bindDragSource, bindDropZone } from '../drag-drop.js';

export async function renderEquipPanel(opts) {
  const { equipped, inventory, allItems, getCurrentDrag, setCurrentDrag, updateSlotHighlights, fetchJson, loadStateAndRenderPartial, getItemType, makeIcon, formatStats } = opts;
  const equipPanel = document.getElementById('equip-panel');
  if (!equipPanel) return;

  function inventoryCardHtml(i) {
    return `
      <div class="inventory-card equipped-card" draggable="false" data-item-id="${i.id}">
        <div class="item-icon">${makeIcon(i)}</div>
        <div class="card-details">
          <div class="item-name">${i.name}</div>
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
    const eq = (equipped || []).find(e => e.slot === slotNum);
    if (eq) {
      return `
        <div class="equip-slot" data-slot="${slotNum}" data-slot-type="${slotDef.type}" draggable="true" data-from="equipped" data-item-id="${eq.item.id}" data-slot-index="${slotNum}">
          <span class="slot-label">${slotDef.label}</span>
          ${inventoryCardHtml(eq.item)}
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
    bindDragSource(slotEl, {
      createPayload: () => {
      const itemId = slotEl.getAttribute('data-item-id');
      const slotIndex = slotEl.getAttribute('data-slot-index');
      const item = (allItems || []).find(a => a.item && a.item.id == itemId) || (inventory || []).find(i => i.item && i.item.id == itemId) || {};
      const itemObj = item.item || null;
      const itemType = itemObj ? getItemType(itemObj) : null;
        return { itemId: itemId ? Number(itemId) : null, itemType, from: 'equipped', slot: slotIndex };
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
        const slot = Number(slotEl.getAttribute('data-slot'));
        const slotType = slotEl.getAttribute('data-slot-type') || 'misc';
        const itemId = Number(payload.itemId);

        const itemObj = ((allItems || []).find(a => a.item && a.item.id === itemId) || {}).item || ((inventory || []).find(i => i.item && i.item.id === itemId) || {}).item;
        const itemType = itemObj ? getItemType(itemObj) : 'misc';
        if (!isSlotCompatible(slotType, itemType)) return;

        await fetchJson('/inventory/equip', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item_id: itemId, slot }) });
        await loadStateAndRenderPartial();
        setCurrentDrag(null);
        updateSlotHighlights();
      }
    });
  });
}
