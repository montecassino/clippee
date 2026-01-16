
# Clippee

I know Twitch has already rolled out their vertical video stream feature https://techcrunch.com/2025/07/17/twitch-starts-testing-vertical-video-streams/, but I don't care. This project is about learning how it would work from an EXTERNAL app perspective. Twitch has access to a streamer's peripherals like webcam and display so changing the orientation from a normal / landscape to vertical is a trivial thing to do.

## Tools
- TurboRepo - To facilitate cross package dependencies like DB. To also have a unified way to box and run multiple apps related to this project. 

- YOLO - Facecam location and dimensions detection.
- FastAPI - To serve an API handler that does the facecam detection logic.
- Remotion - To scale and automate video rendering and production.
- MySQL - To store clip attributes like clip start and clip end.

## Setup
- pnpm install
- turbo run install:python
- change interpreter depending on the app env 
- download VODs and put it inside apps/renderer/public

# Dump
curl -X POST http://localhost:8000/detect-facecam \
     -H "Content-Type: application/json" \
     -d '{
           "video_path": "'$(pwd)'/assets/tenz1.mp4",
           "start_sec": 10.5,
           "end_sec": 15.0
         }'