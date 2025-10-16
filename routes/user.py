from flask import Blueprint, request, jsonify, current_app
from database import get_db_connection
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

user_bp = Blueprint('user_bp', __name__, url_prefix="/user")

def generate_password(username: str) -> str:
    safe_username = "".join(ch for ch in (username or "user") if ch.isalnum()).lower()
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

@user_bp.route('/add_admin', methods=['POST'])
def add_admin():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    contact = data.get("contact")
    company_name = data.get("company_name")
    subscribers = data.get("subscribers",2)
    department = data.get("department")
    business_unit = data.get("business_unit")
    escalation_mail = data.get("escalation_mail", "")
    if not all([email, contact, company_name, department, business_unit, name]):
        return jsonify({"error": "All required fields must be provided"}), 400
    raw_password = generate_password(name)
    role = "admin"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT u.usrlst_id FROM user_list u
            JOIN user_group g ON u.usrlst_user_group_id=g.usgrp_id
            WHERE u.usrlst_role='admin' AND g.usgrp_company_name=%s
        """, (company_name,))
        if cursor.fetchone():
            return jsonify({"error": "Admin already exists for this company"}), 400
        cursor.execute("""
            INSERT INTO user_group (usgrp_company_name, usgrp_subscribers, usgrp_last_updated)
            VALUES (%s, %s, NOW())
        """, (company_name, subscribers))
        conn.commit()
        group_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO user_list 
            (usrlst_user_group_id, usrlst_name, usrlst_email, usrlst_contact, 
             usrlst_role, usrlst_department, usrlst_password, 
             usrlst_last_updated, usrlst_login_flag, usrlst_business_unit,
             usrlst_escalation_mail, usrlst_company_name)
            VALUES (%s, %s, %s, %s, %s, %s, SHA1(%s), NOW(), 0, %s, %s, %s)
        """, (group_id, name, email, contact, role, department, raw_password, business_unit, escalation_mail, company_name))
        conn.commit()
        send_email(
            email,
            "Admin Account Created",
            f"Hello {name},\n\nYour admin account has been created.\n\nEmail: {email}\nPassword: {raw_password}\nCompany: {company_name}\n\nRegards,\nTeam PseudoServices"
        )
    except Exception as e:
        conn.rollback()
        current_app.logger.exception("Failed to add admin: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
    return jsonify({"message": "Admin created successfully"}), 201

@user_bp.route('/add', methods=['POST'])
def add_user():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    contact = data.get("contact")
    role = data.get("role", "user")
    department = data.get("department")
    business_unit = data.get("business_unit")
    company_name = data.get("company_name", "")
    escalation_mail = data.get("escalation_mail", "")
    if not all([name, email, contact, department, business_unit, company_name]):
        return jsonify({"error": "All required fields must be provided"}), 400
    raw_password = generate_password(name)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT u.usrlst_user_group_id 
            FROM user_list u
            JOIN user_group g ON u.usrlst_user_group_id = g.usgrp_id
            WHERE u.usrlst_role='admin' AND g.usgrp_company_name=%s
        """, (company_name,))
        admin_info = cursor.fetchone()
        if not admin_info:
            return jsonify({"error": "No admin found for this company"}), 400
        user_group_id = admin_info["usrlst_user_group_id"]
        cursor.execute("SELECT 1 FROM user_list WHERE usrlst_email=%s OR usrlst_contact=%s", (email, contact))
        if cursor.fetchone():
            return jsonify({"error": "User already exists"}), 400
        cursor.execute("SELECT usgrp_subscribers FROM user_group WHERE usgrp_id=%s", (user_group_id,))
        group_limit = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) AS count FROM user_list WHERE usrlst_user_group_id=%s", (user_group_id,))
        user_count = cursor.fetchone()

        max_users = group_limit["usgrp_subscribers"] or 2

        if user_count["count"] >= max_users:
            return jsonify({"error": f"User limit of {max_users} reached"}), 400

        cursor.execute("""
            INSERT INTO user_list 
            (usrlst_user_group_id, usrlst_name, usrlst_email, usrlst_contact, 
             usrlst_role, usrlst_department, usrlst_password, 
             usrlst_last_updated, usrlst_login_flag, usrlst_business_unit,
             usrlst_escalation_mail, usrlst_company_name)
            VALUES (%s, %s, %s, %s, %s, %s, SHA1(%s), NOW(), 0, %s, %s, %s)
        """, (user_group_id, name, email, contact, role, department, raw_password, business_unit, escalation_mail, company_name))
        conn.commit()
        send_email(
            email,
            "User Account Created",
            f"Hello {name},\n\nYour user account has been created.\n\nEmail: {email}\nPassword: {raw_password}\nCompany: {company_name or 'N/A'}\n\nRegards,\nTeam PseudoServices"
        )
    except Exception as e:
        conn.rollback()
        current_app.logger.exception("Failed to add user: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
    return jsonify({"message": "User added successfully"}), 201

@user_bp.route('/list', methods=['GET'])
def get_user_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                usrlst_id AS id,
                usrlst_name AS name,
                usrlst_email AS email,
                usrlst_contact AS contact,
                usrlst_role AS role,
                usrlst_department AS department,
                usrlst_business_unit AS business_unit,
                usrlst_escalation_mail AS escalation_mail,
                usrlst_company_name AS company_name,
                usrlst_last_updated AS last_updated
            FROM user_list
            ORDER BY usrlst_last_updated DESC
        """)
        users = cursor.fetchall()
        return jsonify(users), 200
    except Exception as e:
        current_app.logger.exception("Failed to fetch users: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
