from flask import Blueprint, request, jsonify, session
from database import get_db_connection
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from email.mime.text import MIMEText
import smtplib

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


# reminder
def calculate_reminders(action_date_str, month_before, day_before, remaining_days_before, escalation_days):
    action_date = datetime.strptime(action_date_str, "%Y-%m-%d")

    month_reminder = action_date - relativedelta(months=month_before) if month_before else None
    day_reminder = action_date - timedelta(days=day_before) if day_before else None
    remaining_days_reminder = action_date - timedelta(days=remaining_days_before) if remaining_days_before else None
    escalation_reminder = action_date - timedelta(days=escalation_days) if escalation_days else None

# date
    return (
        month_reminder.strftime("%Y-%m-%d") if month_reminder else None,
        day_reminder.strftime("%Y-%m-%d") if day_reminder else None,
        remaining_days_reminder.strftime("%Y-%m-%d") if remaining_days_reminder else None,
        escalation_reminder.strftime("%Y-%m-%d") if escalation_reminder else None
    )



@compliance_bp.route("/countries", methods=["GET"])
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
def get_compliance_by_act_and_country():
    try:
        country = request.args.get("country")
        act = request.args.get("act")
        if not country or not act:
            return jsonify({"error": "country and act parameters are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cmplst_particular, cmplst_description
            FROM compliance_list
            WHERE cmplst_country = %s AND cmplst_act = %s
        """, (country, act))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"country": country, "act": act, "records": records}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@compliance_bp.route("/add", methods=["POST"])
def add_compliance():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json()
        required_fields = [
            "cmplst_compliance_key", "cmplst_country", "cmplst_act",
            "cmplst_particular", "cmplst_start_date", "cmplst_end_date",
            "cmplst_action_date", "cmplst_description",
            "cmplst_month", "cmplst_day", "cmplst_remaining_days",
            "cmplst_escalation_mail", "cmplst_reminder_on_escalation_mail"
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        month_reminder, day_reminder, remaining_days_reminder, escalation_reminder = calculate_reminders(
            data["cmplst_action_date"],
            int(data["cmplst_month"]),
            int(data["cmplst_day"]),
            int(data["cmplst_remaining_days"]),
            int(data["cmplst_reminder_on_escalation_mail"])
        )

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO compliance_list (
                cmplst_user_id, cmplst_compliance_key, cmplst_country,
                cmplst_act, cmplst_particular, cmplst_start_date,
                cmplst_end_date, cmplst_action_date, cmplst_description,
                cmplst_month, cmplst_day, cmplst_remaining_days,
                cmplst_escalation_mail, cmplst_reminder_on_escalation_mail,
                cmplst_next_month_date, cmplst_next_day_date,
                cmplst_next_remaining_date, cmplst_next_escalation_date
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id,
            data["cmplst_compliance_key"],
            data["cmplst_country"],
            data["cmplst_act"],
            data["cmplst_particular"],
            data["cmplst_start_date"],
            data["cmplst_end_date"],
            data["cmplst_action_date"],
            data["cmplst_description"],
            data["cmplst_month"],
            data["cmplst_day"],
            data["cmplst_remaining_days"],
            data["cmplst_escalation_mail"],
            data["cmplst_reminder_on_escalation_mail"],
            month_reminder,
            day_reminder,
            remaining_days_reminder,
            escalation_reminder
        ))

        conn.commit()
        cursor.close()
        conn.close()

        if data["cmplst_escalation_mail"]:
            send_email(
                data["cmplst_escalation_mail"],
                "Compliance Escalation Alert",
                f"Action Date: {data['cmplst_action_date']}\nEscalation Reminder Date: {escalation_reminder}"
            )

        return jsonify({
            "message": "Compliance added successfully",
            "month_reminder": month_reminder,
            "day_reminder": day_reminder,
            "remaining_days_reminder": remaining_days_reminder,
            "escalation_reminder": escalation_reminder
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@compliance_bp.route("/list", methods=["GET"])
def list_compliances():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cmplst_id, cmplst_country, cmplst_act, cmplst_particular,
                   cmplst_start_date, cmplst_end_date, cmplst_action_date, cmplst_description,
                   cmplst_next_month_date, cmplst_next_day_date,
                   cmplst_next_remaining_date, cmplst_next_escalation_date,
                   cmplst_escalation_mail
            FROM compliance_list
            WHERE cmplst_user_id = %s
            ORDER BY cmplst_end_date DESC
        """, (user_id,))

        compliances = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"compliances": compliances}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
