export const state = {
  currentUser: null,
  characters: [],
  player: null,
  lastDungeonMessage: null,
  lootCounts: {},
  dungeonLoot: [],
};

export function getCharacterId() {
  return state.player && state.player.id ? state.player.id : null;
}

export function getCharacterInventoryPath(suffix = '') {
  if (!state.player || !state.player.id) return null;
  const normalizedSuffix = suffix ? `/${suffix.replace(/^\//, '')}` : '';
  return `/characters/${state.player.id}/inventory${normalizedSuffix}`;
}