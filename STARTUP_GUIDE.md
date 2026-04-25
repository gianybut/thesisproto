# 🚀 Pothole Detection System — Startup Guide

Welcome to the Pothole Detection System. This guide provides the exact steps needed to start both the backend server and the frontend web application.

> [!IMPORTANT]
> **Always run the startup scripts from the root directory of the project** (`thesisproto`). Do not navigate into the `backend` or `frontend` folders to run these scripts.

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
