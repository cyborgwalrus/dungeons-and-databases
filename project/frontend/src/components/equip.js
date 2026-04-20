import { getCharacterId } from '../app-state.js';

async function unequipItemFromDoubleClick(opts, itemId) {
  const { fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull } = opts;
  if (!itemId) return;
  const characterId = getCharacterId();
  if (!characterId) return;

  await fetchJson(`/characters/${characterId}/equipment/${Number(itemId)}`, {
    method: 'DELETE'
  });

  await loadStateAndRenderPartial();
  if (syncPlayerHealthToFull) await syncPlayerHealthToFull();
}

export async function renderEquipPanel(opts) {
  const { equipped, fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull, makeIcon, formatStats, getItemDisplayName } = opts;
  const equipPanel = document.getElementById('equip-panel');
  if (!equipPanel) return;

  function inventoryCardHtml(i) {
    return `
      <button type="button" class="inventory-card equipped-card" data-item-id="${i.id}">
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
    const equippedCard = slotEl.querySelector('.equipped-card');
    if (equippedCard) {
      equippedCard.addEventListener('dblclick', async event => {
        event.preventDefault();
        event.stopPropagation();
        const itemId = equippedCard.getAttribute('data-item-id');
        try {
          await unequipItemFromDoubleClick({ fetchJson, loadStateAndRenderPartial, syncPlayerHealthToFull }, itemId);
        } catch (error) {
          console.error('Failed to unequip item from double click', error);
        }
      });
    }
  });
}
