import { useRef } from 'react';
import { Text, View } from 'react-native';
import Icon from '../icons';
import { C, F, R, S, T, TAP } from '../theme';

const DIM = 'rgba(23, 32, 27, 0.45)';
const STEP = 0.02;   // one VoiceOver / TalkBack adjustment

/**
 * The road band drawn over the camera preview (src/roadBand.js): the picture outside it dimmed,
 * a dashed line at the horizon and one at the bonnet, each with a handle to drag it. The parent
 * sizes this exactly over the preview, which shows the whole recorded frame, so a line at y here
 * is the same y in the video. Not editable while recording: the band is fixed per survey.
 */
export default function RoadBandOverlay({ band, height, editable, onMove }) {
  return (
    <View pointerEvents="box-none" style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}>
      <View pointerEvents="none" style={{ position: 'absolute', top: 0, left: 0, right: 0, height: `${band.top * 100}%`, backgroundColor: DIM }} />
      <View pointerEvents="none" style={{ position: 'absolute', top: `${band.bottom * 100}%`, left: 0, right: 0, bottom: 0, backgroundColor: DIM }} />
      <Line y={band.top} height={height} label="Horizon" editable={editable} onMove={(y) => onMove('top', y)} />
      <Line y={band.bottom} height={height} label="Bonnet" editable={editable} onMove={(y) => onMove('bottom', y)} />
    </View>
  );
}

function Line({ y, height, label, editable, onMove }) {
  // Where the drag started: the line's position and the finger's, set on touch.
  const drag = useRef(null);
  const responder = editable ? {
    onStartShouldSetResponder: () => true,
    onMoveShouldSetResponder: () => true,
    onResponderTerminationRequest: () => false,
    onResponderGrant: (e) => { drag.current = { y0: y, p0: e.nativeEvent.pageY }; },
    onResponderMove: (e) => {
      if (drag.current && height > 0) onMove(drag.current.y0 + (e.nativeEvent.pageY - drag.current.p0) / height);
    },
    onResponderRelease: () => { drag.current = null; },
  } : {};

  const px = y * height;
  // The handle sits on the line, kept inside the preview when the line is at an edge.
  const handleTop = Math.max(0, Math.min(height - TAP, px - TAP / 2));

  return (
    <>
      <View
        pointerEvents="none"
        style={{ position: 'absolute', left: 0, right: 0, top: Math.min(px, height - 2), borderTopWidth: 2, borderStyle: 'dashed', borderColor: '#FFFFFF' }}
      />
      <View
        {...responder}
        accessible
        accessibilityRole={editable ? 'adjustable' : 'text'}
        accessibilityLabel={`${label} line`}
        accessibilityValue={{ text: `${Math.round(y * 100)}% from the top` }}
        accessibilityActions={editable ? [{ name: 'increment' }, { name: 'decrement' }] : undefined}
        onAccessibilityAction={(e) => onMove(y + (e.nativeEvent.actionName === 'increment' ? -STEP : STEP))}
        hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        style={{
          position: 'absolute', right: S[2], top: handleTop, height: TAP,
          flexDirection: 'row', alignItems: 'center', gap: S[1], paddingHorizontal: S[3],
          borderRadius: R.sm, backgroundColor: C.scrim, borderWidth: 1, borderColor: editable ? '#FFFFFF' : 'transparent',
        }}
      >
        {editable && <Icon name="chevron-down" size={16} color="#FFFFFF" style={{ transform: [{ rotate: '180deg' }] }} />}
        <Text style={{ fontFamily: F.semibold, ...T.sm, color: '#FFFFFF' }}>{label}</Text>
        {editable && <Icon name="chevron-down" size={16} color="#FFFFFF" />}
      </View>
    </>
  );
}
