import amqp from "amqplib";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "path";
import dotenv from "dotenv";

import { FacecamProps } from "./types";

const stage = process.env.NODE_ENV || "dev";

dotenv.config({ path: path.resolve(__dirname, `../../../.env.${stage}`) });

import { prisma } from "@repo/database";
const QUEUE_NAME = "VideoRendererQueue";

async function start() {
  const connection = await amqp.connect(
    process.env.RABBIT_URL || "amqp://localhost"
  );

  const channel = await connection.createChannel();
  await channel.assertQueue(QUEUE_NAME, { durable: true });

  console.log("Bundling Remotion project...");
  const bundleLocation = await bundle(path.resolve("./src/index.ts"));
  console.log(`Waiting for messages in ${QUEUE_NAME}...`);

  channel.consume(QUEUE_NAME, async (msg) => {
    if (!msg) return;

    const { clipId } = JSON.parse(msg.content.toString());
    console.log(`Processing Clip: ${clipId}`);

    try {
      // 1. Fetch data from DB
      const clip = await prisma.clip.findUnique({
        where: { id: clipId },
      });

      if (!clip) {
        console.error(`Clip ${clipId} not found in database.`);
        return channel.ack(msg);
      }

      await prisma.clip.update({
        where: { id: clipId },
        data: { status: "RENDERING" },
      });

      const inputProps: FacecamProps = {
        videoPath: clip.videoPath,
        faceCamX: clip.faceCamX,
        faceCamY: clip.faceCamY,
        faceCamWidth: clip.faceCamWidth,
        faceCamHeight: clip.faceCamHeight,
        clipId: clip.id,
      };

      const composition = await selectComposition({
        id: "Shorts", 
        inputProps,
        serveUrl: bundleLocation,
      });

      await renderMedia({
        composition,
        serveUrl: bundleLocation,
        outputLocation: path.resolve(`./out/${clipId}.mp4`),
        inputProps,
        codec: "h264",
      });

      await prisma.clip.update({
        where: { id: clipId },
        data: { status: "RENDERED" },
      });

      console.log(`Success: ${clipId}.mp4`);
      channel.ack(msg);
    } catch (error) {
      console.error("Task failed:", error);

      await prisma.clip
        .update({
          where: { id: clipId },
          data: { status: "FAILED" },
        })
        .catch(() => {});

      channel.nack(msg, false, false); // Don't requue if it's a code error
    }
  });
}

start().catch(console.error);
