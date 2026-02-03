import sys
import os
import pymysql
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

from database import get_db_connection

SMTP_HOST = "mail.pseudoteam.com"
SMTP_PORT = 587
SMTP_USER = "info@pseudoteam.com"
SMTP_PASS = "dppbHwdU9mKW"
FROM_EMAIL = "info@pseudoteam.com"


def send_email(to_email, subject, body):
    print(f"Sending reminder to: {to_email}")

    msg = MIMEMultipart()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.send_message(msg)
    server.quit()

def fetch_reminder_compliances():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT
            rc.regcmp_title         AS title,
            rc.regcmp_act           AS act,
            rc.regcmp_action_date   AS action_date,
            rc.regcmp_reminder_days AS reminder_days,
            ul.usrlst_email         AS user_email,
            ul.usrlst_name          AS user_name,
            'Regulatory'            AS compliance_type
        FROM regulatory_compliance rc
        JOIN user_list ul
            ON ul.usrlst_id = rc.regcmp_user_id
        WHERE rc.regcmp_status = 'Pending'
          AND rc.regcmp_reminder_days > 0
          AND DATE_SUB(
                STR_TO_DATE(rc.regcmp_action_date, '%d-%m-%Y'),
                INTERVAL rc.regcmp_reminder_days DAY
              ) = CURDATE()
    """)

    regulatory = cursor.fetchall()

    # ---------------- CUSTOM / SELF ----------------
    cursor.execute("""
        SELECT
            sc.slfcmp_particular        AS title,
            sc.slfcmp_act               AS act,
            sc.slfcmp_action_date       AS action_date,
            sc.slfcmp_reminder_days     AS reminder_days,
            ul.usrlst_email             AS user_email,
            ul.usrlst_name              AS user_name,
            'Custom'                    AS compliance_type
        FROM self_compliance sc
        JOIN user_list ul
            ON ul.usrlst_id = sc.slfcmp_user_id
        WHERE sc.slfcmp_status = 'Pending'
          AND sc.slfcmp_reminder_days > 0
          AND DATE_SUB(
                STR_TO_DATE(sc.slfcmp_action_date, '%d-%m-%Y'),
                INTERVAL sc.slfcmp_reminder_days DAY
              ) = CURDATE()
    """)

    custom = cursor.fetchall()

    cursor.close()
    conn.close()

    return list(regulatory) + list(custom)


def send_reminder_emails(rows):
    users = {}

    for row in rows:
        email = row["user_email"]

        if email not in users:
            users[email] = {
                "name": row["user_name"],
                "items": []
            }

        users[email]["items"].append(row)

    for email, data in users.items():
        body = f"""
Dear {data['name']},

This is a reminder for the following compliance(s) that are approaching their due date.

--------------------------------------------------
UPCOMING COMPLIANCE REMINDERS
--------------------------------------------------
"""

        for item in data["items"]:
            body += f"""
Compliance Type : {item['compliance_type']}
Title           : {item['title']}
Act             : {item['act']}
Action Date     : {item['action_date']}
Reminder Days   : {item['reminder_days']}
-----------------------------------------------
"""

        body += """
Please ensure the above compliances are completed before the action date to avoid any risk.

Regards,
Compliance Management System
(This is an automated reminder)
"""

        send_email(
            to_email=email,
            subject="Compliance Reminder – Action Date Approaching",
            body=body
        )


def run_daily_reminder_cron():
    print("Reminder cron started at:", datetime.now())

    reminders = fetch_reminder_compliances()
    print("Reminder compliances found:", len(reminders))

    if reminders:
        send_reminder_emails(reminders)


if __name__ == "__main__":
    run_daily_reminder_cron()
