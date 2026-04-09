export function bindDragSource(el, { createPayload, onDragStart, onDragEnd }) {
  el.addEventListener('dragstart', ev => {
    const payload = createPayload ? createPayload() : null;
    if (payload) {
      ev.dataTransfer.setData('text/plain', JSON.stringify(payload));
    }
    if (onDragStart) onDragStart(ev, payload);
  });

  el.addEventListener('dragend', () => {
    if (onDragEnd) onDragEnd();
  });
}

export function bindDropZone(el, { onDragOver, onDragLeave, onDrop, activeClass = 'drag-over' }) {
  el.addEventListener('dragover', ev => {
    ev.preventDefault();
    el.classList.add(activeClass);
    if (onDragOver) onDragOver(ev);
  });

  el.addEventListener('dragleave', ev => {
    el.classList.remove(activeClass);
    if (onDragLeave) onDragLeave(ev);
  });

  el.addEventListener('drop', ev => {
    ev.preventDefault();
    el.classList.remove(activeClass);
    if (onDrop) onDrop(ev);
  });
}