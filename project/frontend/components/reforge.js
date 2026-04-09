export function initReforge(opts) {
  const { reforgeState, getAllItems, getInventory, fetchJson, loadStateAndRenderPartial, getCurrentDrag, setCurrentDrag, updateSlotHighlights } = opts;
  const reforgeEl = document.getElementById('reforge-area');
  if (!reforgeEl) return;

  function updateReforgeUI() {
    if (!reforgeEl) return;
    if (!reforgeState.baseId) {
      reforgeEl.innerHTML = `<div style="padding:8px;background:rgba(0,0,0,0.25);border:2px dashed rgba(160,160,160,0.12);border-radius:8px;display:flex;align-items:center;gap:10px;justify-content:center"><span class="reforge-icon">⚒</span><div>Drop 3 of the same item here to reforge into a +1 item</div></div>`;
    } else {
      const all = getAllItems() || [];
      const inv = getInventory() || [];
      const base = (all.find(a => a.item && a.item.id === reforgeState.baseId) || inv.find(i => i.item && i.item.id === reforgeState.baseId) || {});
      const name = (base.item && base.item.name) ? base.item.name : 'Item';
      reforgeEl.innerHTML = `<div style="padding:8px;background:rgba(0,0,0,0.25);border:2px dashed rgba(160,160,160,0.12);border-radius:8px;display:flex;align-items:center;justify-content:space-between;gap:8px">
          <div style="display:flex;align-items:center;gap:10px"><span class="reforge-icon">⚒</span><div>Reforge: <strong style="color:#ffd700">${name}</strong> x ${reforgeState.count}/3</div></div>
          <div style="display:flex;gap:8px"><button id="do-reforge" class="dungeon-button" style="padding:8px 14px" ${reforgeState.count < 3 ? 'disabled' : ''}>Reforge</button>
          <button id="clear-reforge" class="dungeon-button" style="background:#666;padding:8px 12px">Clear</button></div>
        </div>`;
      const btn = document.getElementById('do-reforge');
      if (btn) btn.addEventListener('click', async () => {
        if (!reforgeState.baseId) return;
        await fetchJson('/inventory/reforge', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item_id: reforgeState.baseId }) });
        reforgeState.baseId = null; reforgeState.count = 0; updateReforgeUI(); await loadStateAndRenderPartial();
      });

      const clr = document.getElementById('clear-reforge');
      if (clr) clr.addEventListener('click', () => {
        reforgeState.baseId = null; reforgeState.count = 0;
        document.querySelectorAll('.inventory-card.in-reforge').forEach(c => { c.classList.remove('in-reforge'); c.setAttribute('draggable', 'true'); });
        updateReforgeUI();
        if (typeof setCurrentDrag === 'function') setCurrentDrag(null);
        if (typeof updateSlotHighlights === 'function') updateSlotHighlights();
      });
    }
  }
  updateReforgeUI();

  // external Reforge All button is handled by the main action bar now

  if (!reforgeEl.dataset.dndBound) {
    reforgeEl.addEventListener('dragover', ev => { ev.preventDefault(); reforgeEl.classList.add('drag-over'); });
    reforgeEl.addEventListener('dragleave', () => reforgeEl.classList.remove('drag-over'));
    reforgeEl.addEventListener('drop', async ev => {
      ev.preventDefault(); reforgeEl.classList.remove('drag-over');
      const raw = ev.dataTransfer.getData('text/plain') || null;
      const payload = raw ? JSON.parse(raw) : getCurrentDrag();
      if (!payload || payload.from !== 'inventory') return;
      const itemId = Number(payload.itemId);
      const instanceId = payload.instance;
      if (!reforgeState.baseId) { reforgeState.baseId = itemId; reforgeState.count = 1; }
      else if (reforgeState.baseId === itemId) { reforgeState.count = Math.min(3, reforgeState.count + 1); }
      else { reforgeState.baseId = itemId; reforgeState.count = 1; }
      updateReforgeUI();
      if (instanceId) {
        const usedCard = document.querySelector(`.inventory-card[data-instance-id="${instanceId}"]`);
        if (usedCard) { usedCard.classList.add('in-reforge'); usedCard.setAttribute('draggable', 'false'); }
      }
      if (typeof setCurrentDrag === 'function') setCurrentDrag(null);
      if (typeof updateSlotHighlights === 'function') updateSlotHighlights();
    });
    reforgeEl.dataset.dndBound = '1';
  }
}
