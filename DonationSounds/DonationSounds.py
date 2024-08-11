import logging
import os
import json
import asyncio
import requests
import websockets
from discord_webhook import DiscordWebhook, DiscordEmbed
from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.events import FollowEvent, GiftEvent, DisconnectEvent, ConnectEvent, LiveEndEvent, CommentEvent
from TikTokLive.client.logger import LogLevel
from playsound import playsound
import signal

client: TikTokLiveClient = TikTokLiveClient(unique_id="@cam_off_tiktok")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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


user_followers = []

webhook = DiscordWebhook(url=WEBHOOK_URL)


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


async def execute_action_by_diamonds(gift_value):
    if gift_value == 1:
        await controller.manually_play_sound("./sounds/bruit-de-pet.wav")

    elif gift_value == 5:
        await controller.manually_play_sound("./sounds/bruit_de_rot.wav")

    elif gift_value == 10:
        await controller.manually_play_sound("./sounds/ouais_cest_greg.wav")

    elif gift_value == 15:
        await controller.manually_play_sound("./sounds/je_suis_bien.wav")

    elif gift_value == 20:
        await controller.manually_play_sound("./sounds/alerte_au_gogole.wav")

    elif gift_value == 30:
        await controller.manually_play_sound("./sounds/quoicoubeh.wav")

    elif gift_value == 49:
        await controller.manually_play_sound("./sounds/my_movie.wav")

    elif gift_value == 55:
        await controller.manually_play_sound("./sounds/on_sen_bat_les_couilles.wav")

    elif gift_value == 88:
        await controller.manually_play_sound("./sounds/chinese_rap_song.wav")

    elif gift_value == 99:
        await controller.control_multiple_relays({"girophare": devices["girophare"]}, "on")
        await controller.play_video('./videos/alerte-rouge.mp4')
        await controller.manually_play_sound(f"./sounds/nuke_alarm.wav")
        await asyncio.sleep(8)
        await controller.control_multiple_relays({"girophare": devices["girophare"]}, "off")

    elif gift_value == 100:
        await controller.play_video('./videos/cri-de-cochon.mp4')

    elif gift_value == 150:
        await controller.play_video('./videos/rap-contenders-thai.mp4')

    elif gift_value == 169:
        await controller.play_video('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif gift_value == 199:
        await controller.control_multiple_relays({"girophare": devices["girophare"]}, "on")
        await controller.manually_play_sound(f"./sounds/police-sirene.wav")
        await controller.manually_play_sound(f"./sounds/fbi-open-up.wav")
        await asyncio.sleep(10)
        await controller.control_multiple_relays({"girophare": devices["girophare"]}, "off")

    elif gift_value == 200:
        await controller.play_video('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif gift_value == 299:
        await controller.play_video('./videos/alien.mp4')
        await controller.manually_play_sound(f"./sounds/alien.wav")

    elif gift_value == 398:
        await controller.play_video('./videos/got-that.mp4')

    elif gift_value == 399:
        await controller.play_video('./videos/cat.mp4')
        await controller.manually_play_sound(f"./sounds/nyan_cat.wav")

    elif gift_value == 400:
        await controller.play_video('./videos/teuf.mp4')
        await controller.manually_play_sound(f"./sounds/losing-it.wav")

    elif gift_value == 450:
        await controller.play_video('./videos/mr-beast-phonk.mp4')

    elif gift_value == 500:
        await controller.manually_play_sound(f"./sounds/oui_oui.wav")
        await controller.control_multiple_relays({"bulles": devices["bulles"]}, "on")
        await controller.play_video('./videos/oui-oui.mp4')
        await asyncio.sleep(10)
        await controller.control_multiple_relays({"bulles": devices["bulles"]}, "off")

    elif gift_value == 699:
        await controller.send_command(SMOKE_MACHINE_URL)
        await controller.send_command(SMOKE_TWO_MACHINE_URL)
        await controller.manually_play_sound(f"./sounds/la_danse_des_canards.wav")
        await controller.play_video('./videos/cygne.mp4')

    elif gift_value == 899:
        await controller.send_command(SMOKE_MACHINE_URL)
        await controller.send_command(PINGPONG_MACHINE_URL)
        await controller.control_multiple_relays({"spots": devices["spots"]}, "on")
        await controller.play_video('./videos/train.mp4')
        await controller.manually_play_sound(f"./sounds/train.wav")
        await asyncio.sleep(9)
        await controller.control_multiple_relays({"spots": devices["spots"]}, "off")

    elif gift_value == 1000:
        await controller.control_multiple_relays({"spots": devices["spots"]}, "on")
        await controller.send_command(PINGPONG_MACHINE_URL)
        await controller.send_command(SMOKE_MACHINE_URL)
        await controller.send_command(SMOKE_TWO_MACHINE_URL)
        await controller.play_video('./videos/thriller.mp4')
        await controller.manually_play_sound(f"./sounds/thriller.wav")
        await asyncio.sleep(14)
        await controller.send_command(PINGPONG_MACHINE_URL)
        await controller.control_multiple_relays({"spots": devices["spots"]}, "off")

    elif gift_value == 1500:
        await controller.control_multiple_relays({"spots": devices["spots"], "neige": devices["neige"]}, "on")
        await controller.play_video('./videos/film_300.mp4')
        await controller.manually_play_sound(f"./sounds/jump.wav")
        await asyncio.sleep(20)
        await controller.control_multiple_relays({"neige": devices["neige"], "spots": devices["spots"]}, "off")

    elif gift_value == 1999:
        await controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"]}, "on")
        await controller.play_video('./videos/reine-des-neiges.mp4')
        await asyncio.sleep(30)
        await controller.control_multiple_relays(
            {"neige": devices["neige"], "bulles": devices["bulles"], "spots": devices["spots"]}, "off")
        await controller.send_command(SMOKE_MACHINE_URL)
        await controller.send_command(SMOKE_TWO_MACHINE_URL)

    elif gift_value == 3000:
        await controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        await controller.play_video('./videos/guiles.mp4')
        await controller.manually_play_sound(f"./sounds/guiles.wav")
        await asyncio.sleep(20)
        await controller.control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")
        await controller.send_command(SMOKE_MACHINE_URL)
        await controller.send_command(SMOKE_TWO_MACHINE_URL)

    elif gift_value == 4000:
        await controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        await controller.send_command(PINGPONG_MACHINE_URL)
        await controller.play_video('./videos/turn-down-to-what.mp4')
        await asyncio.sleep(22)
        await controller.send_command(SMOKE_MACHINE_URL)
        await controller.send_command(SMOKE_TWO_MACHINE_URL)
        await asyncio.sleep(2)
        await controller.send_command(SMOKE_MACHINE_URL)
        await controller.send_command(SMOKE_TWO_MACHINE_URL)
        await controller.send_command(PINGPONG_MACHINE_URL)
        await controller.control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")

    elif gift_value == 5000:
        await controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        await controller.send_command(PINGPONG_MACHINE_URL)
        await controller.play_video('./videos/interstellar.mp4')
        await controller.manually_play_sound(f"./sounds/interstellar.wav")
        await asyncio.sleep(30)
        await controller.send_command(SMOKE_MACHINE_URL)
        await controller.send_command(SMOKE_TWO_MACHINE_URL)
        await asyncio.sleep(2)
        await controller.send_command(SMOKE_MACHINE_URL)
        await controller.send_command(SMOKE_TWO_MACHINE_URL)
        await controller.send_command(PINGPONG_MACHINE_URL)
        await controller.control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")


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

@client.on(CommentEvent)
async def on_connect(event: CommentEvent):
    client.logger.info(f"Comment from {event.user.unique_id}: {event.comment}")



@client.on(LiveEndEvent)
async def on_liveend(event: LiveEndEvent):
    exit()


@client.on(FollowEvent)
async def on_follow(event: FollowEvent):
    if event.user.unique_id not in user_followers:
        user_followers.append(event.user.unique_id)
        await controller.manually_play_sound(f"./sounds/uwu.wav")


async def noop(_):
    pass

@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    client.logger.info("Received a gift!")
    # Streakable gift & streak is over
    if event.gift.streakable and not event.streaking:
        print(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.name}\"")
        action = ACTIONS.get(event.gift.diamond_count, noop)
        if action:
            await asyncio.create_task(action(event.gift.diamond_count))
        else:
            client.logger.warning(f"No action found for {event.gift.diamond_count} diamonds.")
    # Non-streakable gift
    elif not event.gift.streakable:
        print(f"{event.user.unique_id} sent \"{event.gift.name}\"")
        action = ACTIONS.get(event.gift.diamond_count, noop)
        if action:
            await asyncio.create_task(action(event.gift.diamond_count))
        else:
            client.logger.warning(f"No action found for {event.gift.diamond_count} diamonds.")

def signal_handler(sig, frame):
    send_webhook('Shutdown', 'The client has been shut down', color="FF0000")
    if client.connected:
        client.disconnect()
    print("Client has been shut down")
    exit()

signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    client.logger.setLevel(LogLevel.INFO.value)
    send_webhook('Start', 'The client has started', color="00FF00")
    try:
        client.run()
    except KeyboardInterrupt:
        send_webhook('Shutdown', 'The client has been shut down', color="FF0000")
        signal_handler(signal.SIGINT, None)
        print("Client has been shut down")