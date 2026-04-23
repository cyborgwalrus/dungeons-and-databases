export const state = {
  currentUser: null,
  characters: [],
  player: null,
  inventory: [],
  equipped: [],
  lastDungeonMessage: null,
  lootCounts: {},
  activeEncounter: null,
  activeCombat: null,
  dungeonActionMode: 'run',
};

/** Return the active character ID from local state, or null when unavailable. */
export function getCharacterId() {
  return state.player && state.player.id ? state.player.id : null;
}
