import asyncio
import functools
import json
import logging
import os.path
import time
from asyncio import AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor

import os
import requests
import websockets
from discord_webhook import DiscordEmbed
from playsound import playsound
import pyttsx3

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

from pyttsx3 import Engine
from discord_webhook import DiscordWebhook, DiscordEmbed


WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1102639998987145426/_9xjoxzaFR_UoCyibmK3XuLA_5vkhzKbn0yQxgg8dNDZdkSxR7EqWul_6-9O8VkIDDr1'


webhook = DiscordWebhook(url=WEBHOOK_URL)

hostName = "0.0.0.0"
serverPort = 5050

loop: AbstractEventLoop = asyncio.get_event_loop()

# Constantes regroupées
SHELLY_PLUG_URL = "https://shelly-40-eu.shelly.cloud/device/relay/control"
WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1102639998987145426/_9xjoxzaFR_UoCyibmK3XuLA_5vkhzKbn0yQxgg8dNDZdkSxR7EqWul_6-9O8VkIDDr1'
SMOKE_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/C7BDBFBB7A3E/commands"
SMOKE_TWO_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/D5D127EFF039/commands"
PINGPONG_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/F3DFF2EAB30F/commands"

devices = {
    "girophare": "9047579382045",
    "bulles": "15819010",
    "neige": "15805966",
    "mousse": "15811858",
    "spots": "70518405971645"
}

body = json.dumps({
    "command": "turnOn",
    "parameter": "default",
    "commandType": "command"
})
headers = {
    'Authorization': 'Bearer 09f984c25288d88849a45b8dce8010b5f03104f8abc47ee87beb9031d97d6db550f2e903358b84f039b23ab3371032bc',
    'Content-Type': 'application/json'
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client_id = "shelly-sas"
auth_code = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzaGVsbHktc2FzIiwiaWF0IjoxNzIyNjg0ODcwLCJ1c2VyX2lkIjoiMTE4NjYzNSIsInNuIjoiMSIsInVzZXJfYXBpX3VybCI6Imh0dHBzOlwvXC9zaGVsbHktNDAtZXUuc2hlbGx5LmNsb3VkIiwibiI6MjUzM30.D0p1Vysbq6cILgrbT194cmg4TmQ-UcClQHVmypw77GM"
redirect_uri = "https://futurateck.com"

access_token = None  # Initialisation globale


class DeviceController:
    def __init__(self, client=None):
        self.client = client

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
                response = websocket.recv()
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
        tasks = [self.control_relay(device_id, state) for device_id in devices.values()]
        await asyncio.gather(*tasks)

    async def send_command(self, url):
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

    async def manually_play_sound(self, sound, count=1):
        try:
            for _ in range(count):
                await asyncio.to_thread(playsound, sound)
        except Exception as e:
            self.send_webhook('Error', 'Error playing sound', error_detail=e, color="FF0000")
            print(f"Error playing sound: {e}")

    async def play_video(self, video_path):
        try:
            os.system(f'/Applications/VLC.app/Contents/MacOS/VLC {video_path} --play-and-exit -f &')
        except Exception as e:
            self.send_webhook('Error', 'Error playing video', error_detail=e, color="FF0000")
            print(f"Error playing video: {e}")

controller = DeviceController()
access_token = controller.get_oauth_token(client_id, auth_code, redirect_uri)


def on_gift(gift_name: str):
    print(f'oeoe y a le gift : {gift_name}')

    if gift_name == "1":
        controller.manually_play_sound(f"./sounds/bruit-de-pet.wav")

    elif gift_name == "5":
        controller.manually_play_sound(f"./sounds/bruit_de_rot.wav")

    elif gift_name == "10":
        controller.manually_play_sound(f"./sounds/ouais_cest_greg.wav")

    elif gift_name == "15":
        controller.manually_play_sound(f"./sounds/je_suis_bien.wav")

    elif gift_name == "20":
        controller.manually_play_sound(f"./sounds/alerte_au_gogole.wav")

    elif gift_name == "30":
        controller.manually_play_sound(f"./sounds/quoicoubeh.wav")

    elif gift_name == "49":
        controller.manually_play_sound(f"./sounds/my_movie.wav")

    elif gift_name == "55":
        controller.manually_play_sound(f"./sounds/on_sen_bat_les_couilles.wav")

    elif gift_name == "88":
        controller.manually_play_sound(f"./sounds/chinese_rap_song.wav")

    elif gift_name == "99":
        controller.control_multiple_relays({"girophare": devices["girophare"]}, "on")
        controller.play_video('./videos/alerte-rouge.mp4')
        controller.manually_play_sound(f"./sounds/nuke_alarm.wav")
        asyncio.sleep(8)
        controller.control_multiple_relays({"girophare": devices["girophare"]}, "off")

    elif gift_name == "100":
        controller.play_video('./videos/cri-de-cochon.mp4')

    elif gift_name == "150":
        controller.play_video('./videos/rap-contenders-thai.mp4')

    elif gift_name == "169":
        controller.play_video('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif gift_name == "199":
        controller.control_multiple_relays({"girophare": devices["girophare"]}, "on")
        controller.manually_play_sound(f"./sounds/police-sirene.wav")
        controller.manually_play_sound(f"./sounds/fbi-open-up.wav")
        asyncio.sleep(10)
        controller.control_multiple_relays({"girophare": devices["girophare"]}, "off")

    elif gift_name == "200":
        controller.play_video('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif gift_name == "299":
        controller.play_video('./videos/alien.mp4')
        controller.manually_play_sound(f"./sounds/alien.wav")

    elif gift_name == "398":
        controller.play_video('./videos/got-that.mp4')

    elif gift_name == "399":
        controller.play_video('./videos/cat.mp4')
        controller.manually_play_sound(f"./sounds/nyan_cat.wav")

    elif gift_name == "400":
        controller.play_video('./videos/teuf.mp4')
        controller.manually_play_sound(f"./sounds/losing-it.wav")

    elif gift_name == "450":
        controller.play_video('./videos/mr-beast-phonk.mp4')

    elif gift_name == "500":
        controller.manually_play_sound(f"./sounds/oui_oui.wav")
        controller.control_multiple_relays({"bulles": devices["bulles"]}, "on")
        controller.play_video('./videos/oui-oui.mp4')
        asyncio.sleep(10)
        controller.control_multiple_relays({"bulles": devices["bulles"]}, "off")

    elif gift_name == "699":
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        controller.manually_play_sound(f"./sounds/la_danse_des_canards.wav")
        controller.play_video('./videos/cygne.mp4')

    elif gift_name == "899":
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(PINGPONG_MACHINE_URL)
        controller.control_multiple_relays({"spots": devices["spots"]}, "on")
        controller.play_video('./videos/train.mp4')
        controller.manually_play_sound(f"./sounds/train.wav")
        asyncio.sleep(9)
        controller.control_multiple_relays({"spots": devices["spots"]}, "off")

    elif gift_name == "1000":
        controller.control_multiple_relays({"spots": devices["spots"]}, "on")
        controller.send_command(PINGPONG_MACHINE_URL)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        controller.play_video('./videos/thriller.mp4')
        controller.manually_play_sound(f"./sounds/thriller.wav")
        asyncio.sleep(14)
        controller.send_command(PINGPONG_MACHINE_URL)
        controller.control_multiple_relays({"spots": devices["spots"]}, "off")

    elif gift_name == "1500":
        controller.control_multiple_relays({"spots": devices["spots"], "neige": devices["neige"]}, "on")
        controller.play_video('./videos/film_300.mp4')
        controller.manually_play_sound(f"./sounds/jump.wav")
        asyncio.sleep(20)
        controller.control_multiple_relays({"neige": devices["neige"], "spots": devices["spots"]}, "off")

    elif gift_name == "1999":
        controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"]}, "on")
        controller.play_video('./videos/reine-des-neiges.mp4')
        asyncio.sleep(30)
        controller.control_multiple_relays(
            {"neige": devices["neige"], "bulles": devices["bulles"], "spots": devices["spots"]}, "off")
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)

    elif gift_name == "3000":
        controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        controller.play_video('./videos/guiles.mp4')
        controller.manually_play_sound(f"./sounds/guiles.wav")
        asyncio.sleep(20)
        controller.control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)

    elif gift_name == "4000":
        controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        controller.send_command(PINGPONG_MACHINE_URL)
        controller.play_video('./videos/turn-down-to-what.mp4')
        asyncio.sleep(22)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        asyncio.sleep(2)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        controller.send_command(PINGPONG_MACHINE_URL)
        controller.control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")

    elif gift_name == "5000":
        controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        controller.send_command(PINGPONG_MACHINE_URL)
        controller.play_video('./videos/interstellar.mp4')
        controller.manually_play_sound(f"./sounds/interstellar.wav")
        asyncio.sleep(30)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        asyncio.sleep(2)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        controller.send_command(PINGPONG_MACHINE_URL)
        controller.control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")
class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        parameters = urllib.parse.parse_qs(self.path)
        gift_name = next(iter(parameters.get('gift_name', [])[0:1]), None)
        like_count = next(iter(parameters.get('likes', [])[0:1]), None)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if gift_name:
            on_gift(gift_name)

if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
