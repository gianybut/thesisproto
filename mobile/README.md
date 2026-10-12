# Bantay Kalsada Capture (mobile)

Capture-only companion app for iPhone and Android. It records road survey video and a GPS
track on the same phone, then uploads both to the existing `POST /api/videos/upload`. It
does **no inference**; detection stays on the server (thesis Sec 1.7).

The upload has the same fields the web app sends — `video`, `gps_file` (GPX 1.1),
`time_offset`, `road_name` — so the backend needs no changes and cannot tell where the
files came from.

## Stack

Expo SDK 57 (React Native 0.86, React 19.2), plain JavaScript, no router. Modules:
`expo-camera`, `expo-location` + `expo-task-manager` (background GPS: an Android foreground
service, iOS background location mode), `expo-file-system`, `expo-secure-store`,
`expo-network`, `expo-keep-awake`, `expo-build-properties` (allows plain HTTP to the LAN
server on Android).

## Running it

Background location is not in Expo Go, so the app needs a development build.
**Putting it on an iPhone, step by step: [IPHONE_SETUP.md](IPHONE_SETUP.md).**

```bash
cd mobile
npm install
npx expo lint

# iPhone (needs a Mac with Xcode; a free Apple ID is enough for your own phone)
npx expo run:ios --device     # pick the connected iPhone; first run: trust the developer
                              # certificate in Settings > General > VPN & Device Management

# Android (needs Android Studio / SDK)
npx expo run:android
```

The phone and the Flask server must be on the same network. `backend/run.py` already binds
`0.0.0.0:5000`. Enter `http://<computer's LAN IP>:5000` as the server address on the login
screen; it is remembered. iOS asks for "Local Network" access the first time.

A free Apple ID signs builds for 7 days. After that, the app stops opening until it is
rebuilt with `npx expo run:ios --device`. Recordings stored in the app survive the rebuild.

## How it works

| File | Role |
|---|---|
| `src/auth.js` | Login, JWT in SecureStore, any 401 (expired, invalid) → back to login with recordings and queue kept. |
| `src/locationTask.js` | Background GPS task; appends each fix to `points.jsonl` as it arrives. |
| `src/gpx.js` | GPX 1.1 writer, stale-fix filter and the `time_offset` calculation. No Expo imports, so it runs under Node. |
| `src/capture.js` | After stop: moves the video out of the camera cache, checks it is complete, builds the GPX, stores the session. |
| `src/api.js` | The upload: `XMLHttpRequest` on Android, a streamed file upload on iOS (see below). |
| `src/platform.js` | Everything that differs by platform, in one place. |
| `src/mp4.js`, `src/multipart.js` | Movie completeness check and the iOS request body. Pure, tested under Node. |
| `src/uploadQueue.js` | One upload at a time, backoff 15 s → 30 s → 60 s …, five tries before manual retry, Wi-Fi-only switch. |
| `src/storage.js` | Session list in `documents/sessions.json`; files in `documents/sessions/<id>/` (`<id>.mov`/`.mp4`, `<id>.gpx`, `thumb.jpg`; sessions recorded before this naming have `video.*`/`track.gpx`). Files are kept after upload until the session is deleted. |
| `src/media.js` | List thumbnails (`expo-video-thumbnails`, one at a time, made on first view), Save to Photos (`expo-media-library`, add-only) and the share sheet for the video and GPX (`expo-sharing`). |
| `src/screens/PreviewScreen.js` | Plays a stored session (`expo-video`, native controls, muted) and offers the copy-out actions above; works for uploaded sessions too. |

**Starting a recording.** The record button stays disabled until a fresh fix (under 5 s
old) is within ±20 m (`MIN_FIX_ACCURACY_M`). This is a requirement, not a preference.
`interpolate_gps` clamps anything before the first track point to that point's position,
so a segment recorded before the first fix would be placed wrongly rather than left
without a position. A cached last-known fix handed over when logging starts is dropped
from the track (`dropStalePoints`).

**`time_offset`.** The backend computes `gps_time = video_time + time_offset`, with GPX time
counted from the first track point (`backend/services/gps_service.py`). The app sends

```
time_offset = (video_start_device − clock_skew) − first_fix_time
clock_skew  = median over all fixes of (device receipt time − fix timestamp)
```

GPX times are the fix timestamps. The skew term moves the device-clock video start onto
that clock. The GPX `<metadata><extensions><bk:capture …/>` records these for the write-up:
platform and OS version, location permission level, offset, skew, achieved sample rate,
GPS error count, stale fixes dropped and video container.

**Checks on a finished recording.** The app confirms the movie has its `moov` index, which
the camera writes last. A file cut off without one is accepted by the server and then
fails to process (OpenCV reads 0 frames), so the app marks it failed and doesn't upload it.

**Limits** (`src/config.js`, each under the backend's): 590 s maximum (backend rejects
> 600 s), no size cap for now (`MAX_VIDEO_BYTES = null`; backend `MAX_CONTENT_LENGTH` is off too),
1080p H.264 at 5 Mbit/s with no audio (estimated ~37 MB/min). Recording won't start with
less than 2 GB free (544 MB while the size cap was on).

**Queue.** Sessions are `recorded → queued → uploading → uploaded`, or `failed`. The queue is
saved to disk, and on launch an interrupted upload goes back to `queued`. Upload pauses
while recording. A 401 leaves the session queued and returns to login; it resumes after
login. A 400 or 413 from the server fails straight away, because a retry would be
rejected the same way.

## Platform differences

Report which platform a survey came from; the GPX metadata records it on every track.
Items marked *from source* were read from the native module code. They are not yet
observed on a device and must be confirmed in the device tests below.

| | Android | iOS |
|---|---|---|
| **Screen lock / app switch** | Video ends: `expo-camera` stops the camera. Session labelled `app_left_foreground`. | **Same:** video ends. `expo-camera` calls `session.stopRunning()` when the app is backgrounded, and iOS does not let third-party iPhone apps use the camera in the background. *From source.* |
| **Therefore** | A session is only as long as its video on both platforms. Neither can record survey video with the screen off; the app keeps the screen awake while recording. This is a system limitation for Scope and Limitations, not a platform quirk. | ← |
| **Background GPS** | Foreground service with a persistent notification. Needs "While using" only. | `UIBackgroundModes: location`. Updates started in the foreground continue in the background with "While Using" (blue status-bar pill). "Always" is requested once and not required. Its only extra is letting iOS relaunch the app after terminating it, which cannot save a session whose video has already stopped. |
| **GPS sampling rate** | Requested at 1 s (`timeInterval`). | **Not settable:** iOS ignores `timeInterval`; the rate is whatever Core Location delivers at best-for-navigation accuracy, typically about 1 Hz. *From source.* Report `achievedHz` per session. |
| **Video file** | `.mp4`, H.264 (MediaRecorder). | `.mov` (QuickTime), H.264 forced with `codec: 'avc1'`. Without that, current iPhones write HEVC and ignore the bitrate. Uploaded as `.mov`, which the backend accepts. |
| **Recovery when the camera stops badly** | Not needed so far. | If AVFoundation reports the stop as a failure, `expo-camera` rejects without giving a file path. The app then looks in the camera cache for the recording and keeps it only if it is complete. |
| **Upload transport** | `XMLHttpRequest`, streams from disk. | RN's iOS networking would hold the whole body in RAM (RCTNetworking.mm). The app writes the multipart body to a file and streams it with a native upload task. This needs a temporary copy of the video on disk (checked before starting). |
| **Uploads when app is backgrounded** | Stop; retried from zero. | Same, deliberately (`sessionType: 'foreground'`). A background session would keep going, but if iOS then killed the app the queue would upload the survey again, creating a duplicate. |
| **Free space check** | `Paths.availableDiskSpace`. | `getFreeDiskStorageAsync` (important-usage capacity). `Paths.availableDiskSpace` reads `.systemFreeSize`, which leaves out purgeable space and can be gigabytes too low. |
| **Copying a session off the phone** | Save to gallery asks for media permission (`READ_MEDIA_VIDEO` on Android 13+). Share sheet takes `mimeType`. | Save to Photos asks for add-only access (`NSPhotoLibraryAddUsageDescription`); the app never requests read access to the library. Share sheet takes a UTI: `com.apple.quicktime-movie` for `.mov`, `public.xml` for GPX. "Save to Files" is in the share sheet. |
| **Microphone prompt** | `RECORD_AUDIO` blocked; never asked. | Recording is muted, but `expo-camera` may briefly add an audio input before `mute` applies. The usage string is kept so that cannot crash the app; iOS may show a microphone prompt, and either answer is fine. |

Checked on the development Mac (no phone test yet): lint, both JS bundles, and an iOS prebuild
whose generated Info.plist has the background mode and every usage string. The native iOS
compile has **not** been run: that Mac lacks Xcode's iOS platform component. The following
were run against the real backend code. An iPhone-style H.264 `.mov`
and an HEVC `.mov`, each sent as the exact iOS multipart body, were both accepted (201).
OpenCV decoded every frame of both. A truncated `.mov` is flagged by the completeness check.

## Device tests (real phone; the simulator has no GPS, camera or heat)

- [ ] `npx expo run:ios --device` installs and opens on a physical iPhone.
- [ ] Full 590 s session in a moving vehicle; note `achievedHz` and gaps from the Sessions list / GPX.
- [ ] Lock the screen mid-session: confirm video ends, the session is saved as `app_left_foreground`, and GPS logged right up to the stop.
- [ ] GPX opens in a viewer (GPXSee) and the track matches the road.
- [ ] Upload accepted, processed end-to-end, detections placed on the web map.
- [ ] Turn Wi-Fi off mid-upload: the session retries and completes.
- [ ] Expired token (set `JWT_EXPIRY_HOURS=0.01` on the server) returns to login with recordings kept.
- [ ] **Thermal:** windshield mount, screen on, full session at midday. Note throttling, the
      iOS "temperature" warning screen, or recording stopping. Chapter 2 argues from thermal
      throttling, so a capture failure here is material.
- [ ] **Video start gap:** film a running stopwatch that shows milliseconds. Compare the
      time in the first frame with `videoStart` in the GPX metadata. The difference is the
      measured gap for Chapter 3.
- [ ] File size per minute at 1080p / 5 Mbit/s (Sessions list shows size and length).
- [ ] Thumbnail appears for each session; preview plays; Save to Photos, Share video → Save to Files and Share GPX all work on an uploaded session.
- [ ] Repeat the vehicle, lock and upload checks on Android to confirm no regression.

## Checking the pure modules

```bash
node scripts/check-gpx.mjs /tmp/sample.gpx               # synthetic drive: a gap, a duplicate and a stale cached fix
xmllint --noout --schema gpx.xsd /tmp/sample.gpx         # gpx.xsd from topografix.com/GPX/1/1/
node scripts/check-upload-body.mjs video.mov /tmp/sample.gpx /tmp/body.bin   # atoms + the iOS request body
```
