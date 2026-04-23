# RoadScan AI — Pothole Detection System for LGUs

A web-based pothole detection system that uses **YOLOv8** to automatically detect potholes in road survey videos uploaded by Local Government Unit (LGU) personnel.

## Features (75% Prototype)

- 🔐 **User Authentication** — Login/Register for LGU inspectors
- 📤 **Video Upload** — Drag-and-drop road survey footage (MP4, AVI, MOV, MKV)
- 🤖 **AI Detection** — YOLOv8 model trained on RDD2022 (D40 pothole class)
- 📦 **Bounding Boxes** — Detected potholes highlighted with color-coded confidence
- ⏱️ **Clickable Timestamps** — Detection log with video seek-to-timestamp
- 📊 **Dashboard** — Aggregate stats (total videos, detections, avg confidence)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite |
| Styling | Vanilla CSS (dark theme, glassmorphism) |
| Backend | Flask + SQLAlchemy (SQLite) |
| ML Model | YOLOv8 (Ultralytics) |
| Video Processing | OpenCV |

## Setup Instructions

### 1. Clone & Install Backend

```bash
git clone <your-repo-url>
cd Prototype

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Frontend

```bash
cd frontend
npm install
```

### 3. Download/Train the Model

If you don't have `ml/models/best.pt`, train the model:

```bash
cd ml
python dataset_prep.py --download       # Generate sample dataset
python train_model.py --epochs 50       # Train YOLOv8
```

Or copy `best.pt` from your shared storage into `ml/models/`.

### 4. Run the Application

**Terminal 1 — Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

**Default login:** `admin` / `admin123`

## Project Structure

```
Prototype/
├── backend/
│   ├── app.py                    # Flask app factory
│   ├── models.py                 # User, Video, Detection models
│   ├── routes/
│   │   ├── auth.py               # Login/Register API
│   │   ├── videos.py             # Video upload/manage API
│   │   └── detections.py         # Detection results & dashboard API
│   └── services/
│       └── video_processor.py    # YOLOv8 inference pipeline
├── frontend/
│   ├── src/
│   │   ├── pages/                # Login, Dashboard, Upload, Videos, DetectionViewer
│   │   ├── components/           # Navbar
│   │   ├── api.js                # Axios API client
│   │   ├── App.jsx               # Router & auth state
│   │   └── index.css             # Design system
│   └── package.json
├── ml/
│   ├── train_model.py            # YOLOv8 training script
│   ├── dataset_prep.py           # RDD2022 dataset preparation
│   ├── convert_rdd2022.py        # RDD2022 format converter
│   ├── data.yaml                 # Dataset config
│   └── models/
│       └── best.pt               # Trained model weights
├── Documents/
│   └── Thesis Paper Chapter 1.pdf
├── requirements.txt
└── .gitignore
```

## Requirements

- Python 3.9+
- Node.js 18+
- ffmpeg (optional, for browser-compatible video encoding)
