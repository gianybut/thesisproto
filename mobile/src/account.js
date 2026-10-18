// Whether this phone is signed in, and the two ways to change that, for any screen that needs
// them (the header's account panel, the survey list). App.js provides the value.
//
// Signed out is a normal state, not a locked app: recording and the survey list keep working,
// and only uploading waits for a sign-in. A sign-in lasts JWT_EXPIRY_HOURS on the server
// (12 h by default), so a phone left signed in overnight is signed out the next time it
// reaches the server; that must never stop anyone from recording a road.
import { createContext, useContext } from 'react';

export const AccountContext = createContext({ signedIn: false, signIn: () => {}, signOut: () => {} });

export const useAccount = () => useContext(AccountContext);
