from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from database import get_db_connection
from datetime import datetime, timedelta, timezone

activity_log_bp = Blueprint('activity_log_bp', __name__, url_prefix="/activity_log")


IST = timezone(timedelta(hours=5, minutes=30))

@activity_log_bp.route('/', methods=['GET'])
@jwt_required()
def get_activity_logs():
    try:
        claims = get_jwt()
        user_role = claims.get("role")
        user_group_id = claims.get("user_group_id")

        if not user_role or user_role.lower() != "admin":
            return jsonify({"error": "Unauthorized access — admin only"}), 403

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
                    SELECT
                        acty_user_id,
                        acty_user_group_id,
                        acty_department,
                        acty_email,
                        # acty_date,
                        # acty_time,
                        acty_action
                    FROM activity_log
                    WHERE acty_user_group_id = %s
                    ORDER BY acty_date DESC, acty_time DESC
                """, (user_group_id,))




        activities = cursor.fetchall()

        cursor.close()
        conn.close()

        ist_now = datetime.now(timezone.utc).astimezone(IST)

        for activity in activities:
            activity["acty_date"] = ist_now.strftime("%Y-%m-%d")
            activity["acty_time"] = ist_now.strftime("%H:%M:%S")

        # for activity in activities:
        #     for key, value in activity.items():
        #         if isinstance(value, (datetime, timedelta)):
        #             activity[key] = str(value)

        return jsonify({
            "timezone": "IST",
            "total_records": len(activities),
            "activities": activities
        }), 200


    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500