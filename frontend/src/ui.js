// Small UI helpers to keep main.js concise
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
