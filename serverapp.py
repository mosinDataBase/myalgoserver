import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os

from app.routes import register_routes
#from app.utils.socket_events import socket_events
from app.utils import socket_events  


load_dotenv()
#python serverapp.py
mainApp = Flask(__name__)

CORS(mainApp,
     supports_credentials=True,
     resources={r"/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"])

mainApp.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default_secret")
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
socketio = SocketIO(mainApp, cors_allowed_origins="*")
socket_events.initialize_socket(socketio)
socket_events.register_socket_events(socketio)

register_routes(mainApp)
#register_socket_events(socketio)

if __name__ == '__main__':
    print("Starting server...")
    socketio.run(mainApp, host="0.0.0.0", port=10000, debug=DEBUG_MODE)
