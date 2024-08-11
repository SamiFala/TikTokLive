import sys
import threading
from asyncio import Queue
import os
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.events import FollowEvent, GiftEvent, ConnectEvent, LiveEndEvent, CommentEvent
from device_controller import DeviceController
from flask_socketio import SocketIO
import json
import asyncio
from flask_httpauth import HTTPBasicAuth

if sys.platform == 'darwin':  # Vérifie si le système est macOS
    print("macOS détecté")
    # Forcer asyncio à utiliser le sélecteur de base qui est plus stable sur macOS
    asyncio.set_event_loop(asyncio.get_event_loop())

loop = asyncio.get_event_loop()

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_loop, args=(loop,)).start()

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'uploads'
EVENTS_FILE = 'events.json'

# Initialisation de Flask et des composants associés
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialisation de SocketIO sans gevent
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration de l'authentification
auth = HTTPBasicAuth()

# Configuration du logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialisation des objets globaux
event_queue = Queue()
client = TikTokLiveClient(unique_id="@cam_off_tiktok")
controller = DeviceController(client)
users = {
    "yoyo": "sami",
    "yaya": "sami"
}

devices = {
    "girophare": "9047579382045",
    "bulles": "15819010",
    "neige": "15805966",
    "mousse": "15811858",
    "spots": "70518405971645"
}

# Charger les événements depuis le fichier JSON
def load_events():
    try:
        with open(EVENTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

events = load_events()
event_id_counter = max(event['id'] for event in events) + 1 if events else 1

client: TikTokLiveClient = TikTokLiveClient(unique_id="@vraregirl")

user_followers = []

# Constantes regroupées
SHELLY_PLUG_URL = "https://shelly-40-eu.shelly.cloud/device/relay/control"
WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1102639998987145426/_9xjoxzaFR_UoCyibmK3XuLA_5vkhzKbn0yQxgg8dNDZdkSxR7EqWul_6-9O8VkIDDr1'
SMOKE_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/C7BDBFBB7A3E/commands"
SMOKE_TWO_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/D5D127EFF039/commands"
PINGPONG_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/F3DFF2EAB30F/commands"

controller = DeviceController(client)

# Vérification des fichiers autorisés
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes Flask
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('web/uploads', filename)

@app.route('/start', methods=['POST'])
def start_script():
    asyncio.run_coroutine_threadsafe(client.start(), loop)
    return jsonify({"status": "Script started"}), 200

@app.route('/stop', methods=['POST'])
def stop_script():
    asyncio.run_coroutine_threadsafe(client.disconnect(), loop)
    return jsonify({"status": "Script stopped"}), 200

@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory('static/videos', filename)

@app.route('/sounds/<path:filename>')
def serve_sound(filename):
    return send_from_directory('static/sounds', filename)

@app.route('/handle_gift', methods=['POST'])
def handle_gift():
    gift_name = request.args.get('gift_name')
    if gift_name:
        gift_value = int(gift_name)
        asyncio.run_coroutine_threadsafe(gift_actions(gift_value), loop)
        return jsonify({"status": "Gift processed"}), 200
    return jsonify({"status": "No gift name provided"}), 400

@app.route('/add_event', methods=['POST'])
def add_event():
    global event_id_counter, events
    event_name = request.json.get('name')
    if event_name:
        new_event = {"id": event_id_counter, "name": event_name}
        events.append(new_event)
        event_id_counter += 1
        save_events(events)
        return jsonify(new_event), 200
    return jsonify({"error": "Invalid event name"}), 400

@app.route('/delete_event', methods=['POST'])
def delete_event():
    global events
    event_id = int(request.json.get('id'))
    events = [event for event in events if event['id'] != event_id]
    save_events(events)
    return jsonify({"success": True}), 200

def save_events(events):
    try:
        with open(EVENTS_FILE, 'w') as f:
            json.dump(events, f, indent=4)
        logging.info("Events saved to file")
    except Exception as e:
        logging.error(f"Error saving events: {e}", exc_info=True)

# Gestion des événements TikTok
@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    logging.info(f"Connected to @{event.unique_id}!")

@client.on(LiveEndEvent)
async def on_liveend(_: LiveEndEvent):
    await client.disconnect()

@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    logging.info(f"Received a comment from {event.user.unique_id}: {event.comment}")

@client.on(FollowEvent)
async def on_follow(event: FollowEvent):
    logging.info(f"Received a follow from {event.user.unique_id}")
    if event.user.unique_id not in user_followers:
        user_followers.append(event.user.unique_id)
        await play_sound_web("uwu.wav")

@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    logging.info(f"Received a gift: {event.gift.name}")
    if event.gift.streakable and not event.streaking:
        for _ in range(event.repeat_count):
            await event_queue.put(event.gift.diamond_count)
    elif not event.gift.streakable:
        await event_queue.put(event.gift.diamond_count)

async def gift_actions(gift_value):
    print(f"Handling gift action for value: {gift_value}")
    try:
        logging.info(f"Triggering event: {gift_value}")
        if gift_value == 1:
            await play_sound_web("bruit-de-pet.wav")
        print(f"Gift action for value {gift_value} completed")
        logging.info(f"Gift action for value {gift_value} completed")
    except Exception as e:
        print(f"Error in gift_actions: {e}")
        logging.error(f"Error handling gift action for value {gift_value}: {e}", exc_info=True)

async def play_sound_web(sound_path):
    sound_url = url_for('serve_sound', filename=sound_path, _external=True)
    print(f"Emitting play_sound with URL: {sound_url}")
    logging.info(f"Emitting play_sound with URL: {sound_url}")
    socketio.emit('play_sound', {'sound': sound_url})

@app.route('/test_event', methods=['POST'])
def test_event():
    socketio.emit('play_sound', {'sound': 'http://127.0.0.1:8082/sounds/bruit-de-pet.wav'})
    return jsonify({"status": "Test event sent"}), 200

async def play_video_web(video_path):
    socketio.emit('play_video', {'video': video_path})

# Authentification de l'utilisateur
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

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=8082)