// Plotly.js — bundle minifié auto-suffisant (tous les types de traces inclus).
// Plus robuste que l'import multi-subpath `lib/core` + `register([...])` qui
// dépend de l'interop CJS de Vite et charge @plotly/d3 (référence `self`).
import Plotly from 'plotly.js-dist-min';

export default Plotly;