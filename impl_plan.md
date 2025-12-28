# Dog Poop Detector
## Technical Project Plan

**Input**: IP camera RTMP stream  
**Detection Model**: YOLOv8x (highest accuracy)  
**Goal**: Detect defecation events, track poop locations until cleanup

---

## System Overview

```
RTMP Stream ──▶ Frame Capture ──▶ YOLO Detection ──▶ Event Tracker ──▶ Alerts/Dashboard
                                       │
                            Detects: dogs, poop,
                            humans, pickup actions
```

**Core Logic**:
1. Detect dog in "pooping posture" → log event start
2. Detect new poop appears after dog leaves → confirm deposit, assign ID & location
3. Track poop location persistently across frames
4. Detect human near poop + poop disappears → mark as cleaned
5. Maintain count of active (uncleaned) poop locations

---

## Detection Strategy

### Classes to Detect

| Class | Purpose | Detection Method |
|-------|---------|------------------|
| Dog | Track animal presence | YOLO pretrained (COCO class 16) |
| Dog-pooping | Identify defecation in progress | Custom trained or pose heuristic |
| Poop | Track deposits | Custom trained class |
| Human | Identify cleanup person | YOLO pretrained (COCO class 0) |

### Model Recommendation

**Primary**: YOLOv8x with custom training for "poop" class
- Base: `yolov8x.pt` (highest accuracy YOLOv8)
- Fine-tune on dataset of dog feces images (outdoor/grass backgrounds)
- Alternative: YOLOv8x-worldv2 for open-vocabulary detection ("dog feces")

**Pooping Posture Detection** (heuristic approach):
- Dog detected in hunched/squatting position for 3+ seconds
- Bounding box aspect ratio changes (dog becomes more compact)
- Dog stationary with lowered hindquarters

---

## Architecture

### Components

| Component | Responsibility |
|-----------|----------------|
| Stream Capture | Connect to RTMP, extract frames |
| Detector | Run YOLO inference, return detections |
| Poop Tracker | Maintain persistent poop locations with IDs |
| Event Detector | Identify pooping/cleanup events |
| State Manager | Track active poops, generate alerts |

### Poop Tracking State Machine

```
[No Poop] ──dog pooping detected──▶ [Pending]
                                        │
                        poop visible after dog leaves
                                        │
                                        ▼
                                   [Active] ◄─────────────────┐
                                        │                     │
                      human near + poop gone          poop still visible
                                        │                     │
                                        ▼                     │
                                   [Cleaned] ─────────────────┘
                                                    (false positive)
```

### Data Structures

**PoopInstance**:
- id: unique identifier
- location: (x, y) center point in frame
- bbox: bounding box coordinates
- first_seen: timestamp
- last_seen: timestamp
- status: pending | active | cleaned
- deposited_by: dog tracking ID (if available)

**TrackerState**:
- active_poops: list of PoopInstance
- cleaned_count: int
- total_deposits: int

---

## Implementation Sequence

```
STEP 1: Project Setup
□ Create project structure
□ Dependencies: opencv-python, ultralytics, numpy, pyyaml

STEP 2: Stream Capture Module
□ RTMP input via OpenCV or ffmpeg
□ Frame queue with bounded buffer
□ Reconnection handling

STEP 3: Detection Module  
□ Load YOLOv8x model
□ Run inference on frames
□ Filter to relevant classes (dog, person, poop)
□ Return detections with confidence scores

STEP 4: Pooping Event Detection
□ Track dog positions across frames
□ Detect stationary + hunched posture (aspect ratio heuristic)
□ Flag "pooping in progress" after 3 second threshold
□ Mark location for poop monitoring

STEP 5: Poop Tracker
□ When new poop detected near flagged location → create PoopInstance
□ Track poop across frames using IoU matching
□ Handle occlusions (poop hidden temporarily)
□ Age out stale detections

STEP 6: Cleanup Detection
□ Detect human within threshold distance of poop
□ If poop disappears while human present → mark cleaned
□ Require poop gone for N frames to confirm (avoid false positives)

STEP 7: State & Alerts
□ Maintain running count of active poops
□ Generate alerts (new poop, cleanup, poop aged > threshold)
□ Optional: REST API or dashboard for status
```

---

## Configuration

```yaml
stream:
  url: "rtmp://192.168.1.100/live/backyard"
  reconnect_delay: 5

detection:
  model: "yolov8x.pt"  # or custom trained model
  confidence_threshold: 0.5
  inference_interval: 5  # frames between inference

tracking:
  iou_threshold: 0.3  # for matching poop across frames
  stale_threshold: 300  # frames before losing track
  cleanup_confirm_frames: 15  # frames poop must be gone

pooping_detection:
  stationary_threshold: 3.0  # seconds dog must be still
  aspect_ratio_threshold: 0.8  # height/width ratio for squat
  
alerts:
  new_poop: true
  cleanup: true
  aged_minutes: 30  # alert if poop uncleaned for this long
```

---

## Key Algorithms

### Pooping Posture Heuristic

```
1. Track dog bounding boxes over sliding window (3 sec)
2. Calculate movement: if center moves < threshold → stationary
3. Calculate aspect ratio: height / width
4. If stationary AND aspect_ratio < 0.8 (squatting) → pooping
5. Mark ground location below dog bbox as "pending poop zone"
```

### Poop-to-Track Matching (IoU)

```
For each new poop detection:
  1. Calculate IoU with all active PoopInstances
  2. If IoU > threshold → update existing instance
  3. If no match → create new PoopInstance
  
For each active PoopInstance not matched:
  1. Increment missing_frames counter
  2. If missing_frames > stale_threshold → check if cleaned
```

### Cleanup Detection

```
For each active poop:
  1. Check if human bbox within radius of poop location
  2. If human present AND poop not detected:
     - Increment cleanup_candidate_frames
  3. If cleanup_candidate_frames > confirm_threshold:
     - Mark poop as cleaned
     - Increment cleaned_count
```

---

## Project Structure

```
dog-poop-detector/
├── config/
│   └── config.yaml
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── capture.py           # RTMP stream capture
│   ├── detector.py          # YOLO inference wrapper
│   ├── poop_tracker.py      # Poop instance tracking
│   ├── event_detector.py    # Pooping/cleanup event logic
│   └── state_manager.py     # Overall state & alerts
├── models/
│   └── .gitkeep             # Custom trained models here
├── requirements.txt
└── README.md
```

---

## Dependencies

```
opencv-python>=4.8.0
ultralytics>=8.0.0
numpy>=1.24.0
pyyaml>=6.0
```

---

## Testing Checklist

| Test | Validation |
|------|------------|
| Stream connection | Frames received from RTMP |
| Dog detection | Dogs identified in frame |
| Poop detection | Poop visible after deposit detected |
| Tracking persistence | Same poop maintains ID across frames |
| Cleanup detection | Poop marked cleaned when human picks up |
| False positive handling | Poop reappears if cleanup was incorrect |

---

## Notes for Implementation

- **Custom Training**: For best poop detection, collect 200+ images of dog feces in similar environment and fine-tune YOLOv8x
- **Pose Detection Alternative**: Could use YOLOv8-pose for dog posture instead of bbox heuristics
- **Night Vision**: If camera has IR, test detection accuracy in low light
- **Multiple Dogs**: Tracker should handle multiple dogs and associate deposits with specific animals if possible
- **Weather**: Rain may wash away poop - consider environmental factors for aged alerts
