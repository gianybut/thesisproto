# Installing OcuLubak on an iPhone

The app is not on the App Store. It is built on a Mac and installed over a USB cable.
One Mac and one Apple ID can install it on every team phone.

## You need

- A Mac with **Xcode** (App Store) and ~30 GB free.
- An **Apple ID** (a free one is enough).
- The **iPhone** and its cable.

## 1. Set up the Mac (once)

1. Open Xcode once and accept the licence.
2. **Xcode › Settings › Components**: download **iOS**.
3. **Xcode › Settings › Accounts › +**: add your Apple ID.
4. In Terminal:

   ```bash
   xcode-select --install          # skip if already installed
   brew install node cocoapods     # needs Homebrew: https://brew.sh
   cd thesisproto/mobile
   npm install
   ```

## 2. Set up the iPhone (once)

1. Plug it in, unlock it, tap **Trust**.
2. On the phone: **Settings › Privacy & Security › Developer Mode › On**. It restarts; confirm **Turn On**.

## 3. Build and install

From `thesisproto/mobile`, with the phone plugged in and unlocked:

```bash
npx expo prebuild --platform ios --clean
npx expo run:ios --device --configuration Release
```

Pick the iPhone from the list. The first build takes 10–20 minutes.

- Always use `--configuration Release`. Without it the app loads its code from the Mac and
  shows a blank or red screen anywhere else.
- `prebuild --clean` is only needed after pulling changes to `app.json` or `package.json`,
  but it is safe to run every time. Recordings on the phone are kept.

Then on the phone: **Settings › General › VPN & Device Management › your Apple ID › Trust**,
and open the app. Allow **Camera**, **Location** and **Local Network**.

Free Apple ID apps stop opening after **7 days**. Plug in and run the build command again.

## 4. Connect to the server

1. Start the backend on the server computer (`./start_backend.sh` or `start_backend.bat`).
2. In the web app, **Overview › Connect a phone › Show** gives the address.
3. On the phone's sign-in screen, enter it (e.g. `192.168.1.23:5000`) with your username and password.

The phone must be on the **same Wi-Fi** as the server to sign in and upload. Recording works offline:
tap **Record without signing in** to skip this step, and sign in later (header › **Sign in**) to upload.

## 5. Recording

1. Mount the phone in landscape facing the road, on a charger.
2. Wait for the GPS label to turn green. Drag **Horizon** to where the road ends and **Bonnet** to
   the top of the car's bonnet. Damage is only looked for between the two lines. They are
   remembered, so this is needed again only when the mount moves.
3. Tap **Start recording**. **Do not lock the phone or switch apps**; that stops the recording.
   There is no time limit: every 9:50 the video is saved as a part and the next part starts by itself.
4. Enter the road name, then **Upload this survey** or keep it for later
   (**Surveys on this phone** uploads it when you are back on the server's Wi-Fi).

## Problems

| Problem | Fix |
|---|---|
| Signing / certificate error | Open `ios/OcuLubak.xcworkspace` in Xcode › **OcuLubak** target › **Signing & Capabilities**: tick *Automatically manage signing*, pick your team. Or set `ios.appleTeamId` in `app.json` to your team ID. |
| "Bundle identifier is not available" | Another Apple ID registered it. Build from the same Mac and Apple ID, or change `ios.bundleIdentifier` in `app.json`. |
| Install fails with `ApplicationVerificationFailed` | `rm -rf ~/Library/Developer/Xcode/DerivedData/OcuLubak-* ios/build`, then build again. |
| App opens to a blank white screen | It was a Debug build, or an old build. Run both commands in step 3 again. |
| App won't open after a week | Rebuild (step 3). |
| "Could not reach …" when signing in | Same Wi-Fi? Address and `:5000` right? Local Network allowed (Settings › OcuLubak)? Backend running? On a Mac server, turn off **AirPlay Receiver** (it uses port 5000). |
| Start recording stays dimmed | The line above it says why, usually weak GPS. Move to open sky. |

More detail on the app: [README.md](README.md).
