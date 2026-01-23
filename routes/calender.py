from flask import Blueprint, request, jsonify
from database import get_db_connection
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt
from utils.activity_logger import log_activity

calender_bp = Blueprint('calender_bp', __name__, url_prefix="/calender")


# ---------------- ADD EVENT ----------------
@calender_bp.route('/add', methods=['POST'])
@jwt_required()
def add_event():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        claims = get_jwt()
        user_id = claims.get("sub")  # identity is stored as "sub"
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        cal_date = data.get("date")
        cal_event = data.get("event")
        if not cal_date or not cal_event:
            return jsonify({"error": "Date and event are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO compliance_calendar (cal_user_id, cal_date, cal_event)
            VALUES (%s, %s, %s)
        """, (user_id, cal_date, cal_event))
        conn.commit()

        log_activity(
            user_id=user_id,
            user_group_id=user_group_id,
            department=department,
            email=email,
            action=f"Calendar Event Added: {cal_event} on {cal_date}"
        )

        return jsonify({"message": "Event added"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ---------------- LIST EVENTS ----------------
@calender_bp.route('/list', methods=['GET'])
@jwt_required()
def list_events():
    try:
        user_id = get_jwt().get("sub")
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cal_id, cal_date, cal_event, created_at
            FROM compliance_calendar
            WHERE cal_user_id = %s
            ORDER BY cal_date ASC
        """, (user_id,))
        events = cursor.fetchall()

        return jsonify(events), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ---------------- EDIT EVENT ----------------
@calender_bp.route('/edit/<int:cal_id>', methods=['PUT'])
@jwt_required()
def edit_event(cal_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        user_id = get_jwt().get("sub")
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        cal_date = data.get("date")
        cal_event = data.get("event")
        if not cal_date and not cal_event:
            return jsonify({"error": "Nothing to update"}), 400

        updates = []
        values = []
        if cal_date:
            updates.append("cal_date = %s")
            values.append(cal_date)
        if cal_event:
            updates.append("cal_event = %s")
            values.append(cal_event)

        values.extend([user_id, cal_id])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE compliance_calendar
            SET {', '.join(updates)}
            WHERE cal_user_id = %s AND cal_id = %s
        """, tuple(values))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Event not found"}), 404

        log_activity(
            user_id=user_id,
            user_group_id=user_group_id,
            department=department,
            email=email,
            action=f"Calendar Event Updated (ID: {cal_id})"
        )

        return jsonify({"message": "Event updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ---------------- DELETE EVENT ----------------
@calender_bp.route('/delete/<int:cal_id>', methods=['DELETE'])
@jwt_required()
def delete_event(cal_id):
    try:
        user_id = get_jwt().get("sub")
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM compliance_calendar
            WHERE cal_user_id = %s AND cal_id = %s
        """, (user_id, cal_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Event not found or unauthorized"}), 404

        log_activity(
            user_id=user_id,
            user_group_id=user_group_id,
            department=department,
            email=email,
            action=f"Calendar Event Deleted (ID: {cal_id})"
        )


        return jsonify({"message": "Event deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
