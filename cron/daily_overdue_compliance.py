import sys
import os
import pymysql
import smtplib
from datetime import datetime
from email.message import EmailMessage


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

from database import get_db_connection

#config
SMTP_HOST = "mail.pseudoteam.com"
SMTP_PORT = 587
SMTP_USER = "info@pseudoteam.com"
SMTP_PASS = "dppbHwdU9mKW"   # move to env later
FROM_EMAIL = "info@pseudoteam.com"

#email
def send_email(to_email, user_name, items):
    msg = EmailMessage()

    msg["From"] = "Compliance Team <info@pseudoteam.com>"
    msg["To"] = to_email
    msg["Subject"] = "Pending compliances to review"
    msg["Reply-To"] = FROM_EMAIL


    text_content = f"""Hi {user_name},

You have pending compliances that need your attention.

Please log in to your account to review and complete them.

Regards,
PseudoTeam
https://pseudoteam.com
"""
    msg.set_content(text_content)

    # -------- HTML version --------
    rows_html = ""
    for item in items:
        rows_html += f"""
        <tr>
            <td>{item['compliance_type']}</td>
            <td>{item['title']}</td>
            <td>{item['act']}</td>
            <td>{item['action_date']}</td>
        </tr>
        """

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color:#333;">
        <p>Hi <strong>{user_name}</strong>,</p>

        <p>You have the following compliances pending review:</p>

        <table border="1" cellpadding="8" cellspacing="0" width="100%">
          <tr style="background:#f2f2f2;">
            <th>Type</th>
            <th>Title</th>
            <th>Act</th>
            <th>Due Date</th>
          </tr>
          {rows_html}
        </table>

        <p style="margin-top:15px;">
          Please log in to your account to take action.
        </p>

        <hr>
        <p style="font-size:12px;color:#777;">
          This email was sent by <strong>PseudoTeam</strong><br>
          https://pseudoteam.com<br>
          If you were not expecting this email, you may ignore it.
        </p>
      </body>
    </html>
    """

    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    print(f" Email sent -> {to_email}")


def fetch_overdue_compliances():
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT
            rc.regcmp_title         AS title,
            rc.regcmp_act           AS act,
            rc.regcmp_action_date   AS action_date,
            ul.usrlst_email         AS user_email,
            ul.usrlst_name          AS user_name,
            'Regulatory'            AS compliance_type
        FROM regulatory_compliance rc
        JOIN user_list ul
            ON ul.usrlst_id = rc.regcmp_user_id
        WHERE rc.regcmp_status = 'Pending'
          AND STR_TO_DATE(rc.regcmp_action_date, '%d-%m-%Y') < CURDATE()
    """)
    regulatory = cursor.fetchall()

    cursor.execute("""
        SELECT
            sc.slfcmp_particular    AS title,
            sc.slfcmp_act           AS act,
            sc.slfcmp_action_date   AS action_date,
            ul.usrlst_email         AS user_email,
            ul.usrlst_name          AS user_name,
            'Custom'                AS compliance_type
        FROM self_compliance sc
        JOIN user_list ul
            ON ul.usrlst_id = sc.slfcmp_user_id
        WHERE sc.slfcmp_status = 'Pending'
          AND STR_TO_DATE(sc.slfcmp_action_date, '%d-%m-%Y') < CURDATE()
    """)
    custom = cursor.fetchall()

    cursor.close()
    conn.close()


    return list(regulatory) + list(custom)


def send_overdue_emails(rows):
    users = {}

    for row in rows:
        email = row["user_email"]
        users.setdefault(email, {
            "name": row["user_name"],
            "items": []
        })["items"].append(row)

    for email, data in users.items():
        send_email(
            to_email=email,
            user_name=data["name"],
            items=data["items"]
        )


def run_daily_cron():
    print("Cron started at:", datetime.now())

    overdue = fetch_overdue_compliances()
    print("Overdue compliances found:", len(overdue))

    if overdue:
        send_overdue_emails(overdue)
    else:
        print("No overdue compliances found")


if __name__ == "__main__":
    run_daily_cron()
