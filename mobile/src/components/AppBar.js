import { useEffect, useState } from 'react';
import { Pressable, Switch, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getServerUrl, getUser } from '../auth';
import Icon from '../icons';
import { roleLabel } from '../labels';
import { getSettings, onSettings, setWifiOnly } from '../uploadQueue';
import { C, F, R, S, T, TAP, s } from '../theme';
import Button from './Button';
import Logo from './Logo';
import Sheet from './Sheet';

/**
 * The one navy bar, as the web header: the logo on a white tile (the green is 2.2:1 on navy)
 * and "OcuLubak" on the left, the account button on the right. The account panel holds the
 * name, role, server, the Wi-Fi-only setting and Sign out.
 */
export default function AppBar({ onSignOut }) {
  const insets = useSafeAreaInsets();
  const [open, setOpen] = useState(false);
  const user = getUser();
  const name = user?.full_name || user?.username || 'Account';

  return (
    <View style={{ backgroundColor: C.header, paddingTop: insets.top }}>
      <View style={[s.row, { height: 56, paddingHorizontal: S.gutter, gap: S[3] }]}>
        <View style={[s.row, { gap: S[3], flex: 1 }]} accessibilityRole="header" accessibilityLabel="OcuLubak">
          <View style={{ width: 36, height: 36, borderRadius: 6, backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center' }}>
            <Logo width={28} />
          </View>
          <Text style={{ fontFamily: F.bold, ...T.md, color: '#FFFFFF' }}>OcuLubak</Text>
        </View>
        <Pressable
          onPress={() => setOpen(true)}
          accessibilityRole="button"
          accessibilityLabel={`Account: ${name}, ${roleLabel(user)}`}
          style={({ pressed }) => [{
            flexDirection: 'row', alignItems: 'center', gap: S[2], minHeight: TAP, paddingHorizontal: S[2],
            borderRadius: R.sm, maxWidth: '55%',
          }, pressed && { backgroundColor: 'rgba(255,255,255,0.08)' }]}
        >
          <Icon name="user-circle" color="#FFFFFF" />
          <View style={{ flexShrink: 1 }}>
            <Text style={{ fontFamily: F.semibold, ...T.sm, color: '#FFFFFF' }} numberOfLines={1}>{name}</Text>
            <Text style={{ fontFamily: F.regular, fontSize: 12, lineHeight: 16, color: C.headerMuted }} numberOfLines={1}>{roleLabel(user)}</Text>
          </View>
          <Icon name="chevron-down" size={16} color="#FFFFFF" />
        </Pressable>
      </View>
      <AccountSheet visible={open} onClose={() => setOpen(false)} name={name} user={user} onSignOut={onSignOut} />
    </View>
  );
}

function AccountSheet({ visible, onClose, name, user, onSignOut }) {
  const [settings, setSettings] = useState(getSettings());
  useEffect(() => onSettings(setSettings), []);

  return (
    <Sheet visible={visible} onClose={onClose} title={name}>
      <View style={{ gap: S[4] }}>
        <View style={{ gap: S[1] }}>
          <Text style={[s.body, { color: C.muted }]}>{roleLabel(user)}</Text>
          <Text style={[s.muted, s.num]}>Server {getServerUrl()}</Text>
        </View>

        <View style={[s.row, { gap: S[4], paddingVertical: S[3], borderTopWidth: 1, borderBottomWidth: 1, borderColor: C.border }]}>
          <View style={{ flex: 1, gap: S[1] }}>
            <Text style={s.fieldLabel}>Upload on Wi-Fi only</Text>
            <Text style={s.fieldHint}>Turn off to upload over mobile data. Survey videos are large.</Text>
          </View>
          <Switch
            value={settings.wifiOnly}
            onValueChange={setWifiOnly}
            accessibilityLabel="Upload on Wi-Fi only"
            trackColor={{ true: C.primary, false: C.borderStrong }}
            thumbColor="#FFFFFF"
            ios_backgroundColor={C.borderStrong}
          />
        </View>

        <View style={{ gap: S[2] }}>
          <Button label="Sign out" icon="logout" block onPress={() => { onClose(); onSignOut(); }} />
          <Text style={s.fieldHint}>Surveys on this phone are kept, and waiting uploads continue after you sign in again.</Text>
        </View>
      </View>
    </Sheet>
  );
}
