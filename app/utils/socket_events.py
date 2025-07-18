from flask_socketio import emit
from app.utils.shared_state import socketData
import json


socketio = None  # Global socketio instance

def initialize_socket(sio):
    """Set the global SocketIO instance for broadcasting."""
    global socketio
    socketio = sio


def on_message(message):
    """Called when data is received from Kotak Neo WebSocket."""
    try:
        # message is already a dict, no need to json.loads()
        if isinstance(message, dict) and message.get('type') == 'stock_feed':
            filtered_data = [
                item for item in message.get('data', [])
                if 'ltp' in item and 'tk' in item and 'e' in item
            ]
            if filtered_data:
                socketio.emit("live_data", {
                    "type": "stock_feed",
                    "data": filtered_data
                })
        else:
            print("Ignored non-stock_feed or invalid format:", message)
    except Exception as e:
        print("Error filtering live_data:", e)

def on_message_live_option_chain_data(message):
    """Called when data is received from Kotak Neo WebSocket."""
    try:
        if not isinstance(message, dict):
            print("Invalid message format:", message)
            return

        msg_type = message.get('type')
        data = message.get('data', [])

        if msg_type == 'stock_feed':
            filtered_data = [
                item for item in data
                if 'ltp' in item and 'tk' in item and 'e' in item
            ]
            if filtered_data:
                socketio.emit("option_quotes_update", {
                    "type": "stock_feed",
                    "data": filtered_data
                })

        elif msg_type == 'quotes':
            filtered_data = [
                item for item in data
                if 'last_traded_price' in item and 'instrument_token' in item and 'exchange_segment' in item
            ]
            if filtered_data:
                socketio.emit("option_quotes_update", {
                    "type": "quotes",
                    "data": filtered_data
                })

        else:
            print("Ignored unknown message type:", message)

    except Exception as e:
        print("Error filtering live_data:", e)



def on_error(message):
    """Handle WebSocket error from Neo API."""
    print('[OnError]:', message)


def on_open(message):
    """Handle WebSocket open event from Neo API."""
    print('[OnOpen]:', message)


def on_close(message):
    """Handle WebSocket close event from Neo API."""
    print('[OnClose]:', message)


def register_socket_events(sio):
    """Register Flask-SocketIO connect/disconnect events."""
    @sio.on('connect')
    def handle_connect():
        print("Client connected")
        emit('message', {'data': 'Connected to socket'})

    @sio.on('disconnect')
    def handle_disconnect():
        print("Client disconnected")
