from pathlib import Path
import os
from dotenv import load_dotenv

stage = os.getenv("STAGE", "example") 
env_file = f".env.{stage}"
env_path = Path(__file__).resolve().parent.parent.parent / env_file
load_dotenv(dotenv_path=env_path)

import cv2
import uuid6
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from ultralytics import YOLO
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from rmq import connect_rabbitmq, close_rabbitmq, publish_clip_event

# internal imports here
from database import get_db
import models

# STORAGE_DIR = Path("facecam_crops")
# STORAGE_DIR.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_rabbitmq()
    yield
    await close_rabbitmq()

app = FastAPI(lifespan=lifespan)

model = YOLO("yolo11n.pt") 

class DetectionRequest(BaseModel):
    video_path: str
    start_sec: float
    end_sec: float

def extract_facecam_coords(video_path: str, start: float, end: float):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, "Could not open video file"

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(start * fps))
    
    detections = []
    
    while cap.isOpened():
        current_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        if current_sec > end:
            break
            
        ret, frame = cap.read()
        if not ret:
            break
            
        current_frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if current_frame_num % max(1, int(fps)) == 0:
            results = model(frame, classes=[0], verbose=False)
            
            for r in results:
                if len(r.boxes) > 0:
                    box = r.boxes.xywh[0].cpu().numpy()
                    x_c, y_c, w, h = box

                    # 40 percent expansion logic with boundary clamping
                    x1 = max(0, int(x_c - (w * 1.4 / 2)))
                    y1 = max(0, int(y_c - (h * 1.4 / 2)))
                    x2 = min(frame_w, int(x1 + (w * 1.4)))
                    y2 = min(frame_h, int(y1 + (h * 1.4)))

                    detections.append({
                        "x": float(x1),
                        "y": float(y1),
                        "w": float(x2 - x1),
                        "h": float(y2 - y1),
                    })

    cap.release()
    
    if not detections:
        return None, "No streamer detected"

    # Sort to find the median detection (to avoid outliers)
    detections.sort(key=lambda d: d['x'])
    return detections[len(detections) // 2], None

@app.post("/detect-facecam", status_code=status.HTTP_201_CREATED)
async def detect_facecam(req: DetectionRequest, db: AsyncSession = Depends(get_db)):
    final_box, error = extract_facecam_coords(req.video_path, req.start_sec, req.end_sec)
    
    if error:
        raise HTTPException(status_code=400, detail=error)

    try:
        clip_id = str(uuid6.uuid7())

        # image_path = STORAGE_DIR / f"{clip_id}_face.jpg"
        # cv2.imwrite(str(image_path), final_box["crop_img"])

        cleaned_path = os.path.basename(req.video_path)

        new_clip = models.Clip(
            id=clip_id,
            videoPath=cleaned_path,
            faceCamX=final_box["x"],
            faceCamY=final_box["y"],
            faceCamWidth=final_box["w"],
            faceCamHeight=final_box["h"],
            clipStartTimestamp=req.start_sec,
            clipEndTimestamp=req.end_sec,
            status="DRAFT"
        )
        
        db.add(new_clip)
        await db.commit() 
        await db.refresh(new_clip)

        await publish_clip_event(clip_id)

        return {
            "success": True,
            "clip_id": new_clip.id,
            "coords": {k: v for k, v in final_box.items() if k != "crop_img"},
        }

    except Exception as e:
        await db.rollback()
        print(f"Error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to save detection"
        )