// Small UI helpers to keep main.js concise
export function createActionButton({ id = null, text = '', classNames = '', onClick = null } = {}) {
  const btn = document.createElement('button');
  if (id) btn.id = id;
  const classes = ['dungeon-button', 'action-button', classNames].filter(Boolean).join(' ');
  btn.className = classes;
  btn.textContent = text;
  btn.style.flex = '1';
  if (onClick) btn.addEventListener('click', (ev) => onClick(ev, btn));
  return btn;
}

export function createActionBar(buttons = []) {
  const bar = document.createElement('div');
  bar.className = 'action-bar';
  buttons.forEach(b => bar.appendChild(b));
  return bar;
}
