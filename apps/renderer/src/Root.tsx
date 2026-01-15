import React from "react";
import { Composition } from "remotion";
import { ShortsComposition } from "./Composition";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="Shorts"
        component={ShortsComposition}
        durationInFrames={300} // Default 10s at 30fps
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
