from flask_socketio import emit, disconnect, join_room
from app.utils.shared_state import clients, subscribed_tokens
from app.utils.logger import logger

socketio = None  # This will be initialized from serverapp.py


def initialize_socket(sio):
    """Set the global SocketIO instance for broadcasting."""
    global socketio
    socketio = sio


def register_socket_events(sio):
    """Register Flask-SocketIO event handlers."""

    @sio.on('connect')
    def handle_connect():
        print("Client connected")
        emit('message', {'data': 'Connected to socket'})

    @sio.on('disconnect')
    def handle_disconnect():
        print("Client disconnected")

    @sio.on('register_mobile')
    def handle_register_mobile(data):
        mobile = data.get("mobile")
        if not mobile:
            disconnect()
            return
        join_room(mobile)  # Join mobile room
        logger.info(f"Socket joined room for mobile {mobile}")

    @sio.on('unsubscribe_all')
    def unsubscribe_all_tokens(data):
            mobile = data.get("mobile")
            if not mobile:
                logger.warning("Mobile number not provided for unsubscribe_all")
                return
            user_data = clients.get(mobile)
            if not user_data:
                logger.warning(f"User not found for {mobile}")
                return

            client = user_data.get("client")
            category_map = subscribed_tokens.get(mobile, {})
            all_tokens = []
            for token_list in category_map.values():
                all_tokens.extend(token_list)

            if not all_tokens:
                logger.info(f"No tokens to unsubscribe for {mobile}")
                return

            try:
                client.un_subscribe(all_tokens, isIndex=False, isDepth=False)
                subscribed_tokens[mobile] = {}
                logger.info(f"Unsubscribed ALL tokens for {mobile}")
            except Exception as e:
                logger.error(f"Error unsubscribing all tokens for {mobile}: {e}")

def unsubscribe_specific_token(mobile, token_list):
    user_data = clients.get(mobile)
    if not user_data:
        logger.warning(f"User not found for {mobile}")
        logger.debug(f"instrument_token are  {token_list}")
        return

    client = user_data.get("client")
   
    try:
        # Send as a list of strings to NeoAPI client
        client.un_subscribe(token_list, isIndex=False, isDepth=False)

        # Remove token from list
       # subscribed_tokens[mobile][category] = {}
    except Exception as e:
        logger.error(f"Error unsubscribing token  for {mobile}: {e}")

def on_message(message):
    try:
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


def on_main_index_message(message):
    try:
        print("on_main_index_message:", message)
        if isinstance(message, dict) and message.get('type') == 'stock_feed':
                socketio.emit("live_index_data", {
                    "type": "stock_feed",
                    "data": message
                    })
    except Exception as e:
        print("Error filtering live_data:", e)


def on_message_live_option_chain_data(message, mobile):
    try:
        print(f"on_message_live_option_chain_data for {mobile}:", message)

        if not isinstance(message, dict):
            print("Invalid message format:", message)
            return

        msg_type = message.get('type')
        data = message.get('data', [])

        if msg_type == 'stock_feed':
            filtered_data = [
                item for item in data
                if item.get('request_type') != 'SUB' and (
                    'ltp' in item or 'lp' in item or 'ap' in item
                ) and 'tk' in item and 'e' in item
            ]
            if filtered_data:
                socketio.emit("option_quotes_update", {
                    "type": "stock_feed",
                    "data": filtered_data
                }, room=mobile)

        elif msg_type == 'quotes':
            filtered_data = [
                item for item in data
                if 'last_traded_price' in item and 'instrument_token' in item and 'exchange_segment' in item
            ]
            if filtered_data:
                socketio.emit("quotes_quotes_update", {
                    "type": "quotes",
                    "data": filtered_data
                }, room=mobile)

    except Exception as e:
        print(f"Error filtering live_data for {mobile}:", e)


def on_error(message):
    print('[OnError]:', message)


def on_open(message):
    print('[OnOpen]:', message)


def on_close(message):
    print('[OnClose]:', message)
