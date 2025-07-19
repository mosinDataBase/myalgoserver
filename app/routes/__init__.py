from .auth_routes import auth_bp
from .quotes_routes import quotes_bp
from .master_routes import master_bp
from .socket_routes import socket_bp
from .order_logs_routes import order_logs_bp
from .net_positions_routes import net_positions_bp
from .symbol_search import symbol_search_bp
from .expiry_routes import expiry_bp

def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(quotes_bp, url_prefix="/quotes")
    app.register_blueprint(master_bp, url_prefix="/masterscript")
    app.register_blueprint(socket_bp, url_prefix="/socket")
    app.register_blueprint(order_logs_bp, url_prefix="/execute-orders")
    app.register_blueprint(net_positions_bp, url_prefix="/net")
    app.register_blueprint(symbol_search_bp, url_prefix="/scriptsearch")
    app.register_blueprint(expiry_bp, url_prefix="/expiry")
    

    
    
