from flask import Blueprint, request, jsonify, session
import smtplib
from email.mime.text import MIMEText

form_submission_bp = Blueprint("form_submission_bp", __name__, url_prefix="/Submission")

def send_email(body):
    SMTP_SERVER = "mail.pseudoteam.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "info@pseudoteam.com"
    SENDER_PASSWORD = "dppbHwdU9mKW"

    msg = MIMEText(body)
    msg["Subject"] = "New Compliance Form Submission"
    msg["From"] = "info@pseudoteam.com"
    msg["To"] = "info@pseudoteam.com"

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            print("Form submission email sent successfully.")
    except Exception as e:
        print("Failed to send email:", e)
        raise e


@form_submission_bp.route("/submit", methods=["POST"])
def submit_form():
    try:

        if "user_id" not in session:
            return jsonify({"error": "Unauthorized. Please log in first."}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400


        user_name = session.get("user_name", "Unknown User")
        user_email = session.get("user_email", "Unknown Email")
        user_department = session.get("user_department", "Unknown Department")

        # Create email body with user + submitted data
        body = f"""
New Compliance Form Submission

Submitted by:
Name: {user_name}
Email: {user_email}
Department: {user_department}

Submitted Details:
"""
        for key, value in data.items():
            body += f"{key}: {value}\n"

        send_email(body)

        return jsonify({"message": "Form details sent successfully to info@pseudoteam.com"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500