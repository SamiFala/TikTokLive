import asyncio
import json
import requests
import logging

import websockets
from discord_webhook import DiscordWebhook, DiscordEmbed

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1102639998987145426/_9xjoxzaFR_UoCyibmK3XuLA_5vkhzKbn0yQxgg8dNDZdkSxR7EqWul_6-9O8VkIDDr1'
webhook = DiscordWebhook(url=WEBHOOK_URL)

client_id = "shelly-sas"
auth_code = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzaGVsbHktc2FzIiwiaWF0IjoxNzIyNjg0ODcwLCJ1c2VyX2lkIjoiMTE4NjYzNSIsInNuIjoiMSIsInVzZXJfYXBpX3VybCI6Imh0dHBzOlwvXC9zaGVsbHktNDAtZXUuc2hlbGx5LmNsb3VkIiwibiI6MjUzM30.D0p1Vysbq6cILgrbT194cmg4TmQ-UcClQHVmypw77GM"
redirect_uri = "https://futurateck.com"

access_token = None  # Initialisation globale

class DeviceController:
    def __init__(self, client):
        self.client = client

    def send_command(self, url):
        body = json.dumps({
            "command": "turnOn",
            "parameter": "default",
            "commandType": "command"
        })
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, headers=headers, data=body)
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            self.send_webhook('Error', 'Error sending command', error_detail=err, color="FF0000")
            print(f"Error sending command: {err}")

    def get_oauth_token(self, client_id, auth_code, redirect_uri):
        token_url = "https://shelly-40-eu.shelly.cloud/oauth/auth"
        payload = {
            "client_id": client_id,
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri
        }
        try:
            response = requests.post(token_url, data=payload)
            response.raise_for_status()
            token = response.json().get("access_token")
            if token:
                logging.info("Token obtained successfully")
                return token
            else:
                logging.error("Failed to obtain token: No token in response")
                return None
        except requests.exceptions.RequestException as err:
            logging.error(f"Failed to obtain token: {err}")
            return None

    async def control_relay(self, device_id, state):
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
                logging.info(f"Relay control response for {device_id}: {response}")
        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 401:
                logging.warning("Access token expired or invalid. Obtaining a new token.")
                access_token = self.get_oauth_token(client_id, auth_code, redirect_uri)
                if access_token:
                    await self.control_relay(device_id, state)
                else:
                    logging.error("Failed to obtain new token")
            else:
                logging.error(f"WebSocket connection failed with status code: {e.status_code}")

    async def control_multiple_relays(self, devices, state):
        tasks = [self.control_relay(devices[device], state) for device in devices]
        await asyncio.gather(*tasks)

    def send_webhook(self, event, description, error_detail=None, color="242424"):
        embed = DiscordEmbed(title=f"Evenement de {event}", description=description, color=color)
        if error_detail:
            embed.add_embed_field(name="Détails de l'erreur", value=str(error_detail))
        webhook.add_embed(embed)
        try:
            response = webhook.execute()
            if response.status_code != 200:
                print(f"Webhook failed with status code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Failed to send webhook: {e}")

# Initialisation du token OAuth lors de l'initialisation du contrôleur de périphérique
controller = DeviceController(client=None)
access_token = controller.get_oauth_token(client_id, auth_code, redirect_uri)

# Ensuite, vous pouvez appeler les fonctions asynchrones `control_multiple_relays` ou `control_relay` comme précédemment.
