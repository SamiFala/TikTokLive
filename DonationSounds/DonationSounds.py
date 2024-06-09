import os
import json
import asyncio
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.events import FollowEvent, GiftEvent, DisconnectEvent, UnknownEvent
from concurrent.futures import ThreadPoolExecutor
from playsound import playsound
from ratelimiter import RateLimiter

client: TikTokLiveClient = TikTokLiveClient(unique_id="@flawlyss_keke97")

# Constantes regroupées
SHELLY_PLUG_URL = "https://shelly-40-eu.shelly.cloud/device/relay/control"
WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1102639998987145426/_9xjoxzaFR_UoCyibmK3XuLA_5vkhzKbn0yQxgg8dNDZdkSxR7EqWul_6-9O8VkIDDr1'
SMOKE_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/C7BDBFBB7A3E/commands"
SMOKE_TWO_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/D5D127EFF039/commands"
PINGPONG_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/F3DFF2EAB30F/commands"

user_followers = []
requestToSend = requests.Session()
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


def send_webhook(event, description, error_detail=None, color="242424"):
    embed = DiscordEmbed(title=f"Evenement de {event}", description=description, color=color)
    if error_detail:
        embed.add_embed_field(name='Détails de l\'erreur', value=str(error_detail))
    webhook.add_embed(embed)
    try:
        response = webhook.execute()
        if response.status_code != 200:
            print(f"Webhook failed with status code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Failed to send webhook: {e}")


class DeviceController:
    def __init__(self, client):
        self.client = client

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


controller = DeviceController(client)


# Actions pour les diamants
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


ACTIONS = {
    1: lambda count: perform_action(sound="./sounds/bruit-de-pet.wav", sound_count=count),
    5: lambda count: perform_action(sound="./sounds/bruit_de_rot.wav", sound_count=count),
    10: lambda count: perform_action(sound="./sounds/ouais_cest_greg.wav", sound_count=count),
    15: lambda count: perform_action(sound="./sounds/je_suis_bien.wav", sound_count=count),
    20: lambda count: perform_action(sound="./sounds/alerte_au_gogole.wav", sound_count=count),
    30: lambda count: perform_action(sound="./sounds/quoicoubeh.wav", sound_count=count),
    49: lambda count: perform_action(sound="./sounds/my_movie.wav", sound_count=count),
    55: lambda count: perform_action(sound="./sounds/on_sen_bat_les_couilles.wav", sound_count=count),
    88: lambda count: perform_action(sound="./sounds/chinese_rap_song.wav", sound_count=count),
    99: lambda count: perform_action(video='./videos/alerte-rouge.mp4', sound="./sounds/nuke_alarm.wav", device_on="giro", sleep_before_off=8, device_off="giro"),
    100: lambda count: perform_action(video='./videos/cri-de-cochon.mp4'),
    150: lambda count: perform_action(video='./videos/rap-contenders-thai.mp4'),
    169: lambda count: perform_action(video='./videos/crazy-frog.mp4'),
    199: lambda count: perform_action(sound="./sounds/police-sirene.wav", device_on="giro", sleep_before_off=10, device_off="giro"),
    200: lambda count: perform_action(video='./videos/tu-vas-repartir-mal-mon-copain.mp4'),
    299: lambda count: perform_action(video='./videos/alien.mp4', sound="./sounds/alien.wav"),
    398: lambda count: perform_action(video='./videos/got-that.mp4'),
    399: lambda count: perform_action(video='./videos/cat.mp4', sound="./sounds/nyan_cat.wav"),
    400: lambda count: perform_action(video='./videos/oui-oui.mp4', sound="./sounds/oui_oui.wav", device_on="souffleur", sleep_before_off=10, device_off="souffleur"),
    450: lambda count: perform_action(video='./videos/mr-beast-phonk.mp4'),
    500: lambda count: perform_action(video='./videos/cygne.mp4', sound="./sounds/la_danse_des_canards.wav", device_on="bubble", sleep_before_off=16, device_off="bubble"),
    699: lambda count: perform_action(video='./videos/train.mp4', sound="./sounds/train.wav", device_on="spots", sleep_before_off=9, device_off="spots"),
    899: lambda count: perform_action(video='./videos/thriller.mp4', sound="./sounds/thriller.wav", device_on="spots", sleep_before_off=14, device_off="spots"),
    1000: lambda count: perform_action(video='./videos/film_300.mp4', sound="./sounds/jump.wav", device_on="spots", sleep_before_off=20, device_off="spots"),
    1500: lambda count: perform_action(video='./videos/reine-des-neiges.mp4', device_on="neige", sleep_before_off=22, device_off="neige"),
    1999: lambda count: perform_action(video='./videos/motorcycle.mp4', sound="./sounds/motorcycle.wav", device_on="neige", sleep_before_off=10, device_off="neige"),
    3000: lambda count: perform_action(video='./videos/guiles.mp4', sound="./sounds/guiles.wav", device_on="mousse", sleep_before_off=22, device_off="mousse"),
    4000: lambda count: perform_action(video='./videos/turn-down-to-what.mp4', device_on="confettis", sleep_before_off=2, device_off="confettis"),
    5000: lambda count: print("5000")
}


@client.on(DisconnectEvent)
async def relaunch(_: DisconnectEvent):
    await client.start()


@client.on(FollowEvent)
async def on_follow(event: FollowEvent):
    if event.user.unique_id not in user_followers:
        user_followers.append(event.user.unique_id)
        await controller.manually_play_sound(f"./sounds/uwu.wav")


"""@client.on(UnknownEvent)
async def on_error(event: UnknownEvent):
    send_webhook('Unknown Event', 'An unknown event occurred', str(event))
    print(event)"""


@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    client.logger.info("Received a gift!")

    # Streakable gift & streak is over
    if event.gift.streakable and not event.streaking:
        print(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.name}\"")
        await ACTIONS.get(event.gift.diamond_count, lambda count: asyncio.sleep(0))(event.repeat_count)

    # Non-streakable gift
    elif not event.gift.streakable:
        print(f"{event.user.unique_id} sent \"{event.gift.name}\"")
        await ACTIONS.get(event.gift.diamond_count, lambda count: asyncio.sleep(0))(event.repeat_count)


if __name__ == '__main__':
    send_webhook('Start', 'The client has started', color="00FF00")
    try:
        client.run()
    except KeyboardInterrupt:
        send_webhook('Shutdown', 'The client has been shut down', color="FF0000")
        print("Client has been shut down")
