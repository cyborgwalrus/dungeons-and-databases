// Small UI helpers to keep main.js concise
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

export function createActionBar(buttons = []) {
  const bar = document.createElement('div');
  bar.className = 'action-bar';
  buttons.forEach(b => bar.appendChild(b));
  while (bar.children.length < 6) {
    const spacer = document.createElement('div');
    spacer.className = 'action-bar-spacer';
    spacer.setAttribute('aria-hidden', 'true');
    bar.appendChild(spacer);
  }
  return bar;
}
