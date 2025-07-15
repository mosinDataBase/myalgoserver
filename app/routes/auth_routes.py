from flask import Blueprint, request, jsonify
from pprint import pprint
from app.services.client_manager import create_client, verify_otp_and_prepare_data, clients

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        mobile = data.get("mobileNumber")
        password = data.get("password")
        ucc = data.get("ucc")
        consumerKey = data.get("consumerKey")
        consumerSecret = data.get("consumerSecret")

        if not all([mobile, password, consumerKey, consumerSecret]):
            return jsonify({"status": "error", "message": "Missing credentials"}), 400

        client = create_client(mobile, password, consumerKey, consumerSecret)
        otp = client.login(mobilenumber=mobile, password=password)
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
