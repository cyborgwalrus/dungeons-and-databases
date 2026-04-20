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
