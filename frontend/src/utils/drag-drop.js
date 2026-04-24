/**
 * Drag and drop zone management utilities.
 * Centralizes the drag/drop event handling patterns used across inventory, equipment, and trash zones.
 */

const DEFAULT_DRAG_MIME = 'application/x-dd-item';

/**
 * Setup a drag-drop zone with standardized event handlers.
 * Reduces repeated code across equip.js and inventory.js.
 *
 * @param {HTMLElement} element - The drop zone element.
 * @param {Object} config - Configuration object.
 * @param {Function} config.validatePayload - Validates drag payload; returns truthy if valid, falsy to reject.
 * @param {Function} config.onDrop - Async handler called when valid item is dropped.
 * @param {string} [config.activeClass='dropzone-active'] - CSS class applied while dragging over zone.
 * @returns {void}
 */
export function setupDragDropZone(element, config) {
  if (!element || !config || !config.validatePayload || !config.onDrop) {
    console.warn('setupDragDropZone: missing required element or config properties');
    return;
  }

  const activeClass = config.activeClass || 'dropzone-active';
  const dragMIME = config.dragMIME || DEFAULT_DRAG_MIME;

  element.ondragover = (event) => {
    const dragTypes = event.dataTransfer?.types ? Array.from(event.dataTransfer.types) : [];
    const acceptsDrag = dragTypes.includes(dragMIME) || Boolean(config.validatePayload(event));
    if (!acceptsDrag) return;
    event.preventDefault();
    element.classList.add(activeClass);
    if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
  };

  element.ondragleave = () => {
    element.classList.remove(activeClass);
  };

  element.ondrop = async (event) => {
    element.classList.remove(activeClass);
    const payload = config.validatePayload(event);
    if (!payload) return;
    event.preventDefault();
    try {
      await config.onDrop(payload);
    } catch (error) {
      console.error('Drop handler failed:', error);
    }
  };
}

/**
 * Setup a draggable item element with standardized handlers.
 * Adds drag start/end visual feedback and data transport.
 *
 * @param {HTMLElement} element - The draggable element.
 * @param {Object} config - Configuration object.
 * @param {Object} config.dragData - Data object to transport on drag (e.g., { itemId, source }).
 * @param {string} [config.activeClass='dragging'] - CSS class applied while dragging.
 * @param {string} [config.dragMIME] - MIME type for drag data transport.
 * @returns {void}
 */
export function setupDraggableItem(element, config) {
  if (!element || !config || !config.dragData) {
    console.warn('setupDraggableItem: missing required element or config.dragData');
    return;
  }

  const activeClass = config.activeClass || 'dragging';
  const dragMIME = config.dragMIME || 'application/x-dd-item';

  element.addEventListener('dragstart', (event) => {
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData(dragMIME, JSON.stringify(config.dragData));
    }
    element.classList.add(activeClass);
  });

  element.addEventListener('dragend', () => {
    element.classList.remove(activeClass);
  });

  // Double-click handler can be added via separate addEventListener if needed
  // Keep this utility focused on drag operations only
}
