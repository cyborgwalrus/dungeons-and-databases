const API_BASE = (window.__API_BASE__ || 'http://localhost:5000') + '/api';

const root = document.getElementById('root');

function el(html) {
  const container = document.createElement('div');
  container.innerHTML = html.trim();
  return container.firstChild;
}

async function fetchJson(path, options) {
  try {
    const res = await fetch(`${API_BASE}${path}`, options);
    const data = await res.json();
    return { ok: res.ok, data };
  } catch (e) {
    console.error('Fetch error', e);
    return { ok: false, data: null };
  }
}

/* --- Home view --- */
function renderPlayerStats(player) {
  return `
    <div class="player-stats">
      <h2>Player Stats</h2>
      <div class="stat"><span class="stat-label">Health:</span><span class="stat-value">${player.health} HP</span></div>
      <div class="stat"><span class="stat-label">Damage:</span><span class="stat-value">${player.damage}</span></div>
      <div class="stat"><span class="stat-label">Level:</span><span class="stat-value">${player.level}</span></div>
      ${player.bonus_health > 0 ? `<div class="stat" style="color:#4ecdc4"><span class="stat-label">+Health Bonus:</span><span class="stat-value">+${player.bonus_health}</span></div>` : ''}
      ${player.bonus_damage > 0 ? `<div class="stat" style="color:#4ecdc4"><span class="stat-label">+Attack Bonus:</span><span class="stat-value">+${player.bonus_damage}</span></div>` : ''}
    const API_BASE = (window.__API_BASE__ || 'http://localhost:5000') + '/api';

    const root = document.getElementById('root');

    let player = null;
    let inventory = [];
    let equipped = [];
    let allItems = [];

    async function fetchJson(path, options) {
      try {
        const res = await fetch(`${API_BASE}${path}`, options);
        const data = await res.json();
        return { ok: res.ok, data };
      } catch (e) {
        console.error('Fetch error', e);
        return { ok: false, data: null };
      }
    }

    function renderPlayerStatsInto(container) {
      container.innerHTML = `
        <div class="player-stats">
          <h2>Player Stats</h2>
          <div class="stat"><span class="stat-label">Health:</span><span class="stat-value">${player.health} HP</span></div>
          <div class="stat"><span class="stat-label">Damage:</span><span class="stat-value">${player.damage}</span></div>
          <div class="stat"><span class="stat-label">Level:</span><span class="stat-value">${player.level}</span></div>
          ${player.bonus_health > 0 ? `<div class="stat" style="color:#4ecdc4"><span class="stat-label">+Health Bonus:</span><span class="stat-value">+${player.bonus_health}</span></div>` : ''}
          ${player.bonus_damage > 0 ? `<div class="stat" style="color:#4ecdc4"><span class="stat-label">+Attack Bonus:</span><span class="stat-value">+${player.bonus_damage}</span></div>` : ''}
        </div>`;
    }

    function makeIcon(i) {
      return i.bonus_attack > 0 && i.bonus_health === 0 ? '⚔️' : i.bonus_health > 0 && i.bonus_attack === 0 ? '🛡️' : i.bonus_health > 0 && i.bonus_attack > 0 ? '💎' : '💰';
    }

    function renderEquipPanel() {
      const equipPanel = document.getElementById('equip-panel');
      const slotsHtml = Array.from({ length: 5 }).map((_, slotNum) => {
        const eq = equipped.find(e => e.slot === slotNum);
        if (eq) {
          return `
            <div class="equip-slot" data-slot="${slotNum}" draggable="true" data-from="equipped" data-item-id="${eq.item.id}">
              <span class="slot-label">Slot ${slotNum + 1}</span>
              <p class="item-name">${eq.item.name}</p>
              <p class="item-type">+${eq.item.bonus_health}HP / +${eq.item.bonus_attack}ATK</p>
              <button class="unequip-button" data-unequip-slot="${slotNum}">Unequip</button>
            </div>`;
        }
        return `<div class="equip-slot empty" data-slot="${slotNum}"><span class="slot-label">Slot ${slotNum + 1}</span><div class="empty-label">Empty</div></div>`;
      }).join('');

      const availableHtml = allItems.length > 0 ? allItems.map(item => `
        <div class="available-item" draggable="true" data-item-id="${item.item.id}" data-equipped="${item.equipped ? '1' : '0'}">
          <p class="item-name">${item.item.name}</p>
          <p class="item-type">+${item.item.bonus_health} HP / +${item.item.bonus_attack} ATK | Qty: ${item.quantity}</p>
        </div>
      `).join('') : '<p style="color:#999;font-style:italic">No items in inventory</p>';

      equipPanel.innerHTML = `
        <div style="background:rgba(0,0,0,0.3);border:2px solid #4ecdc4;border-radius:10px;padding:20px;margin-bottom:20px">
          <div style="margin-bottom:20px">
            <h4 style="margin-top:0;color:#4ecdc4">Equipped Items:</h4>
            <div id="slots-grid" style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px">${slotsHtml}</div>
          </div>
          <hr style="opacity:0.3;margin:20px 0" />
          <h4 style="margin-top:0;color:#4ecdc4">Available Items (${inventory.length})</h4>
          <div id="available-list" style="display:flex;flex-direction:column;gap:10px;max-height:300px;overflow-y:auto">${availableHtml}</div>
        </div>
      `;

      // attach DnD handlers to slots
      document.querySelectorAll('.equip-slot').forEach(slotEl => {
        slotEl.addEventListener('dragstart', ev => {
          const itemId = slotEl.getAttribute('data-item-id');
          ev.dataTransfer.setData('text/plain', JSON.stringify({ itemId, from: 'equipped', slot: slotEl.getAttribute('data-slot') }));
        });

        slotEl.addEventListener('dragover', ev => {
          ev.preventDefault();
          slotEl.classList.add('drag-over');
        });
        slotEl.addEventListener('dragleave', () => slotEl.classList.remove('drag-over'));
        slotEl.addEventListener('drop', async ev => {
          ev.preventDefault();
          slotEl.classList.remove('drag-over');
          const payload = JSON.parse(ev.dataTransfer.getData('text/plain'));
          if (!payload) return;
          // If dragging from available items, equip into this slot
          if (payload.from === 'available' || payload.from === 'inventory') {
            const itemId = Number(payload.itemId);
            const slot = Number(slotEl.getAttribute('data-slot'));
            await fetchJson('/inventory/equip', {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item_id: itemId, slot })
            });
            await loadStateAndRenderPartial();
          } else if (payload.from === 'equipped') {
            // swapping slots: equip item into this slot
            const itemId = Number(payload.itemId);
            const slot = Number(slotEl.getAttribute('data-slot'));
            await fetchJson('/inventory/equip', {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ item_id: itemId, slot })
            });
            await loadStateAndRenderPartial();
          }
        });
      });

      // available items dragstart
      document.querySelectorAll('.available-item').forEach(it => {
        it.addEventListener('dragstart', ev => {
          const id = it.getAttribute('data-item-id');
          ev.dataTransfer.setData('text/plain', JSON.stringify({ itemId: id, from: 'available' }));
        });
      });

      // unequip buttons
      document.querySelectorAll('.unequip-button').forEach(btn => {
        btn.addEventListener('click', async () => {
          const slot = btn.getAttribute('data-unequip-slot');
          await fetchJson(`/inventory/unequip/${slot}`, { method: 'DELETE' });
          await loadStateAndRenderPartial();
        });
      });
    }

    function renderInventoryGrid() {
      const invContainer = document.getElementById('inventory-grid');
      if (!invContainer) return;
      invContainer.innerHTML = inventory.length === 0 ? '<p style="color:#999;font-style:italic">Your inventory is empty</p>' : inventory.map(invItem => {
        const i = invItem.item;
        return `
          <div class="inventory-card" draggable="true" data-item-id="${i.id}">
            <div class="item-icon">${makeIcon(i)}</div>
            <div class="card-details">
              <div class="item-name">${i.name}</div>
              <div class="item-type">+${i.bonus_health} HP / +${i.bonus_attack} ATK</div>
            </div>
            <div class="qty">×${invItem.quantity}</div>
          </div>`;
      }).join('');

      // add drag handlers
      document.querySelectorAll('.inventory-card').forEach(card => {
        card.addEventListener('dragstart', ev => {
          const id = card.getAttribute('data-item-id');
          ev.dataTransfer.setData('text/plain', JSON.stringify({ itemId: id, from: 'inventory' }));
        });
      });

      // allow dropping equipped items back to inventory to unequip
      invContainer.addEventListener('dragover', ev => { ev.preventDefault(); invContainer.classList.add('drag-over'); });
      invContainer.addEventListener('dragleave', () => invContainer.classList.remove('drag-over'));
      invContainer.addEventListener('drop', async ev => {
        ev.preventDefault(); invContainer.classList.remove('drag-over');
        const payload = JSON.parse(ev.dataTransfer.getData('text/plain'));
        if (!payload) return;
        if (payload.from === 'equipped') {
          const slot = payload.slot !== undefined ? payload.slot : null;
          if (slot !== null) {
            await fetchJson(`/inventory/unequip/${slot}`, { method: 'DELETE' });
            await loadStateAndRenderPartial();
          }
        }
      });
    }

    async function loadStateAndRenderPartial() {
      const [pRes, invRes, eqRes, allRes] = await Promise.all([
        fetchJson('/player'), fetchJson('/inventory'), fetchJson('/inventory/equipped'), fetchJson('/inventory/items')
      ]);
      if (pRes.ok) player = pRes.data;
      inventory = invRes.ok ? invRes.data : [];
      equipped = eqRes.ok ? eqRes.data : [];
      allItems = allRes.ok ? allRes.data : [];

      // update parts
      const mainContent = document.getElementById('main-content');
      if (!mainContent) return;
      renderPlayerStatsInto(document.getElementById('player-stats-container'));
      renderEquipPanel();
      renderInventoryGrid();
    }

    async function renderHome() {
      root.innerHTML = `<div class="game-container"><h1>Dungeons and Databases</h1><div id="main-content"></div></div>`;
      const main = document.getElementById('main-content');
      main.innerHTML = `
        <div id="player-stats-container"></div>
        <div style="margin-top:30px">
          <h3 style="margin-bottom:15px;cursor:pointer;color:#4ecdc4">Equipment</h3>
          <div id="equip-panel"></div>
        </div>
        <h3 style="margin-top:20px;color:#ffd700">Inventory</h3>
        <div id="inventory-grid" class="inventory-grid" style="margin-top:10px"></div>
        <div style="margin-bottom:20px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:20px">
          <button class="dungeon-button" id="enter-dungeon">Enter the Dungeon</button>
        </div>
      `;

      document.getElementById('enter-dungeon').addEventListener('click', () => navigateTo('/dungeon'));

      await loadStateAndRenderPartial();
    }

    /* --- Dungeon view remains mostly unchanged but uses player updates from API --- */
    async function renderDungeon() {
      root.innerHTML = `<div class="game-container"><h1>The Dungeon</h1><div id="dungeon-content">Loading...</div></div>`;
      const content = document.getElementById('dungeon-content');

      const [pRes, encRes] = await Promise.all([fetchJson('/player'), fetchJson('/dungeon/encounter')]);
      player = pRes.ok ? pRes.data : player;
      const enemy = encRes.ok ? encRes.data : { name: '', health: 0, max_health: 0, damage: 0, description: '' };

      content.innerHTML = `
        <div style="margin-top:20px;font-size:1.2em;min-height:60px">
          <p id="dungeon-message">A wild ${enemy.name || 'creature'} appears! ${enemy.description || ''}</p>
          <div id="loot" style="margin-top:10px"></div>
        </div>

        <div style="display:flex;gap:20;justify-content:center;flex-wrap:wrap;margin-top:30px">
          <div class="player-stats" style="flex:1;min-width:250px;max-width:400px">${player ? '' : ''}</div>
          <div class="player-stats" style="flex:1;min-width:250px;max-width:400px;border-color:#ff6b6b">
            <h2 style="color:#ff6b6b">Enemy: ${enemy.name || 'None'}</h2>
            <div class="stat"><span class="stat-label">Health:</span><span class="stat-value">${enemy.health} / ${enemy.max_health} HP</span></div>
            <div class="stat"><span class="stat-label">Damage:</span><span class="stat-value">${enemy.damage}</span></div>
          </div>
        </div>

        <div style="margin-top:40px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
          <button class="dungeon-button" id="attack">Attack</button>
          <button class="dungeon-button" id="run" style="background:linear-gradient(135deg,#ff9f1c 0%,#ffb700 100%)">Run Away</button>
          <button class="dungeon-button" id="back">Back to Home</button>
        </div>
      `;

      // render player stats into dungeon layout if needed
      renderPlayerStatsInto(document.createElement('div'));

      document.getElementById('attack').addEventListener('click', async () => {
        const res = await fetchJson('/dungeon/attack', { method: 'POST' });
        if (res.ok && res.data) {
          const d = res.data;
          document.getElementById('dungeon-message').textContent = d.message || 'You attacked the monster!';
          const lootEl = document.getElementById('loot');
          if (d.items_dropped && d.items_dropped.length) {
            lootEl.innerHTML = `<div style="margin-top:10px;padding:10px;background:#2d3436;border-left:4px solid #fdcb6e;border-radius:4px"><strong style="color:#fdcb6e">🎁 Loot obtained:</strong><p>${d.items_dropped.map(it => it.name).join(', ')}</p></div>`;
          }
          if (d.player_died) {
            setTimeout(() => navigateTo('/'), 3000);
          } else {
            await loadStateAndRenderPartial();
            setTimeout(() => renderDungeon(), 500);
          }
        }
      });

      document.getElementById('run').addEventListener('click', async () => {
        const res = await fetchJson('/dungeon/run', { method: 'POST' });
        if (res.ok && res.data) {
          const d = res.data;
          document.getElementById('dungeon-message').textContent = d.message || 'Action result';
          if (d.player_died) {
            setTimeout(() => navigateTo('/'), 3000);
          } else if (d.success) {
            setTimeout(() => navigateTo('/'), 1500);
          } else {
            setTimeout(() => renderDungeon(), 500);
          }
        }
      });

      document.getElementById('back').addEventListener('click', () => navigateTo('/'));
    }

    /* --- Router --- */
    function navigateTo(path) { if (path === '/') location.hash = '#/'; else location.hash = `#${path}`; }

    function route() { const hash = location.hash.replace('#', '') || '/'; if (hash === '/' || hash === '') renderHome(); else if (hash === '/dungeon') renderDungeon(); else renderHome(); }

    window.addEventListener('hashchange', route);
    window.addEventListener('load', route);
