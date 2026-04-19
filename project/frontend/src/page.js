import { createActionButton, createActionBar } from './ui.js';

export function setupActionButtons(actionsContainer, deps) {
  const { fetchJson, loadStateAndRenderPartial, getCharacterId, syncPlayerHealthToFull } = deps;
  if (!actionsContainer || actionsContainer.dataset.buttonsBound) return;

  function getInventoryPath(suffix = '') {
    const characterId = getCharacterId && getCharacterId();
    return characterId ? `/characters/${characterId}/inventory/${suffix}` : null;
  }

  function getReforgeAllPath() {
    const characterId = getCharacterId && getCharacterId();
    return characterId ? `/forge/reforge_all/${characterId}` : null;
  }

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
        const inventoryPath = getInventoryPath();
        if (!inventoryPath) {
          btn.disabled = false;
          return;
        }
        const res = await fetchJson(`${inventoryPath}unequip_all`, { method: 'POST' });
        if (!res.ok) console.error('Unequip all failed', res.data);
        await loadStateAndRenderPartial();
        if (syncPlayerHealthToFull) await syncPlayerHealthToFull();
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
        const reforgePath = getReforgeAllPath();
        if (!reforgePath) {
          btn.disabled = false;
          return;
        }
        const res = await fetchJson(reforgePath, { method: 'POST' });
        if (!res.ok) console.error('Server reforge_all failed', res.data);
        await loadStateAndRenderPartial();
        if (syncPlayerHealthToFull) await syncPlayerHealthToFull();
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
        const inventoryPath = getInventoryPath();
        if (!inventoryPath) {
          btn.disabled = false;
          return;
        }
        const res = await fetchJson(`${inventoryPath}equip_best_items`, { method: 'POST' });
        if (!res.ok) console.error('Equip best items failed', res.data);
        await loadStateAndRenderPartial();
        if (syncPlayerHealthToFull) await syncPlayerHealthToFull();
      } catch (err) { console.error('Equip best failed', err); }
      btn.disabled = false;
    }
  });

  const btnBar = createActionBar([unequipAllBtn, reforgeAllBtn, equipBestBtn]);
  actionsContainer.appendChild(btnBar);
  actionsContainer.dataset.buttonsBound = '1';
}

export function setupRubbishBin(bin, deps) {
  const { fetchJson, loadStateAndRenderPartial, getCurrentDrag, setCurrentDrag, updateSlotHighlights, getCharacterId, syncPlayerHealthToFull } = deps;
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
    const characterId = getCharacterId ? getCharacterId() : null;
    const inventoryPath = characterId ? `/characters/${characterId}/inventory/` : null;
    try {
      if (payload.from === 'inventory') {
        if (inventoryPath) {
          await fetchJson(`${inventoryPath}${itemId}`, { method: 'DELETE' });
        }
      } else if (payload.from === 'equipped') {
        if (inventoryPath) {
          await fetchJson(inventoryPath, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item_id: itemId, is_equipped: false }) });
          await fetchJson(`${inventoryPath}${itemId}`, { method: 'DELETE' });
        }
      }
      await loadStateAndRenderPartial();
      if (syncPlayerHealthToFull) await syncPlayerHealthToFull();
    } catch (e) {
      console.error('Destroy failed', e);
    }
    setCurrentDrag(null); updateSlotHighlights();
  });
  bin.dataset.dndBound = '1';
}
