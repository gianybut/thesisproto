import { Text, View } from 'react-native';
import { C, S, s } from '../theme';

/**
 * Label and value rows with a divider between rows (design.md §6: lines only between rows in a
 * list). rows: [[label, value]]; a null value hides the row. Values use tabular figures.
 */
export default function Facts({ rows, style }) {
  const shown = rows.filter((r) => r && r[1] != null);
  return (
    <View style={style}>
      {shown.map(([label, value], i) => (
        <View
          key={label}
          style={{
            flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: S[4],
            paddingVertical: S[2], borderTopWidth: i ? 1 : 0, borderTopColor: C.border,
          }}
        >
          <Text style={[s.body, { color: C.muted }]}>{label}</Text>
          <Text style={[s.body, s.num, { flexShrink: 1, textAlign: 'right' }]}>{value}</Text>
        </View>
      ))}
    </View>
  );
}
