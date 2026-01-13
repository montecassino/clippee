import cv2
import os
from ultralytics import YOLO
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# load yolo nano
model = YOLO("yolo11n.pt") 

class DetectionRequest(BaseModel):
    video_path: str
    start_sec: float
    end_sec: float

# in production this should be a background worker working asynchronously 
# but fuck it
@app.post("/detect-facecam")
async def detect_facecam(req: DetectionRequest):
    video_capture = cv2.VideoCapture(req.video_path)
    if not video_capture.isOpened():
        raise HTTPException(status_code=400, detail="Could not open video file")

    fps = video_capture.get(cv2.CAP_PROP_FPS)

    # point playhead to start timestamp
    video_capture.set(cv2.CAP_PROP_POS_FRAMES, int(req.start_sec * fps))
    
    detections = []
    
    while video_capture.isOpened() and (video_capture.get(cv2.CAP_PROP_POS_MSEC) / 1000.0) <= req.end_sec:
        # move playhead to next frame until we exit
        ret, frame = video_capture.read()
        if not ret:
            break
            
        current_frame_num = int(video_capture.get(cv2.CAP_PROP_POS_FRAMES))
        if current_frame_num % int(fps) == 0:
            # yolov11 inference limit person classification using classes=[0]
            results = model(frame, classes=[0], verbose=False)
            
            for r in results:
                boxes = r.boxes.xywh.cpu().numpy() # Get [x_center, y_center, w, h]
                if len(boxes) > 0:
                    box = results[0].boxes.xywh[0].cpu().numpy()
                    x_center, y_center, w, h = box

                    # EXPAND: Increase the width and height by 40%
                    # This captures the microphone, chair, and frame
                    w_expanded = w * 1.4
                    h_expanded = h * 1.4

                    # Convert back to top-left coordinates for cropping
                    x = int(x_center - (w_expanded / 2))
                    y = int(y_center - (h_expanded / 2))
                    w = int(w_expanded)
                    h = int(h_expanded)
                    detections.append((x, y, int(w), int(h)))

    if not detections:
        return {"detected": False, "message": "No streamer detected in this timeframe"}

    # median frame
    detections.sort(key=lambda d: d[0]) 
    mid = len(detections) // 2
    final_box = detections[mid]

    # just checking if face detected
    # if final_box:
    #     x, y, w, h = final_box
        
    #     debug_dir = os.path.join(os.path.dirname(__file__), "debug")
    #     os.makedirs(debug_dir, exist_ok=True)

    #     video_capture.set(cv2.CAP_PROP_POS_MSEC, (req.start_sec + req.end_sec) / 2 * 1000)
    #     ret, debug_frame = video_capture.read()

    #     if ret:
    #         cv2.rectangle(debug_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
    #         cv2.putText(debug_frame, "Detected Facecam", (x, y - 10), 
    #                     cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    #         debug_path = os.path.join(debug_dir, "last_detection.jpg")
    #         cv2.imwrite(debug_path, debug_frame)
    #         print(f"Debug screenshot saved to: {debug_path}")

    video_capture.release()

    return {
        "detected": True,
        "coords": {
            "x": final_box[0],
            "y": final_box[1],
            "width": final_box[2],
            "height": final_box[3]
        }
    }