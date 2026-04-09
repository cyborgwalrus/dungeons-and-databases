import { createActionButton, createActionBar } from './ui.js';
import { getEquipScore, isSlotCompatible } from './helpers.js';

export function setupActionButtons(actionsContainer, deps) {
  const { fetchJson, loadStateAndRenderPartial, getEquipped, getInventory, getItemType } = deps;
  if (!actionsContainer || actionsContainer.dataset.buttonsBound) return;

  // The button bar is mounted once per page render; reuse it instead of rebinding handlers.
  actionsContainer.style.minHeight = '90px';
  actionsContainer.style.display = 'flex';
  actionsContainer.style.alignItems = 'stretch';

  const unequipAllBtn = createActionButton({
    text: 'Unequip All',
    classNames: 'unequip-button',
    onClick: async (_ev, btn) => {
      btn.disabled = true;
      try {
        const equipped = getEquipped();
        if (equipped && equipped.length) {
          for (const eq of equipped.slice()) {
            await fetchJson(`/inventory/unequip/${eq.slot}`, { method: 'DELETE' });
          }
          await loadStateAndRenderPartial();
        }
      } catch (err) { console.error('Unequip all failed', err); }
      btn.disabled = false;
    }
  });

  const reforgeAllBtn = createActionButton({
    id: 'reforge-all',
    text: 'Reforge All',
    classNames: 'reforge-button',
    onClick: async (_ev, btn) => {
      btn.disabled = true;
      try {
        const res = await fetchJson('/inventory/reforge_all', { method: 'POST' });
        if (!res.ok) console.error('Server reforge_all failed', res.data);
        await loadStateAndRenderPartial();
      } catch (e) {
        console.error('Reforge all failed', e);
      }
      btn.disabled = false;
    }
  });

  const equipBestBtn = createActionButton({
    text: 'Equip Best Items',
    classNames: 'equip-best-button',
    onClick: async (_ev, btn) => {
      btn.disabled = true;
      try {
        const inventory = getInventory();
        const equipped = getEquipped();
        // Slot order matches the backend slot layout.
        const SLOT_DEFS = [ 'helmet', 'armor', 'weapon', 'shield', 'ring', 'necklace' ];
        for (let slot = 0; slot < SLOT_DEFS.length; slot++) {
          const type = SLOT_DEFS[slot];
          let best = null;
          let bestScore = -Infinity;
          for (const invItem of inventory) {
            const item = invItem.item;
            if (!item) continue;
            const itype = getItemType(item);
            if (!isSlotCompatible(type, itype)) continue;
            const score = getEquipScore(item, type);
            if (score > bestScore) { bestScore = score; best = item; }
          }
          const currentlyEquipped = (equipped || []).find(e => e.slot === slot);
          let currentScore = -Infinity;
          if (currentlyEquipped && currentlyEquipped.item) {
            const ci = currentlyEquipped.item;
            currentScore = getEquipScore(ci, type);
          }
          if (best && bestScore > currentScore) {
            await fetchJson('/inventory/equip', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item_id: best.id, slot }) });
          }
        }
        await loadStateAndRenderPartial();
      } catch (err) { console.error('Equip best failed', err); }
      btn.disabled = false;
    }
  });

  const btnBar = createActionBar([unequipAllBtn, reforgeAllBtn, equipBestBtn]);
  actionsContainer.appendChild(btnBar);
  actionsContainer.dataset.buttonsBound = '1';
}

export function setupRubbishBin(bin, deps) {
  const { fetchJson, loadStateAndRenderPartial, getCurrentDrag, setCurrentDrag, updateSlotHighlights } = deps;
  if (!bin || bin.dataset.dndBound) return;
  // The bin is a shared drag target, so wire it once and let the state helpers keep it current.
  bin.addEventListener('dragover', ev => { ev.preventDefault(); bin.classList.add('drag-over'); });
  bin.addEventListener('dragleave', () => bin.classList.remove('drag-over'));
  bin.addEventListener('drop', async ev => {
    ev.preventDefault(); bin.classList.remove('drag-over');
    const raw = ev.dataTransfer.getData('text/plain');
    const payload = raw ? JSON.parse(raw) : getCurrentDrag();
    if (!payload) return;
    const itemId = Number(payload.itemId);
    try {
      if (payload.from === 'inventory') {
        await fetchJson(`/inventory/item/${itemId}`, { method: 'DELETE' });
      } else if (payload.from === 'equipped') {
        const slot = payload.slot !== undefined ? payload.slot : (getCurrentDrag() && getCurrentDrag().slot !== undefined ? getCurrentDrag().slot : null);
        if (slot !== null) {
          await fetchJson(`/inventory/unequip/${slot}`, { method: 'DELETE' });
          await fetchJson(`/inventory/item/${itemId}`, { method: 'DELETE' });
        }
      }
      await loadStateAndRenderPartial();
    } catch (e) {
      console.error('Destroy failed', e);
    }
    setCurrentDrag(null); updateSlotHighlights();
  });
  bin.dataset.dndBound = '1';
}
