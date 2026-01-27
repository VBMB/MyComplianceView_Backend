from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import get_db_connection
from datetime import datetime
import bcrypt
import smtplib
from email.mime.text import MIMEText
from utils.activity_logger import log_activity

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
            VALUES (%s,%s,%s,%s,'user',%s,%s,NOW(),0,%s,%s,%s)
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
    cursor = conn.cursor()

    # cursor.execute("""
    #     SELECT usrlst_id, usrlst_name, usrlst_email, usrlst_contact,
    #            usrlst_department_id, usrlst_business_unit_id, usrlst_escalation_mail
    #     FROM user_list
    #     WHERE usrlst_role!='admin' AND usrlst_user_group_id=%s
    #     ORDER BY usrlst_last_updated DESC
    # """, (claims["user_group_id"],))

    # cursor.execute("""
    #     SELECT *
    #     FROM user_list
    #     WHERE usrlst_role!='admin' AND usrlst_user_group_id=%s
    #     ORDER BY usrlst_last_updated DESC
    # """, (claims["user_group_id"],))

    cursor.execute("""
    SELECT
        usrlst_id,
        usrlst_user_group_id,
        usrlst_business_unit_id,
        usrlst_department_id,
        usrlst_name,
        usrlst_email,
        usrlst_contact,
        usrlst_login_flag,
        usrlst_last_updated,
        usrlst_role,
        usrlst_escalation_mail
    FROM user_list
    WHERE usrlst_role != 'admin'
      AND usrlst_user_group_id = %s
    ORDER BY usrlst_last_updated DESC
""", (claims["user_group_id"],))

    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(users), 200

# --------------------------------------------------
# UPDATE USER (ADMIN ONLY)
# --------------------------------------------------

@user_bp.route("/update/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin only"}), 403

    data = request.get_json() or {}
    fields, values = [], []

    for col in ["name", "contact", "department_id", "escalation_mail"]:
        if data.get(col):
            fields.append(f"usrlst_{col}=%s")
            values.append(data[col])

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    fields.append("usrlst_last_updated=NOW()")
    values.append(user_id)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
        UPDATE user_list SET {', '.join(fields)}
        WHERE usrlst_id=%s
    """, tuple(values))

    conn.commit()
    cursor.close()
    conn.close()

    log_activity(
        user_id=claims.get("sub"),
        user_group_id=claims.get("user_group_id"),
        department=data.get("department_id", "N/A"),
        email=claims.get("email"),
        action=f"User Updated (ID {user_id})"
    )

    return jsonify({"message": "User updated"}), 200

# --------------------------------------------------
# DELETE USER (ADMIN ONLY)
# --------------------------------------------------

# @user_bp.route("/delete", methods=["POST"])
# @jwt_required()
# def delete_user():
#     claims = get_jwt()
#     if claims.get("role") != "admin":
#         return jsonify({"error": "Admin only"}), 403

#     email = (request.get_json() or {}).get("email")
#     if not email:
#         return jsonify({"error": "Email required"}), 400

#     conn = get_db_connection()
#     cursor = conn.cursor()

#     cursor.execute("SELECT usrlst_id FROM user_list WHERE usrlst_email=%s", (email,))
#     user = cursor.fetchone()
#     if not user:
#         return jsonify({"error": "User not found"}), 404

#     cursor.execute("DELETE FROM regulatory_compliance WHERE regcmp_user_id=%s", (user["usrlst_id"],))
#     cursor.execute("DELETE FROM self_compliance WHERE slfcmp_user_id=%s", (user["usrlst_id"],))
#     cursor.execute("DELETE FROM user_list WHERE usrlst_id=%s", (user["usrlst_id"],))

#     conn.commit()
#     cursor.close()
#     conn.close()

#     log_activity(
#         user_id=claims.get("sub"),
#         user_group_id=claims.get("user_group_id"),
#         department="N/A",
#         email=email,
#         action=f"User Deleted ({email})"
#     )

#     return jsonify({"message": f"User {email} deleted"}), 200
