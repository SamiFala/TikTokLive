import functools
import aiohttp
from aiohttp import web
import os
import json
import asyncio
# import pyttsx3
import requests
import shelve
from discord_webhook import DiscordWebhook, DiscordEmbed
from TikTokLive import TikTokLiveClient
from TikTokLive.types import GiftDetailed
from TikTokLive.types.events import CommentEvent, ConnectEvent, FollowEvent, LikeEvent, GiftEvent, MoreShareEvent, \
    EnvelopeEvent, DisconnectEvent
from concurrent.futures import ThreadPoolExecutor
from playsound import playsound

webhook = DiscordWebhook(
    url='https://discordapp.com/api/webhooks/1102639998987145426/_9xjoxzaFR_UoCyibmK3XuLA_5vkhzKbn0yQxgg8dNDZdkSxR7EqWul_6-9O8VkIDDr1')


def send_webhook(title, descrition, color):
    embed = DiscordEmbed(title=title, description=descrition, color=color)
    webhook.add_embed(embed)
    webhook.execute()


# Instantiate the client with the user's username
client: TikTokLiveClient = TikTokLiveClient(unique_id="@cam_off_tiktok")


def manually_play_sound(sound):
    client.loop.run_in_executor(ThreadPoolExecutor(), functools.partial(playsound, sound))


def play_video(video_path: str):
    os.system(f'/Applications/VLC.app/Contents/MacOS/VLC {video_path} --play-and-exit -f &')


"""def change_voice(language, gender='VoiceGenderFemale'):
    for voice in engine.getProperty('voices'):
        if language in voice.languages and gender == voice.gender:
            engine.setProperty('voice', voice.id)
            return True

    raise RuntimeError("Language '{}' for gender '{}' not found".format(language, gender))"""

requestToSend = requests.Session()
# commandes pour lancer
runGiroMachine = requests.Request('GET', 'http://192.168.1.21/relay/0?turn=on').prepare()
runBubbleMachine = requests.Request('GET', 'http://192.168.1.27/relay/0?turn=on').prepare()
runNeigeMachine = requests.Request('GET', 'http://192.168.1.29/relay/0?turn=on').prepare()
runMousseMachine = requests.Request('GET', 'http://192.168.1.26/relay/0?turn=on').prepare()
runSouffleurMachine = requests.Request('GET', 'http://192.168.1.28/relay/0?turn=on').prepare()
runConfettisMachine = requests.Request('GET', 'http://192.168.1.30/relay/0?turn=on').prepare()
runSpotsLights = requests.Request('GET', 'http://192.168.1.22/relay/0?turn=on').prepare()

# commandes pour stopper
stopGiroMachine = requests.Request('GET', 'http://192.168.1.21/relay/0?turn=off').prepare()
stopBubbleMachine = requests.Request('GET', 'http://192.168.1.27/relay/0?turn=off').prepare()
stopNeigeMachine = requests.Request('GET', 'http://192.168.1.29/relay/0?turn=off').prepare()
stopMousseMachine = requests.Request('GET', 'http://192.168.1.26/relay/0?turn=off').prepare()
stopSouffleurMachine = requests.Request('GET', 'http://192.168.1.28/relay/0?turn=off').prepare()
stopConfettisMachine = requests.Request('GET', 'http://192.168.1.30/relay/0?turn=off').prepare()
stopSpotsLight = requests.Request('GET', 'http://192.168.1.22/relay/0?turn=off').prepare()

shelly_plug_url = "https://shelly-40-eu.shelly.cloud/device/relay/control"

spot = "083a8dc1511d"
mousse = "f169d0"
souffleur = "f14512"
bulles = "f16102"
confettis = "4022d889bebd"
girophare = "4022d8871163"
neige = "f12e0e"

smoke_machine_url = "https://api.switch-bot.com/v1.0/devices/C7BDBFBB7A3E/commands"
pingpong_machine_url = "https://api.switch-bot.com/v1.0/devices/F3DFF2EAB30F/commands"
smoke_two_machine_url = "https://api.switch-bot.com/v1.0/devices/D5D127EFF039/commands"

body = json.dumps({
    "command": "turnOn",
    "parameter": "default",
    "commandType": "command"
})
headers = {
    'Authorization': 'Bearer 09f984c25288d88849a45b8dce8010b5f03104f8abc47ee87beb9031d97d6db550f2e903358b84f039b23ab3371032bc',
    'Content-Type': 'application/json'
}


def control_device(device_id, turn):
    data = {
        "channel": "0",
        "turn": turn,
        "id": device_id,
        "auth_key": "MTIxYjRidWlk73D0630FF6F6F4CA17F97B081604C84BE95B7997AC2BACD24EBC858C94EB4445B1C523DE1069652C"
    }
    requests.request("POST", shelly_plug_url, data=data)


def save_like_last_step():
    with shelve.open('like') as db:
        db['last_step'] = last_step


def get_like_last_step():
    result = 0

    with shelve.open('like') as db:
        result = db.get('last_step', 0)

    return result


last_step = get_like_last_step()
STEP_SIZE = 100

# engine = pyttsx3.init()
user_followers = []
objectifs = []


@client.on("connect")
async def on_connect(_: ConnectEvent):
    global objectifs
    print("Connected to Room ID:", client.room_id)
    await client.retrieve_available_gifts()
    objectifs = [
        {
            'name': '100% = MOUSSE',
            'targetCoins': 5000,
            'gifts': [gift.name for gift in client.available_gifts.values() if isinstance(gift, GiftDetailed)],
        },

    ]
    """{
        'name': 'Mon Objectif 2',
        'targetCoins': 100,
        'gifts': ["TikTok"],
    },"""


@client.on("disconnect")
async def relaunch(_: DisconnectEvent):
    await client.start()


@client.on("follow")
async def on_follow(event: FollowEvent):
    print(f"@{event.user.unique_id} followed the streamer!")
    # await send_message_to_all_clients('follow')
    if event.user.unique_id not in user_followers:
        user_followers.append(event.user.unique_id)
        manually_play_sound(f"./sounds/uwu.wav")


"""@client.on("more_share")
async def on_connect(event: MoreShareEvent):
    change_voice("fr_FR", "VoiceGenderMale")
    engine.say(f"Plus de {event.amount} personnes nous ont rejoint grace au partage de {event.user.unique_id}. Merci.")
    engine.runAndWait()"""

"""@client.on("weekly_ranking")
async def on_connect(event: WeeklyRankingEvent):
    if event.rank and event.rank % 10 == 0:
        requestToSend.send(runSpotsLights)
        manually_play_sound(f"./sounds/john_cena.wav")
        await asyncio.sleep(2)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        requestToSend.send(stopSpotsLight)"""

"""@client.on("envelope")
async def on_connect(event: EnvelopeEvent):
    change_voice("fr_FR", "VoiceGenderMale")
    engine.say(f"{event.treasure_box_user.unique_id} a envoyé un coffre. Merci.")
    engine.runAndWait()
    # print(f"{event.treasure_box_user.unique_id} -> {event.treasure_box_data}")"""

# Cassé Remettre quand c'est bon
# @client.on("like")
# async def on_like(event: LikeEvent):
#     global last_step
#     if event.total_likes < last_step * STEP_SIZE:
#         print('on a moins de like, je reset')
#         last_step = 0
#         save_like_last_step()
#     elif event.total_likes > 0 and event.total_likes >= last_step * STEP_SIZE:
#         requestToSend.send(runSpotsLights)
#         await asyncio.sleep(2)
#         manually_play_sound(f"./sounds/suu_cristiano.wav")
#         requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
#         last_step = event.total_likes // STEP_SIZE + 1
#         print(f'on passe au palier {last_step} ({event.total_likes})')
#         save_like_last_step()
#         requestToSend.send(stopSpotsLight)

"""@client.on("comment")
async def on_comment(event: CommentEvent):
    print(f"{event.user.nickname} -> {event.comment}")"""


async def execute_action_by_name(event):
    if event.gift.info.name == "Rose":
        manually_play_sound(f"./sounds/bruit-de-pet.wav")

    if event.gift.info.name == "TikTok":
        manually_play_sound(f"./sounds/bruit_de_rot.wav")

    if event.gift.info.name == "Doughnut":
        manually_play_sound(f"./sounds/quoicoubeh.wav")

    if event.gift.info.name == "Gamepad":
        requestToSend.send(runGiroMachine)
        play_video('./videos/alerte-rouge.mp4')
        manually_play_sound(f"./sounds/alerte_rouge.wav")
        await asyncio.sleep(8)
        requestToSend.send(stopGiroMachine)

    if event.gift.info.name == "I'm shy":
        requestToSend.send(runGiroMachine)
        manually_play_sound(f"./sounds/police-sirene.wav")
        manually_play_sound(f"./sounds/fbi-open-up.wav")
        await asyncio.sleep(10)
        requestToSend.send(stopGiroMachine)

    if event.gift.info.name == "Confetti":
        play_video('./videos/cri-de-cochon.mp4')

    if event.gift.info.name == "Sceptre":
        play_video('./videos/alien.mp4')
        manually_play_sound(f"./sounds/alien.wav")

    if event.gift.info.name == "Corgi":
        play_video('./videos/cat.mp4')
        manually_play_sound(f"./sounds/nyan_cat.wav")

    if event.gift.info.name == "Duck":
        play_video('./videos/oui-oui.mp4')
        manually_play_sound(f"./sounds/oui_oui.wav")
        requestToSend.send(runSouffleurMachine)
        await asyncio.sleep(10)
        requestToSend.send(stopSouffleurMachine)

    if event.gift.info.name == "Swing":
        play_video('./videos/teuf.mp4')
        manually_play_sound(f"./sounds/losing-it.wav")

    if event.gift.info.name == "Swan":
        play_video('./videos/cygne.mp4')
        manually_play_sound(f"./sounds/la_danse_des_canards.wav")
        requestToSend.send(runBubbleMachine)
        await asyncio.sleep(16)
        requestToSend.send(stopBubbleMachine)

    if event.gift.info.name == "Train":
        play_video('./videos/train.mp4')
        manually_play_sound(f"./sounds/train.wav")
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requestToSend.send(runSpotsLights)
        await asyncio.sleep(9)
        requestToSend.send(stopSpotsLight)

    if event.gift.info.name == "Gold Mine":
        play_video('./videos/thriller.mp4')
        manually_play_sound(f"./sounds/thriller.wav")
        requestToSend.send(runSpotsLights)
        requests.request("POST", pingpong_machine_url, headers=headers, data=body)
        await asyncio.sleep(14)
        requests.request("POST", pingpong_machine_url, headers=headers, data=body)
        requestToSend.send(stopSpotsLight)

    if event.gift.info.name == "Champion":
        play_video('./videos/film_300.mp4')
        manually_play_sound(f"./sounds/jump.wav")
        requestToSend.send(runSpotsLights)
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        await asyncio.sleep(30)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        requestToSend.send(stopSpotsLight)

    if event.gift.info.name == "Whale diving":
        play_video('./videos/reine-des-neiges.mp4')
        requestToSend.send(runSpotsLights)
        requestToSend.send(runNeigeMachine)
        await asyncio.sleep(12)
        requestToSend.send(stopNeigeMachine)
        await asyncio.sleep(10)
        requestToSend.send(stopSpotsLight)

    if event.gift.info.name == "Motorcycle":
        play_video('./videos/motorcycle.mp4')
        manually_play_sound(f"./sounds/motorcycle.wav")
        requestToSend.send(runSpotsLights)
        requestToSend.send(runNeigeMachine)
        await asyncio.sleep(10)
        await asyncio.sleep(9)
        requestToSend.send(stopSpotsLight)
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(2)
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(2)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(runBubbleMachine)
        await asyncio.sleep(10)
        requestToSend.send(stopBubbleMachine)

    if event.gift.info.name == "Private Jet":
        play_video('./videos/guiles.mp4')
        manually_play_sound(f"./sounds/guiles.wav")
        requestToSend.send(runSpotsLights)
        requestToSend.send(runNeigeMachine)
        await asyncio.sleep(4)
        requestToSend.send(runMousseMachine)
        await asyncio.sleep(22)
        requestToSend.send(stopSpotsLight)
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(2)
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        requestToSend.send(stopMousseMachine)
        requestToSend.send(stopNeigeMachine)
        requestToSend.send(runBubbleMachine)
        await asyncio.sleep(16)
        requestToSend.send(stopBubbleMachine)

    if event.gift.info.name == "Sports Car":
        play_video('./videos/turn-down-to-what.mp4')
        requestToSend.send(runSpotsLights)
        requests.request("POST", pingpong_machine_url, headers=headers, data=body)
        requestToSend.send(runBubbleMachine)
        await asyncio.sleep(12)
        requestToSend.send(stopBubbleMachine)
        requests.request("POST", pingpong_machine_url, headers=headers, data=body)
        requestToSend.send(runNeigeMachine)
        await asyncio.sleep(12)
        requestToSend.send(stopNeigeMachine)
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(2)
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(2)
        requestToSend.send(runConfettisMachine)
        await asyncio.sleep(2)
        requestToSend.send(stopConfettisMachine)
        requestToSend.send(stopSpotsLight)


async def execute_action_by_price(event):
    if event.gift.info.diamond_count == 1:
        manually_play_sound(f"./sounds/bruit-de-pet.wav")

    if event.gift.info.diamond_count == 5:
        manually_play_sound(f"./sounds/bruit_de_rot.wav")

    if event.gift.info.diamond_count == 10:
        manually_play_sound(f"./sounds/ouais_cest_greg.wav")

    if event.gift.info.diamond_count == 15:
        manually_play_sound(f"./sounds/je_suis_bien.wav")

    if event.gift.info.diamond_count == 20:
        manually_play_sound(f"./sounds/alerte_au_gogole.wav")

    if event.gift.info.diamond_count == 30:
        manually_play_sound(f"./sounds/quoicoubeh.wav")

    if event.gift.info.diamond_count == 49:
        manually_play_sound(f"./sounds/my_movie.wav")

    if event.gift.info.diamond_count == 55:
        manually_play_sound(f"./sounds/on_sen_bat_les_couilles.wav")

    if event.gift.info.diamond_count == 88:
        manually_play_sound(f"./sounds/chinese_rap_song.wav")

    if event.gift.info.diamond_count == 99:
        control_device(girophare, "on")
        play_video('./videos/alerte-rouge.mp4')
        manually_play_sound(f"./sounds/nuke_alarm.wav")
        await asyncio.sleep(8)
        control_device(girophare, "off")

    if event.gift.info.diamond_count == 100:
        play_video('./videos/cri-de-cochon.mp4')

    if event.gift.info.diamond_count == 150:
        play_video('./videos/rap-contenders-thai.mp4')

    if event.gift.info.diamond_count == 169:
        play_video('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    if event.gift.info.diamond_count == 199:
        control_device(girophare, "on")
        manually_play_sound(f"./sounds/police-sirene.wav")
        manually_play_sound(f"./sounds/fbi-open-up.wav")
        await asyncio.sleep(10)
        control_device(girophare, "off")

    if event.gift.info.diamond_count == 200:
        play_video('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    if event.gift.info.diamond_count == 299:
        play_video('./videos/alien.mp4')
        manually_play_sound(f"./sounds/alien.wav")

    if event.gift.info.diamond_count == 398:
        play_video('./videos/got-that.mp4')

    if event.gift.info.diamond_count == 399:
        play_video('./videos/cat.mp4')
        manually_play_sound(f"./sounds/nyan_cat.wav")

    if event.gift.info.diamond_count == 400:
        play_video('./videos/teuf.mp4')
        manually_play_sound(f"./sounds/losing-it.wav")

    if event.gift.info.diamond_count == 450:
        play_video('./videos/mr-beast-phonk.mp4')

    if event.gift.info.diamond_count == 500:
        play_video('./videos/oui-oui.mp4')
        manually_play_sound(f"./sounds/oui_oui.wav")
        control_device(souffleur, "on")
        await asyncio.sleep(10)
        control_device(souffleur, "off")

    if event.gift.info.diamond_count == 699:
        play_video('./videos/cygne.mp4')
        manually_play_sound(f"./sounds/la_danse_des_canards.wav")
        control_device(bulles, "on")
        await asyncio.sleep(16)
        control_device(bulles, "off")

    if event.gift.info.diamond_count == 899:
        play_video('./videos/train.mp4')
        manually_play_sound(f"./sounds/train.wav")
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        control_device(spot, "on")
        await asyncio.sleep(9)
        control_device(spot, "off")

    if event.gift.info.diamond_count == 1000:
        play_video('./videos/thriller.mp4')
        manually_play_sound(f"./sounds/thriller.wav")
        control_device(spot, "on")
        requests.request("POST", pingpong_machine_url, headers=headers, data=body)
        await asyncio.sleep(14)
        requests.request("POST", pingpong_machine_url, headers=headers, data=body)
        control_device(spot, "off")

    if event.gift.info.diamond_count == 1500:
        play_video('./videos/film_300.mp4')
        manually_play_sound(f"./sounds/jump.wav")
        control_device(spot, "on")
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(10)
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(20)
        control_device(spot, "off")

    if event.gift.info.diamond_count == 1999:
        play_video('./videos/reine-des-neiges.mp4')
        control_device(spot, "on")
        control_device(neige, "on")
        await asyncio.sleep(12)
        control_device(neige, "off")
        await asyncio.sleep(10)
        control_device(spot, "off")

    if event.gift.info.diamond_count == 3000:
        play_video('./videos/motorcycle.mp4')
        manually_play_sound(f"./sounds/motorcycle.wav")
        control_device(spot, "on")
        control_device(neige, "on")
        await asyncio.sleep(10)
        await asyncio.sleep(9)
        control_device(spot, "off")
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(2)
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(2)
        control_device(neige, "off")
        control_device(bulles, "on")
        await asyncio.sleep(10)
        control_device(bulles, "off")

    if event.gift.info.diamond_count == 4000:
        play_video('./videos/guiles.mp4')
        manually_play_sound(f"./sounds/guiles.wav")
        control_device(spot, "on")
        control_device(neige, "on")
        await asyncio.sleep(4)
        control_device(mousse, "on")
        await asyncio.sleep(22)
        control_device(spot, "off")
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(2)
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        control_device(mousse, "off")
        control_device(neige, "off")
        control_device(bulles, "on")
        await asyncio.sleep(16)
        control_device(bulles, "off")

    if event.gift.info.diamond_count == 5000:
        play_video('./videos/turn-down-to-what.mp4')
        control_device(spot, "on")
        requests.request("POST", pingpong_machine_url, headers=headers, data=body)
        control_device(bulles, "on")
        await asyncio.sleep(12)
        control_device(bulles, "off")
        requests.request("POST", pingpong_machine_url, headers=headers, data=body)
        control_device(neige, "on")
        await asyncio.sleep(12)
        control_device(neige, "off")
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(2)
        requests.request("POST", smoke_machine_url, headers=headers, data=body)
        requests.request("POST", smoke_two_machine_url, headers=headers, data=body)
        await asyncio.sleep(2)
        control_device(confettis, "on")
        await asyncio.sleep(2)
        control_device(confettis, "off")
        control_device(spot, "off")


@client.on("error")
async def on_connect(error: Exception):
    send_webhook('Erreur', str(error), 'ff0000')
    print(error)


@client.on("gift")
async def on_gift(event: GiftEvent):
    # Streakable gift & streak is over
    if event.gift and event.gift.streakable and not event.gift.streaking:
        print(f"{event.user.unique_id} sent {event.gift.count}x \"{event.gift.info.name}\"")
        await send_message_to_all_clients('gift', {
            'name': event.gift.info.name,
            'count': event.gift.count,
            'image_url': event.gift.info.image.urls[0],
            'username': event.user.unique_id,
            'price': event.gift.info.diamond_count,
        })
        await execute_action_by_price(event)
    # Non-streakable gift
    elif not event.gift.streakable:
        print(f"{event.user.unique_id} sent \"{event.gift.info.name}\"")
        await send_message_to_all_clients('gift', {
            'name': event.gift.info.name,
            'count': 1,
            'image_url': event.gift.info.image.urls[0],
            'username': event.user.unique_id,
            'price': event.gift.info.diamond_count,
        })
        await execute_action_by_price(event)


def set_objectif_status(objectif_name, progress):
    with shelve.open('objectifs_progress') as db:
        db[objectif_name] = progress


def get_objectif_status(objectif_name):
    result = 0

    with shelve.open('objectifs_progress') as db:
        result = db.get(objectif_name, 0)

    return result


async def index(request):
    with open('./frontend/index.html', 'r') as f:
        content = f.read()
    return web.Response(content_type='text/html', text=content)


connected_clients = set()


async def websocket_handler(request):
    global objectifs
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    connected_clients.add(ws)
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'request_data':
                    data = {"action": "init", "params": objectifs}
                    await ws.send_json(data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('WebSocket connection closed with exception %s' % ws.exception())
    finally:
        connected_clients.remove(ws)

    return ws


async def send_message_to_all_clients(action, params=None):
    data = {"action": action, "params": params}
    for ws in connected_clients:
        await ws.send_json(data)


async def public_handler(request):
    path = request.match_info['path']
    with open(f'./frontend/public/{path}', 'r') as f:
        content = f.read()
    content_type = 'application/javascript'
    if path.endswith('.css'):
        content_type = 'text/css'
    return web.Response(content_type=content_type, text=content)


async def get_objectif_progress_handler(request):
    objectif_name = request.match_info['objectif_name']
    count = get_objectif_status(objectif_name)
    return web.Response(content_type='text', text=str(count))


async def set_objectif_progress_handler(request):
    body = await request.json()
    set_objectif_status(body['name'], body['progress'])
    return web.Response(content_type='text', text='ok')


async def run_server_and_client():
    app = web.Application()
    app.add_routes(
        [
            web.get('/', index),
            web.get('/websocket', websocket_handler),
            web.get(r'/public/{path:.*}', public_handler),
            web.get(r'/status/{objectif_name:.*}', get_objectif_progress_handler),
            web.post(r'/setstatus', set_objectif_progress_handler),
        ]
    )

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    print('http://localhost:8080')

    # Lancez le client TikTok en parallèle avec le serveur web
    client_task = asyncio.create_task(client.start())

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
        client_task.cancel()

    await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(run_server_and_client())
