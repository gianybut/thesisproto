// Colours live only in index.css. Leaflet needs real values (SVG attributes ignore var()),
// so map code reads the token at draw time.
export const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
