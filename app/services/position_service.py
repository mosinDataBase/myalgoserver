from flask import current_app
from app.utils.position_calculator import calculate_positions_summary

def get_net_positions(client):
    try:
        response = client.positions()
        if response.get("stat") == "Ok":
            return {
                "status": "success",
                "positions": calculate_positions_summary(response.get("data", []))
            }
        return {"status": "error", "message": response.get("emsg", "Failed to fetch positions")}
    except Exception as e:
        return {"status": "error", "message": str(e)}
