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
 * @param {Function} [config.isEligibleDrag] - Returns true when the drag should show hover feedback for this zone.
 * @param {string} [config.activeClass='dropzone-active'] - CSS class applied while dragging a valid payload over zone.
 * @param {string} [config.invalidClass] - CSS class applied while dragging an invalid but eligible payload over zone.
 * @returns {void}
 */
export function setupDragDropZone(element, config) {
  if (!element || !config || !config.validatePayload || !config.onDrop) {
    console.warn('setupDragDropZone: missing required element or config properties');
    return;
  }

  const activeClass = config.activeClass || 'dropzone-active';
  const invalidClass = config.invalidClass || '';
  const dragMIME = config.dragMIME || DEFAULT_DRAG_MIME;

  element.ondragover = (event) => {
    const payload = config.validatePayload(event);
    const dragTypes = event.dataTransfer?.types ? Array.from(event.dataTransfer.types) : [];
    const hasKnownMime = dragTypes.includes(dragMIME);
    const isEligible = typeof config.isEligibleDrag === 'function'
      ? Boolean(config.isEligibleDrag(event))
      : Boolean(payload) || hasKnownMime;

    if (!isEligible) return;

    event.preventDefault();
    const isValid = Boolean(payload);
    element.classList.toggle(activeClass, isValid);
    if (invalidClass) element.classList.toggle(invalidClass, !isValid);
    if (event.dataTransfer) event.dataTransfer.dropEffect = isValid ? 'move' : 'none';
  };

  element.ondragleave = () => {
    element.classList.remove(activeClass);
    if (invalidClass) element.classList.remove(invalidClass);
  };

  element.ondrop = async (event) => {
    element.classList.remove(activeClass);
    if (invalidClass) element.classList.remove(invalidClass);

    const payload = config.validatePayload(event);
    const isEligible = typeof config.isEligibleDrag === 'function'
      ? Boolean(config.isEligibleDrag(event))
      : Boolean(payload);

    if (isEligible) event.preventDefault();
    if (!payload) return;

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
