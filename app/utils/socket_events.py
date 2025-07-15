from flask_socketio import emit
from app.utils.shared_state import socketData

def on_message(message):
    socketData["data"] = message
    print('[Res]:', message)
    emit("live_data", message, broadcast=True)

def register_socket_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        emit('message', {'data': 'Connected to socket'})

    @socketio.on('disconnect')
    def handle_disconnect():
        print("Client disconnected")
