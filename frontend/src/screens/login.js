import { buildScreenShell } from '../ui.js';

/**
 * Login screen module.
 * Renders the sign-in/sign-up forms and handles authentication.
 */

/**
 * Render the login/signup screen with auth form.
 * 
 * @param {HTMLElement} root - Root DOM element to render into
 * @param {Object} deps - Dependencies object
 * @param {Function} deps.fetchJson - HTTP client for API calls
 * @param {Function} deps.setAuthToken - Store auth token function
 * @param {Function} deps.navigateTo - Client-side router function
 * @param {Object} deps.state - App state object
 */
export async function renderLogin(root, deps) {
  const { fetchJson, setAuthToken, navigateTo, state } = deps;

  root.innerHTML = buildScreenShell({
    className: 'screen-shell--auth',
    title: 'Dungeons & Databases',
    subtitle: 'Sign in or create an account',
    sections: [{ id: 'login-content', body: 'Loading...' }],
  });

  const content = document.getElementById('login-content');
  content.innerHTML = `
    <div class="screen-stack">
      <div class="screen-panel screen-panel--dark">
        <div id="login-container" class="auth-form-wrapper">
          <div class="auth-form-group">
            <label for="username" class="auth-form-label">Username</label>
            <input type="text" id="username" placeholder="Enter username" class="auth-form-input">
          </div>
          <div class="auth-form-group">
            <label for="password" class="auth-form-label">Password</label>
            <input type="password" id="password" placeholder="Enter password" class="auth-form-input">
          </div>
          <div id="login-message" class="auth-message"></div>
          <div class="screen-button-stack auth-button-group">
            <button id="signin-btn" class="dungeon-button auth-button">Sign In</button>
            <button id="signup-btn" class="dungeon-button dungeon-button-secondary auth-button">Sign Up</button>
            <button id="api-docs-link" class="dungeon-button dungeon-button-secondary auth-button" type="button">
              API DOCS
            </button>
          </div>
        </div>
      </div>
    </div>
  `;

  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const messageEl = document.getElementById('login-message');

  async function submitAuth(actionPath, fallbackMessage) {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    if (!username || !password) {
      messageEl.textContent = 'Username and password required';
      return;
    }

    const res = await fetchJson(actionPath, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (res.ok && res.data.user) {
      if (res.data.token) setAuthToken(res.data.token);
      state.currentUser = res.data.user;
      navigateTo('/character-select');
    } else {
      messageEl.textContent = res.data?.message || fallbackMessage;
    }
  }

  document.getElementById('signin-btn').addEventListener('click', () => submitAuth('/login/signin', 'Sign in failed'));
  document.getElementById('signup-btn').addEventListener('click', () => submitAuth('/login/signup', 'Sign up failed'));
  document.getElementById('api-docs-link').addEventListener('click', () => {
    window.open('/api/docs', '_blank', 'noreferrer');
  });
}
