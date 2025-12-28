"""Web server module with REST API, WebSocket, and video streaming."""

import asyncio
import logging
import threading
import json
import cv2
from typing import Dict, Optional, Set
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
import uvicorn


class WebServer:
    """FastAPI web server for dashboard, API, and video streaming."""

    def __init__(self, config: dict):
        """
        Initialize web server.

        Args:
            config: Web server configuration dict
        """
        self.logger = logging.getLogger(__name__)
        self.host = config['host']
        self.port = config['port']
        self.enable_video_stream = config['enable_video_stream']
        self.video_quality = config['video_quality']

        # Shared state
        self.current_state = {}
        self.current_frame = None
        self.frame_lock = threading.Lock()

        # WebSocket connections
        self.active_connections: Set[WebSocket] = set()

        # FastAPI app
        self.app = FastAPI(title="Dog Poop Detector API")
        self._setup_routes()

        # Server thread
        self.server_thread = None

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/")
        async def root():
            """Serve dashboard HTML."""
            web_dir = Path(__file__).parent.parent / "web"
            return FileResponse(web_dir / "index.html")

        @self.app.get("/api/status")
        async def get_status():
            """Get current poop tracking status."""
            return self._format_status(self.current_state)

        @self.app.get("/api/config")
        async def get_config():
            """Get current configuration."""
            return {
                "video_enabled": self.enable_video_stream,
                "video_quality": self.video_quality
            }

        @self.app.get("/video/feed")
        async def video_feed():
            """MJPEG video stream."""
            if not self.enable_video_stream:
                return {"error": "Video streaming is disabled"}

            return StreamingResponse(
                self._generate_video_stream(),
                media_type="multipart/x-mixed-replace; boundary=frame"
            )

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.active_connections.add(websocket)
            self.logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

            try:
                # Send initial state
                await websocket.send_json({
                    "type": "status_update",
                    "data": self._format_status(self.current_state)
                })

                # Keep connection alive and listen for client messages
                while True:
                    try:
                        data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                        # Handle client messages if needed
                    except asyncio.TimeoutError:
                        # No message received, continue loop
                        continue

            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
                self.logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

        # Mount static files
        web_dir = Path(__file__).parent.parent / "web"
        if web_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

    def _format_status(self, state: Dict) -> Dict:
        """Format tracker state for API response."""
        active_poops = state.get('active_poops', [])
        pending_poops = state.get('pending_poops', [])

        return {
            "active_poops": [
                {
                    "id": poop.id,
                    "location": list(poop.location),
                    "bbox": list(poop.bbox),
                    "age_seconds": (datetime.now() - poop.first_seen).total_seconds(),
                    "status": poop.status
                }
                for poop in active_poops
            ],
            "pending_poops": [
                {
                    "id": poop.id,
                    "location": list(poop.location),
                    "status": poop.status
                }
                for poop in pending_poops
            ],
            "metrics": {
                "active_count": len(active_poops),
                "pending_count": len(pending_poops),
                "cleaned_count": state.get('cleaned_count', 0),
                "total_deposits": state.get('total_deposits', 0)
            }
        }

    def _generate_video_stream(self):
        """Generate MJPEG video stream."""
        while True:
            with self.frame_lock:
                if self.current_frame is None:
                    continue

                # Encode frame as JPEG
                ret, buffer = cv2.imencode(
                    '.jpg',
                    self.current_frame,
                    [cv2.IMWRITE_JPEG_QUALITY, self.video_quality]
                )

                if not ret:
                    continue

                frame_bytes = buffer.tobytes()

            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def update_state(self, state: Dict):
        """
        Update current state and broadcast to WebSocket clients.

        Args:
            state: New state from PoopTracker
        """
        self.current_state = state

    def update_frame(self, frame):
        """
        Update current video frame.

        Args:
            frame: Annotated frame as numpy array
        """
        with self.frame_lock:
            self.current_frame = frame

    async def broadcast_event(self, event_type: str, data: Dict):
        """
        Broadcast event to all connected WebSocket clients.

        Args:
            event_type: Event type (poop_detected, poop_confirmed, poop_cleaned, etc.)
            data: Event data
        """
        if not self.active_connections:
            return

        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

        # Send to all connections
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.error(f"Error sending to WebSocket client: {e}")
                disconnected.add(connection)

        # Remove disconnected clients
        self.active_connections -= disconnected

    def broadcast_event_sync(self, event_type: str, data: Dict):
        """
        Synchronous wrapper for broadcasting events.

        Args:
            event_type: Event type
            data: Event data
        """
        # This will be called from the main processing thread
        # We need to schedule the async broadcast in the event loop
        if self.active_connections:
            try:
                # Get the event loop running in the server thread
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.broadcast_event(event_type, data))
                loop.close()
            except Exception as e:
                self.logger.error(f"Error broadcasting event: {e}")

    def start(self):
        """Start web server in background thread."""
        self.logger.info(f"Starting web server on {self.host}:{self.port}")

        def run_server():
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        self.logger.info(f"Web dashboard available at http://{self.host}:{self.port}")

    def stop(self):
        """Stop web server."""
        # Uvicorn doesn't provide easy programmatic shutdown
        # The daemon thread will stop when main program exits
        self.logger.info("Web server stopping...")
