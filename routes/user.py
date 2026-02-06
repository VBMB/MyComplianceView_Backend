from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import get_db_connection
from datetime import datetime
import bcrypt
import smtplib
from email.mime.text import MIMEText
from utils.activity_logger import log_activity
import pymysql

user_bp = Blueprint("user_bp", __name__, url_prefix="/user")

# --------------------------------------------------
# Utilities
# --------------------------------------------------

def generate_password(username: str) -> str:
    safe = "".join(ch for ch in (username or "user") if ch.isalnum()).lower()
    now = datetime.now()
    return f"{safe}@{now.hour}{now.second}"

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

# --------------------------------------------------
# ADD ADMIN (NO JWT – SYSTEM ACTION)
# --------------------------------------------------

@user_bp.route("/add_admin", methods=["POST"])
def add_admin():
    data = request.get_json() or {}
    required = ["name", "email", "contact", "company_name", "department", "business_unit"]

    if not all(data.get(k) for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    raw_password = generate_password(data["name"])
    hashed_pw = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 1 FROM user_list u
            JOIN user_group g ON u.usrlst_user_group_id = g.usgrp_id
            WHERE u.usrlst_role='admin' AND g.usgrp_company_name=%s
        """, (data["company_name"],))
        if cursor.fetchone():
            return jsonify({"error": "Admin already exists"}), 400

        cursor.execute("""
            INSERT INTO user_group (usgrp_company_name, usgrp_subscribers, usgrp_last_updated)
            VALUES (%s, %s, NOW())
        """, (data["company_name"], data.get("subscribers", 2)))
        conn.commit()
        group_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO user_list (
                usrlst_user_group_id, usrlst_name, usrlst_email, usrlst_contact,
                usrlst_role, usrlst_department_id, usrlst_password,
                usrlst_last_updated, usrlst_login_flag,
                usrlst_business_unit_id, usrlst_escalation_mail, usrlst_company_name
            )
            VALUES (%s,%s,%s,%s,'admin',%s,%s,NOW(),0,%s,%s,%s)
        """, (
            group_id, data["name"], data["email"], data["contact"],
            data["department"], hashed_pw,
            data["business_unit"], data.get("escalation_mail", ""),
            data["company_name"]
        ))

        conn.commit()

        send_email(
            data["email"],
            "Admin Account Created",
            f"Email: {data['email']}\nPassword: {raw_password}"
        )

        return jsonify({"message": "Admin created"}), 201

    except Exception as e:
        conn.rollback()
        current_app.logger.exception(e)
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --------------------------------------------------
# ADD USER (ADMIN ONLY)
# --------------------------------------------------

@user_bp.route("/add", methods=["POST"])
@jwt_required()
def add_user():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin only"}), 403

    data = request.get_json() or {}
    required = ["name", "email", "contact", "department_id", "business_unit_id", "user_group_id"]

    if not all(data.get(k) for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    raw_password = generate_password(data["name"])
    hashed_pw = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        user_group_id = claims.get("user_group_id")

        cursor.execute("SELECT 1 FROM user_list WHERE usrlst_email=%s", (data["email"],))
        if cursor.fetchone():
            return jsonify({"error": "User already exists"}), 400

        cursor.execute("""
            INSERT INTO user_list (
                usrlst_user_group_id, usrlst_name, usrlst_email, usrlst_contact,
                usrlst_role, usrlst_department_id, usrlst_password,
                usrlst_last_updated, usrlst_login_flag,
                usrlst_business_unit_id, usrlst_escalation_mail
            )
            VALUES (%s,%s,%s,%s,'user',%s,%s,NOW(),1,%s,%s)
        """, (
            user_group_id, data["name"], data["email"], data["contact"],
            data["department_id"], hashed_pw,
            data["business_unit_id"], data.get("escalation_mail", "")
        ))

        conn.commit()

        log_activity(
            user_id=claims.get("sub"),
            user_group_id=user_group_id,
            department=data["department_id"],
            email=data["email"],
            action=f"User Created ({data['name']})"
        )

        send_email(
            data["email"],
            "User Account Created",
            f"Email: {data['email']}\nPassword: {raw_password}"
        )

        return jsonify({"message": "User added"}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --------------------------------------------------
# LIST USERS (ADMIN ONLY)
# --------------------------------------------------

@user_bp.route("/list", methods=["GET"])
@jwt_required()
def list_users():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin only"}), 403

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor) 

    cursor.execute("""
        SELECT
            ul.usrlst_id,
            ul.usrlst_user_group_id,

            ul.usrlst_business_unit_id,
            bu.usrbu_business_unit_name AS bu_name,

            ul.usrlst_department_id,
            ud.usrdept_department_name AS dept_name,

            ul.usrlst_name,
            ul.usrlst_email,
            ul.usrlst_contact,
            ul.usrlst_login_flag,
            ul.usrlst_last_updated,
            ul.usrlst_role,
            ul.usrlst_escalation_mail
        FROM user_list ul
        LEFT JOIN user_business_unit bu
            ON bu.usrbu_id = ul.usrlst_business_unit_id
        LEFT JOIN user_departments ud
            ON ud.usrdept_id = ul.usrlst_department_id
        WHERE ul.usrlst_role != 'admin'
          AND ul.usrlst_user_group_id = %s
        ORDER BY ul.usrlst_last_updated DESC
    """, (claims["user_group_id"],))

    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(users), 200


#update user

@user_bp.route("/update/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    claims = get_jwt()

    if claims.get("role") != "admin":
        return jsonify({"error": "Admin only"}), 403

    user_group_id = claims.get("user_group_id")
    data = request.get_json() or {}

    fields = []
    values = []

    department_id = None
    department_name = "N/A"

    field_map = {
        "name": "usrlst_name",
        "email": "usrlst_email",
        "contact": "usrlst_contact",
        "business_unit_id": "usrlst_business_unit_id",
        "department_id": "usrlst_department_id",
        "login_flag": "usrlst_login_flag"
    }

    for key, db_col in field_map.items():
        if key in data:
            fields.append(f"{db_col} = %s")
            values.append(data[key])

            if key == "department_id":
                department_id = data[key]

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    fields.append("usrlst_last_updated = NOW()")

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:

        cursor.execute("""
            SELECT usrlst_id
            FROM user_list
            WHERE usrlst_id = %s
              AND usrlst_user_group_id = %s
        """, (user_id, user_group_id))

        if not cursor.fetchone():
            return jsonify({"error": "User not found"}), 404

        values.extend([user_id, user_group_id])

        cursor.execute(
            f"""
            UPDATE user_list
            SET {', '.join(fields)}
            WHERE usrlst_id = %s
              AND usrlst_user_group_id = %s
            """,
            tuple(values)
        )


        if department_id:
            cursor.execute("""
                SELECT usrdept_department_name
                FROM user_departments
                WHERE usrdept_id = %s
                  AND usrdept_user_group_id = %s
            """, (department_id, user_group_id))

            dept_row = cursor.fetchone()
            if dept_row:
                department_name = dept_row["usrdept_department_name"]  # ✅ FIX

        conn.commit()

        log_activity(
            user_id=claims.get("sub"),
            user_group_id=user_group_id,
            department=department_name,
            email=claims.get("email"),
            action=f"User Updated (ID {user_id})"
        )

        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@user_bp.route("/forgot/password", methods=["POST"])
def forgot_password():

    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute("""
            SELECT usrlst_id, usrlst_name, usrlst_email, usrlst_role
            FROM user_list
            WHERE usrlst_email = %s
        """, (email,))

        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        ADMIN_EMAIL = "sanskarsharma0119@gmail.com" 

        subject = "Forgot Password Request"

        body = f"""
Hello Admin,

A user has requested a password reset.

User Details:
---------------------
User ID : {user['usrlst_id']}
Name  : {user['usrlst_name']}
Email : {user['usrlst_email']}
Role  : {user['usrlst_role']}

Please reset the password manually and share with the user.

Regards,
MyComplianceView
"""

        send_email(
            ADMIN_EMAIL,
            subject,
            body
        )


        return jsonify({
            "message": "Password reset request sent!"
        }), 200


    except Exception as e:
        current_app.logger.exception(e)
        return jsonify({"error": "Something went wrong"}), 500


    finally:
        cursor.close()
        conn.close()
