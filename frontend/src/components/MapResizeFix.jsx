import { useEffect } from 'react';
import { useMap } from 'react-leaflet';

/**
 * Keeps Leaflet's idea of the map's size in step with the page. Leaflet measures its box once,
 * when it mounts; if the layout settles a moment later (fonts, a scrollbar, the sidebar), it keeps
 * loading tiles for the old size, which shows as a grey map or patches of missing tiles after
 * zooming. Re-measuring whenever the box changes fixes that. Place inside every <MapContainer>.
 */
export default function MapResizeFix() {
  const map = useMap();
  useEffect(() => {
    const el = map.getContainer();
    let frame = 0;
    const observer = new ResizeObserver(() => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => map.invalidateSize());
    });
    observer.observe(el);
    return () => { cancelAnimationFrame(frame); observer.disconnect(); };
  }, [map]);
  return null;
}

// One tile source for every map. OpenStreetMap asks for this address, without the old a/b/c
// subdomains, and for the attribution below to stay visible.
export const OSM_TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
export const OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
