from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from database import get_db_connection
from utils.activity_logger import log_activity
import pymysql

calender_bp = Blueprint("calender_bp", __name__, url_prefix="/calender")

def get_user_email_and_department(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT
            u.usrlst_email,
            d.usrdept_department_name AS department_name
        FROM user_list u
        JOIN user_departments d
            ON d.usrdept_id = u.usrlst_department_id
        WHERE u.usrlst_id = %s
    """, (user_id,))

    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


@calender_bp.route("/add", methods=["POST"])
@jwt_required()
def add_event():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        claims = get_jwt()
        user_id = claims.get("sub")
        user_group_id = claims.get("user_group_id")

        cal_date = data.get("date")
        cal_event = data.get("event")

        if not cal_date or not cal_event:
            return jsonify({"error": "Date and event are required"}), 400

        user = get_user_email_and_department(user_id)
        if not user:
            return jsonify({"error": "User department not set"}), 400

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
            department=user["department_name"],
            email=user["usrlst_email"],
            action=f"Calendar Event Added: {cal_event} on {cal_date}"
        )

        cursor.close()
        conn.close()

        return jsonify({"message": "Event added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@calender_bp.route("/list", methods=["GET"])
@jwt_required()
def list_events():
    try:
        user_id = get_jwt().get("sub")

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT cal_id, cal_date, cal_event, created_at
            FROM compliance_calendar
            WHERE cal_user_id = %s
            ORDER BY cal_date ASC
        """, (user_id,))
        events = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(events), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# EDIT EVENT
# =====================================================
@calender_bp.route("/edit/<int:cal_id>", methods=["PUT"])
@jwt_required()
def edit_event(cal_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        claims = get_jwt()
        user_id = claims.get("sub")
        user_group_id = claims.get("user_group_id")

        updates = []
        values = []

        if "date" in data:
            updates.append("cal_date = %s")
            values.append(data["date"])

        if "event" in data:
            updates.append("cal_event = %s")
            values.append(data["event"])

        if not updates:
            return jsonify({"error": "Nothing to update"}), 400

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

        user = get_user_email_and_department(user_id)

        log_activity(
            user_id=user_id,
            user_group_id=user_group_id,
            department=user["department_name"],
            email=user["usrlst_email"],
            action=f"Calendar Event Updated (ID: {cal_id})"
        )

        cursor.close()
        conn.close()

        return jsonify({"message": "Event updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@calender_bp.route("/delete/<int:cal_id>", methods=["DELETE"])
@jwt_required()
def delete_event(cal_id):
    try:
        claims = get_jwt()
        user_id = claims.get("sub")
        user_group_id = claims.get("user_group_id")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM compliance_calendar
            WHERE cal_user_id = %s AND cal_id = %s
        """, (user_id, cal_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Event not found"}), 404

        user = get_user_email_and_department(user_id)

        log_activity(
            user_id=user_id,
            user_group_id=user_group_id,
            department=user["department_name"],
            email=user["usrlst_email"],
            action=f"Calendar Event Deleted (ID: {cal_id})"
        )

        cursor.close()
        conn.close()

        return jsonify({"message": "Event deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @calender_bp.route("/calendar", methods=["GET"])
# @jwt_required()
# def user_compliance_calendar():
#     try:
#         claims = get_jwt()
#         user_group_id = claims.get("user_group_id")

#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)

#         cursor.execute("""
#             SELECT
#                 regcmp_compliance_id AS id,
#                 regcmp_act AS act,
#                 regcmp_particular AS particular,
#                 regcmp_action_date AS action_date,
#                 regcmp_status AS status,
#                 'regulatory' AS type
#             FROM regulatory_compliance
#             WHERE regcmp_user_group_id = %s
#               AND regcmp_action_date IS NOT NULL
#         """, (user_group_id,))
#         regulatory = cursor.fetchall()

#         cursor.execute("""
#             SELECT
#                 slfcmp_compliance_id AS id,
#                 'self' AS act,
#                 slfcmp_particular AS particular,
#                 slfcmp_action_date AS action_date,
#                 slfcmp_status AS status,
#                 'self' AS type
#             FROM self_compliance
#             WHERE slfcmp_user_group_id = %s
#               AND slfcmp_action_date IS NOT NULL
#         """, (user_group_id,))
#         selfc = cursor.fetchall()

#         cursor.close()
#         conn.close()

#         events = [
#             {
#                 "id": r["id"],
#                 "title": f"{r['act']} : {r['particular']}",
#                 "date": r["action_date"],
#                 "status": r["status"],
#                 "type": r["type"]
#             }
#             for r in (regulatory + selfc)
#         ]

#         return jsonify({
#             "group_id": user_group_id,
#             "total_events": len(events),
#             "events": events
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@calender_bp.route("/user/calendar", methods=["GET"])
@jwt_required()
def user_compliance_calendar():
    try:
        claims = get_jwt()
        user_id = claims.get("sub")
        user_group_id = claims.get("user_group_id")

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                regcmp_compliance_id AS id,
                regcmp_act AS act,
                regcmp_particular AS particular,
                regcmp_action_date AS action_date,
                regcmp_status AS status,
                'regulatory' AS type
            FROM regulatory_compliance
            WHERE regcmp_user_id = %s
              AND regcmp_user_group_id = %s
              AND regcmp_action_date IS NOT NULL
        """, (user_id, user_group_id))
        regulatory = cursor.fetchall()

        cursor.execute("""
            SELECT
                slfcmp_compliance_id AS id,
                'self' AS act,
                slfcmp_particular AS particular,
                slfcmp_action_date AS action_date,
                slfcmp_status AS status,
                'self' AS type
            FROM self_compliance
            WHERE slfcmp_user_id = %s
              AND slfcmp_user_group_id = %s
              AND slfcmp_action_date IS NOT NULL
        """, (user_id, user_group_id))
        selfc = cursor.fetchall()

        cursor.close()
        conn.close()

        events = [
            {
                "id": e["id"],
                "title": f"{e['act']} : {e['particular']}",
                "date": e["action_date"],
                "status": e["status"],
                "type": e["type"]
            }
            # for e in (regulatory + selfc)
            for e in (list(regulatory) + list(selfc))
        ]

        return jsonify({
            "user_id": user_id,
            "group_id": user_group_id,
            "total_events": len(events),
            "events": events
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@calender_bp.route("/admin/calendar", methods=["GET"])
@jwt_required()
def admin_compliance_calendar():
    try:
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                regcmp_compliance_id AS id,
                regcmp_act AS act,
                regcmp_particular AS particular,
                regcmp_action_date AS action_date,
                regcmp_status AS status,
                'regulatory' AS type
            FROM regulatory_compliance
            WHERE regcmp_user_group_id = %s
              AND regcmp_action_date IS NOT NULL
        """, (user_group_id,))
        regulatory = cursor.fetchall()

        cursor.execute("""
            SELECT
                slfcmp_compliance_id AS id,
                'self' AS act,
                slfcmp_particular AS particular,
                slfcmp_action_date AS action_date,
                slfcmp_status AS status,
                'self' AS type
            FROM self_compliance
            WHERE slfcmp_user_group_id = %s
              AND slfcmp_action_date IS NOT NULL
        """, (user_group_id,))
        selfc = cursor.fetchall()

        cursor.close()
        conn.close()

        events = [
            {
                "id": r["id"],
                "title": f"{r['act']} : {r['particular']}",
                "date": r["action_date"],
                "status": r["status"],
                "type": r["type"]
            }
            # for r in (regulatory + selfc)
            for r in (list(regulatory) + list(selfc))
        ]

        return jsonify({
            "group_id": user_group_id,
            "total_events": len(events),
            "events": events
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
