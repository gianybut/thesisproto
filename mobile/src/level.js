// Camera tilt from the phone's motion sensors, and what the camera screen makes of it.
//
// The server looks for damage only in the road band: the strip of the picture between the
// horizon and the bonnet of the vehicle (road_top / road_bottom, see src/roadBand.js and
// backend/services/video_processor.py). Where those lines fall depends on how the phone sits in
// its mount: tipped up or down behind the windshield, high or low on the glass, with more or less
// of the bonnet in view. So the camera screen does not ask for a level camera. It shows the two
// lines over the preview for the user to drag into place, and until the horizon line is dragged
// it follows the tilt estimate below.
//
// expo-sensors DeviceMotion gives accelerationIncludingGravity in the phone's own axes (x right,
// y towards the top of the screen in portrait, z out of the screen). At rest it points DOWN on
// both platforms (iOS reports CoreMotion's gravity; the Android module flips its reading to
// match). The camera looks out of the back, along -z, so:
//   pitch = asin(down.z)   0 level, negative pointing down, positive pointing up
//   roll  = tilt of "down" within the screen plane from the nearest upright orientation
// In a moving vehicle the reading also contains braking and acceleration (0.2 g reads as 11°),
// which is why the tilt is only a starting point and the dragged line is what counts.
import { useEffect, useState } from 'react';
import { DeviceMotion } from 'expo-sensors';

export const LEVEL_ROLL_MAX_DEG = 5;    // phone turned sideways by more than this
export const MIN_ROAD_BAND = 0.25;      // less of the picture than this is road: point lower

// Vertical field of view of a 16:9 recording on a phone's main camera (26 mm equivalent, about
// 41° high in landscape and 67° in portrait). Only used for the first guess of the horizon.
const VFOV_DEG = { landscape: 41, portrait: 67 };

const SMOOTHING = 0.2;   // low-pass filter: dashboard vibration should not make the line jump
const deg = (rad) => (rad * 180) / Math.PI;
const rad = (d) => (d * Math.PI) / 180;

/** { available, pitch, roll } in degrees, smoothed; available is false until data arrives. */
export function useLevel() {
  const [level, setLevel] = useState({ available: false, pitch: 0, roll: 0 });

  useEffect(() => {
    let down = null;
    let sub = null;
    let cancelled = false;
    DeviceMotion.isAvailableAsync().then((ok) => {
      if (!ok || cancelled) return;
      DeviceMotion.setUpdateInterval(100);
      sub = DeviceMotion.addListener(({ accelerationIncludingGravity: g }) => {
        if (!g) return;
        const n = Math.hypot(g.x, g.y, g.z);
        if (!n) return;
        const v = { x: g.x / n, y: g.y / n, z: g.z / n };
        down = down
          ? { x: down.x + SMOOTHING * (v.x - down.x), y: down.y + SMOOTHING * (v.y - down.y), z: down.z + SMOOTHING * (v.z - down.z) }
          : v;
        const pitch = deg(Math.asin(Math.max(-1, Math.min(1, down.z))));
        const inPlane = deg(Math.atan2(down.x, -down.y));         // 0 when upright in portrait
        const roll = inPlane - 90 * Math.round(inPlane / 90);       // from the nearest of the four
        setLevel((prev) => {
          const next = { available: true, pitch: Math.round(pitch), roll: Math.round(roll) };
          return prev.available && prev.pitch === next.pitch && prev.roll === next.roll ? prev : next;
        });
      });
    }).catch(() => {});
    return () => { cancelled = true; sub?.remove(); };
  }, []);

  return level;
}

/**
 * Where the horizon falls in the picture for a camera tilted by `pitch` degrees, as a fraction of
 * the height from the top: 0.5 when level, lower in the picture when pointing up. Pinhole camera:
 * a ray `pitch` degrees below the optical axis lands tan(pitch) / tan(vfov / 2) half-heights
 * below the centre. null without a sensor reading.
 */
export function horizonFromTilt({ available, pitch }, landscape) {
  if (!available) return null;
  const half = Math.tan(rad(VFOV_DEG[landscape ? 'landscape' : 'portrait'] / 2));
  const y = 0.5 + Math.tan(rad(pitch)) / (2 * half);
  return Math.max(0.05, Math.min(0.9, y));
}

/** Status label and one sentence of advice for the camera screen; null advice when fine. */
export function levelStatus({ available, roll }, band) {
  if (available && Math.abs(roll) > LEVEL_ROLL_MAX_DEG) {
    return {
      status: { icon: 'alert-triangle', tone: 'waiting', text: `Tilted ${Math.abs(roll)}°` },
      advice: 'Straighten the phone in its mount so the road is not tilted in the picture.',
    };
  }
  if (band.bottom - band.top < MIN_ROAD_BAND) {
    return {
      status: { icon: 'alert-triangle', tone: 'waiting', text: 'Little road in view' },
      advice: 'Point the camera a little lower, so more of the road is between the two lines.',
    };
  }
  return { status: { icon: 'check', tone: 'ready', text: band.manual ? 'Road lines set' : 'Horizon from tilt' }, advice: null };
}
