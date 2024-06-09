import asyncio
import functools
import json
import os.path
import time
from asyncio import AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

import requests
from playsound import playsound
import pyttsx3

from discord_webhook import DiscordWebhook, DiscordEmbed
from ratelimiter import RateLimiter

# Configuration
hostName = "0.0.0.0"
serverPort = 5050

loop: AbstractEventLoop = asyncio.get_event_loop()

# Constantes regroupées
SHELLY_PLUG_URL = "https://shelly-40-eu.shelly.cloud/device/relay/control"
WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1102639998987145426/_9xjoxzaFR_UoCyibmK3XuLA_5vkhzKbn0yQxgg8dNDZdkSxR7EqWul_6-9O8VkIDDr1'
SMOKE_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/C7BDBFBB7A3E/commands"
SMOKE_TWO_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/D5D127EFF039/commands"
PINGPONG_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/F3DFF2EAB30F/commands"

device_commands = {
    "run": {
        "giro": 'http://192.168.1.22/relay/0?turn=on',
        "bubble": 'http://192.168.1.28/relay/0?turn=on',
        "neige": 'http://192.168.1.25/relay/0?turn=on',
        "mousse": 'http://192.168.1.21/relay/0?turn=on',
        "souffleur": 'http://192.168.1.26/relay/0?turn=on',
        "confettis": 'http://192.168.1.27/relay/0?turn=on',
        "spots": 'http://192.168.1.24/relay/0?turn=on'
    },
    "stop": {
        "giro": 'http://192.168.1.22/relay/0?turn=off',
        "bubble": 'http://192.168.1.28/relay/0?turn=off',
        "neige": 'http://192.168.1.25/relay/0?turn=off',
        "mousse": 'http://192.168.1.21/relay/0?turn=off',
        "souffleur": 'http://192.168.1.26/relay/0?turn=off',
        "confettis": 'http://192.168.1.27/relay/0?turn=off',
        "spots": 'http://192.168.1.24/relay/0?turn=off'
    }
}

webhook = DiscordWebhook(url=WEBHOOK_URL)
rate_limiter = RateLimiter(max_calls=1, period=2)
requestToSend = requests.Session()

# Classe DeviceController pour gérer les appareils
class DeviceController:
    def __init__(self):
        pass

    async def manually_play_sound(self, sound, count=1):
        try:
            for _ in range(count):
                await asyncio.to_thread(playsound, sound)
        except Exception as e:
            print(f"Error playing sound: {e}")

    def play_video(self, video_path):
        try:
            os.system(f'/Applications/VLC.app/Contents/MacOS/VLC {video_path} --play-and-exit -f &')
        except Exception as e:
            print(f"Error playing video: {e}")

    def control_device(self, device_id, turn):
        data = {
            "channel": "0",
            "turn": turn,
            "id": device_id,
            "auth_key": "MTIxYjRidWlk73D0630FF6F6F4CA17F97B081604C84BE95B7997AC2BACD24EBC858C94EB4445B1C523DE1069652C"
        }
        with rate_limiter:
            try:
                response = requests.post(SHELLY_PLUG_URL, data=data)
                response.raise_for_status()
            except requests.exceptions.RequestException as err:
                print(f"Error controlling device: {err}")

controller = DeviceController()

# Fonctions pour les actions
async def perform_action(video=None, sound=None, device_on=None, device_off=None, sleep_before_off=0, sound_count=1):
    if video:
        controller.play_video(video)
    if sound:
        await controller.manually_play_sound(sound, sound_count)
    if device_on:
        requestToSend.get(device_commands["run"][device_on])
    if sleep_before_off > 0 and device_off:
        await asyncio.sleep(sleep_before_off)
        requestToSend.get(device_commands["stop"][device_off])

# Map d'actions
ACTIONS = {
    "Vocal Bienvenue": lambda: perform_action(sound="./sounds/vocal_bienvenue.wav"),
    "Vocal Arrivants": lambda: perform_action(sound="./sounds/vocal_arrivants.wav"),
    "Vocal Global": lambda: perform_action(sound="./sounds/vocal_global.wav"),
    "Rose": lambda: perform_action(sound="./sounds/bruit-de-pet.wav"),
    "TikTok": lambda: perform_action(sound="./sounds/bruit_de_rot.wav"),
    "Donut": lambda: perform_action(sound="./sounds/quoicoubeh.wav"),
    "Alerte": lambda: perform_action(video='./videos/alerte-rouge.mp4', sound="./sounds/nuke_alarm.wav", device_on="giro", sleep_before_off=8, device_off="giro"),
    "Timide": lambda: perform_action(sound="./sounds/police-sirene.wav", device_on="giro", sleep_before_off=10, device_off="giro"),
    "Confettis": lambda: perform_action(video='./videos/cri-de-cochon.mp4'),
    "Sceptre": lambda: perform_action(video='./videos/alien.mp4', sound="./sounds/alien.wav"),
    "398": lambda: perform_action(video='./videos/got-that.mp4'),
    "Corgi": lambda: perform_action(video='./videos/cat.mp4', sound="./sounds/nyan_cat.wav"),
    "Oui oui": lambda: perform_action(video='./videos/oui-oui.mp4', sound="./sounds/oui_oui.wav", device_on="souffleur", sleep_before_off=10, device_off="souffleur"),
    "Balançoire": lambda: perform_action(video='./videos/teuf.mp4', sound="./sounds/losing-it.wav"),
    "Cygne": lambda: perform_action(video='./videos/cygne.mp4', sound="./sounds/la_danse_des_canards.wav", device_on="bubble", sleep_before_off=16, device_off="bubble"),
    "Train": lambda: perform_action(video='./videos/train.mp4', sound="./sounds/train.wav", device_on="spots", sleep_before_off=9, device_off="spots"),
    "Mine dor": lambda: perform_action(video='./videos/thriller.mp4', sound="./sounds/thriller.wav", device_on="spots", sleep_before_off=14, device_off="spots"),
    "Champion": lambda: perform_action(video='./videos/film_300.mp4', sound="./sounds/jump.wav", device_on="spots", sleep_before_off=20, device_off="spots"),
    "Baleine": lambda: perform_action(video='./videos/reine-des-neiges.mp4', device_on="neige", sleep_before_off=22, device_off="neige"),
    "Moto": lambda: perform_action(video='./videos/motorcycle.mp4', sound="./sounds/motorcycle.wav", device_on="neige", sleep_before_off=10, device_off="neige"),
    "Jet": lambda: perform_action(video='./videos/guiles.mp4', sound="./sounds/guiles.wav", device_on="mousse", sleep_before_off=22, device_off="mousse"),
    "Interstellar": lambda: perform_action(video='./videos/turn-down-to-what.mp4', device_on="confettis", sleep_before_off=2, device_off="confettis"),
}

# Fonction pour changer la voix
def change_voice(language, gender='VoiceGenderFemale'):
    engine = pyttsx3.init()
    for voice in engine.getProperty('voices'):
        if language in voice.languages and gender == voice.gender:
            engine.setProperty('voice', voice.id)
            return True

    raise RuntimeError("Language '{}' for gender '{}' not found".format(language, gender))

# Fonction pour jouer un son manuellement
def manually_play_sound(sound):
    loop.run_in_executor(ThreadPoolExecutor(), functools.partial(playsound, sound))

# Fonction pour jouer une vidéo
def play_video(video_path: str):
    os.system(f'/Applications/VLC.app/Contents/MacOS/VLC {video_path} --play-and-exit -f &')

# Classe pour gérer le serveur HTTP
class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        parameters = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        gift_name = next(iter(parameters.get('gift_name', [])), None)
        like_count = next(iter(parameters.get('likes', [])), None)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if gift_name:
            asyncio.run(ACTIONS.get(gift_name, lambda: print(f"No action for gift {gift_name}"))())
        if like_count:
            on_like(int(like_count))

# Fonction pour gérer les likes
def on_like(total_likes: int):
    change_voice("fr_FR", "VoiceGenderMale")
    engine = pyttsx3.init()
    engine.say(f"Merci pour les {total_likes} coeurs les amis")
    engine.runAndWait()
    requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)

# Point d'entrée principal
if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
