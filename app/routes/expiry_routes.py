from flask import Blueprint, request, jsonify
from app.utils.expiry_utils import get_unique_expiries
from app.utils.logger import logger

expiry_bp = Blueprint('expiry', __name__)

@expiry_bp.route('/getExpiries', methods=['GET'])
def get_expiries_from_db():
    symbol = request.args.get('symbol', '').upper()
    segment = request.args.get('segment', 'nse_fo')

    logger.info(f"Received expiry request for symbol={symbol}, segment={segment}")

    if not symbol:
        logger.warning("Missing 'symbol' in request")
        return jsonify({"error": "Missing required parameter: symbol"}), 400

    try:
        expiries = get_unique_expiries(symbol, segment)
        logger.debug(f"Found {len(expiries)} expiries for {symbol} in {segment}")
        return jsonify({
            "symbol": symbol,
            "segment": segment,
            "expiries": expiries
        })
    except Exception as e:
        logger.exception("Error occurred while fetching expiries")
        return jsonify({"error": str(e)}), 500
