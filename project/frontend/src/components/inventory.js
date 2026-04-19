import { bindDragSource, bindDropZone } from '../drag-drop.js';

export function renderInventoryGrid(opts) {
  const { inventory, getCharacterId, getCurrentDrag, setCurrentDrag, updateSlotHighlights, fetchJson, loadStateAndRenderPartial, getItemType, makeIcon, formatStats, getItemDisplayName } = opts;
  const invContainer = document.getElementById('inventory-grid');
  if (!invContainer) return;
  if (!inventory || inventory.length === 0) {
    invContainer.innerHTML = '<p style="color:#999;font-style:italic">Your inventory is empty</p>';
    return;
  }

  // Keep the strongest upgraded items near the top so equip scans are easier to follow.
  const sortedInventory = [...inventory].filter(Boolean).sort((a, b) => {
    const la = a.level || 1;
    const lb = b.level || 1;
    if (la !== lb) return lb - la;
    return (getItemDisplayName(a) || '').localeCompare(getItemDisplayName(b) || '');
  });

  const cards = [];
  sortedInventory.forEach(invItem => {
    const i = invItem;
    const itype = getItemType(i);
    const instanceId = `card-${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
    cards.push(`
      <div class="inventory-card" draggable="true" data-instance-id="${instanceId}" data-item-id="${i.id}" data-item-type="${itype}">
        <div class="item-icon">${makeIcon(i)}</div>
        <div class="card-details">
          <div class="item-name">${getItemDisplayName(i)}</div>
          <div class="item-type">${formatStats(i)}</div>
        </div>
      </div>`);
  });
  invContainer.innerHTML = cards.join('');

  document.querySelectorAll('.inventory-card').forEach(card => {
    bindDragSource(card, {
      createPayload: () => {
      const id = card.getAttribute('data-item-id');
      const type = card.getAttribute('data-item-type');
      const instance = card.getAttribute('data-instance-id');
        return { itemId: Number(id), itemType: type, from: 'inventory', instance };
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
  });

  if (!invContainer.dataset.dndBound) {
    bindDropZone(invContainer, {
      onDrop: async ev => {
      const raw = ev.dataTransfer.getData('text/plain');
      if (!raw) return;
      const payload = JSON.parse(raw);
      if (!payload) return;
      const characterId = getCharacterId ? getCharacterId() : null;
      const inventoryPath = characterId ? `/characters/${characterId}/inventory/` : null;
      if (payload.from === 'equipped' && inventoryPath) {
        const itemId = Number(payload.itemId);
        await fetchJson(inventoryPath, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item_id: itemId, is_equipped: false }) });
        await loadStateAndRenderPartial();
      }
      setCurrentDrag(null);
      updateSlotHighlights();
      }
    });
    invContainer.dataset.dndBound = '1';
  }
}
