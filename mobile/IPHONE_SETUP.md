# Setting up OcuLubak on an iPhone

The capture app is not on the App Store, so it is built on a Mac and installed on each
phone over a cable. One Mac and one Apple ID can install it on all three team phones.
Allow about an hour the first time, most of it downloads.

> This procedure has not yet been run end to end on a team iPhone. If a step does not
> match what you see, note what happened and update this file.

## What you need

- A Mac with **Xcode** (App Store, free) and about 30 GB free disk.
- An **Apple ID**. A free one is enough; no paid developer account.
- The **iPhone** and its USB cable.
- The **computer running the backend**, reachable on the same Wi-Fi as the phone when you
  upload. It can be the same Mac.

## 1. One-time Mac setup

1. Install Xcode, open it once, and accept the licence.
2. Install the iOS platform: **Xcode › Settings › Components** (called *Platforms* in
   older Xcode), then download **iOS**. Without it, the build stops with "iOS xx.x is not
   installed". The version must cover the iPhone's iOS version.
3. Add your Apple ID: **Xcode › Settings › Accounts › +**, then choose **Apple ID**. It
   appears as a team named "*Your Name* (Personal Team)".
4. Install the command-line tools:

   ```bash
   xcode-select --install                 # skip if already installed
   brew install node cocoapods            # Node 20 or newer; https://brew.sh for Homebrew
   ```

5. Get the code and install the app's packages:

   ```bash
   git clone <repo url> thesisproto       # or git pull if you have it
   cd thesisproto/mobile
   npm install
   ```

## 2. One-time iPhone setup

1. Connect the iPhone to the Mac with the cable. Unlock it and tap **Trust** when asked.
2. In Xcode, open **Window › Devices and Simulators**. Wait while it says "Preparing
   device for development"; the first time can take several minutes.
3. On the iPhone, turn on **Developer Mode**: **Settings › Privacy & Security › Developer
   Mode**. The phone restarts; after it does, confirm **Turn On**. The switch only appears
   after step 1–2.

## 3. Build and install

From `thesisproto/mobile`, with the iPhone connected and unlocked:

```bash
npx expo run:ios --device --configuration Release
```

Pick the iPhone from the list. The first build takes 10–20 minutes; later ones are faster.

**After pulling a change to `app.json` or to the native packages** (for example the
OcuLubak redesign, which added `react-native-svg` and `react-native-safe-area-context` and
renamed the app), regenerate the native project first, then build as above:

```bash
npx expo prebuild --platform ios --clean
```

`mobile/ios` is generated and gitignored, so nothing is lost, but `--clean` resets signing:
do the signing steps below once more. Recordings on the phone are kept, because the bundle
identifier does not change.

**Use `--configuration Release` for survey work.** A Debug build (the command without
`--configuration Release`) loads its code from the Mac over Wi-Fi each time it opens, so it
does not work in a car. Debug is only for changing the app while sitting at the Mac.

If the build complains about **signing** or **"No code signing certificates"**:

1. Open `mobile/ios/OcuLubak.xcworkspace` in Xcode (`BantayKalsadaCapture.xcworkspace` if
   the folder was generated before the rename).
2. Click the **OcuLubak** project at the top of the file list, then the **OcuLubak** target
   and the **Signing & Capabilities** tab.
3. Tick **Automatically manage signing** and set **Team** to your Personal Team.
4. Close Xcode and run the command again.

If it says the **bundle identifier is not available**, someone else's Apple ID has already
registered `com.bantaykalsada.capture`. That happens when two teammates each build with
their own Apple ID. Fix it by building every phone from the same Mac and Apple ID. If you
must use a different Apple ID, change `ios.bundleIdentifier` in `app.json` to something
unique, for example `com.yourname.bantaykalsada`. Then delete the `mobile/ios` folder and
build again. A new identifier installs as a separate app, so recordings in the old one do
not move across.

To install on the next team phone, connect it, do step 2 on that phone, and run the same
command.

## 4. First launch on the phone

1. Tap the app. iOS says **Untrusted Developer**. Go to **Settings › General › VPN &
   Device Management**, tap your Apple ID under *Developer App* and tap **Trust**. Open the
   app again.
2. Allow the permissions it asks for:
   - **Camera:** Allow.
   - **Location:** **Allow While Using App**. It then asks whether to **Change to Always
     Allow**; choose it if you like. The app works with either, and each recording notes
     which one was set.
   - **Local Network:** **Allow**. It is needed to reach the server. If you refused it,
     turn it on in **Settings › OcuLubak › Local Network**.
   - **Microphone:** may appear even though videos are silent. Either answer is fine.

   If Camera or Location was refused, the app lists what is missing, with an **Open
   Settings** button. Turn them on there and switch back; the camera opens without a restart.

## 5. Connect to the server

1. Start the backend on the server computer (`./start_backend.sh` or `start_backend.bat` from the repo root).
2. Find that computer's address on the Wi-Fi. The easiest way: sign in to the web app on that
   computer; the **Overview** page has a **Connect a phone** panel with the address (press
   **Show**, or **Copy**). Or look it up:
   - Mac: `ipconfig getifaddr en0`
   - Windows: `ipconfig`, then the *IPv4 Address* of the Wi-Fi adapter.
3. On the phone's sign-in screen, enter `http://<that address>:5000` as the server address,
   for example `http://192.168.1.23:5000` (`http://` may be left out). Then enter your
   username and password and tap **Sign in**. The address is remembered; tap **Change**
   beside it to use another server.

The phone and server must be on the **same Wi-Fi** to sign in and upload. Recording does
not need a connection.

## 6. Recording a survey

1. Mount the phone on the windshield in landscape, camera facing the road, with a charger
   connected.
2. Open the app. Wait until the GPS label at the top turns green with a tick (within
   ±20 m). The **Start recording** button stays dimmed until then, and the line above it
   says why; being under open sky helps.
3. Tap **Start recording**. Leave the app on screen and **do not lock the phone**: iOS
   stops the camera when the app leaves the screen, and the recording ends there. The app
   keeps the screen from sleeping on its own.
4. Recording stops by itself at 9:50. Tap **Stop recording** earlier if you like.
5. Enter the road name, then tap **Upload this survey** or **Keep on this phone for now**.

## 7. Uploading

Back on the server's Wi-Fi, open the app and tap **Surveys on this phone** under the record
button. Surveys waiting to upload go one at a time, and failed uploads retry by themselves.
Keep the app open while it uploads: iOS pauses uploads when the app is in the background.
After upload each survey follows the analysis on the server, as the web app does:
*Waiting to start*, *Analysing n%*, then *Ready* with the number of damages found.

**Upload on Wi-Fi only** is on by default so a 350 MB video doesn't use mobile data. It is
in the account panel (tap your name at the top right). While a survey is waiting for Wi-Fi,
the survey list also offers **Upload over mobile data**. Uploading needs free space about
the size of the video for a temporary copy.

Sign-ins last 12 hours (`JWT_EXPIRY_HOURS` on the server). After that the app keeps working:
you can still record and see your surveys, and the header shows **Sign in** instead of your
name. Surveys wait on the phone and upload once you sign in again. The sign-in screen only
appears by itself the first time, to set the server address; after that it has **Record
without signing in**.

## 8. Every 7 days: rebuild

Apps signed with a free Apple ID stop opening after 7 days. Connect the phone and run the
build command from step 3 again. Recordings already in the app are kept. A free Apple ID
can also keep only 3 of your own apps on a phone at a time.

## Troubleshooting

| What you see | What to do |
|---|---|
| Build: "iOS xx.x is not installed" | Step 1.2: install the iOS platform in Xcode › Settings › Components. |
| Build: signing / certificate / provisioning errors | Step 3: set your Personal Team in Xcode once. |
| Build succeeds, then install fails with `ApplicationVerificationFailed` | Run `xcrun devicectl device install app --device <id> <path to OcuLubak.app>` to see the reason. If it names an unsigned framework (`hermesvm.framework`, `React.framework` …), an earlier Debug build left stale copies. Delete `~/Library/Developer/Xcode/DerivedData/OcuLubak-*` and `mobile/ios/build`, run `pod install` in `mobile/ios` (it regenerates `ios/build`), then build again. |
| Xcode doesn't list the iPhone | Unlock the phone, re-plug the cable, tap Trust, and check Developer Mode (step 2). |
| App won't open, "Untrusted Developer" | Step 4.1. |
| App won't open after about a week | Rebuild (step 8). |
| App still shows the old name or icon | The native project predates the change. Run `npx expo prebuild --platform ios --clean` (step 3), then build. |
| Sign in: "Could not reach …" | Check the phone is on the server's Wi-Fi and that the address and `:5000` are right. Check Local Network is allowed (step 4.2) and the backend is running. On the server computer, allow Python through the firewall. |
| Server is a Mac and sign-in returns an odd 403 | macOS AirPlay Receiver also uses port 5000. Turn it off in **System Settings › General › AirDrop & Handoff › AirPlay Receiver**. |
| Start recording stays dimmed | The line above it says why: usually GPS isn't within ±20 m yet. Move to open sky and wait a minute. |
| "Not enough free space" | Needs 2 GB free to record (`MIN_FREE_BYTES` in `src/config.js`); free up storage. |
| Recording stopped by itself early | The app left the screen (lock, call, app switch). The survey keeps what was recorded and says so. |
| Debug build shows a red "No bundle URL" screen | That's a Debug build away from the Mac. Rebuild with `--configuration Release`. |

For what each part does, the iPhone/Android differences, and the tests to run before
survey data counts for the thesis, see [README.md](README.md).
