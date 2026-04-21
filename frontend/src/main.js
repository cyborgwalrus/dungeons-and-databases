import { route } from './app-core.js';

window.addEventListener('hashchange', route);
window.addEventListener('load', route);
