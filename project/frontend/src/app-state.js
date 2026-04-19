export const state = {
  currentUser: null,
  characters: [],
  player: null,
  inventory: [],
  equipped: [],
  allItems: [],
  currentDrag: null,
  lastDungeonMessage: null,
  lootCounts: {},
  dungeonLoot: [],
};

export function getCharacterId() {
  return state.player && state.player.id ? state.player.id : null;
}

export function getUserId() {
  return state.currentUser && state.currentUser.id ? state.currentUser.id : null;
}

export function getCharacterInventoryPath(suffix = '') {
  const characterId = getCharacterId();
  if (!characterId) return null;
  return `/characters/${characterId}/inventory/${suffix}`;
}

export function getFullHealthForPlayer(playerState) {
  if (!playerState) return null;
  const level = playerState.level || 1;
  const baseMax = 100 + (Math.max(0, level - 1) * 10);
  return baseMax + (playerState.bonus_health || 0);
}