// The GPS task must be defined before the app registers, so Android can wake
// it with fixes while the screen is off.
import './src/locationTask';
import { registerRootComponent } from 'expo';

import App from './App';

registerRootComponent(App);
