from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from database import get_db_connection
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from email.mime.text import MIMEText
from uuid import uuid4
from utils.activity_logger import log_activity
import smtplib
from uuid import uuid4
import pymysql

compliance_bp = Blueprint('compliance_bp', __name__, url_prefix="/compliance")

def send_email(to_email, subject, body):
    SMTP_SERVER = "mail.pseudoteam.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "info@pseudoteam.com"
    SENDER_PASSWORD = "dppbHwdU9mKW"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())


def calculate_reminders(action_date_str, month_before, day_before, remaining_days_before, escalation_days):
    action_date = datetime.strptime(action_date_str, "%Y-%m-%d")

    month_reminder = action_date - relativedelta(months=month_before) if month_before else None
    day_reminder = action_date - timedelta(days=day_before) if day_before else None
    remaining_days_reminder = action_date - timedelta(days=remaining_days_before) if remaining_days_before else None
    escalation_reminder = action_date - timedelta(days=escalation_days) if escalation_days else None

    return (
        month_reminder.strftime("%Y-%m-%d") if month_reminder else None,
        day_reminder.strftime("%Y-%m-%d") if day_reminder else None,
        remaining_days_reminder.strftime("%Y-%m-%d") if remaining_days_reminder else None,
        escalation_reminder.strftime("%Y-%m-%d") if escalation_reminder else None
    )

def calculate_reminder_date(action_date, reminder_days):
    if not reminder_days:
        return None

    action_date = datetime.strptime(action_date, "%Y-%m-%d")
    return (action_date - timedelta(days=int(reminder_days))).strftime("%Y-%m-%d")

@compliance_bp.route("/countries", methods=["GET"])
@jwt_required()
def get_countries():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT cmplst_country
            FROM compliance_list
            WHERE cmplst_country IS NOT NULL
            ORDER BY cmplst_country
        """)

        countries = [row["cmplst_country"] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({"countries": countries}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@compliance_bp.route("/acts", methods=["GET"])
@jwt_required()
def get_acts_by_country():
    try:
        country = request.args.get("country")
        if not country:
            return jsonify({"error": "country parameter is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT cmplst_act
            FROM compliance_list
            WHERE cmplst_country = %s AND cmplst_act IS NOT NULL
            ORDER BY cmplst_act
        """, (country,))

        acts = [row["cmplst_act"] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({"country": country, "acts": acts}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@compliance_bp.route("/filter", methods=["GET"])
@jwt_required()
def get_compliance_by_act_and_country():
    try:
        country = request.args.get("country")
        act = request.args.get("act")

        if not country or not act:
            return jsonify({"error": "country and act parameters are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # cursor.execute("""
        #     SELECT *
        #     FROM compliance_list
        #     WHERE cmplst_country = %s AND cmplst_act = %s
        # """, (country, act))

        cursor.execute("""
        SELECT cl.*
        FROM compliance_list cl
        INNER JOIN (
        SELECT cmplst_particular, MIN(cmplst_id) AS min_id
        FROM compliance_list
        WHERE cmplst_country = %s
        AND cmplst_act = %s
        GROUP BY cmplst_particular
        ) t
        ON cl.cmplst_particular = t.cmplst_particular
        AND cl.cmplst_id = t.min_id
        WHERE cl.cmplst_country = %s
        AND cl.cmplst_act = %s;""", (country, act , country, act))

        records = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"records": records}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @compliance_bp.route("/add/regulatory", methods=["POST"])
# @jwt_required()
# def add_regulatory_compliance():
#     try:
#         claims = get_jwt()
#         user_id = claims.get("sub")
#         user_group_id = claims.get("user_group_id")

#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "Invalid JSON body"}), 400

#         required_fields = [
#             "regcmp_country",
#             "regcmp_act",
#             "regcmp_particular",
#             "regcmp_compliance_key",
#             "regcmp_description",
#             "regcmp_reminder_days",
#             "regcmp_escalation_email",
#             "regcmp_escalation_reminder_days"
#         ]

#         for field in required_fields:
#             if field not in data or str(data[field]).strip() == "":
#                 return jsonify({"error": f"Missing field: {field}"}), 400

#         reminder_days = int(data["regcmp_reminder_days"])
#         escalation_days = int(data["regcmp_escalation_reminder_days"])

#         conn = get_db_connection()
#         cursor = conn.cursor()

#         #order by ASC to maintain consistency
#         cursor.execute("""
#             SELECT *
#             FROM compliance_list
#             WHERE cmplst_country = %s
#               AND cmplst_act = %s
#               AND cmplst_particular = %s
#               AND cmplst_compliance_key = %s
#         """, (
#             data["regcmp_country"],
#             data["regcmp_act"],
#             data["regcmp_particular"],
#             data["regcmp_compliance_key"]
#         ))

#         master_rows = cursor.fetchall()

#         if not master_rows:
#             cursor.close()
#             conn.close()
#             return jsonify({"error": "No matching compliance found"}), 404

#         inserted = 0

#         for row in master_rows:
#             cursor.execute("""
#                 INSERT INTO regulatory_compliance (
#                     regcmp_act,
#                     regcmp_particular,
#                     regcmp_description,
#                     regcmp_long_description,
#                     regcmp_title,
#                     regcmp_compliance_id,
#                     regcmp_reminder_days,
#                     regcmp_start_date,
#                     regcmp_end_date,
#                     regcmp_action_date,
#                     regcmp_status,
#                     regcmp_escalation_email,
#                     regcmp_escalation_reminder_days,
#                     regcmp_original_action_date,
#                     regcmp_user_id,
#                     regcmp_user_group_id
#                 ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
#             """, (
#                 row["cmplst_act"],
#                 row["cmplst_particular"],
#                 data["regcmp_description"],
#                 row.get("cmplst_long_description", ""),
#                 row.get("cmplst_title", ""),
#                 data["regcmp_compliance_key"],
#                 reminder_days,
#                 row["cmplst_start_date"],
#                 row["cmplst_end_date"],
#                 row["cmplst_action_date"], 
#                 "Pending",
#                 data["regcmp_escalation_email"],
#                 escalation_days,
#                 row["cmplst_action_date"],
#                 user_id,
#                 user_group_id
#             ))

#             inserted += 1

#         conn.commit()
#         cursor.close()
#         conn.close()

#         log_activity(
#             user_id=user_id,
#             user_group_id=user_group_id,
#             department="Compliance",
#             email=claims.get("email"),
#             action=f"Regulatory Compliance Added | Act: {data['regcmp_act']} | Country: {data['regcmp_country']}"
#         )

#         return jsonify({
#             "message": "Regulatory compliance added successfully",
#             "instances_created": inserted
#         }), 201

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

#chnage made here

@compliance_bp.route("/add/regulatory", methods=["POST"])
@jwt_required()
def add_regulatory_compliance():
    try:
        claims = get_jwt()
        user_id = claims.get("sub")
        user_group_id = claims.get("user_group_id")

        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        required_fields = [
            "regcmp_country",
            "regcmp_act",
            "regcmp_particular",
            "regcmp_compliance_key",
            "regcmp_description"
        ]

        for field in required_fields:
            if field not in data or str(data[field]).strip() == "":
                return jsonify({"error": f"Missing field: {field}"}), 400

        reminder_days = int(data.get("regcmp_reminder_days", 0))
        escalation_days = int(data.get("regcmp_escalation_reminder_days", 0))
        escalation_email = data.get("regcmp_escalation_email")

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT *
            FROM compliance_list
            WHERE cmplst_country = %s
              AND cmplst_act = %s
              AND cmplst_particular = %s
              AND cmplst_compliance_key = %s
        """, (
            data["regcmp_country"],
            data["regcmp_act"],
            data["regcmp_particular"],
            data["regcmp_compliance_key"]
        ))

        master_rows = cursor.fetchall()

        if not master_rows:
            cursor.close()
            conn.close()
            return jsonify({"error": "No matching compliance found"}), 404

        inserted = 0

        for row in master_rows:
            cursor.execute("""
                INSERT INTO regulatory_compliance (
                    regcmp_act,
                    regcmp_particular,
                    regcmp_description,
                    regcmp_long_description,
                    regcmp_title,
                    regcmp_compliance_id,
                    regcmp_reminder_days,
                    regcmp_start_date,
                    regcmp_end_date,
                    regcmp_action_date,
                    regcmp_status,
                    regcmp_escalation_email,
                    regcmp_escalation_reminder_days,
                    regcmp_original_action_date,
                    regcmp_user_id,
                    regcmp_user_group_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                row["cmplst_act"],
                row["cmplst_particular"],
                data["regcmp_description"],
                row.get("cmplst_long_description"),
                row.get("cmplst_title"),
                data["regcmp_compliance_key"],
                reminder_days,
                row["cmplst_start_date"],
                row["cmplst_end_date"],
                row["cmplst_action_date"],
                "Pending",
                escalation_email,
                escalation_days,
                row["cmplst_action_date"],
                user_id,
                user_group_id
            ))

            inserted += 1

        conn.commit()
        cursor.close()
        conn.close()

        log_activity(
            user_id=user_id,
            user_group_id=user_group_id,
            department="Compliance",
            email=claims.get("email"),
            action=f"Regulatory Compliance Added | Act: {data['regcmp_act']} | Country: {data['regcmp_country']}"
        )

        return jsonify({
            "message": "Regulatory compliance added successfully",
            "instances_created": inserted
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
# @compliance_bp.route("/add/custom", methods=["POST"])
# @jwt_required()
# def add_custom_compliance():
#     try:
#         claims = get_jwt()
#         user_id = claims.get("sub")
#         user_group_id = claims.get("user_group_id")

#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "Invalid JSON body"}), 400

#         required_fields = [
#             "slfcmp_act",
#             "slfcmp_particular",
#             "slfcmp_description",
#             "slfcmp_long_description",
#             "slfcmp_title",
#             "slfcmp_reminder_days",
#             "slfcmp_start_date",
#             "slfcmp_end_date",
#             "slfcmp_action_date",
#             "slfcmp_escalation_email",
#             "slfcmp_escalation_reminder_days",
#             "repeat_type"      
#         ]

#         for field in required_fields:
#             if field not in data or str(data[field]).strip() == "":
#                 return jsonify({"error": f"Missing field: {field}"}), 400

#         repeat_type = data["repeat_type"]    
#         repeat_value = int(data.get("repeat_value", 0)) 

#         start_date = datetime.strptime(data["slfcmp_start_date"], "%Y-%m-%d")
#         end_date = datetime.strptime(data["slfcmp_end_date"], "%Y-%m-%d")
#         action_date = datetime.strptime(data["slfcmp_action_date"], "%Y-%m-%d")

#         compliance_id = "com" + datetime.now().strftime("%Y%m%d%H%M%S") + uuid4().hex[:4]

#         conn = get_db_connection()
#         cursor = conn.cursor()

#         inserted = 0
#         current_action_date = action_date

#         if repeat_type == "months":
#             if repeat_value <= 0:
#                 return jsonify({"error": "repeat_value must be > 0 for months"}), 400

#             while current_action_date <= end_date:
#                 cursor.execute("""
#                     INSERT INTO self_compliance (
#                         slfcmp_act,
#                         slfcmp_particular,
#                         slfcmp_description,
#                         slfcmp_long_description,
#                         slfcmp_title,
#                         slfcmp_compliance_id,
#                         slfcmp_reminder_days,
#                         slfcmp_start_date,
#                         slfcmp_end_date,
#                         slfcmp_action_date,
#                         slfcmp_status,
#                         slfcmp_escalation_email,
#                         slfcmp_escalation_reminder_days,
#                         slfcmp_requested_date,
#                         slfcmp_original_action_date,
#                         slfcmp_user_id,
#                         slfcmp_user_group_id,
#                         slfcmp_compliance_key
#                     )
#                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
#                 """, (
#                     data["slfcmp_act"],
#                     data["slfcmp_particular"],
#                     data["slfcmp_description"],
#                     data["slfcmp_long_description"],
#                     data["slfcmp_title"],
#                     compliance_id,
#                     data["slfcmp_reminder_days"],
#                     data["slfcmp_start_date"],
#                     data["slfcmp_end_date"],
#                     current_action_date.strftime("%Y-%m-%d"),
#                     "Pending",
#                     data["slfcmp_escalation_email"],
#                     data["slfcmp_escalation_reminder_days"],
#                     datetime.now().strftime("%Y-%m-%d"),
#                     current_action_date.strftime("%Y-%m-%d"),
#                     user_id,
#                     user_group_id,
#                     1
#                 ))
#                 inserted += 1
#                 current_action_date += relativedelta(months=repeat_value)

#         elif repeat_type == "days":
#             if repeat_value <= 0:
#                 return jsonify({"error": "repeat_value must be > 0 for days"}), 400

#             while current_action_date <= end_date:
#                 cursor.execute(""" INSERT INTO self_compliance (...) VALUES (...) """, (
#                     data["slfcmp_act"],
#                     data["slfcmp_particular"],
#                     data["slfcmp_description"],
#                     data["slfcmp_long_description"],
#                     data["slfcmp_title"],
#                     compliance_id,
#                     data["slfcmp_reminder_days"],
#                     data["slfcmp_start_date"],
#                     data["slfcmp_end_date"],
#                     current_action_date.strftime("%Y-%m-%d"),
#                     "Pending",
#                     data["slfcmp_escalation_email"],
#                     data["slfcmp_escalation_reminder_days"],
#                     datetime.now().strftime("%Y-%m-%d"),
#                     current_action_date.strftime("%Y-%m-%d"),
#                     user_id,
#                     user_group_id,
#                     1
#                 ))
#                 inserted += 1
#                 current_action_date += timedelta(days=repeat_value)

#         else:
#             cursor.execute(""" INSERT INTO self_compliance (...) VALUES (...) """, (
#                 data["slfcmp_act"],
#                 data["slfcmp_particular"],
#                 data["slfcmp_description"],
#                 data["slfcmp_long_description"],
#                 data["slfcmp_title"],
#                 compliance_id,
#                 data["slfcmp_reminder_days"],
#                 data["slfcmp_start_date"],
#                 data["slfcmp_end_date"],
#                 data["slfcmp_action_date"],
#                 "Pending",
#                 data["slfcmp_escalation_email"],
#                 data["slfcmp_escalation_reminder_days"],
#                 datetime.now().strftime("%Y-%m-%d"),
#                 data["slfcmp_action_date"],
#                 user_id,
#                 user_group_id,
#                 1
#             ))
#             inserted = 1

#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({
#             "message": "Custom compliance added successfully",
#             "compliance_id": compliance_id,
#             "instances_created": inserted
#         }), 201

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @compliance_bp.route("/add/custom", methods=["POST"])
# @jwt_required()
# def add_custom_compliance():
#     try:
#         claims = get_jwt()
#         user_id = claims.get("sub")
#         user_group_id = claims.get("user_group_id")

#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "Invalid JSON body"}), 400


#         required_fields = [
#             "slfcmp_act",
#             "slfcmp_particular",
#             "slfcmp_description",
#             "slfcmp_long_description",
#             "slfcmp_title",
#             "slfcmp_reminder_days",
#             "slfcmp_start_date",
#             "slfcmp_end_date",
#             "slfcmp_action_date",
#             "slfcmp_escalation_email",
#             "slfcmp_escalation_reminder_days",
#             "repeat_type"
#         ]

#         for field in required_fields:
#             if field not in data or str(data[field]).strip() == "":
#                 return jsonify({"error": f"Missing field: {field}"}), 400

#         start_date = datetime.strptime(data["slfcmp_start_date"], "%Y-%m-%d")
#         end_date = datetime.strptime(data["slfcmp_end_date"], "%Y-%m-%d")
#         action_date = datetime.strptime(data["slfcmp_action_date"], "%Y-%m-%d")

#         if not (start_date <= action_date <= end_date):
#             return jsonify({
#                 "error": "Invalid date sequence (start <= action <= end required)"
#             }), 400

#         repeat_type = data["repeat_type"].lower().strip()
#         repeat_value = int(data.get("repeat_value", 0))

#         if repeat_type in ("month", "months", "monthly"):
#             repeat_mode = "months"
#         elif repeat_type in ("day", "days", "daily"):
#             repeat_mode = "days"
#         else:
#             repeat_mode = "none"

#         if repeat_mode in ("months", "days") and repeat_value <= 0:
#             return jsonify({
#                 "error": "repeat_value must be provided and > 0"
#             }), 400

#         compliance_id = (
#             "com" +
#             datetime.now().strftime("%Y%m%d%H%M%S") +
#             uuid4().hex[:4]
#         )

#         conn = get_db_connection()
#         cursor = conn.cursor()

#         insert_sql = """
#         INSERT INTO self_compliance (
#             slfcmp_act,
#             slfcmp_particular,
#             slfcmp_description,
#             slfcmp_long_description,
#             slfcmp_title,
#             slfcmp_compliance_id,
#             slfcmp_reminder_days,
#             slfcmp_start_date,
#             slfcmp_end_date,
#             slfcmp_action_date,
#             slfcmp_status,
#             slfcmp_escalation_email,
#             slfcmp_escalation_reminder_days,
#             slfcmp_requested_date,
#             slfcmp_original_action_date,
#             slfcmp_user_id,
#             slfcmp_user_group_id,
#             slfcmp_compliance_key
#         )
#         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
#         """

#         inserted = 0
#         current_action_date = action_date

#         if repeat_mode == "months":
#             while current_action_date <= end_date:
#                 cursor.execute(insert_sql, (
#                     data["slfcmp_act"],
#                     data["slfcmp_particular"],
#                     data["slfcmp_description"],
#                     data["slfcmp_long_description"],
#                     data["slfcmp_title"],
#                     compliance_id,
#                     data["slfcmp_reminder_days"],
#                     data["slfcmp_start_date"],
#                     data["slfcmp_end_date"],
#                     current_action_date.strftime("%Y-%m-%d"),
#                     "Pending",
#                     data["slfcmp_escalation_email"],
#                     data["slfcmp_escalation_reminder_days"],
#                     datetime.now().strftime("%Y-%m-%d"),
#                     current_action_date.strftime("%Y-%m-%d"),
#                     user_id,
#                     user_group_id,
#                     compliance_id
#                 ))
#                 inserted += 1
#                 current_action_date += relativedelta(months=repeat_value)

#         elif repeat_mode == "days":
#             while current_action_date <= end_date:
#                 cursor.execute(insert_sql, (
#                     data["slfcmp_act"],
#                     data["slfcmp_particular"],
#                     data["slfcmp_description"],
#                     data["slfcmp_long_description"],
#                     data["slfcmp_title"],
#                     compliance_id,
#                     data["slfcmp_reminder_days"],
#                     data["slfcmp_start_date"],
#                     data["slfcmp_end_date"],
#                     current_action_date.strftime("%Y-%m-%d"),
#                     "Pending",
#                     data["slfcmp_escalation_email"],
#                     data["slfcmp_escalation_reminder_days"],
#                     datetime.now().strftime("%Y-%m-%d"),
#                     current_action_date.strftime("%Y-%m-%d"),
#                     user_id,
#                     user_group_id,
#                     compliance_id
#                 ))
#                 inserted += 1
#                 current_action_date += timedelta(days=repeat_value)

#         else:
#             cursor.execute(insert_sql, (
#                 data["slfcmp_act"],
#                 data["slfcmp_particular"],
#                 data["slfcmp_description"],
#                 data["slfcmp_long_description"],
#                 data["slfcmp_title"],
#                 compliance_id,
#                 data["slfcmp_reminder_days"],
#                 data["slfcmp_start_date"],
#                 data["slfcmp_end_date"],
#                 data["slfcmp_action_date"],
#                 "Pending",
#                 data["slfcmp_escalation_email"],
#                 data["slfcmp_escalation_reminder_days"],
#                 datetime.now().strftime("%Y-%m-%d"),
#                 data["slfcmp_action_date"],
#                 user_id,
#                 user_group_id,
#                 compliance_id
#             ))
#             inserted = 1

#         conn.commit()
#         cursor.close()
#         conn.close()

#         return jsonify({
#             "message": "Custom compliance added successfully",
#             "compliance_id": compliance_id,
#             "instances_created": inserted
#         }), 201

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@compliance_bp.route("/add/custom", methods=["POST"])
@jwt_required()
def add_custom_compliance():
    try:
        claims = get_jwt()
        user_id = claims.get("sub")
        user_group_id = claims.get("user_group_id")

        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        required_fields = [
            "slfcmp_act",
            "slfcmp_particular",
            "slfcmp_description",
            "slfcmp_long_description",
            "slfcmp_title",
            "slfcmp_reminder_days",
            "slfcmp_start_date",
            "slfcmp_end_date",
            "slfcmp_action_date",
            "slfcmp_escalation_email",
            "slfcmp_escalation_reminder_days",
            "repeat_type"
        ]

        for field in required_fields:
            if field not in data or str(data[field]).strip() == "":
                return jsonify({"error": f"Missing field: {field}"}), 400

        # start_date = datetime.strptime(data["slfcmp_start_date"], "%d-%m-%y")
        # end_date = datetime.strptime(data["slfcmp_end_date"], "%d-%m-%y")
        # action_date = datetime.strptime(data["slfcmp_action_date"], "%d-%m-%y")

        start_date = datetime.strptime(data["slfcmp_start_date"], "%d-%m-%Y")
        end_date = datetime.strptime(data["slfcmp_end_date"], "%d-%m-%Y")
        action_date = datetime.strptime(data["slfcmp_action_date"], "%d-%m-%Y")

        if not (start_date <= action_date <= end_date):
            return jsonify({
                "error": "Invalid date sequence (start <= action <= end required)"
            }), 400

        repeat_type = data["repeat_type"].lower().strip()
        repeat_value = int(data.get("repeat_value", 0))

        if repeat_type in ("month", "months", "monthly"):
            repeat_mode = "months"
        elif repeat_type in ("day", "days", "daily"):
            repeat_mode = "days"
        else:
            repeat_mode = "none"

        if repeat_mode in ("months", "days") and repeat_value <= 0:
            return jsonify({"error": "repeat_value must be > 0"}), 400

        compliance_id = (
            "com" +
            datetime.now().strftime("%Y%m%d%H%M%S") +
            uuid4().hex[:4]
        )

        conn = get_db_connection()
        cursor = conn.cursor()

        insert_sql = """
        INSERT INTO self_compliance (
            slfcmp_act,
            slfcmp_particular,
            slfcmp_description,
            slfcmp_long_description,
            slfcmp_title,
            slfcmp_compliance_id,
            slfcmp_reminder_days,
            slfcmp_start_date,
            slfcmp_end_date,
            slfcmp_action_date,
            slfcmp_status,
            slfcmp_escalation_email,
            slfcmp_escalation_reminder_days,
            slfcmp_original_action_date,
            slfcmp_user_id,
            slfcmp_user_group_id,
            slfcmp_compliance_key
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        inserted = 0
        current_action_date = action_date

        # 🔑 FIX: anchor day (DO NOT CHANGE)
        anchor_day = action_date.day

        # ---------- MONTHLY (NO DATE DRIFT) ----------
        if repeat_mode == "months":
            while current_action_date <= end_date:
                cursor.execute(insert_sql, (
                    data["slfcmp_act"],
                    data["slfcmp_particular"],
                    data["slfcmp_description"],
                    data["slfcmp_long_description"],
                    data["slfcmp_title"],
                    compliance_id,
                    data["slfcmp_reminder_days"],
                    data["slfcmp_start_date"],
                    data["slfcmp_end_date"],
                    current_action_date.strftime("%d-%m-%Y"),
                    "Pending",
                    data["slfcmp_escalation_email"],
                    data["slfcmp_escalation_reminder_days"],
                    current_action_date.strftime("%d-%m-%Y"),
                    user_id,
                    user_group_id,
                    compliance_id
                ))
                inserted += 1

                next_date = current_action_date + relativedelta(months=repeat_value)
                last_day = (next_date + relativedelta(day=31)).day
                current_action_date = next_date.replace(
                    day=min(anchor_day, last_day)
                )

        # ---------- DAILY ----------
        elif repeat_mode == "days":
            while current_action_date <= end_date:
                cursor.execute(insert_sql, (
                    data["slfcmp_act"],
                    data["slfcmp_particular"],
                    data["slfcmp_description"],
                    data["slfcmp_long_description"],
                    data["slfcmp_title"],
                    compliance_id,
                    data["slfcmp_reminder_days"],
                    data["slfcmp_start_date"],
                    data["slfcmp_end_date"],
                    current_action_date.strftime("%d-%m-%Y"),
                    "Pending",
                    data["slfcmp_escalation_email"],
                    data["slfcmp_escalation_reminder_days"],
                    current_action_date.strftime("%d-%m-%Y"),
                    user_id,
                    user_group_id,
                    compliance_id
                ))
                inserted += 1
                current_action_date += timedelta(days=repeat_value)

        # ---------- ONE-TIME ----------
        else:
            cursor.execute(insert_sql, (
                data["slfcmp_act"],
                data["slfcmp_particular"],
                data["slfcmp_description"],
                data["slfcmp_long_description"],
                data["slfcmp_title"],
                compliance_id,
                data["slfcmp_reminder_days"],
                data["slfcmp_start_date"],
                data["slfcmp_end_date"],
                data["slfcmp_action_date"],
                "Pending",
                data["slfcmp_escalation_email"],
                data["slfcmp_escalation_reminder_days"],
                data["slfcmp_action_date"],
                user_id,
                user_group_id,
                compliance_id
            ))
            inserted = 1

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": "Custom compliance added successfully",
            "compliance_id": compliance_id,
            "instances_created": inserted
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# fetch regulatory
@compliance_bp.route("/fetch/regulatory", methods=["GET"])
@jwt_required()
def fetch_regulatory_compliance():
    try:
        user_id = get_jwt().get("sub")

        conn = get_db_connection()
        # cursor = conn.cursor(dictionary=True)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT * FROM ( SELECT *, ROW_NUMBER() OVER ( PARTITION BY regcmp_act, regcmp_particular ORDER BY regcmp_id ASC ) AS rn FROM regulatory_compliance WHERE regcmp_user_id = %s ) t WHERE rn = 1 and regcmp_user_id = %s;
        """, (user_id, user_id))

        records = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "user_id": user_id,
            "count": len(records),
            "data": records
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# fetch custom
@compliance_bp.route("/fetch/custom", methods=["GET"])
@jwt_required()
def fetch_custom_compliance():
    try:
        user_id = get_jwt().get("sub")

        conn = get_db_connection()
        # cursor = conn.cursor(dictionary=True)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
                SELECT * FROM ( SELECT *, ROW_NUMBER() OVER ( PARTITION BY slfcmp_act, slfcmp_particular ORDER BY slfcmp_id ASC ) AS rn FROM self_compliance WHERE slfcmp_user_id = %s ) t WHERE rn = 1 and slfcmp_user_id = %s;
                       """, (user_id, user_id))

        records = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "user_id": user_id,
            "count": len(records),
            "data": records
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
      
@compliance_bp.route("/fetch/custom/<string:compliance_id>", methods=["GET"])
@jwt_required()
def fetch_custom_compliance_instances(compliance_id):
    try:
        user_id = get_jwt().get("sub")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM self_compliance
            WHERE slfcmp_user_id = %s
              AND slfcmp_compliance_id = %s
            ORDER BY slfcmp_action_date
        """, (user_id, compliance_id))

        records = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "user_id": user_id,
            "compliance_id": compliance_id,
            "count": len(records),
            "data": records
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@compliance_bp.route("/fetch/regulatory/<int:compliance_id>", methods=["GET"])
@jwt_required()
def fetch_regulatory_compliance_instances(compliance_id):
    try:
        user_id = get_jwt().get("sub")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM regulatory_compliance
            WHERE regcmp_user_id = %s
              AND regcmp_compliance_id = %s
            ORDER BY regcmp_action_date
        """, (user_id, compliance_id))

        records = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "user_id": user_id,
            "compliance_id": compliance_id,
            "count": len(records),
            "data": records
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@compliance_bp.route("/edit/regulatory/<int:regcmp_id>", methods=["GET"])
@jwt_required()
def get_regulatory_compliance_for_edit(regcmp_id):
    try:
        claims = get_jwt()
        user_id = claims.get("sub")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM regulatory_compliance
            WHERE regcmp_id = %s
              AND regcmp_user_id = %s
            LIMIT 1
        """, (regcmp_id, user_id))

        record = cursor.fetchone()

        cursor.close()
        conn.close()

        if not record:
            return jsonify({
                "error": "Compliance not found or unauthorized"
            }), 404

        return jsonify({
            "data": record
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# regulatory compliance edit
# @compliance_bp.route("/edit/regulatory/<int:regcmp_id>", methods=["PUT"])
# @jwt_required()
# def edit_regulatory_action_date(regcmp_id):
#     try:
#         claims = get_jwt()
#         user_id = claims.get("sub")
#         user_group_id = claims.get("user_group_id")

#         data = request.get_json()

#         if not data or "regcmp_id" not in data:
#             return jsonify({
#                 "error": "regcmp_id not found!"
#             }), 400

#         if not data or "regcmp_action_date" not in data:
#             return jsonify({
#                 "error": "Only regcmp_action_date is allowed"
#             }), 400

#         new_action_date = data["regcmp_action_date"]

#         conn = get_db_connection()
#         cursor = conn.cursor()

#         cursor.execute("""
#             UPDATE regulatory_compliance
#             SET regcmp_action_date = %s
#             WHERE regcmp_id = %s
#               AND regcmp_user_id = %s
#         """, (new_action_date, regcmp_id, user_id))

#         conn.commit()

#         if cursor.rowcount == 0:
#             cursor.close()
#             conn.close()
#             return jsonify({
#                 "error": "Not found or unauthorized"
#             }), 403


#         cursor.close()
#         conn.close()

#         log_activity(
#             user_id=user_id,
#             user_group_id=user_group_id,
#             department="Compliance",
#             email=claims.get("email"),
#             action=f"Regulatory Compliance Action Date Updated | ID: {regcmp_id} | New Date: {new_action_date}"
#         )

#         return jsonify({
#             "message": "Action date updated successfully",
#             "regcmp_action_date": new_action_date
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@compliance_bp.route("/edit/custom/<int:slfcmp_id>", methods=["GET"])
@jwt_required()
def get_custom_compliance_for_edit(slfcmp_id):
    try:
        user_id = get_jwt().get("sub")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM self_compliance
            WHERE slfcmp_id = %s
              AND slfcmp_user_id = %s
            LIMIT 1
        """, (slfcmp_id, user_id))

        record = cursor.fetchone()

        cursor.close()
        conn.close()

        if not record:
            return jsonify({
                "error": "Compliance not found or unauthorized"
            }), 404

        return jsonify({
            "data": record
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@compliance_bp.route("/edit/custom/<int:slfcmp_id>", methods=["PUT"])
@jwt_required()
def edit_custom_compliance(slfcmp_id):
    try:
        claims = get_jwt()
        user_id = claims.get("sub")
        user_group_id = claims.get("user_group_id")

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        allowed_fields = {
            "slfcmp_action_date",
            "slfcmp_reminder_days",
            "slfcmp_escalation_email",
            "slfcmp_escalation_reminder_days"
        }

        updates = {}
        values = []

        for field in allowed_fields:
            if field in data:
                value = data[field]

                if field == "slfcmp_action_date":
                    try:
                        datetime.strptime(value, "%d-%m-%Y")
                    except ValueError:
                        return jsonify({
                            "error": "Invalid date format. Use DD-MM-YYYY"
                        }), 400

                if field in (
                    "slfcmp_reminder_days",
                    "slfcmp_escalation_reminder_days"
                ):
                    if not str(value).isdigit() or int(value) < 0:
                        return jsonify({
                            "error": f"{field} must be a non-negative integer"
                        }), 400

                updates[field] = value

        if not updates:
            return jsonify({
                "error": "No valid fields to update"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT slfcmp_status
            FROM self_compliance
            WHERE slfcmp_id = %s
              AND slfcmp_user_id = %s
        """, (slfcmp_id, user_id))

        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({"error": "Compliance not found"}), 404

        if row["slfcmp_status"] != "Pending":
            cursor.close()
            conn.close()
            return jsonify({
                "error": "Only Pending compliances can be edited"
            }), 403

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values.extend(updates.values())
        values.extend([slfcmp_id, user_id])

        cursor.execute(f"""
            UPDATE self_compliance
            SET {set_clause}
            WHERE slfcmp_id = %s
              AND slfcmp_user_id = %s
        """, tuple(values))

        conn.commit()
        cursor.close()
        conn.close()
        
        log_activity(
            user_id=user_id,
            user_group_id=user_group_id,
            department="Compliance",
            email=claims.get("email"),
            action=(
                f"Custom Compliance Updated | "
                f"ID: {slfcmp_id} | "
                f"Fields: {', '.join(updates.keys())}"
            )
        )

        return jsonify({
            "message": "Custom compliance updated successfully",
            "slfcmp_id": slfcmp_id,
            "updated_fields": updates
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
   

@compliance_bp.route("/edit/regulatory/<int:regcmp_id>", methods=["PUT"])
@jwt_required()
def edit_regulatory_compliance(regcmp_id):
    try:
        claims = get_jwt()
        user_id = claims.get("sub")
        user_group_id = claims.get("user_group_id")

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        allowed_fields = {
            "regcmp_action_date",
            "regcmp_reminder_days",
            "regcmp_escalation_email",
            "regcmp_escalation_reminder_days"
        }

        updates = {}
        values = []

        for field in allowed_fields:
            if field in data:
                value = data[field]

                if field == "regcmp_action_date":
                    try:
                        datetime.strptime(value, "%d-%m-%Y")
                    except ValueError:
                        return jsonify({
                            "error": "Invalid date format. Use DD-MM-YYYY"
                        }), 400

                if field in ("regcmp_reminder_days", "regcmp_escalation_reminder_days"):
                    if not str(value).isdigit() or int(value) < 0:
                        return jsonify({
                            "error": f"{field} must be a non-negative integer"
                        }), 400

                updates[field] = value

        if not updates:
            return jsonify({
                "error": "No valid fields to update"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT regcmp_status
            FROM regulatory_compliance
            WHERE regcmp_id = %s
              AND regcmp_user_id = %s
        """, (regcmp_id, user_id))

        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({"error": "Compliance not found"}), 404

        if row["regcmp_status"] != "Pending":
            cursor.close()
            conn.close()
            return jsonify({
                "error": "Only Pending compliances can be edited"
            }), 403

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values.extend(updates.values())
        values.extend([regcmp_id, user_id])

        cursor.execute(f"""
            UPDATE regulatory_compliance
            SET {set_clause}
            WHERE regcmp_id = %s
              AND regcmp_user_id = %s
        """, tuple(values))

        conn.commit()

        cursor.close()
        conn.close()

        log_activity(
            user_id=user_id,
            user_group_id=user_group_id,
            department="Compliance",
            email=claims.get("email"),
            action=f"Regulatory Compliance Updated | ID: {regcmp_id} | Fields: {', '.join(updates.keys())}"
        )

        return jsonify({
            "message": "Compliance updated successfully",
            "regcmp_id": regcmp_id,
            "updated_fields": updates
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@compliance_bp.route("/custom/<int:slfcmp_id>", methods=["PUT"])
@jwt_required()
def edit_custom_action_date(slfcmp_id):
    try:
        claims = get_jwt()
        user_id = claims.get("sub")
        user_group_id = claims.get("user_group_id")

        data = request.get_json()
        if not data or "slfcmp_action_date" not in data:
            return jsonify({
                "error": "Only slfcmp_action_date is allowed"
            }), 400

        new_action_date = data["slfcmp_action_date"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE self_compliance
            SET slfcmp_action_date = %s
            WHERE slfcmp_id = %s
              AND slfcmp_user_id = %s
        """, (new_action_date, slfcmp_id, user_id))

        conn.commit()

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({
                "error": "Not found or unauthorized"
            }), 403


        cursor.close()
        conn.close()

        log_activity(
            user_id=user_id,
            user_group_id=user_group_id,
            department="Compliance",
            email=claims.get("email"),
            action=f"Custom Compliance Action Date Updated | ID: {slfcmp_id} | New Date: {new_action_date}"
        )

        return jsonify({
            "message": "Action date updated successfully",
            "slfcmp_action_date": new_action_date
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500