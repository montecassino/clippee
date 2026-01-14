import os
import json
import aio_pika
from aio_pika import Message, DeliveryMode

RABBITMQ_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@localhost/")

connection = None
channel = None

async def connect_rabbitmq():
    global connection, channel
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.declare_queue("VideoRendererQueue", durable=True)
    print("Connected to RabbitMQ")

async def close_rabbitmq():
    if connection:
        await connection.close()
        print("RabbitMQ Connection Closed")

async def publish_clip_event(clip_id: str):
    if channel is None:
        raise Exception("RabbitMQ channel is not initialized")

    payload = {"clipId": clip_id, "event" : "FACECAM_DETECTED"}
    
    await channel.default_exchange.publish(
        Message(
            body=json.dumps(payload).encode(),
            delivery_mode=DeliveryMode.PERSISTENT
        ),
        routing_key="VideoRendererQueue",
    )
    print(f"Instant Publish: {clip_id}")