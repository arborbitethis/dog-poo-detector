# Dog Poop Detector

Computer vision system that monitors your backyard via RTSP/IP camera to detect and track dog defecation events in real-time.

## 🎯 Project Status

### ✅ Implemented (v0.1)

- **Modern React Dashboard**: Built with React + Vite, component-based architecture
- **Real-time WebSocket Updates**: Live metrics, alerts, and poop tracking with auto-reconnect
- **Backend Processing Pipeline**: FastAPI server with YOLO detection, event tracking, state management
- **Demo Simulation**: Full workflow demonstration with static image
- **Frame Annotation**: Live video feed with bounding boxes, poop markers, age timers
- **IoU-based Tracking**: Persistent poop instance tracking across frames
- **Cleanup Detection**: Human proximity + disappearance confirmation
- **One-Command Startup**: Scripts to run both servers together
- **Development Environment**: Hot reload, proxy configuration, clean separation

### 🚧 In Progress / TODO

- **Custom YOLO Model**: Train poop detection model (currently using pretrained COCO)
- **Live RTSP Integration**: Connect to actual IP camera stream (currently demo mode)
- **Production Build**: Optimize and bundle frontend for deployment
- **Notification System**: Email/SMS/push notifications for alerts
- **Historical Data**: Database storage for metrics and events
- **Settings UI**: Dashboard configuration panel
- **Mobile App**: React Native companion app
- **Multi-camera Support**: Handle multiple camera feeds

## Features

- **Real-time Detection**: Uses YOLOv8x to detect dogs, poop, and cleanup events
- **Persistent Tracking**: Maintains state of each poop instance from detection to cleanup
- **Modern Web Dashboard**: React-based interface with live video feed and real-time alerts
- **Smart Detection**: Identifies pooping behavior using posture heuristics
- **Cleanup Tracking**: Detects when humans pick up poop
- **Live Alerts**: WebSocket-powered real-time notifications

## Quick Start

### Option 1: One-Command Startup (Recommended)

Run both backend and frontend together:

```bash
python start.py
# or
./start.sh
```

This will:
- ✅ Check dependencies
- ✅ Start backend server (port 8080)
- ✅ Start frontend dev server (port 5173)
- ✅ Run demo simulation with your backyard image
- ✅ Open dashboard at **http://localhost:5173**

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```bash
pip install -r requirements.txt
python demo.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Open:** http://localhost:5173

### Stopping the Servers

Press **`Ctrl+C`** in the terminal to stop all servers. The startup script automatically cleans up both backend and frontend processes.

If processes don't stop:
```bash
pkill -f "demo.py"
pkill -f "vite"
```

### Option 3: Production Mode

```bash
# Build frontend
cd frontend && npm run build && cd ..

# Start backend (serves built frontend)
python backend/main.py
```

**Open:** http://localhost:8080

## Dashboard Features

- **Live Video Feed**: Annotated camera view with bounding boxes and poop markers
- **Real-time Metrics**: Active, Pending, Cleaned, and Total counts
- **Active Poops List**: Each poop with age timer and location
- **Alert Log**: Chronological event history
- **WebSocket Status**: Connection indicator

## Configuration

Edit `config/config.yaml` to customize:

- **Stream settings**: RTSP URL, reconnection delay
- **Detection thresholds**: Confidence, inference interval
- **Tracking parameters**: IoU threshold, stale frames
- **Pooping detection**: Stationary time, aspect ratio
- **Web server**: Port, video quality
- **Alerts**: New poop, cleanup, aging threshold

## Project Structure

```
dog-poop-detector/
├── backend/                  # AI/ML Processing
│   ├── main.py               # Entry point for live system
│   ├── capture.py            # RTSP stream handling
│   ├── detector.py           # YOLOv8 inference
│   ├── poop_tracker.py       # Poop instance tracking
│   ├── event_detector.py     # Pooping posture detection
│   ├── state_manager.py      # Alert generation
│   ├── web_server.py         # FastAPI server
│   └── frame_annotator.py    # Video annotation
├── frontend/                 # React Dashboard
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks (WebSocket)
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js        # Dev server + proxy config
├── config/
│   └── config.yaml           # Configuration
├── models/                   # Custom trained models
├── start.py                  # One-command startup script
├── start.sh                  # Shell script alternative
├── demo.py                   # Demo simulation
└── README.md
```

## How It Works

1. **Stream Capture**: Connects to RTSP camera stream
2. **YOLO Detection**: Identifies dogs, poop, and humans
3. **Event Detection**: Recognizes pooping posture (stationary + squatting)
4. **Poop Tracking**: Maintains persistent poop instances with IoU matching
5. **Cleanup Detection**: Identifies when human picks up poop
6. **Web Dashboard**: Displays live feed with annotations and metrics
7. **Real-time Updates**: WebSocket pushes events to browser instantly

## Custom Model Training

For best poop detection accuracy:

1. Collect 200+ images of dog feces in your yard
2. Annotate poop instances
3. Fine-tune YOLOv8x: `yolo train data=poop_dataset.yaml model=yolov8x.pt`
4. Place trained model in `models/` directory
5. Update `config.yaml` to use custom model

## Troubleshooting

**White screen on dashboard?**
- Open browser DevTools (F12) and check Console for errors
- Try hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Verify both servers are running: check ports 8080 and 5173
- Check if Vite compiled successfully in terminal output

**Dashboard not loading?**
- Backend should be on port 8080: http://localhost:8080/api/status
- Frontend should be on port 5173: http://localhost:5173
- Check terminal for startup errors
- Verify Node.js and Python are installed

**Video feed not showing?**
- In demo mode, ensure `IMG_3490.jpeg` exists
- For live camera: Check RTSP stream is accessible
- Verify stream URL in `config/config.yaml`
- Test stream URL directly: `ffplay rtsp://your-camera-ip:554/stream1`
- Try VLC: Media → Open Network Stream → enter RTSP URL

**No detections?**
- Lower `detection.confidence_threshold` in config.yaml
- Check if YOLOv8x model downloaded successfully (first run downloads automatically)
- For poop detection, custom trained model required (see Custom Model Training section)

**WebSocket disconnected?**
- Check browser console for connection errors
- Verify backend is running on port 8080
- Check `config/config.yaml` web_server settings
- Refresh page to reconnect

**Processes won't stop?**
```bash
# Force kill all processes
pkill -f "demo.py"
pkill -f "vite"
pkill -f "start.py"
```
