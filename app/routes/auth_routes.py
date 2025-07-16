from flask import Blueprint, request, jsonify
from pprint import pprint
import logging
import time
from app.services.client_manager import create_client, verify_otp_and_prepare_data, clients
from app.utils.shared_state import file_paths, dfs, combined_database

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        start = time.time()
        data = request.get_json()
        mobile = data.get("mobileNumber")
        password = data.get("password")
        ucc = data.get("ucc")
        consumerKey = data.get("consumerKey")
        consumerSecret = data.get("consumerSecret")

        if not all([mobile, password, consumerKey, consumerSecret]):
            return jsonify({"status": "error", "message": "Missing credentials"}), 400
        
        client = create_client(mobile, password, consumerKey, consumerSecret)
        logger.info(f"[TIMING] create_client: {time.time() - start:.2f}s")
        start_login = time.time()
        otp = client.login(mobilenumber=mobile, password=password)
        logger.info(f"[TIMING] client.login: {time.time() - start_login:.2f}s")
        pprint(otp)

        if otp and "data" in otp and otp["data"].get("token"):
            return jsonify({
                "status": "success",
                "message": "Login successful",
                "data": otp["data"]
            })
        else:
            return jsonify({
                "status": "fail",
                "message": "Login failed or invalid response",
                "details": otp
            }), 401
    except Exception as e:
        print(f"Login Exception: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    try:
        data = request.get_json()
        mobile = data.get("mobileNumber")
        otp = data.get("otp")

        if not all([mobile, otp]):
            return jsonify({"error": "Missing mobile number or OTP"}), 400

        result = verify_otp_and_prepare_data(mobile, otp)
        return jsonify(result), 200
    except Exception as e:
        print("❌ OTP verification failed:", e)
        return jsonify({"status": "fail", "message": "OTP verification failed"}), 401
    
@auth_bp.route("/logout", methods=["POST"])
def logout():
    try:
        data = request.get_json()
        mobile = data.get("mobileNumber")

        if not mobile:
            return jsonify({"status": "error", "message": "Mobile number is required"}), 400

        user_entry = clients.get(mobile)
        client = user_entry.get("client") if isinstance(user_entry, dict) else user_entry

        if client:
            try:
                logout_response = client.logout()
                logger.info(f"[LOGOUT] NeoAPI logout response for {mobile}: {logout_response}")
            except Exception as e:
                logger.warning(f"[LOGOUT FAIL] NeoAPI logout failed for {mobile}: {e}")

            # Clean up client
            clients.pop(mobile, None)

            # You don't need to pop file_paths, dfs, combined_database
            # because they are global and not per-user
            logger.info(f"[CLEANUP DONE] Client removed for {mobile}")
            return jsonify({
                "status": "success",
                "message": f"User {mobile} logged out and cleaned up."
            }), 200
        else:
            return jsonify({
                "status": "fail",
                "message": "Client not found or already logged out."
            }), 404

    except Exception as e:
        logger.exception(f"[LOGOUT ERROR] Exception during logout: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
 

