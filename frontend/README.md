# Pothole Detection Frontend — React + Vite

Premium dark-themed user interface for the Pothole Detection System. Built with React 19, Vite, React Router, and Axios.

## Features

- 🎨 **Premium UI Design** — Dark theme with glassmorphism cards
- 🔐 **Authentication** — Login/register system for LGU users
- 📤 **Video Upload** — Drag-and-drop with progress tracking
- 📹 **Detection Viewer** — Play annotated videos with clickable detection timeline
- 📊 **Dashboard** — Real-time statistics and recent activity
- 📋 **Video Library** — Browse and manage all uploaded videos
- 🔄 **Live Status Updates** — Auto-refresh detection progress
- 📱 **Responsive Design** — Works on desktop and tablet

## Quick Start

### Prerequisites

- Node.js 16+ and npm
- Backend running at `http://localhost:5000`

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

Frontend will start at: **`http://localhost:5173`**

### Production Build

```bash
npm run build
npm run preview
```

---

## Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/
│   │   └── Navbar.jsx     # Navigation bar
│   ├── pages/
│   │   ├── LoginPage.jsx          # Login/register
│   │   ├── DashboardPage.jsx      # Statistics & overview
│   │   ├── UploadPage.jsx         # Video upload form
│   │   ├── VideoListPage.jsx      # Video library
│   │   └── DetectionViewerPage.jsx # Video playback with detections
│   ├── api.js             # Axios API client
│   ├── App.jsx            # Main app with routing
│   ├── index.css          # Premium styling
│   └── main.jsx           # React entry point
├── index.html             # HTML template
├── package.json           # Dependencies
├── vite.config.js         # Vite configuration
└── README.md              # This file
```

---

## Pages

### 1. **LoginPage** (`/`)
- Dual-mode: login & registration
- Session management with localStorage
- Default credentials for testing:
  - Username: `admin`
  - Password: `admin123`

### 2. **DashboardPage** (`/`)
- Overview statistics:
  - Total videos uploaded
  - Total potholes detected
  - Average confidence score
  - Total video duration processed
- Quick action buttons
- Recent videos list
- Auto-refresh every 5 seconds

### 3. **UploadPage** (`/upload`)
- Drag-and-drop video upload
- File validation
- Real-time upload progress
- Success notification with direct link to viewer

### 4. **VideoListPage** (`/videos`)
- Grid view of all videos
- Display metadata (duration, file size, status)
- Detection count badges
- Processing progress bars
- Delete with confirmation
- Click to view detections
- Auto-refresh every 5 seconds

### 5. **DetectionViewerPage** (`/videos/:id`)
- Video player (original or processed with bounding boxes)
- Detection timeline sidebar
  - Click to jump to timestamp
  - Confidence score visualization
  - Frame number reference
- Processing progress indicator
- Metadata display (resolution, FPS)
- Loading states with spinners

---

## Components

### **Navbar** (`components/Navbar.jsx`)
- Logo with brand name
- Navigation links (Dashboard, Upload, Videos)
- User info (LGU name)
- Logout button
- Sticky positioning

---

## API Integration

All API calls handled via `src/api.js`:

```javascript
// Authentication
authAPI.login(username, password)
authAPI.register({ username, password, full_name, lgu_name })
authAPI.me()
authAPI.logout()

// Videos
videosAPI.upload(formData, onProgress)
videosAPI.list()
videosAPI.get(id)
videosAPI.delete(id)
videosAPI.streamUrl(id)
videosAPI.processedUrl(id)

// Dashboard
dashboardAPI.stats()

// Detections
detectionsAPI.getForVideo(videoId)
```

Authentication token automatically added to all requests via axios interceptor.

---

## Styling

### Design System

- **Color Scheme:** Dark blue with blue/teal accents
- **Typography:** Inter font family
- **Components:** Glassmorphism cards with blur effects
- **Animations:** Smooth transitions and fade-ins

### CSS Variables

```css
--bg-primary: #0a0e1a;
--text-primary: #f1f5f9;
--accent: #3b82f6;
--success: #10b981;
--warning: #f59e0b;
--danger: #ef4444;
```

All styles in `src/index.css` (600+ lines)

---

## Development

### Scripts

```bash
npm run dev       # Start dev server (Vite)
npm run build     # Build for production
npm run lint      # Run ESLint
npm run preview   # Preview production build
```

### Hot Module Replacement (HMR)

Vite automatically reloads changes during development.

### Debugging

- React DevTools browser extension recommended
- Check browser console for API errors
- Network tab to inspect API requests

---

## Configuration

### Backend URL

Edit `src/api.js` to change backend:

```javascript
const API_BASE = 'http://localhost:5000/api';
```

### Vite Config

`vite.config.js`:

```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false
  }
})
```

---

## Troubleshooting

### Frontend won't start

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### API connection errors

1. Check backend is running: `http://localhost:5000/api`
2. Verify API_BASE in `src/api.js`
3. Check CORS is enabled in backend
4. Look at browser console for error details

### Videos not loading

- Ensure backend is serving video files
- Check network tab for 404 errors
- Verify processed videos exist in `backend/processed/`

### Styling issues

- Clear browser cache (Ctrl+Shift+Delete)
- Check CSS variables in `:root`
- Verify all CSS classes are applied correctly

---

## Performance Tips

1. **Lazy Load:** Videos are streamed, not embedded
2. **Auto-refresh:** Dashboard and video list refresh every 5 seconds
3. **Progress Bars:** Show upload and processing progress
4. **Responsive:** Optimized for desktop and tablet
5. **Smooth:** CSS animations and transitions for UX

---

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 15+
- Opera 76+

Requires modern JavaScript (ES2020+)

---

## Production Deployment

### Build

```bash
npm run build  # Creates dist/ folder
```

### Serve

```bash
# Using static server
npx serve -s dist

# Using Node/Express
const express = require('express');
const app = express();
app.use(express.static('dist'));
app.listen(3000);
```

### Environment Variables

Create `.env.production`:

```
VITE_API_BASE=https://api.yourdomain.com
```

Access via `import.meta.env.VITE_API_BASE`

---

## Contributing

To add new pages:

1. Create `src/pages/NewPage.jsx`
2. Import in `src/App.jsx`
3. Add route: `<Route path="/new" element={<NewPage />} />`
4. Add navbar link in `components/Navbar.jsx`

---

## Dependencies

### Runtime

- **react** 19.2.5 — UI library
- **react-dom** 19.2.5 — React DOM renderer
- **react-router-dom** 7.14.1 — Client-side routing
- **axios** 1.15.1 — HTTP client

### Dev Tools

- **vite** 8.0.9 — Build tool
- **@vitejs/plugin-react** 6.0.1 — React plugin
- **eslint** 9.39.4 — Code linting

---

## Version Info

- **Frontend Version:** 1.0
- **React:** 19.x
- **Vite:** 8.x
- **Node:** 16+

---

## Support

For issues:
1. Check backend is running
2. Review browser console for errors
3. Check network tab for API calls
4. Review backend logs
5. Test with cURL: `curl http://localhost:5000/api/auth/me`

---

**🎨 Premium UI for Pothole Detection System**

Built with React + Vite for fast, modern development.
