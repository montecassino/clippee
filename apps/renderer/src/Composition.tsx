import {
  AbsoluteFill,
  OffthreadVideo,
  getInputProps,
  staticFile,
} from "remotion";
import { FacecamProps } from "./types";

export const ShortsComposition: React.FC = () => {
  const { videoPath, faceCamX, faceCamY, faceCamWidth, faceCamHeight } =
    getInputProps<FacecamProps>();

  const screenWidth = 1080;
  const screenHeight = 1920;
  const facecamAreaHeight = screenHeight * 0.3; // 576px
  const gameplayAreaHeight = screenHeight * 0.7; // 1344px

  const ZOOM_OUT_FACTOR = 0.95;
  const faceScale = (screenWidth / faceCamWidth) * ZOOM_OUT_FACTOR;

  const xOffset = (screenWidth - faceCamWidth * faceScale) / 2;
  const yOffset = (facecamAreaHeight - faceCamHeight * faceScale) / 2;

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* 1. FACECAM (TOP 30%) */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: screenWidth,
          height: facecamAreaHeight,
          overflow: "hidden",
          zIndex: 10,
          backgroundColor: "#1a1a1a", 
        }}
      >
        <OffthreadVideo
          src={staticFile(videoPath)}
          style={{
            position: "absolute",
            transform: `translate(${xOffset}px, ${yOffset}px) scale(${faceScale}) translate(${-faceCamX}px, ${-faceCamY}px)`,
            transformOrigin: "0 0",
            width: "auto",
            height: "auto",
          }}
        />
      </div>

      {/* 2. GAMEPLAY (BOTTOM 70%) */}
      <div
        style={{
          position: "absolute",
          top: facecamAreaHeight,
          width: screenWidth,
          height: gameplayAreaHeight,
          overflow: "hidden",
        }}
      >
        <OffthreadVideo
          src={staticFile(videoPath)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
