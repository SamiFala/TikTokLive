import logging
import asyncio
import websockets
import json
import requests
import threading
from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import ConnectEvent, GiftEvent, CommentEvent

# Informations de la prise Shelly
device_id = "70518405971645"  # Assurez-vous que cet ID est correct
client_id = "shelly-sas"
auth_code = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzaGVsbHktc2FzIiwiaWF0IjoxNzIyNjg0ODcwLCJ1c2VyX2lkIjoiMTE4NjYzNSIsInNuIjoiMSIsInVzZXJfYXBpX3VybCI6Imh0dHBzOlwvXC9zaGVsbHktNDAtZXUuc2hlbGx5LmNsb3VkIiwibiI6MjUzM30.D0p1Vysbq6cILgrbT194cmg4TmQ-UcClQHVmypw77GM"
redirect_uri = "https://futurateck.com"

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@aminezz102"
)

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_oauth_token(client_id, auth_code, redirect_uri):
    token_url = "https://shelly-40-eu.shelly.cloud/oauth/auth"
    payload = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        logger.error(f"Failed to obtain token: {response.status_code} - {response.text}")
        return None

async def connect_shelly_websocket(access_token):
    ws_url = f"wss://shelly-40-eu.shelly.cloud:6113/shelly/wss/hk_sock?t={access_token}"
    async with websockets.connect(ws_url) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            logger.info(f"Received message: {data}")
            if data.get("event") == "Shelly:StatusOnChange":
                logger.info(f"Status changed: {data}")
            elif data.get("event") == "Shelly:Online":
                logger.info(f"Device online status changed: {data}")
            elif data.get("event") == "Shelly:CommandResponse":
                logger.info(f"Command response: {data}")

async def control_relay(state):
    global access_token
    ws_url = f"wss://shelly-40-eu.shelly.cloud:6113/shelly/wss/hk_sock?t={access_token}"
    try:
        async with websockets.connect(ws_url) as websocket:
            command = {
                "event": "Shelly:CommandRequest",
                "trid": 1,
                "deviceId": device_id,
                "data": {
                    "cmd": "relay",
                    "params": {
                        "turn": state,
                        "id": 0
                    }
                }
            }
            await websocket.send(json.dumps(command))
            response = await websocket.recv()
            logger.info(f"Relay control response: {response}")
    except websockets.exceptions.InvalidStatusCode as e:
        if e.status_code == 401:
            logger.warning("Access token expired or invalid. Obtaining a new token.")
            access_token = get_oauth_token(client_id, auth_code, redirect_uri)
            if access_token:
                await control_relay(state)
            else:
                logger.error("Failed to obtain new token")
        else:
            logger.error(f"WebSocket connection failed with status code: {e.status_code}")

@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    logger.info(f"Connected to @{event.unique_id}!")
    print(f"Connected to @{event.unique_id}!")

@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    logger.info("Received a comment!")
    print("Received a comment!")
    await control_relay("on")
    await asyncio.sleep(1)
    await control_relay("off")

@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    logger.info("Received a gift!")
    print("Received a gift!")

    if event.gift.streakable and not event.streaking:
        logger.info(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.name}\"")
        print(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.name}\"")

    elif not event.gift.streakable:
        logger.info(f"{event.user.unique_id} sent \"{event.gift.name}\"")
        print(f"{event.user.unique_id} sent \"{event.gift.name}\"")

async def main():
    global access_token
    access_token = get_oauth_token(client_id, auth_code, redirect_uri)
    if access_token:
        # Connect to Shelly WebSocket
        await asyncio.create_task(connect_shelly_websocket(access_token))
    else:
        logger.error("Failed to obtain access token")

def start_tiktok_client():
    # Connect to TikTok
    client.run()
    logger.info("Client is running.")

if __name__ == '__main__':
    # Enable debug info
    client.logger.setLevel(LogLevel.INFO.value)
    logger.info("Client logger level set to INFO.")

    # Start TikTok client in a separate thread
    tiktok_thread = threading.Thread(target=start_tiktok_client)
    tiktok_thread.start()

    # Run the main function
    asyncio.run(main())
