from flask import Blueprint, request, jsonify, session
from database import get_db_connection
from datetime import datetime

calendar_bp = Blueprint('calendar_bp', __name__, url_prefix="/calendar")

# event add
@calendar_bp.route('/add', methods=['POST'])
def add_event():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        cal_date = data.get("date")
        cal_event = data.get("event")

        if not cal_date or not cal_event:
            return jsonify({"error": "Date and event are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO compliance_calendar (cal_user_id, cal_date, cal_event)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (user_id, cal_date, cal_event))
        conn.commit()

        return jsonify({"message": "Event added "}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# get events
@calendar_bp.route('/list', methods=['GET'])
def list_events():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT cal_id, cal_date, cal_event, created_at
            FROM compliance_calendar
            WHERE cal_user_id = %s
            ORDER BY cal_date ASC
        """
        cursor.execute(query, (user_id,))
        events = cursor.fetchall()

        return jsonify(events), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
