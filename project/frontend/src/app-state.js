export const state = {
  currentUser: null,
  characters: [],
  player: null,
  lastDungeonMessage: null,
  lootCounts: {},
};

export function getCharacterId() {
  return state.player && state.player.id ? state.player.id : null;
}
