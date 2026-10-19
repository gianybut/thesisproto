# 🚀 Pothole Detection System — Startup Guide

Welcome to the Pothole Detection System. This guide provides the exact steps needed to start both the backend server and the frontend web application.

> [!IMPORTANT]
> **Always run the startup scripts from the root directory of the project** (`thesisproto`). Do not navigate into the `backend` or `frontend` folders to run these scripts.

## The easy way: install once, then click OcuLubak

You need **Python 3.10–3.12**, **Node.js 20 or newer** and **Git** (with Git LFS; the Mac installer
adds Git LFS through Homebrew if it is missing). Then, in the project folder, double-click:

- **Mac:** `install_mac.command` (if macOS blocks it, right-click › Open). It creates **OcuLubak**
  and **Stop OcuLubak** in your Applications folder and can add OcuLubak to the Dock.
- **Windows:** `install_windows.bat`. It creates **OcuLubak** on the Desktop and in the Start menu,
  and **Stop OcuLubak** in the Start menu.

The installer sets up the Python and website packages and downloads the detection model with
Git LFS. The first run can take 10 minutes or more. After that, clicking **OcuLubak** starts the
server and the website in the background and opens http://localhost:5173. Clicking it again while
it runs just opens the browser. Logs are in the `.oculubak` folder.

- The first time on a Mac, allow OcuLubak to access your Documents folder when asked.
- If every survey's analysis fails at 0%, the model was not downloaded. Run `git lfs pull` in the
  project folder (or the installer again), then choose **Analyse again** on the survey.

The manual steps below still work if you prefer two terminals.

## Step 0: Install ffmpeg (once)

The backend re-encodes every annotated video to browser-playable MP4 with ffmpeg. Without it
the output stays as an AVI that most browsers refuse to play, and the backend prints a warning
at startup.

**Windows:**
```bash
winget install Gyan.FFmpeg
```
**Linux:** `sudo apt-get install ffmpeg` · **Mac:** `brew install ffmpeg`

Open a new terminal afterwards so it is on your PATH, and check with `ffmpeg -version`.

## Step 1: Start the Backend Server

Open a new terminal, navigate to the `thesisproto` root directory, and run the backend startup script:

**Windows:**
```bash
.\start_backend.bat
```

**Linux/Mac:**
```bash
./start_backend.sh
```

Wait until you see the message indicating that the Flask backend server has started on `http://localhost:5000`. Keep this terminal open.

## Step 2: Start the Frontend Application

Open a **second** terminal, navigate to the `thesisproto` root directory, and run the frontend startup script:

**Windows:**
```bash
.\start_frontend.bat
```

**Linux/Mac:**
```bash
./start_frontend.sh
```

This will start the React development server. Keep this terminal open.

## Step 3: Access the Web App

Once both servers are running, open your web browser and navigate to:

👉 **http://localhost:5173**

### Default Login Credentials
- **Username:** `admin`
- **Password:** `admin123`

---

## 🛠️ Troubleshooting

- **Virtual Environment Not Found:** Make sure you have installed the requirements using `pip install -r requirements.txt` in a `.venv` directory at the root of the project.
- **Port Already in Use:** If you see an error about ports `5000` or `5173` being in use, make sure you don't have other instances of the app running in the background. You can close them or use Task Manager / Activity Monitor to kill the processes.
- **Node.js Not Installed:** If the frontend script fails, ensure you have [Node.js](https://nodejs.org/) installed (version 16 or higher).
- **Processed video won't play:** ffmpeg is missing — see Step 0. The backend warns about this at startup.
- **A video is stuck at "processing":** processing runs inside the backend process, so it dies if the backend is stopped. On the next start the backend marks any interrupted video as *failed*; upload it again.
- **Upload rejected as too long:** videos are capped at 10 minutes and 500 MB. Trim the clip and retry.
- **Database column errors after pulling new code:** run `python backend/migrate.py` once (safe to re-run).
