import gevent.monkey
from flask_httpauth import HTTPBasicAuth

gevent.monkey.patch_all()

import os

from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
import logging

from discord_webhook import DiscordWebhook

from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.events import FollowEvent, GiftEvent, ConnectEvent, LiveEndEvent, CommentEvent
from device_controller import DeviceController
from flask_socketio import SocketIO
import json
import threading
import boto3
import asyncio
from botocore.client import Config

from werkzeug.utils import secure_filename

"""minio_client = boto3.client(
    's3',
    endpoint_url='http://5.196.8.104:9000/',
    aws_access_key_id='03oMEV2ciBbT1FsdVEFi',
    aws_secret_access_key='kTrkqfAwDgx5hc5vFwF30Hp7NUkcnLzinHQgOWxz',
    config=Config(signature_version='s3v4')
)

response = minio_client.list_buckets()
for bucket in response['Buckets']:
    print(bucket['Name'])

# Dossier où les fichiers téléchargés seront stockés"""
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

UPLOAD_FOLDER = 'uploads'
EVENTS_FILE = 'events.json'

auth = HTTPBasicAuth()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Limiter la taille maximale des fichiers téléchargés à 16 Mo
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
socketio = SocketIO(app, async_mode='gevent', logger=True, engineio_logger=True, cors_allowed_origins="*")
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

loop = asyncio.get_event_loop()

devices = {
    "girophare": "9047579382045",
    "bulles": "15819010",
    "neige": "15805966",
    "mousse": "15811858",
    "spots": "70518405971645"
    # "souffleur": "f14512",
    # "confettis": "d889bebd",
}

users = {
    "yoyo": "sami",
    "yaya": "sami"
}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Charger les événements depuis le fichier JSON
def load_events():
    try:
        with open(EVENTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Charger les événements en mémoire
events = load_events()
event_id_counter = max(event['id'] for event in events) + 1 if events else 1

client: TikTokLiveClient = TikTokLiveClient(unique_id="@cam_off_tiktok")

user_followers = []

# Constantes regroupées
SHELLY_PLUG_URL = "https://shelly-40-eu.shelly.cloud/device/relay/control"
WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1102639998987145426/_9xjoxzaFR_UoCyibmK3XuLA_5vkhzKbn0yQxgg8dNDZdkSxR7EqWul_6-9O8VkIDDr1'
SMOKE_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/C7BDBFBB7A3E/commands"
SMOKE_TWO_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/D5D127EFF039/commands"
PINGPONG_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/F3DFF2EAB30F/commands"

controller = DeviceController(client)

# Thread pour asyncio
def start_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Créez une nouvelle boucle d'événements pour le thread
asyncio_loop = asyncio.new_event_loop()
asyncio_thread = threading.Thread(target=start_asyncio_loop, args=(asyncio_loop,))
asyncio_thread.start()

async def play_sound_web(sound_path):
    socketio.emit('play_sound', {'sound': sound_path})

async def play_video_web(video_path):
    socketio.emit('play_video', {'video': video_path})

async def gift_actions(gift_value):
    if gift_value == 1:
        await play_sound_web("./sounds/bruit-de-pet.wav")

    elif gift_value == 5:
        await play_sound_web("./sounds/bruit_de_rot.wav")

    elif gift_value == 10:
        await play_sound_web("./sounds/ouais_cest_greg.wav")

    elif gift_value == 15:
        await play_sound_web("./sounds/je_suis_bien.wav")

    elif gift_value == 20:
        await play_sound_web("./sounds/alerte_au_gogole.wav")

    elif gift_value == 30:
        await play_sound_web("./sounds/quoicoubeh.wav")

    elif gift_value == 49:
        await play_sound_web("./sounds/my_movie.wav")

    elif gift_value == 55:
        await play_sound_web("./sounds/on_sen_bat_les_couilles.wav")

    elif gift_value == 88:
        await play_sound_web("./sounds/chinese_rap_song.wav")

    elif gift_value == 99:
        await controller.control_multiple_relays({"girophare": devices["girophare"]}, "on")
        await play_video_web('./videos/alerte-rouge.mp4')
        await play_sound_web(f"./sounds/nuke_alarm.wav")
        await asyncio.sleep(8)
        await controller.control_multiple_relays({"girophare": devices["girophare"]}, "off")

    elif gift_value == 100:
        await play_video_web('./videos/cri-de-cochon.mp4')

    elif gift_value == 150:
        await play_video_web('./videos/rap-contenders-thai.mp4')

    elif gift_value == 169:
        await play_video_web('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif gift_value == 199:
        await controller.control_multiple_relays({"girophare": devices["girophare"]}, "on")
        await play_sound_web(f"./sounds/police-sirene.wav")
        await play_sound_web(f"./sounds/fbi-open-up.wav")
        await asyncio.sleep(10)
        await controller.control_multiple_relays({"girophare": devices["girophare"]}, "off")

    elif gift_value == 200:
        await play_video_web('./videos/tu-vas-repartir-mal-mon-copain.mp4')

    elif gift_value == 299:
        await play_video_web('./videos/alien.mp4')
        await play_sound_web(f"./sounds/alien.wav")

    elif gift_value == 398:
        await play_video_web('./videos/got-that.mp4')

    elif gift_value == 399:
        await play_video_web('./videos/cat.mp4')
        await play_sound_web(f"./sounds/nyan_cat.wav")

    elif gift_value == 400:
        await play_video_web('./videos/teuf.mp4')
        await play_sound_web(f"./sounds/losing-it.wav")

    elif gift_value == 450:
        await play_video_web('./videos/mr-beast-phonk.mp4')

    elif gift_value == 500:
        await play_sound_web(f"./sounds/oui_oui.wav")
        await controller.control_multiple_relays({"bulles": devices["bulles"]}, "on")
        await play_video_web('./videos/oui-oui.mp4')
        await asyncio.sleep(10)
        await controller.control_multiple_relays({"bulles": devices["bulles"]}, "off")

    elif gift_value == 699:
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        await play_sound_web(f"./sounds/la_danse_des_canards.wav")
        await play_video_web('./videos/cygne.mp4')

    elif gift_value == 899:
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(PINGPONG_MACHINE_URL)
        await controller.control_multiple_relays({"spots": devices["spots"]}, "on")
        await play_video_web('./videos/train.mp4')
        await play_sound_web(f"./sounds/train.wav")
        await asyncio.sleep(9)
        await controller.control_multiple_relays({"spots": devices["spots"]}, "off")

    elif gift_value == 1000:
        await controller.control_multiple_relays({"spots": devices["spots"]}, "on")
        controller.send_command(PINGPONG_MACHINE_URL)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        await play_video_web('./videos/thriller.mp4')
        await play_sound_web(f"./sounds/thriller.wav")
        await asyncio.sleep(14)
        controller.send_command(PINGPONG_MACHINE_URL)
        await controller.control_multiple_relays({"spots": devices["spots"]}, "off")

    elif gift_value == 1500:
        await controller.control_multiple_relays({"spots": devices["spots"], "neige": devices["neige"]}, "on")
        await play_video_web('./videos/film_300.mp4')
        await play_sound_web(f"./sounds/jump.wav")
        await asyncio.sleep(20)
        await controller.control_multiple_relays({"neige": devices["neige"], "spots": devices["spots"]}, "off")

    elif gift_value == 1999:
        await controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"]}, "on")
        await play_video_web('./videos/reine-des-neiges.mp4')
        await asyncio.sleep(30)
        await controller.control_multiple_relays(
            {"neige": devices["neige"], "bulles": devices["bulles"], "spots": devices["spots"]}, "off")
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)

    elif gift_value == 3000:
        await controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        await play_video_web('./videos/guiles.mp4')
        await play_sound_web(f"./sounds/guiles.wav")
        await asyncio.sleep(20)
        await controller.control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)

    elif gift_value == 4000:
        await controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        controller.send_command(PINGPONG_MACHINE_URL)
        await play_video_web('./videos/turn-down-to-what.mp4')
        await asyncio.sleep(22)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        await asyncio.sleep(2)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        controller.send_command(PINGPONG_MACHINE_URL)
        await controller.control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")

    elif gift_value == 5000:
        await controller.control_multiple_relays(
            {"spots": devices["spots"], "bulles": devices["bulles"], "neige": devices["neige"],
             "mousse": devices["mousse"]}, "on")
        controller.send_command(PINGPONG_MACHINE_URL)
        await play_video_web('./videos/interstellar.mp4')
        await play_sound_web(f"./sounds/interstellar.wav")
        await asyncio.sleep(30)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        await asyncio.sleep(2)
        controller.send_command(SMOKE_MACHINE_URL)
        controller.send_command(SMOKE_TWO_MACHINE_URL)
        controller.send_command(PINGPONG_MACHINE_URL)
        await controller.control_multiple_relays(
            {"mousse": devices["mousse"], "neige": devices["neige"], "bulles": devices["bulles"],
             "spots": devices["spots"]}, "off")

@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"Connected to @{event.unique_id}!")
    client.logger.info(f"Connected to @{event.unique_id}!")

@client.on(LiveEndEvent)
async def on_liveend(_: LiveEndEvent):
    await client.disconnect()

@client.on(CommentEvent)
async def on_connect(event: CommentEvent):
    print(f"Received a comment from {event.user.unique_id}: {event.comment}")

@client.on(FollowEvent)
async def on_follow(event: FollowEvent):
    print(f"Received a follow from {event.user.unique_id}")
    if event.user.unique_id not in user_followers:
        user_followers.append(event.user.unique_id)
        await play_sound_web(f"./sounds/uwu.wav")

@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    print(f"Received a gift: {event.gift.name}")
    logging.info("Received a gift!")
    if event.gift.streakable and not event.streaking:
        for _ in range(event.repeat_count):
            await gift_actions(event.gift.diamond_count)
    elif not event.gift.streakable:
        await gift_actions(event.gift.diamond_count)

async def start_tiktok_client():
    print("Starting TikTok client")
    await client.start()

async def stop_tiktok_client():
    print("Stopping TikTok client")
    await client.disconnect()

# Route pour télécharger un fichier
"""@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    try:
        # Upload le fichier sur MinIO
        minio_client.upload_fileobj(
            file,
            'tiktoklive',  # Remplacez par le nom de votre bucket MinIO
            filename
        )
        file_url = f"https://api.futurateck.com/tiktoklive/{filename}"
        return jsonify({'success': True, 'url': file_url}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500"""

@app.errorhandler(413)
def too_large(e):
    return "Le fichier est trop volumineux", 413

""""@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # Télécharge le fichier depuis MinIO
        response = minio_client.get_object(
            'tiktoklive',
            filename
        )
        return response['Body'].read(), 200, {
            'Content-Disposition': f'attachment; filename={filename}'
        }

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500"""

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('web/uploads', filename)

@app.route('/start', methods=['POST'])
def start_script():
    try:
        asyncio.run_coroutine_threadsafe(start_tiktok_client(), asyncio_loop)
        return jsonify({"status": "Script started"}), 200
    except Exception as e:
        logging.error(f"Error starting script: {e}", exc_info=True)
        return jsonify({"status": "Failed to start script"}), 500

@app.route('/stop', methods=['POST'])
def stop_script():
    try:
        asyncio.run_coroutine_threadsafe(stop_tiktok_client(), asyncio_loop)
        return jsonify({"status": "Script stopped"}), 200
    except Exception as e:
        logging.error(f"Error stopping script: {e}", exc_info=True)
        return jsonify({"status": "Failed to stop script"}), 500

@app.route('/shutdown', methods=['POST'])
def shutdown():
    try:
        asyncio.run_coroutine_threadsafe(asyncio_loop.stop(), asyncio_loop)
        asyncio_thread.join()
        return jsonify({"status": "Server shutting down"}), 200
    except Exception as e:
        logging.error(f"Error shutting down: {e}", exc_info=True)
        return jsonify({"status": "Failed to shut down server"}), 500


@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory('static/videos', filename)

@app.route('/sounds/<path:filename>')
def serve_sound(filename):
    return send_from_directory('static/sounds', filename)

@app.route('/handle_gift', methods=['POST'])
def handle_gift():
    gift_name = request.args.get('gift_name')
    logging.info(f"Received POST request with gift_name: {gift_name}")

    if gift_name:
        logging.info(f"Triggering gift handling for: {gift_name}")
        gift_value = int(gift_name)
        future = asyncio.run_coroutine_threadsafe(gift_actions(gift_value), asyncio_loop)
        try:
            future.result()  # Attendre le résultat si vous avez besoin de savoir quand la coroutine est terminée
            logging.info(f"Gift {gift_name} processed successfully")
        except Exception as e:
            logging.error(f"Error processing gift {gift_name}: {e}", exc_info=True)
            return jsonify({"status": "Error processing gift"}), 500

        return jsonify({"status": "Gift processed"}), 200
    else:
        return jsonify({"status": "No gift name provided"}), 400

@app.route('/add_event', methods=['POST'])
def add_event():
    global event_id_counter, events
    event_name = request.json.get('name')
    if event_name:
        new_event = {"id": event_id_counter, "name": event_name}
        events.append(new_event)
        event_id_counter += 1
        save_events(events)  # Sauvegarder les événements après ajout
        return jsonify(new_event), 200
    return jsonify({"error": "Invalid event name"}), 400

@app.route('/delete_event', methods=['POST'])
def delete_event():
    try:
        event_id = int(request.json.get('id'))  # Conversion en entier
        global events
        logging.info(f"Before deletion: {events}")  # Log avant suppression
        events = [event for event in events if event['id'] != event_id]
        logging.info(f"After deletion: {events}")  # Log après suppression
        save_events(events)  # Sauvegarder les événements après suppression
        logging.info(f"Event with ID {event_id} deleted.")
        return jsonify({"success": True}), 200
    except Exception as e:
        logging.error(f"Error deleting event: {e}", exc_info=True)
        return jsonify({"error": "Error deleting event"}), 500

def save_events(events):
    try:
        with open(EVENTS_FILE, 'w') as f:
            json.dump(events, f, indent=4)
        logging.info("Events saved to file")  # Confirmation de la sauvegarde
    except Exception as e:
        logging.error(f"Error saving events: {e}", exc_info=True)
@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username
    return None

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html', events=events)

@app.route('/gachette')
@auth.login_required
def gachette():
    return render_template('gachette.html', events=events)

def run_flask():
    socketio.run(app, host='0.0.0.0', port=8081)

if __name__ == "__main__":
    run_flask()
