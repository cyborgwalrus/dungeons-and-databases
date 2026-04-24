import { escapeHtml } from './helpers.js';

// Small UI helpers to keep main.js concise

function renderScreenSection(section = {}) {
  const {
    id = null,
    className = '',
    title = '',
    subtitle = '',
    body = '',
  } = section;

  const classes = ['screen-section', className].filter(Boolean).join(' ');
  const header = title || subtitle ? `
      <div class="screen-section__header">
        ${title ? `<h2 class="screen-section__title">${escapeHtml(title)}</h2>` : ''}
        ${subtitle ? `<p class="screen-section__subtitle">${escapeHtml(subtitle)}</p>` : ''}
      </div>` : '';

  return `
    <section${id ? ` id="${id}"` : ''} class="${classes}">
      ${header}
      ${body}
    </section>`;
}

/** Build the shared retro shell used by all screens. */
export function buildScreenShell({
  className = '',
  title = '',
  subtitle = '',
  sections = [],
} = {}) {
  const classes = ['screen-shell', className].filter(Boolean).join(' ');
  return `
    <div class="${classes}">
      <div class="screen-shell__frame">
        <div class="screen-shell__header">
          ${title ? `<h1 class="screen-shell__title">${escapeHtml(title)}</h1>` : ''}
          ${subtitle ? `<p class="screen-shell__subtitle">${escapeHtml(subtitle)}</p>` : ''}
        </div>
        <div class="screen-shell__stack">
          ${sections.map(renderScreenSection).join('')}
        </div>
      </div>
    </div>`;
}
/** Create a styled action button used across the combat UI. */
export function createActionButton({ id = null, text = '', classNames = '', onClick = null } = {}) {
  const btn = document.createElement('button');
  if (id) btn.id = id;
  const classes = ['dungeon-button', 'action-button', classNames].filter(Boolean).join(' ');
  btn.className = classes;
  btn.textContent = text;
  btn.style.width = '100%';
  btn.style.height = '100%';
  if (onClick) btn.addEventListener('click', (ev) => onClick(ev, btn));
  return btn;
}

/** Create a fixed-width action bar and pad it to the expected slot count. */
export function createActionBar(buttons = []) {
  const bar = document.createElement('div');
  bar.className = 'action-bar';
  buttons.forEach(b => bar.appendChild(b));
  // Keep the action bar at a fixed width so the combat UI stays aligned.
  while (bar.children.length < 6) {
    const spacer = document.createElement('div');
    spacer.className = 'action-bar-spacer';
    spacer.setAttribute('aria-hidden', 'true');
    bar.appendChild(spacer);
  }
  return bar;
}
