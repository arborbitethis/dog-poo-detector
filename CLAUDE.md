# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Computer vision system that monitors a backyard via RTSP/IP camera to detect and track dog defecation events. Modern full-stack application with React frontend and Python backend using YOLOv8x for object detection.

## Project Structure (v0.1)

```
dog-poop-detector/
├── backend/                  # Python AI/ML Processing
│   ├── main.py               # Entry point for live RTSP mode
│   ├── capture.py            # RTSP stream handling with auto-reconnect
│   ├── detector.py           # YOLOv8x inference (dogs, poop, humans)
│   ├── event_detector.py     # Pooping posture detection (heuristic)
│   ├── poop_tracker.py       # IoU-based instance tracking
│   ├── state_manager.py      # Alert generation logic
│   ├── web_server.py         # FastAPI server (REST + WebSocket)
│   └── frame_annotator.py    # OpenCV frame annotation
├── frontend/                 # React + Vite Dashboard
│   ├── src/
│   │   ├── components/       # Dashboard, VideoFeed, Metrics, etc.
│   │   ├── hooks/            # useWebSocket custom hook
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── vite.config.js        # Proxy to backend API
│   └── package.json
├── config/
│   └── config.yaml           # All system configuration
├── models/                   # Custom YOLO models (future)
├── start.py                  # One-command startup (both servers)
├── demo.py                   # Demo simulation mode
└── README.md
```

## Architecture

### Backend Data Flow
```
RTSP/Image → capture.py → detector.py → event_detector.py → poop_tracker.py → state_manager.py
                              ↓                                        ↓
                        frame_annotator.py ←───────────────────────────┘
                              ↓
                        web_server.py (FastAPI)
                              ↓
                      [WebSocket + REST API]
```

### Frontend Architecture
- **React + Vite**: Modern SPA with hot reload
- **Component-based**: Modular dashboard components
- **WebSocket Client**: Real-time updates via custom hook
- **Proxy Configuration**: Vite proxies `/api`, `/video`, `/ws` to backend:8080

### Poop Lifecycle State Machine
```
[No Poop] → [Pending] → [Active] → [Cleaned]
```
- **Pending**: Dog detected in pooping posture (stationary + aspect ratio < 0.8) for 3+ sec
- **Active**: Poop visible in frame, confirmed and assigned UUID
- **Cleaned**: Human within radius + poop missing for 15+ frames

## Development Commands

### Quick Start (Development)
```bash
# Start both backend and frontend
python start.py

# Backend runs on port 8080
# Frontend runs on port 5173
# Open: http://localhost:5173
```

### Manual Start
```bash
# Terminal 1: Backend
python demo.py  # or backend/main.py for live RTSP

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Production Build
```bash
cd frontend && npm run build
# Serves from backend/web_server.py
python backend/main.py
```

## Key Implementation Details

### Backend (Python)

**IoU Tracking (poop_tracker.py)**
- Uses Intersection over Union to match poop detections across frames
- Threshold: 0.3 (configurable in config.yaml)
- Creates new PoopInstance if no match found

**Cleanup Detection**
- Human bbox within 100px of poop center
- Poop must be missing for `cleanup_confirm_frames` (15) to confirm
- Prevents false positives from temporary occlusions

**Event Callbacks**
- `poop_tracker.py` accepts optional `event_callback` parameter
- Broadcasts to WebSocket: `poop_detected`, `poop_confirmed`, `poop_cleaned`
- Used by web_server.py for real-time dashboard updates

**Frame Annotation (frame_annotator.py)**
- Color-coded bounding boxes: Dogs (blue), Persons (green), Poops (red/yellow)
- Age timers on poop markers
- Status overlay with metrics

### Frontend (React)

**useWebSocket Hook (hooks/useWebSocket.js)**
- Auto-connects on mount
- Auto-reconnects on disconnect (5sec delay)
- Returns: `{ isConnected, lastMessage, sendMessage }`

**Component Structure**
- `Dashboard.jsx`: Main layout, state management, WebSocket handling
- `VideoFeed.jsx`: MJPEG stream display (`/video/feed`)
- `MetricsCard.jsx`: Live statistics (active, pending, cleaned, total)
- `PoopList.jsx`: Active poops with live age timers (ticks every 1sec)
- `AlertLog.jsx`: Event timeline with color-coded alerts
- `ConnectionStatus.jsx`: WebSocket connection indicator

**API Integration**
- REST: `GET /api/status` for initial state + refreshes
- WebSocket: `/ws` for real-time events
- Video: `GET /video/feed` for MJPEG stream

## Configuration (config/config.yaml)

Critical parameters:
- `stream.url`: RTMP camera URL (e.g., "rtmp://192.168.1.100/live/backyard")
- `detection.model`: YOLOv8 model path (default: "yolov8x.pt")
- `detection.confidence_threshold`: 0.5 (filter low-confidence detections)
- `detection.inference_interval`: 5 (run YOLO every N frames)
- `tracking.iou_threshold`: 0.3 (poop matching sensitivity)
- `tracking.cleanup_confirm_frames`: 15 (frames to confirm cleanup)
- `pooping_detection.stationary_threshold`: 3.0 seconds
- `pooping_detection.aspect_ratio_threshold`: 0.8 (squat detection)
- `web_server.port`: 8080
- `web_server.video_quality`: 80 (JPEG quality for MJPEG)

## Current Status & Roadmap

### ✅ Implemented (v0.1)
- Modern React dashboard with real-time updates
- Backend processing pipeline (detection, tracking, alerts)
- Demo simulation mode with static image
- One-command startup script
- WebSocket live updates
- IoU-based poop tracking
- Cleanup detection logic
- Frame annotation with age timers

### 🚧 TODO
- **Custom YOLO model** for poop detection (currently uses pretrained COCO)
- **Live RTMP integration** (backend/main.py needs testing with real camera)
- **Production build** configuration and deployment
- **Notification system** (email, SMS, push)
- **Database** for historical metrics and events
- **Settings UI** in dashboard
- **Mobile app** (React Native)

## Important Notes for Future Development

### When Adding Features:
1. **Backend changes**: Update `backend/` files, maintain event callback pattern
2. **Frontend changes**: Create new components in `frontend/src/components/`
3. **Configuration**: Add new params to `config/config.yaml`
4. **API changes**: Update both `backend/web_server.py` and frontend API calls

### When Debugging:
- Backend logs: Check terminal running `demo.py` or `backend/main.py`
- Frontend errors: Browser DevTools Console (F12)
- WebSocket issues: Check connection in Network tab (WS filter)
- Video feed: Test `/video/feed` endpoint directly

### Common Issues:
- **White screen**: Usually syntax error in React components, check browser console
- **WebSocket disconnect**: Backend likely crashed, check backend terminal
- **No detections**: Lower confidence threshold or check model loaded
- **Cleanup not detecting**: Adjust `cleanup_confirm_frames` or human proximity radius

## Testing

### Demo Mode
```bash
python demo.py
# Simulates full workflow with IMG_3490.jpeg
# Creates 2 poops, ages them, human cleans up
```

### Live Mode
```bash
# Edit config/config.yaml with RTMP URL
python backend/main.py
```

## Dependencies

**Backend**: opencv-python, ultralytics (YOLOv8), fastapi, uvicorn, websockets, pyyaml
**Frontend**: react, vite, @vitejs/plugin-react

Install: `pip install -r requirements.txt` and `cd frontend && npm install`
