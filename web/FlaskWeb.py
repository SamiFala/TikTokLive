import gevent.monkey
gevent.monkey.patch_all()

import logging
import asyncio
import websockets
import json
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from discord_webhook import DiscordWebhook, DiscordEmbed
from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.events import FollowEvent, GiftEvent, ConnectEvent, LiveEndEvent
from TikTokLive.client.logger import LogLevel
import os

import shutil
from werkzeug.utils import secure_filename

# Informations de la prise Shelly
devices = {
    "girophare": "9047579382045",
    "bulles": "15819010",
    "neige": "15805966",
    "mousse": "15811858",
    "spots": "70518405971645"
    # "souffleur": "f14512",
    # "confettis": "d889bebd",
}

client_id = "shelly-sas"
auth_code = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzaGVsbHktc2FzIiwiaWF0IjoxNzIyNjg0ODcwLCJ1c2VyX2lkIjoiMTE4NjYzNSIsInNuIjoiMSIsInVzZXJfYXBpX3VybCI6Imh0dHBzOlwvXC9zaGVsbHktNDAtZXUuc2hlbGx5LmNsb3VkIiwibiI6MjUzM30.D0p1Vysbq6cILgrbT194cmg4TmQ-UcClQHVmypw77GM"
redirect_uri = "https://futurateck.com"

# Variables globales
access_token = None
hostName = "0.0.0.0"
serverPort = 5050
process = None
log_thread = None  # Ajouté pour la gestion des logs
client_connected = False  # Variable pour suivre l'état du client

client: TikTokLiveClient = TikTokLiveClient(unique_id="@cam_off_tiktok")

# Constantes regroupées
SHELLY_PLUG_URL = "https://shelly-40-eu.shelly.cloud/device/relay/control"
WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1102639998987145426/_9xjoxzaFR_UoCyibmK3XuLA_5vkhzKbn0yQxgg8dNDZdkSxR7EqWul_6-9O8VkIDDr1'
SMOKE_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/C7BDBFBB7A3E/commands"
SMOKE_TWO_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/D5D127EFF039/commands"
PINGPONG_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/F3DFF2EAB30F/commands"

user_followers = []

webhook = DiscordWebhook(url=WEBHOOK_URL)

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')

socketio = SocketIO(app, async_mode='gevent', logger=True, engineio_logger=True, cors_allowed_origins="*")

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_log_stream(stream, log_type):
    global process
    while process.poll() is None:
        line = stream.readline()
        if line:
            log = line.decode('utf-8').strip()
            logger.info(f"Log du script TikTok ({log_type}): {log}")
            socketio.emit('log', {'data': log})
    stream.close()

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

async def start_tiktok_client():
    global log_thread, client_connected
    if not log_thread or not log_thread.is_alive():
        if not client_connected:
            asyncio.ensure_future(client.start())
            client_connected = True
            socketio.emit('status', {'data': 'ON'})
            logger.info("Le client TikTok a été démarré.")
        else:
            logger.warning("Le client TikTok est déjà connecté.")
    else:
        logger.warning("Le client TikTok est déjà en cours d'exécution.")

async def stop_tiktok_client():
    global client_connected
    if client_connected:
        if hasattr(client, 'disconnect') and callable(getattr(client, 'disconnect')):
            await client.disconnect()
        else:
            logger.error("Client TikTok does not have an awaitable 'disconnect' method.")
        client_connected = False
        socketio.emit('status', {'data': 'OFF'})
        logger.info("Le client TikTok a été arrêté.")
    else:
        logger.warning("Le client TikTok n'est pas en cours d'exécution.")

# Fonction pour jouer un son via le client web
def play_sound_web(sound_path):
    logger.info(f"Emitting play_sound event for: {sound_path}")  # Log supplémentaire
    socketio.emit('play_sound', {'sound': f'/static/{sound_path}'})

# Fonction pour jouer une vidéo via le client web
def play_video_web(video_path):
    logger.info(f"Emitting play_video event for: {video_path}")  # Log supplémentaire
    socketio.emit('play_video', {'video': f'/static/{video_path}'})


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
            'Authorization': 'Bearer 09f984c25288d88849a45b8dce8010b5f03104f8abc47ee87beb9031d97d6db550f2e903358b84f039b23ab3371032bc',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, headers=headers, data=body)
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            send_webhook('Error', 'Error sending command', error_detail=err, color="FF0000")
            print(f"Error sending command: {err}")

controller = DeviceController(client)

async def handle_gift(gift_value):
    gift_value = int(gift_value)  # Convertir en entier si nécessaire

    if gift_value == 1:
        logger.info("Playing sound for gift_value 1")     # Ajoutez un log pour chaque condition
        play_sound_web("./sounds/bruit-de-pet.wav")

    elif gift_value == 5:
        play_sound_web("./sounds/bruit_de_rot.wav")

    elif gift_value == 10:
        play_sound_web("./sounds/ouais_cest_greg.wav")

    elif gift_value == 15:
        play_sound_web("./sounds/je_suis_bien.wav")

    elif gift_value == 20:
        play_sound_web("./sounds/alerte_au_gogole.wav")

    elif gift_value == 30:
        play_sound_web("./sounds/quoicoubeh.wav")

    elif gift_value == 49:
        play_sound_web("./sounds/my_movie.wav")

    elif gift_value == 55:
        play_sound_web("./sounds/on_sen_bat_les_couilles.wav")

    elif gift_value == 88:
        play_sound_web("./sounds/chinese_rap_song.wav")

    elif gift_value == 99:
        await control_multiple_relays({"girophare": devices["girophare"]}, "on")
        play_video_web('./videos/alerte-rouge.mp4')
        play_sound_web(f"./sounds/nuke_alarm.wav")
        await asyncio.sleep(8)
        await control_multiple_relays({"girophare": devices["girophare"]}, "off")

    elif gift_value == 100:
        play_video_web('./videos/cri-de-cochon.mp4')

    elif gift_value == 150:
        play_video_web('./videos/rap-contenders-thai.mp4')

    elif gift_value == 169:
        play_video_web('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif gift_value == 199:
        await control_multiple_relays({"girophare": devices["girophare"]}, "on")
        play_sound_web(f"./sounds/police-sirene.wav")
        play_sound_web(f"./sounds/fbi-open-up.wav")
        await asyncio.sleep(10)
        await control_multiple_relays({"girophare": devices["girophare"]}, "off")

    elif gift_value == 200:
        play_video_web('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif gift_value == 299:
        play_video_web('./videos/alien.mp4')
        play_sound_web(f"./sounds/alien.wav")

    elif gift_value == 398:
        play_video_web('./videos/got-that.mp4')

    elif gift_value == 399:
        play_video_web('./videos/cat.mp4')
        play_sound_web(f"./sounds/nyan_cat.wav")

    elif gift_value == 400:
        play_video_web('./videos/teuf.mp4')
        play_sound_web(f"./sounds/losing-it.wav")

    elif gift_value == 450:
        play_video_web('./videos/mr-beast-phonk.mp4')

    elif gift_value == 500:
        play_sound_web(f"./sounds/oui_oui.wav")
        await control_multiple_relays({"bulles": devices["bulles"]}, "on")
        play_video_web('./videos/oui-oui.mp4')
        await asyncio.sleep(10)
        await control_multiple_relays({"bulles": devices["bulles"]}, "off")

    elif gift_value == 699:
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        play_sound_web(f"./sounds/la_danse_des_canards.wav")
        play_video_web('./videos/cygne.mp4')

    elif gift_value == 899:
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(PINGPONG_MACHINE_URL)
        await control_multiple_relays({"spots": devices["spots"]}, "on")
        play_video_web('./videos/train.mp4')
        play_sound_web(f"./sounds/train.wav")
        await asyncio.sleep(9)
        await control_multiple_relays({"spots": devices["spots"]}, "off")

    elif gift_value == 1000:
        await control_multiple_relays({"spots": devices["spots"]}, "on")
        controller.send_command(PINGPONG_MACHINE_URL)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        play_video_web('./videos/thriller.mp4')
        play_sound_web(f"./sounds/thriller.wav")
        await asyncio.sleep(14)
        controller.send_command(PINGPONG_MACHINE_URL)
        await control_multiple_relays({"spots": devices["spots"]}, "off")

    elif gift_value == 1500:
        await control_multiple_relays({"spots": devices["spots"], "neige": devices["neige"]}, "on")
        play_video_web('./videos/film_300.mp4')
        play_sound_web(f"./sounds/jump.wav")
        await asyncio.sleep(20)
        await control_multiple_relays({"neige": devices["neige"], "spots": devices["spots"]}, "off")

    elif gift_value == 1999:
        await control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"]}, "on")
        play_video_web('./videos/reine-des-neiges.mp4')
        await asyncio.sleep(30)
        await control_multiple_relays(
            {"neige": devices["neige"], "bulles": devices["bulles"], "spots": devices["spots"]}, "off")
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)

    elif gift_value == 3000:
        await control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        play_video_web('./videos/guiles.mp4')
        play_sound_web(f"./sounds/guiles.wav")
        await asyncio.sleep(20)
        await control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)

    elif gift_value == 4000:
        await control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        controller.send_command(PINGPONG_MACHINE_URL)
        play_video_web('./videos/turn-down-to-what.mp4')
        await asyncio.sleep(22)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        await asyncio.sleep(2)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        controller.send_command(PINGPONG_MACHINE_URL)
        await control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")

    elif gift_value == 5000:
        await control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        controller.send_command(PINGPONG_MACHINE_URL)
        play_video_web('./videos/interstellar.mp4')
        play_sound_web(f"./sounds/interstellar.wav")
        await asyncio.sleep(30)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        await asyncio.sleep(2)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        controller.send_command(PINGPONG_MACHINE_URL)
        await control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")

# Gestion des événements TikTok
"""@client.on(DisconnectEvent)
async def relaunch(_: DisconnectEvent):
    await client.disconnect()"""

@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    client.logger.info(f"Connected to @{event.unique_id}!")

@client.on(LiveEndEvent)
async def on_liveend(_: LiveEndEvent):
    await client.disconnect()

@client.on(FollowEvent)
async def on_follow(event: FollowEvent):
    if event.user.unique_id not in user_followers:
        user_followers.append(event.user.unique_id)
        play_sound_web(f"./sounds/uwu.wav")
@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    client.logger.info("Received a gift!")
    # Streakable gift & streak is over
    if event.gift.streakable and not event.streaking:
        print(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.name}\"")
        for _ in range(event.repeat_count):
            await handle_gift(event.gift.diamond_count)
    # Non-streakable gift
    elif not event.gift.streakable:
        print(f"{event.user.unique_id} sent \"{event.gift.name}\"")
        await handle_gift(event.gift.diamond_count)

# Obtenir le token OAuth
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

# Connexion au WebSocket Shelly
async def connect_shelly_websocket(access_token):
    ws_url = f"wss://shelly-40-eu.shelly.cloud:6113/shelly/wss/hk_sock?t={access_token}"
    async with websockets.connect(ws_url) as websocket:
        while True:
            message = await websocket.recv()
            """data = json.loads(message)
            if data.get("event") == "Shelly:StatusOnChange":
                logger.info(f"Status changed")
            elif data.get("event") == "Shelly:Online":
                logger.info(f"Device online status changed")
            elif data.get("event") == "Shelly:CommandResponse":
                logger.info(f"Command response")"""

# Contrôle du relais pour un seul appareil
async def control_relay(device_id, state):
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
            logger.info(f"Relay control response for {device_id}: {response}")
    except websockets.exceptions.InvalidStatusCode as e:
        if e.status_code == 401:
            logger.warning("Access token expired or invalid. Obtaining a new token.")
            access_token = get_oauth_token(client_id, auth_code, redirect_uri)
            if access_token:
                await control_relay(device_id, state)
            else:
                logger.error("Failed to obtain new token")
        else:
            logger.error(f"WebSocket connection failed with status code: {e.status_code}")

# Contrôle des relais pour plusieurs appareils
async def control_multiple_relays(devices, state):
    tasks = [control_relay(devices[device], state) for device in devices]
    await asyncio.gather(*tasks)

# Classe du serveur HTTP
class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        # Lire les données de la requête POST
        # Log the full URL being accessed
        full_url = f"{self.headers['Host']}{self.path}"
        logger.info(f"Full URL: {full_url}")
        logger.info(f"Received POST request: {self.path}")  # Log supplémentaire pour la route
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        logger.info(f"Raw POST data: {post_data}")

        # Analyser les paramètres de l'URL directement
        parameters = urllib.parse.parse_qs(self.path)
        logger.info(f"Parsed parameters: {parameters}")  # Log supplémentaire

        gift_name = next(iter(parameters.get('gift_name', [])[0:1]), None)
        logger.info(f"Gift name received: {gift_name}")  # Log supplémentaire


        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if gift_name:
            logger.info(f"Triggering gift handling for: {gift_name}")  # Log supplémentaire
            asyncio.run_coroutine_threadsafe(la_gachette(gift_name), loop)


async def la_gachette(gift_name: str):
    global process
    logger.info(f"Received gift: {gift_name}")
    print(f"Received gift: {gift_name}")

    try:
        if gift_name == "start":
            await start_tiktok_client()
        elif gift_name == "stop":
            await stop_tiktok_client()
        else:
            await handle_gift(gift_name)
    except Exception as e:
        logger.error(f"Error handling gift '{gift_name}': {str(e)}", exc_info=True)  # Log d'erreur détaillé
        print(f"Error handling gift '{gift_name}': {str(e)}")

async def main():
    global access_token
    access_token = get_oauth_token(client_id, auth_code, redirect_uri)
    if access_token:
        await connect_shelly_websocket(access_token)
    else:
        logger.error("Failed to obtain access token")

    client.logger.setLevel(LogLevel.INFO.value)


# Routes Flask pour l'interface web
@app.route('/upload', methods=['POST'])
def upload_file():
    # Vérifiez si le fichier est dans la requête
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})

    file = request.files['file']

    # Vérifiez si le fichier a un nom valide
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Sauvegarder le fichier
        file.save(filepath)

        return jsonify({'success': True, 'url': f'/uploads/{filename}'})
    else:
        return jsonify({'success': False, 'error': 'Invalid file type'})


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/start', methods=['POST'])
def start_script():
    full_url = request.url
    logger.info(f"Full URL: {full_url}")

    logger.info("Requête de démarrage reçue.")
    asyncio.run_coroutine_threadsafe(start_tiktok_client(), loop)
    socketio.emit('status', {'data': 'ON'})
    logger.info("Le client TikTok a été démarré.")
    return jsonify({"status": "Client started"}), 200

@app.route('/stop', methods=['POST'])
def stop_script():
    # Log the full URL being accessed
    full_url = request.url
    logger.info(f"Full URL: {full_url}")

    logger.info("Requête d'arrêt reçue.")
    asyncio.run_coroutine_threadsafe(stop_tiktok_client(), loop)
    socketio.emit('status', {'data': 'OFF'})
    logger.info("Le client TikTok a été arrêté.")
    return jsonify({"status": "Client stopped"}), 200

@app.before_request
def log_request_info():
    logger.info(f"Full URL accessed: {request.url}")

@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory('static/videos', filename)

@app.route('/sounds/<path:filename>')
def serve_sound(filename):
    return send_from_directory('static/sounds', filename)

@app.route('/logs')
def logs():
    logger.debug("Page des logs demandée.")
    return render_template('logs.html')

# Serveur Python minimal
@socketio.on('connect')
def test_connect():
    logger.info("Client connected")
    socketio.emit('test_message', {'data': 'Server says hello!'})

@app.route('/')
def index():
    logger.info("Page d'accueil demandée.")
    return render_template('index.html')

def run_flask():
    socketio.run(app, host='0.0.0.0', port=8081)

def run_http_server():
    webServer = HTTPServer((hostName, serverPort), MyServer)
    logger.info(f"Server started https://{hostName}:{serverPort}")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    logger.info("Server stopped.")

if __name__ == "__main__":
    # Démarrer le serveur HTTP dans un thread
    http_thread = threading.Thread(target=run_http_server)
    http_thread.start()

    # Démarrer Flask dans un autre thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Démarrer la boucle asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    # Attendre que les threads se terminent
    http_thread.join()
    flask_thread.join()
