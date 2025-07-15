import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os

from app.routes import register_routes
from app.utils.socket_events import register_socket_events

load_dotenv()

app = Flask(__name__)

CORS(app,
     supports_credentials=True,
     resources={r"/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"])

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default_secret")

socketio = SocketIO(app, cors_allowed_origins="*")

register_routes(app)
register_socket_events(socketio)

if __name__ == '__main__':
    print("Starting server...")
    socketio.run(app, host="0.0.0.0", port=10000, debug=True)
