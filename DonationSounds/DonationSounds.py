import os
import json
import asyncio
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.events import FollowEvent, GiftEvent, DisconnectEvent, UnknownEvent, ConnectEvent
from concurrent.futures import ThreadPoolExecutor
from TikTokLive.client.logger import LogLevel
from playsound import playsound
from ratelimiter import RateLimiter

client: TikTokLiveClient = TikTokLiveClient(unique_id="@cam_off_tiktok")

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
        "giro": 'http://192.168.1.20/relay/0?turn=on',
        "bubble": 'http://192.168.1.19/relay/0?turn=on',
        "neige": 'http://192.168.1.17/relay/0?turn=on',
        "mousse": 'http://192.168.1.18/relay/0?turn=on',
        "souffleur": 'http://192.168.1.26/relay/0?turn=on',
        "spots": 'http://192.168.1.16/relay/0?turn=on',
        "confettis": 'http://192.168.1.27/relay/0?turn=on'
    },
    "stop": {
        "giro": 'http://192.168.1.20/relay/0?turn=off',
        "bubble": 'http://192.168.1.19/relay/0?turn=off',
        "neige": 'http://192.168.1.17/relay/0?turn=off',
        "mousse": 'http://192.168.1.18/relay/0?turn=off',
        "souffleur": 'http://192.168.1.26/relay/0?turn=off',
        "spots": 'http://192.168.1.16/relay/0?turn=off',
        "confettis": 'http://192.168.1.27/relay/0?turn=off'
    }
}

device_ids = {
    "spots": "f14512",
    "mousse": "f169d0",
    "souffleur": "f14512",
    "bubble": "f16102",
    "confettis": "4022d889bebd",
    "giro": "083a8dc1511d",
    "neige": "f12e0e"
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
            send_webhook('Error', 'Error playing sound', error_detail=e, color="FF0000")
            print(f"Error playing sound: {e}")

    def play_video(self, video_path):
        try:
            os.system(f'/Applications/VLC.app/Contents/MacOS/VLC {video_path} --play-and-exit -f &')
        except Exception as e:
            send_webhook('Error', 'Error playing video', error_detail=e, color="FF0000")
            print(f"Error playing video: {e}")

    def control_device(self, device_name, turn):
        device_id = device_ids.get(device_name)
        if not device_id:
            print(f"Device {device_name} not found")
            return
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
                send_webhook('Error', 'Error controlling device', error_detail=err, color="FF0000")
                print(f"Error controlling device: {err}")
                print(f"Response content: {response.content}")

    def send_smoke_command(self, url):
        body = json.dumps({
            "command": "turnOn",
            "parameter": "default",
            "commandType": "command"
        })
        headers = {
            'Authorization': 'Bearer 09f984c25288d88849a45b8dce8010b5f03104f8abc47ee87beb9031d97d6db550f2e903358b84f039b23ab3371032bc',
            'Content-Type': 'application/json'
        }
        with rate_limiter:
            try:
                response = requests.post(url, headers=headers, data=body)
                response.raise_for_status()
            except requests.exceptions.RequestException as err:
                send_webhook('Error', 'Error sending smoke command', error_detail=err, color="FF0000")
                print(f"Error sending smoke command: {err}")

    def send_ping_pong_command(self, url):
        body = json.dumps({
            "command": "turnOn",
            "parameter": "default",
            "commandType": "command"
        })
        headers = {
            'Authorization': 'Bearer 09f984c25288d88849a45b8dce8010b5f03104f8abc47ee87beb9031d97d6db550f2e903358b84f039b23ab3371032bc',
            'Content-Type': 'application/json'
        }
        with rate_limiter:
            try:
                response = requests.post(url, headers=headers, data=body)
                response.raise_for_status()
            except requests.exceptions.RequestException as err:
                send_webhook('Error', 'Error sending pingpong command', error_detail=err, color="FF0000")
                print(f"Error sending pingpong command: {err}")


controller = DeviceController(client)


async def execute_action_by_diamonds(diamond_count):
    if diamond_count == 1:
        await controller.manually_play_sound(f"./sounds/bruit-de-pet.wav")

    elif diamond_count == 5:
        await controller.manually_play_sound(f"./sounds/bruit_de_rot.wav")

    elif diamond_count == 10:
        await controller.manually_play_sound(f"./sounds/ouais_cest_greg.wav")

    elif diamond_count == 15:
        await controller.manually_play_sound(f"./sounds/je_suis_bien.wav")

    elif diamond_count == 20:
        await controller.manually_play_sound(f"./sounds/alerte_au_gogole.wav")

    elif diamond_count == 30:
        await controller.manually_play_sound(f"./sounds/quoicoubeh.wav")

    elif diamond_count == 49:
        await controller.manually_play_sound(f"./sounds/my_movie.wav")

    elif diamond_count == 55:
        await controller.manually_play_sound(f"./sounds/on_sen_bat_les_couilles.wav")

    elif diamond_count == 88:
        await controller.manually_play_sound(f"./sounds/chinese_rap_song.wav")

    elif diamond_count == 99:
        controller.control_device("giro", "on")
        controller.play_video('./videos/alerte-rouge.mp4')
        await controller.manually_play_sound(f"./sounds/nuke_alarm.wav")
        await asyncio.sleep(8)
        controller.control_device("giro", "off")

    elif diamond_count == 100:
        controller.play_video('./videos/cri-de-cochon.mp4')

    elif diamond_count == 150:
        controller.play_video('./videos/rap-contenders-thai.mp4')

    elif diamond_count == 169:
        controller.play_video('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif diamond_count == 199:
        controller.control_device("giro", "on")
        await controller.manually_play_sound(f"./sounds/police-sirene.wav")
        await controller.manually_play_sound(f"./sounds/fbi-open-up.wav")
        await asyncio.sleep(10)
        controller.control_device("giro", "off")

    elif diamond_count == 200:
        controller.play_video('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif diamond_count == 299:
        controller.play_video('./videos/alien.mp4')
        await controller.manually_play_sound(f"./sounds/alien.wav")

    elif diamond_count == 398:
        controller.play_video('./videos/got-that.mp4')

    elif diamond_count == 399:
        controller.play_video('./videos/cat.mp4')
        await controller.manually_play_sound(f"./sounds/nyan_cat.wav")

    elif diamond_count == 400:
        controller.play_video('./videos/teuf.mp4')
        await controller.manually_play_sound(f"./sounds/losing-it.wav")

    elif diamond_count == 450:
        controller.play_video('./videos/mr-beast-phonk.mp4')

    elif diamond_count == 500:
        await controller.manually_play_sound(f"./sounds/oui_oui.wav")
        controller.control_device("bubble", "on")
        controller.play_video('./videos/oui-oui.mp4')
        await asyncio.sleep(10)
        controller.control_device("bubble", "off")

    elif diamond_count == 699:
        controller.send_smoke_command(SMOKE_MACHINE_URL)
        controller.send_smoke_command(SMOKE_TWO_MACHINE_URL)
        await controller.manually_play_sound(f"./sounds/la_danse_des_canards.wav")
        controller.play_video('./videos/cygne.mp4')

    elif diamond_count == 899:
        controller.send_smoke_command(SMOKE_MACHINE_URL)
        controller.send_ping_pong_command(PINGPONG_MACHINE_URL)
        controller.control_device("spots", "on")
        controller.play_video('./videos/train.mp4')
        await controller.manually_play_sound(f"./sounds/train.wav")
        await asyncio.sleep(9)
        controller.control_device("spots", "off")
        controller.send_ping_pong_command(PINGPONG_MACHINE_URL)

    elif diamond_count == 1000:
        controller.control_device("spots", "on")
        controller.send_ping_pong_command(PINGPONG_MACHINE_URL)
        controller.send_smoke_command(SMOKE_MACHINE_URL)
        controller.send_smoke_command(SMOKE_TWO_MACHINE_URL)
        controller.play_video('./videos/thriller.mp4')
        await controller.manually_play_sound(f"./sounds/thriller.wav")
        await asyncio.sleep(14)
        controller.send_ping_pong_command(PINGPONG_MACHINE_URL)
        controller.control_device("spots", "off")

    elif diamond_count == 1500:
        controller.control_device("spots", "on")
        controller.control_device("neige", "on")
        controller.play_video('./videos/film_300.mp4')
        await controller.manually_play_sound(f"./sounds/jump.wav")
        await asyncio.sleep(20)
        controller.control_device("neige", "off")
        controller.control_device("spots", "off")

    elif diamond_count == 1999:
        controller.control_device("spots", "on")
        controller.control_device("bubble", "on")
        controller.control_device("neige", "on")
        controller.play_video('./videos/reine-des-neiges.mp4')
        await asyncio.sleep(30)
        controller.control_device("neige", "off")
        controller.control_device("bubble", "off")
        controller.send_smoke_command(SMOKE_MACHINE_URL)
        controller.send_smoke_command(SMOKE_TWO_MACHINE_URL)
        controller.control_device("spots", "off")

    elif diamond_count == 3000:
        controller.control_device("spots", "on")
        controller.control_device("bubble", "on")
        controller.control_device("neige", "on")
        controller.control_device("mousse", "on")
        controller.play_video('./videos/guiles.mp4')
        await controller.manually_play_sound(f"./sounds/guiles.wav")
        await asyncio.sleep(20)
        controller.control_device("mousse", "off")
        controller.control_device("neige", "off")
        controller.control_device("bubble", "off")
        controller.control_device("spots", "off")
        controller.send_smoke_command(SMOKE_MACHINE_URL)
        controller.send_smoke_command(SMOKE_TWO_MACHINE_URL)

    elif diamond_count == 4000:
        controller.control_device("spots", "on")
        controller.control_device("bubble", "on")
        controller.control_device("neige", "on")
        controller.control_device("mousse", "on")
        controller.send_ping_pong_command(PINGPONG_MACHINE_URL)
        controller.play_video('./videos/turn-down-to-what.mp4')
        await asyncio.sleep(22)
        controller.send_smoke_command(SMOKE_MACHINE_URL)
        controller.send_smoke_command(SMOKE_TWO_MACHINE_URL)
        await asyncio.sleep(2)
        controller.send_smoke_command(SMOKE_MACHINE_URL)
        controller.send_smoke_command(SMOKE_TWO_MACHINE_URL)
        controller.send_ping_pong_command(PINGPONG_MACHINE_URL)
        controller.control_device("mousse", "off")
        controller.control_device("neige", "off")
        controller.control_device("bubble", "off")
        controller.control_device("spots", "off")

    elif diamond_count == 5000:
        controller.control_device("spots", "on")
        controller.control_device("bubble", "on")
        controller.control_device("neige", "on")
        controller.control_device("mousse", "on")
        controller.send_ping_pong_command(PINGPONG_MACHINE_URL)
        controller.play_video('./videos/interstellar.mp4')
        await controller.manually_play_sound(f"./sounds/interstellar.wav")
        await asyncio.sleep(30)
        controller.send_smoke_command(SMOKE_MACHINE_URL)
        controller.send_smoke_command(SMOKE_TWO_MACHINE_URL)
        await asyncio.sleep(2)
        controller.send_smoke_command(SMOKE_MACHINE_URL)
        controller.send_smoke_command(SMOKE_TWO_MACHINE_URL)
        controller.send_ping_pong_command(PINGPONG_MACHINE_URL)
        controller.control_device("mousse", "off")
        controller.control_device("neige", "off")
        controller.control_device("bubble", "off")
        controller.control_device("spots", "off")


ACTIONS = {
    1: execute_action_by_diamonds,
    5: execute_action_by_diamonds,
    10: execute_action_by_diamonds,
    15: execute_action_by_diamonds,
    20: execute_action_by_diamonds,
    30: execute_action_by_diamonds,
    49: execute_action_by_diamonds,
    55: execute_action_by_diamonds,
    88: execute_action_by_diamonds,
    99: execute_action_by_diamonds,
    100: execute_action_by_diamonds,
    150: execute_action_by_diamonds,
    169: execute_action_by_diamonds,
    199: execute_action_by_diamonds,
    200: execute_action_by_diamonds,
    299: execute_action_by_diamonds,
    398: execute_action_by_diamonds,
    399: execute_action_by_diamonds,
    400: execute_action_by_diamonds,
    450: execute_action_by_diamonds,
    500: execute_action_by_diamonds,
    699: execute_action_by_diamonds,
    899: execute_action_by_diamonds,
    1000: execute_action_by_diamonds,
    1500: execute_action_by_diamonds,
    1999: execute_action_by_diamonds,
    3000: execute_action_by_diamonds,
    4000: execute_action_by_diamonds,
    5000: execute_action_by_diamonds
}


@client.on(DisconnectEvent)
async def relaunch(_: DisconnectEvent):
    await client.start()


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    client.logger.info(f"Connected to @{event.unique_id}!")


@client.on(FollowEvent)
async def on_follow(event: FollowEvent):
    if event.user.unique_id not in user_followers:
        user_followers.append(event.user.unique_id)
        await controller.manually_play_sound(f"./sounds/uwu.wav")


@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    client.logger.info("Received a gift!")
    # Streakable gift & streak is over
    if event.gift.streakable and not event.streaking:
        print(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.name}\"")
        await ACTIONS.get(event.gift.diamond_count, lambda _: None)(event.gift.diamond_count)
    # Non-streakable gift
    elif not event.gift.streakable:
        print(f"{event.user.unique_id} sent \"{event.gift.name}\"")
        await ACTIONS.get(event.gift.diamond_count, lambda _: None)(event.gift.diamond_count)


if __name__ == '__main__':
    client.logger.setLevel(LogLevel.INFO.value)
    send_webhook('Start', 'The client has started', color="00FF00")
    try:
        client.run()
    except KeyboardInterrupt:
        send_webhook('Shutdown', 'The client has been shut down', color="FF0000")
        print("Client has been shut down")
