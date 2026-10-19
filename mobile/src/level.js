// Camera level from the phone's motion sensors, for the guide on the camera screen.
//
// The server only looks for damage below the middle line of the picture (ROAD_REGION_TOP in
// backend/services/video_processor.py). With the camera pointing level, the horizon is exactly
// that middle line and everything below it is road. Pointing up moves the horizon below the
// middle, so buildings and trees end up in the analysed half; pointing a little down is fine.
//
// expo-sensors DeviceMotion gives accelerationIncludingGravity in the phone's own axes (x right,
// y towards the top of the screen in portrait, z out of the screen). At rest it points DOWN on
// both platforms (iOS reports CoreMotion's gravity; the Android module flips its reading to
// match). The camera looks out of the back, along -z, so:
//   pitch = asin(down.z)   0 level, negative pointing down, positive pointing up
//   roll  = tilt of "down" within the screen plane from the nearest upright orientation
import { useEffect, useState } from 'react';
import { DeviceMotion } from 'expo-sensors';

export const LEVEL_UP_MAX_DEG = 3;      // more than this upwards: buildings enter the analysed half
export const LEVEL_DOWN_MAX_DEG = 15;   // more than this downwards: little road ahead is left in view
export const LEVEL_ROLL_MAX_DEG = 5;    // phone turned sideways by more than this

const SMOOTHING = 0.2;   // low-pass filter: dashboard vibration should not make the label flicker
const deg = (rad) => (rad * 180) / Math.PI;

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

/** Status label and one sentence of advice for the camera screen; null advice when level. */
export function levelStatus({ available, pitch, roll }) {
  if (!available) {
    return { status: { icon: 'info-circle', tone: 'waiting', text: 'Level not available' }, advice: null };
  }
  if (pitch > LEVEL_UP_MAX_DEG) {
    return {
      status: { icon: 'alert-triangle', tone: 'waiting', text: `Pointing up ${pitch}°` },
      advice: 'Point the camera a little lower. Damage is only looked for below the middle line, and pointing up puts buildings there.',
    };
  }
  if (pitch < -LEVEL_DOWN_MAX_DEG) {
    return {
      status: { icon: 'alert-triangle', tone: 'waiting', text: `Pointing down ${-pitch}°` },
      advice: 'Point the camera a little higher, so the road ahead stays in view.',
    };
  }
  if (Math.abs(roll) > LEVEL_ROLL_MAX_DEG) {
    return {
      status: { icon: 'alert-triangle', tone: 'waiting', text: `Tilted ${Math.abs(roll)}°` },
      advice: 'Straighten the phone in its mount so the picture is not tilted.',
    };
  }
  return { status: { icon: 'check', tone: 'ready', text: 'Level' }, advice: null };
}
