from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__, static_url_path='/static')
socketio = SocketIO(app, async_mode='gevent', logger=True, engineio_logger=True, cors_allowed_origins="*")
