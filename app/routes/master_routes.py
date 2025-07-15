from flask import Blueprint, jsonify
from app.services.master_service import load_master_scrips, get_symbol_list

master_bp = Blueprint("master", __name__)

@master_bp.route("/load", methods=["GET"])
def load():
    return load_master_scrips()

@master_bp.route("/symbols", methods=["GET"])
def symbols():
    return get_symbol_list()
