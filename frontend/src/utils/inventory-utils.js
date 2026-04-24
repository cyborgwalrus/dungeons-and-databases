/**
 * Inventory and item management utilities.
 * Extracts business logic for item scoring, comparison, and sorting from UI rendering.
 */

/**
 * Calculate a numeric score for an item based on its stats.
 * Used for sorting and comparing items to determine upgrades.
 * Score = health + damage (simple linear combination).
 *
 * @param {Object} item - Item object with optional health/damage properties.
 * @returns {number} Total score (sum of stat gains).
 */
export function scoreItem(item) {
  if (!item) return 0;
  return (item.health || 0) + (item.damage || 0);
}

/**
 * Determine if an item is better than what's currently equipped.
 * Used for inventory sorting to highlight meaningful upgrades.
 *
 * @param {Object} item - Item to evaluate.
 * @param {Object} equippedBySlot - Map of slot to equipped item; e.g. { helmet: itemObj, armor: itemObj }.
 * @returns {boolean} True if item is better than equipped item in same slot, or if no item is equipped.
 */
export function isBetterThanEquipped(item, equippedBySlot) {
  if (!item || !equippedBySlot) return false;

  const itemSlot = item.slot_type;
  if (!itemSlot) return false; // Items without slots can't be compared

  const equippedInSlot = equippedBySlot[itemSlot];
  if (!equippedInSlot) {
    // No item equipped in this slot, so this item is an upgrade
    return true;
  }

  // Compare scores: higher score = better item
  const equippedScore = scoreItem(equippedInSlot);
  const itemScore = scoreItem(item);
  return itemScore > equippedScore;
}

/**
 * Sort inventory items by upgrade potential and slot type.
 * Places better items first, grouped by their equipment slot.
 *
 * @param {Array} inventory - Unequipped items to sort.
 * @param {Object} equippedBySlot - Map of slot to equipped item.
 * @returns {Array} Sorted inventory (new array, original unchanged).
 */
export function sortInventoryByUpgrades(inventory, equippedBySlot) {
  if (!Array.isArray(inventory)) return [];

  // Create a comparison key for each item
  return [...inventory].sort((a, b) => {
    // Items that are upgrades sort first
    const aIsUpgrade = isBetterThanEquipped(a, equippedBySlot);
    const bIsUpgrade = isBetterThanEquipped(b, equippedBySlot);

    if (aIsUpgrade !== bIsUpgrade) {
      return aIsUpgrade ? -1 : 1; // Upgrades first
    }

    // Within same upgrade status, sort by score (higher scores first)
    const scoreA = scoreItem(a);
    const scoreB = scoreItem(b);
    if (scoreB !== scoreA) {
      return scoreB - scoreA;
    }

    // Stable sort: maintain original order for equal items
    return 0;
  });
}

/**
 * Build a map of equipment slots to equipped items for O(1) lookup.
 *
 * @param {Array} equippedArray - Array of equipped item objects.
 * @returns {Object} Map where keys are slot names and values are item objects.
 */
export function buildEquippedSlotMap(equippedArray) {
  if (!Array.isArray(equippedArray)) return {};

  const map = {};
  equippedArray.forEach((item) => {
    if (item && item.slot_type) {
      map[item.slot_type] = item;
    }
  });
  return map;
}
