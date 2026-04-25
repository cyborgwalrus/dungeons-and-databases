import { buildScreenShell } from '../ui.js';

/**
 * Character select screen module.
 * Renders the character list, creation form, and character selection.
 */

import { escapeHtml } from '../helpers.js';
import { signOutAndClearSession } from '../utils/state-updater.js';

/**
 * Render the character picker and allow the user to create or select one.
 * 
 * @param {HTMLElement} root - Root DOM element to render into
 * @param {Object} deps - Dependencies object
 * @param {Function} deps.fetchJson - HTTP client for API calls
 * @param {Function} deps.setAuthToken - Store auth token function
 * @param {Function} deps.navigateTo - Client-side router function
 * @param {Function} deps.clearAuthToken - Clear auth token function
 * @param {Object} deps.state - App state object
 */
export async function renderCharacterSelect(root, deps) {
  const { fetchJson, setAuthToken, navigateTo, state } = deps;

  root.innerHTML = buildScreenShell({
    className: 'screen-shell--auth',
    title: 'Dungeons & Databases',
    subtitle: 'Choose your hero',
    sections: [{ id: 'char-select-content', body: 'Loading...' }],
  });
  const content = document.getElementById('char-select-content');
  if (!state.currentUser) {
    navigateTo('/login');
    return;
  }

  const res = await fetchJson(`/users/${state.currentUser.id}/characters`);
  state.characters = res.ok ? res.data : [];

  content.innerHTML = `
    <div class="screen-stack">
      <div class="screen-panel screen-panel--dark">
        <h2 class="character-select-title">Characters</h2>
        <div id="character-list" class="character-list"></div>
      </div>
      <div class="screen-panel screen-panel--nested">
        <div class="auth-form-group">
          <label for="create-char-name" class="auth-form-label">Character name</label>
          <input type="text" id="create-char-name" placeholder="Enter character name" class="character-create-input">
        </div>
        <div class="screen-button-stack">
          <button id="create-char-btn" class="dungeon-button dungeon-button-primary character-action-button">Create New Character</button>
          <button id="logout-btn" class="dungeon-button dungeon-button-secondary character-action-button">Logout</button>
        </div>
      </div>
    </div>
  `;

  const charList = document.getElementById('character-list');
  if (state.characters.length === 0) {
    charList.innerHTML = '<p class="character-empty-message">No characters yet. Create one to start playing!</p>';
  } else {
    state.characters.forEach(character => {
      const charEl = document.createElement('button');
      charEl.className = 'character-item';
      charEl.innerHTML = `
        <div class="character-item-name">${escapeHtml(character.name)}</div>
        <div class="character-item-stats">Level ${character.level} | ${character.health} HP</div>
      `;
      charEl.addEventListener('click', async () => {
        const selectRes = await fetchJson(`/characters/${character.id}/select`, {
          method: 'POST'
        });
        if (selectRes.ok && selectRes.data.character) {
          if (selectRes.data.token) setAuthToken(selectRes.data.token);
          state.player = selectRes.data.character;
          navigateTo('/');
        }
      });
      charList.appendChild(charEl);
    });
  }

  const createCharNameInput = document.getElementById('create-char-name');

  document.getElementById('create-char-btn').addEventListener('click', async () => {
    const charName = createCharNameInput.value.trim() || 'Hero';
    const createRes = await fetchJson(`/users/${state.currentUser.id}/characters`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: charName })
    });
    if (createRes.ok && createRes.data) {
      state.characters = [...state.characters, createRes.data];
      await renderCharacterSelect(root, deps);
    }
  });

  document.getElementById('logout-btn').addEventListener('click', async () => {
    await signOutAndClearSession(fetchJson, state);
    navigateTo('/login');
  });
}
