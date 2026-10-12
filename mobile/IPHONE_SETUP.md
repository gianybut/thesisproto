# Setting up Bantay Kalsada Capture on an iPhone

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

**Use `--configuration Release` for survey work.** A Debug build (the command without
`--configuration Release`) loads its code from the Mac over Wi-Fi each time it opens, so it
does not work in a car. Debug is only for changing the app while sitting at the Mac.

If the build complains about **signing** or **"No code signing certificates"**:

1. Open `mobile/ios/BantayKalsadaCapture.xcworkspace` in Xcode.
2. Click the **BantayKalsadaCapture** project at the top of the file list, then the
   **BantayKalsadaCapture** target and the **Signing & Capabilities** tab.
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
     turn it on in **Settings › Bantay Kalsada Capture › Local Network**.
   - **Microphone:** may appear even though videos are silent. Either answer is fine.

## 5. Connect to the server

1. Start the backend on the server computer (`./start_backend.sh` or `start_backend.bat` from the repo root).
2. Find that computer's address on the Wi-Fi:
   - Mac: `ipconfig getifaddr en0`
   - Windows: `ipconfig`, then the *IPv4 Address* of the Wi-Fi adapter.
3. On the phone's login screen, enter `http://<that address>:5000` as the server address,
   for example `http://192.168.1.23:5000`. Then enter your username and password; the
   address is remembered.

The phone and server must be on the **same Wi-Fi** to log in and upload. Recording does
not need a connection.

## 6. Recording a survey

1. Mount the phone on the windshield in landscape, camera facing the road, with a charger
   connected.
2. Open the app. Wait until the top bar shows GPS within ±20 m. The **Start recording**
   button stays grey until then; being under open sky helps.
3. Tap **Start recording**. Leave the app on screen and **do not lock the phone**: iOS
   stops the camera when the app leaves the screen, and the recording ends there. The app
   keeps the screen from sleeping on its own.
4. Recording stops by itself at 9:50. Tap **Stop recording** earlier if you like.
5. Enter the road name, then tap **Queue for upload** or **Keep on phone for now**.

## 7. Uploading

Back on the server's Wi-Fi, open the app and go to **Recorded sessions**. Queued sessions
upload one at a time, and failed uploads retry by themselves. Keep the app open while it
uploads: iOS pauses uploads when the app is in the background. The **Upload on Wi-Fi only**
switch is on by default so a 350 MB video doesn't use mobile data. Uploading needs free
space about the size of the video for a temporary copy.

Logins last 12 hours. After that, the app returns to the login screen; your recordings and
queue are kept and resume after you log in.

## 8. Every 7 days: rebuild

Apps signed with a free Apple ID stop opening after 7 days. Connect the phone and run the
build command from step 3 again. Recordings already in the app are kept. A free Apple ID
can also keep only 3 of your own apps on a phone at a time.

## Troubleshooting

| What you see | What to do |
|---|---|
| Build: "iOS xx.x is not installed" | Step 1.2: install the iOS platform in Xcode › Settings › Components. |
| Build: signing / certificate / provisioning errors | Step 3: set your Personal Team in Xcode once. |
| Xcode doesn't list the iPhone | Unlock the phone, re-plug the cable, tap Trust, and check Developer Mode (step 2). |
| App won't open, "Untrusted Developer" | Step 4.1. |
| App won't open after about a week | Rebuild (step 8). |
| Login: "Could not reach …" | Check the phone is on the server's Wi-Fi and that the address and `:5000` are right. Check Local Network is allowed (step 4.2) and the backend is running. On the server computer, allow Python through the firewall. |
| Server is a Mac and login returns an odd 403 | macOS AirPlay Receiver also uses port 5000. Turn it off in **System Settings › General › AirDrop & Handoff › AirPlay Receiver**. |
| Start recording stays grey | GPS isn't within ±20 m yet. Move to open sky and wait a minute. |
| "Not enough free space" | Needs 2 GB free to record (`MIN_FREE_BYTES` in `src/config.js`); free up storage. |
| Recording stopped by itself early | The app left the screen (lock, call, app switch). The session keeps what was recorded and says so. |
| Debug build shows a red "No bundle URL" screen | That's a Debug build away from the Mac. Rebuild with `--configuration Release`. |

For what each part does, the iPhone/Android differences, and the tests to run before
survey data counts for the thesis, see [README.md](README.md).
