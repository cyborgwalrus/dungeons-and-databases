export function renderInventoryGrid(opts) {
  const { inventory, reforgeState, getCurrentDrag, setCurrentDrag, updateSlotHighlights, fetchJson, loadStateAndRenderPartial, getItemType, makeIcon, formatStats } = opts;
  const invContainer = document.getElementById('inventory-grid');
  if (!invContainer) return;
  if (!inventory || inventory.length === 0) {
    invContainer.innerHTML = '<p style="color:#999;font-style:italic">Your inventory is empty</p>';
    return;
  }

  const sortedInventory = [...inventory].sort((a, b) => {
    function levelOf(inv) {
      const name = (inv.item && inv.item.name) ? inv.item.name : '';
      const m = name.match(/\s\+(\d+)$/);
      return m ? parseInt(m[1], 10) : 0;
    }
    const la = levelOf(a), lb = levelOf(b);
    if (la !== lb) return lb - la;
    return (a.item.name || '').localeCompare(b.item.name);
  });

  const cards = [];
  sortedInventory.forEach(invItem => {
    const i = invItem.item;
    const itype = getItemType(i);
    const qty = Math.max(1, invItem.quantity || 1);
    for (let q = 0; q < qty; q++) {
      const instanceId = `card-${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
      cards.push(`
        <div class="inventory-card" draggable="true" data-instance-id="${instanceId}" data-item-id="${i.id}" data-item-type="${itype}">
          <div class="item-icon">${makeIcon(i)}</div>
          <div class="card-details">
            <div class="item-name">${i.name}</div>
            <div class="item-type">${formatStats(i)}</div>
          </div>
        </div>`);
    }
  });
  invContainer.innerHTML = cards.join('');

  if (reforgeState && reforgeState.baseId && reforgeState.count > 0) {
    const matchEls = invContainer.querySelectorAll(`.inventory-card[data-item-id="${reforgeState.baseId}"]`);
    for (let i = 0; i < Math.min(matchEls.length, reforgeState.count); i++) {
      const el = matchEls[i];
      el.classList.add('in-reforge');
      el.setAttribute('draggable', 'false');
    }
  }

  document.querySelectorAll('.inventory-card').forEach(card => {
    card.addEventListener('dragstart', ev => {
      const id = card.getAttribute('data-item-id');
      const type = card.getAttribute('data-item-type');
      const instance = card.getAttribute('data-instance-id');
      setCurrentDrag({ itemId: Number(id), itemType: type, from: 'inventory', instance });
      updateSlotHighlights();
      ev.dataTransfer.setData('text/plain', JSON.stringify({ itemId: id, from: 'inventory', instance }));
    });
    card.addEventListener('dragend', () => { setCurrentDrag(null); updateSlotHighlights(); });
  });

  if (!invContainer.dataset.dndBound) {
    invContainer.addEventListener('dragover', ev => { ev.preventDefault(); invContainer.classList.add('drag-over'); });
    invContainer.addEventListener('dragleave', () => invContainer.classList.remove('drag-over'));
    invContainer.addEventListener('drop', async ev => {
      ev.preventDefault(); invContainer.classList.remove('drag-over');
      const raw = ev.dataTransfer.getData('text/plain');
      if (!raw) return;
      const payload = JSON.parse(raw);
      if (!payload) return;
      if (payload.from === 'equipped') {
        const slot = payload.slot !== undefined ? payload.slot : (getCurrentDrag && getCurrentDrag().slot !== undefined ? getCurrentDrag().slot : null);
        if (slot !== null) {
          await fetchJson(`/inventory/unequip/${slot}`, { method: 'DELETE' });
          await loadStateAndRenderPartial();
        }
      }
      setCurrentDrag(null);
      updateSlotHighlights();
    });
    invContainer.dataset.dndBound = '1';
  }
}
