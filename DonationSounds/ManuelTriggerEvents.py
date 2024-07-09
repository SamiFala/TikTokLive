import asyncio
import functools
import json
import os.path
import time
from asyncio import AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor

import os
import requests
from playsound import playsound
import pyttsx3

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

from pyttsx3 import Engine

hostName = "0.0.0.0"
serverPort = 5050

loop: AbstractEventLoop = asyncio.get_event_loop()

spot = "f14512"
mousse = "f169d0"
souffleur = "f14512"
bulles = "f16102"
confettis = "d889bebd"
girophare = "a8dc1511d"
neige = "f12e0e"

requestToSend = requests.Session()
# commandes pour lancer
runGiroMachine = requests.Request('GET', 'http://192.168.1.25/relay/0?turn=on').prepare()
runBubbleMachine = requests.Request('GET', 'http://192.168.1.19/relay/0?turn=on').prepare()
runNeigeMachine = requests.Request('GET', 'http://192.168.1.17/relay/0?turn=on').prepare()
runMousseMachine = requests.Request('GET', 'http://192.168.1.16/relay/0?turn=on').prepare()
runSouffleurMachine = requests.Request('GET', 'http://192.168.1.26/relay/0?turn=on').prepare()
runConfettisMachine = requests.Request('GET', 'http://192.168.1.27/relay/0?turn=on').prepare()
runSpotsLights = requests.Request('GET', 'http://192.168.1.25/relay/0?turn=on').prepare()

# commandes pour stopper
stopGiroMachine = requests.Request('GET', 'http://192.168.1.25/relay/0?turn=off').prepare()
stopBubbleMachine = requests.Request('GET', 'http://192.168.1.19/relay/0?turn=off').prepare()
stopNeigeMachine = requests.Request('GET', 'http://192.168.1.17/relay/0?turn=off').prepare()
stopMousseMachine = requests.Request('GET', 'http://192.168.1.16/relay/0?turn=off').prepare()
stopSouffleurMachine = requests.Request('GET', 'http://192.168.1.26/relay/0?turn=off').prepare()
stopConfettisMachine = requests.Request('GET', 'http://192.168.1.27/relay/0?turn=off').prepare()
stopSpotsLight = requests.Request('GET', 'http://192.168.1.25/relay/0?turn=off').prepare()

# Constantes regroupées
SHELLY_PLUG_URL = "https://shelly-40-eu.shelly.cloud/device/relay/control"
WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1102639998987145426/_9xjoxzaFR_UoCyibmK3XuLA_5vkhzKbn0yQxgg8dNDZdkSxR7EqWul_6-9O8VkIDDr1'
SMOKE_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/C7BDBFBB7A3E/commands"
SMOKE_TWO_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/D5D127EFF039/commands"
PINGPONG_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/F3DFF2EAB30F/commands"

body = json.dumps({
    "command": "turnOn",
    "parameter": "default",
    "commandType": "command"
})
headers = {
    'Authorization': 'Bearer 09f984c25288d88849a45b8dce8010b5f03104f8abc47ee87beb9031d97d6db550f2e903358b84f039b23ab3371032bc',
    'Content-Type': 'application/json'
}


#engine: Engine = pyttsx3.init()


def control_device(device_id, turn):
    data = {
        "channel": "0",
        "turn": turn,
        "id": device_id,
        "auth_key": "MTIxYjRidWlk73D0630FF6F6F4CA17F97B081604C84BE95B7997AC2BACD24EBC858C94EB4445B1C523DE1069652C"
    }
    requests.request("POST", SHELLY_PLUG_URL, data=data)


"""def on_like(total_likes: int):
    change_voice("fr_FR", "VoiceGenderMale")
    engine.say(f"Merci pour les {total_likes} coeurs les amis")
    engine.runAndWait()
    requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)"""


def on_gift(gift_name: str):
    print(f'oeoe y a le gift : {gift_name}')

    """if gift_name == "Vocal Bienvenue":
        manually_play_sound(f"./sounds/vocal_bienvenue.wav")

    if gift_name == "Vocal Arrivants":
        manually_play_sound(f"./sounds/vocal_arrivants.wav")

    if gift_name == "Vocal Global":
        manually_play_sound(f"./sounds/vocal_global.wav")

    if gift_name == "Rose":
        manually_play_sound(f"./sounds/bruit-de-pet.wav")

    if gift_name == "TikTok":
        manually_play_sound(f"./sounds/bruit_de_rot.wav")

    if gift_name == "Donut":
        manually_play_sound(f"./sounds/quoicoubeh.wav")

    if gift_name == "Alerte":
        requestToSend.send(runGiroMachine)
        play_video('./videos/alerte-rouge.mp4')
        manually_play_sound(f"./sounds/nuke_alarm.wav")
        time.sleep(8)
        requestToSend.send(stopGiroMachine)

    if gift_name == "Timide":
        requestToSend.send(runGiroMachine)
        manually_play_sound(f"./sounds/police-sirene.wav")
        manually_play_sound(f"./sounds/fbi-open-up.wav")
        time.sleep(10)
        requestToSend.send(stopGiroMachine)

    if gift_name == "Confettis":
        play_video('./videos/cri-de-cochon.mp4')

    if gift_name == "Sceptre":
        play_video('./videos/alien.mp4')
        manually_play_sound(f"./sounds/alien.wav")

    if gift_name == "398":
        play_video('./videos/got-that.mp4')

    if gift_name == "Corgi":
        play_video('./videos/cat.mp4')
        manually_play_sound(f"./sounds/nyan_cat.wav")

    if gift_name == "Oui oui":
        play_video('./videos/oui-oui.mp4')
        manually_play_sound(f"./sounds/oui_oui.wav")
        requestToSend.send(runSouffleurMachine)
        time.sleep(10)
        requestToSend.send(stopSouffleurMachine)

    if gift_name == "Balançoire":
        play_video('./videos/teuf.mp4')
        manually_play_sound(f"./sounds/losing-it.wav")

    if gift_name == "Cygne":
        play_video('./videos/cygne.mp4')
        manually_play_sound(f"./sounds/la_danse_des_canards.wav")
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)

    if gift_name == "Train":
        requestToSend.send(runSpotsLights)
        play_video('./videos/train.mp4')
        manually_play_sound(f"./sounds/train.wav")
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        time.sleep(9)
        requestToSend.send(stopSpotsLight)

    if gift_name == "Mine dor":
        requestToSend.send(runSpotsLights)
        play_video('./videos/thriller.mp4')
        manually_play_sound(f"./sounds/thriller.wav")
        requests.request("POST", PINGPONG_MACHINE_URL, headers=headers, data=body)
        time.sleep(14)
        requests.request("POST", PINGPONG_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)
        requestToSend.send(stopSpotsLight)

    if gift_name == "Champion":
        requestToSend.send(runSpotsLights)
        play_video('./videos/film_300.mp4')
        manually_play_sound(f"./sounds/jump.wav")
        requestToSend.send(runNeigeMachine)
        time.sleep(20)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(stopSpotsLight)

    if gift_name == "Baleine":
        requestToSend.send(runSpotsLights)
        play_video('./videos/reine-des-neiges.mp4')
        requestToSend.send(runBubbleMachine)
        requestToSend.send(runNeigeMachine)
        time.sleep(30)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(stopBubbleMachine)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)
        requestToSend.send(stopSpotsLight)

    if gift_name == "Moto":
        requestToSend.send(runSpotsLights)
        requestToSend.send(runBubbleMachine)
        requestToSend.send(runNeigeMachine)
        play_video('./videos/motorcycle.mp4')
        manually_play_sound(f"./sounds/motorcycle.wav")
        time.sleep(20)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(stopBubbleMachine)
        requestToSend.send(stopSpotsLight)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)

    if gift_name == "Jet":
        requestToSend.send(runSpotsLights)
        requestToSend.send(runBubbleMachine)
        requestToSend.send(runNeigeMachine)
        requestToSend.send(runMousseMachine)
        play_video('./videos/guiles.mp4')
        manually_play_sound(f"./sounds/guiles.wav")
        time.sleep(20)
        requestToSend.send(runMousseMachine)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(stopBubbleMachine)
        requestToSend.send(stopSpotsLight)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)

    if gift_name == "Interstellar":
        requestToSend.send(runSpotsLights)
        requestToSend.send(runBubbleMachine)
        requests.request("POST", PINGPONG_MACHINE_URL, headers=headers, data=body)
        requestToSend.send(runNeigeMachine)
        requestToSend.send(runMousseMachine)
        play_video('./videos/turn-down-to-what.mp4')
        time.sleep(30)
        requestToSend.send(runMousseMachine)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(stopBubbleMachine)
        requests.request("POST", PINGPONG_MACHINE_URL, headers=headers, data=body)
        requestToSend.send(stopSpotsLight)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)"""

    if gift_name == "1":
        manually_play_sound(f"./sounds/bruit-de-pet.wav")

    elif gift_name == "5":
        manually_play_sound(f"./sounds/bruit_de_rot.wav")

    elif gift_name == "10":
        manually_play_sound(f"./sounds/ouais_cest_greg.wav")

    elif gift_name == "15":
        manually_play_sound(f"./sounds/je_suis_bien.wav")

    elif gift_name == "20":
        manually_play_sound(f"./sounds/alerte_au_gogole.wav")

    elif gift_name == "30":
        manually_play_sound(f"./sounds/quoicoubeh.wav")

    elif gift_name == "49":
        manually_play_sound(f"./sounds/my_movie.wav")

    elif gift_name == "55":
        manually_play_sound(f"./sounds/on_sen_bat_les_couilles.wav")

    elif gift_name == "88":
        manually_play_sound(f"./sounds/chinese_rap_song.wav")

    elif gift_name == "99":
        play_video('./videos/alerte-rouge.mp4')
        manually_play_sound(f"./sounds/nuke_alarm.wav")
        time.sleep(8)
        #requestToSend.send(runGiroMachine)
        #requestToSend.send(stopGiroMachine)

    elif gift_name == "100":
        play_video('./videos/cri-de-cochon.mp4')

    elif gift_name == "150":
        play_video('./videos/rap-contenders-thai.mp4')

    elif gift_name == "169":
        play_video('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif gift_name == "199":
        manually_play_sound(f"./sounds/police-sirene.wav")
        manually_play_sound(f"./sounds/fbi-open-up.wav")
        time.sleep(10)
        #requestToSend.send(runGiroMachine)
        #requestToSend.send(stopGiroMachine)

    elif gift_name == "200":
        play_video('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif gift_name == "299":
        play_video('./videos/alien.mp4')
        manually_play_sound(f"./sounds/alien.wav")

    elif gift_name == "398":
        play_video('./videos/got-that.mp4')

    elif gift_name == "399":
        play_video('./videos/cat.mp4')
        manually_play_sound(f"./sounds/nyan_cat.wav")

    elif gift_name == "400":
        play_video('./videos/teuf.mp4')
        manually_play_sound(f"./sounds/losing-it.wav")

    elif gift_name == "450":
        play_video('./videos/mr-beast-phonk.mp4')

    elif gift_name == "500":
        requestToSend.send(runBubbleMachine)
        manually_play_sound(f"./sounds/oui_oui.wav")
        play_video('./videos/oui-oui.mp4')
        time.sleep(10)
        requestToSend.send(stopBubbleMachine)

    elif gift_name == "699":
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)
        manually_play_sound(f"./sounds/la_danse_des_canards.wav")
        play_video('./videos/cygne.mp4')

    elif gift_name == "899":
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", PINGPONG_MACHINE_URL, headers=headers, data=body)
        requestToSend.send(runSpotsLights)
        play_video('./videos/train.mp4')
        manually_play_sound(f"./sounds/train.wav")
        time.sleep(9)
        requestToSend.send(stopSpotsLight)

    elif gift_name == "1000":
        requestToSend.send(runSpotsLights)
        requests.request("POST", PINGPONG_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)
        play_video('./videos/thriller.mp4')
        manually_play_sound(f"./sounds/thriller.wav")
        time.sleep(14)
        requests.request("POST", PINGPONG_MACHINE_URL, headers=headers, data=body)
        requestToSend.send(stopSpotsLight)

    elif gift_name == "1500":
        requestToSend.send(runSpotsLights)
        requestToSend.send(runNeigeMachine)
        play_video('./videos/film_300.mp4')
        manually_play_sound(f"./sounds/jump.wav")
        time.sleep(20)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(stopSpotsLight)

    elif gift_name == "1999":
        requestToSend.send(runSpotsLights)
        requestToSend.send(runBubbleMachine)
        requestToSend.send(runNeigeMachine)
        play_video('./videos/reine-des-neiges.mp4')
        time.sleep(30)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(stopBubbleMachine)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)
        requestToSend.send(stopSpotsLight)

    elif gift_name == "3000":
        requestToSend.send(runSpotsLights)
        requestToSend.send(runBubbleMachine)
        requestToSend.send(runNeigeMachine)
        requestToSend.send(runMousseMachine)
        play_video('./videos/guiles.mp4')
        manually_play_sound(f"./sounds/guiles.wav")
        time.sleep(20)
        requestToSend.send(stopMousseMachine)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(stopBubbleMachine)
        requestToSend.send(stopSpotsLight)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)

    elif gift_name == "4000":
        requestToSend.send(runSpotsLights)
        requestToSend.send(runBubbleMachine)
        requestToSend.send(runNeigeMachine)
        requestToSend.send(runMousseMachine)
        requests.request("POST", PINGPONG_MACHINE_URL, headers=headers, data=body)
        play_video('./videos/turn-down-to-what.mp4')
        time.sleep(22)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)
        time.sleep(2)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", PINGPONG_MACHINE_URL, headers=headers, data=body)
        requestToSend.send(stopMousseMachine)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(stopBubbleMachine)
        requestToSend.send(stopSpotsLight)

    elif gift_name == "5000":
        requestToSend.send(runSpotsLights)
        requestToSend.send(runBubbleMachine)
        requestToSend.send(runNeigeMachine)
        requestToSend.send(runMousseMachine)
        requests.request("POST", PINGPONG_MACHINE_URL, headers=headers, data=body)
        play_video('./videos/interstellar.mp4')
        manually_play_sound(f"./sounds/interstellar.wav")
        time.sleep(30)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)
        time.sleep(2)
        requests.request("POST", SMOKE_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", SMOKE_TWO_MACHINE_URL, headers=headers, data=body)
        requests.request("POST", PINGPONG_MACHINE_URL, headers=headers, data=body)
        requestToSend.send(stopMousseMachine)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(stopBubbleMachine)
        requestToSend.send(stopSpotsLight)


def manually_play_sound(sound):
    loop.run_in_executor(ThreadPoolExecutor(), functools.partial(playsound, sound))


def play_video(video_path: str):
    os.system(f'/Applications/VLC.app/Contents/MacOS/VLC {video_path} --play-and-exit -f &')


"""def change_voice(language, gender='VoiceGenderFemale'):
    for voice in engine.getProperty('voices'):
        if language in voice.languages and gender == voice.gender:
            engine.setProperty('voice', voice.id)
            return True

    raise RuntimeError("Language '{}' for gender '{}' not found".format(language, gender))"""


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

        """if like_count:
            on_like(int(like_count))
            print("ici")"""


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
