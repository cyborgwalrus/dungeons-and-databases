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

  root.innerHTML = `
    <div class="game-container auth-container">
      <div class="auth-form-wrapper">
        <h1>Dungeons & Databases</h1>
        <div id="login-container">
          <div class="auth-form-group">
            <label for="username" class="auth-form-label">Username:</label>
            <input type="text" id="username" placeholder="Enter username" class="auth-form-input">
          </div>
          <div class="auth-form-group">
            <label for="password" class="auth-form-label">Password:</label>
            <input type="password" id="password" placeholder="Enter password" class="auth-form-input">
          </div>
          <div id="login-message" class="auth-message"></div>
          <div class="auth-button-group">
            <button id="signin-btn">Sign In</button>
            <button id="signup-btn">Sign Up</button>
          </div>
        </div>
      </div>
    </div>
  `;

  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const messageEl = document.getElementById('login-message');

  document.getElementById('signin-btn').addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    if (!username || !password) {
      messageEl.textContent = 'Username and password required';
      return;
    }

    const res = await fetchJson('/login/signin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (res.ok && res.data.user) {
      if (res.data.token) setAuthToken(res.data.token);
      state.currentUser = res.data.user;
      navigateTo('/character-select');
    } else {
      messageEl.textContent = res.data?.message || 'Sign in failed';
    }
  });

  document.getElementById('signup-btn').addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    if (!username || !password) {
      messageEl.textContent = 'Username and password required';
      return;
    }

    const res = await fetchJson('/login/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (res.ok && res.data.user) {
      if (res.data.token) setAuthToken(res.data.token);
      state.currentUser = res.data.user;
      navigateTo('/character-select');
    } else {
      messageEl.textContent = res.data?.message || 'Sign up failed';
    }
  });
}
