from flask import Blueprint, request, jsonify, current_app
from database import get_db_connection  # your DictCursor setup
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

user_bp = Blueprint('user_bp', __name__, url_prefix="/user")

def generate_password(username: str) -> str:
    safe_username = "".join(ch for ch in username if ch.isalnum()).lower()
    now = datetime.now()
    return f"{safe_username}@{now.hour}:{now.second}"

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

@user_bp.route('/add', methods=['POST'])
def add_user():
    data = request.get_json() or {}

    name = data.get("name")
    email = data.get("email")
    contact = data.get("contact")
    role = data.get("role", "user")
    department = data.get("department")
    user_group_id = data.get("user_group_id")
    business_unit = data.get("business_unit")
    escalation_mail = data.get("escalation_mail")
    company_name = data.get("company_name")
    # debug_return_password = data.get("debug_return_password", False)


    if not name or not email:
        return jsonify({"error": "Name and Email are required"}), 400
    if not user_group_id:
        return jsonify({"error": "User group ID is required"}), 400

    raw_password = generate_password(name)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT 1 FROM user_list
            WHERE usrlst_email = %s OR usrlst_contact = %s
        """, (email, contact))
        if cursor.fetchone():
            return jsonify({"error": "User already exists"}), 400

        # --- Check user group subscriber limit ---
        cursor.execute("SELECT usgrp_subscribers FROM user_group WHERE usgrp_id = %s", (user_group_id,))
        group_info = cursor.fetchone()
        if not group_info:
            return jsonify({"error": "Invalid user group ID"}), 400

        max_subscribers = group_info['usgrp_subscribers']

        cursor.execute("SELECT COUNT(*) as count FROM user_list WHERE usrlst_user_group_id = %s", (user_group_id,))
        current_count = cursor.fetchone()['count']

        if current_count >= max_subscribers:
            return jsonify({"error": f"Cannot add user. User group limit of {max_subscribers} reached."}), 400


        cursor.execute("""
            INSERT INTO user_list 
            (usrlst_user_group_id, usrlst_name, usrlst_email, usrlst_contact, 
             usrlst_role, usrlst_department, usrlst_password, 
             usrlst_last_updated, usrlst_login_flag, usrlst_business_unit,
             usrlst_escalation_mail, usrlst_company_name)
            VALUES (%s, %s, %s, %s, %s, %s, SHA1(%s), NOW(), 0, %s, %s, %s)
        """, (
            user_group_id, name, email, contact, role, department,
            raw_password, business_unit, escalation_mail, company_name
        ))
        conn.commit()


        try:
            send_email(
                email,
                "Your Account Credentials",
                f"Hello {name},\n\nYour account has been created.\n\n"
                f"Email: {email}\nPassword: {raw_password}\n\n"
                f"Company: {company_name or 'N/A'}\n"
                f"Escalation Email: {escalation_mail or 'N/A'}\n\n"
                f"Regards,\nTeam PseudoServices"
            )
        except Exception as email_err:
            current_app.logger.exception("Failed to send email: %s", email_err)
            return jsonify({"message": "User added but failed to send email. Check server logs."}), 201

    except Exception as e:
        conn.rollback()
        current_app.logger.exception("Failed to add user: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    resp = {"message": "User added successfully. Credentials sent to email."}
    #if debug_return_password:
        #resp["generated_password"] = raw_password

    return jsonify(resp), 201
