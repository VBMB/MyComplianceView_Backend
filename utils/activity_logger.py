from datetime import datetime
from database import get_db_connection

def log_activity(user_id, user_group_id, department, email, action):
    conn = get_db_connection()
    cur = conn.cursor()

    action_message = (
        f"User ID: {user_id} | "
        f"User Group ID: {user_group_id} | "
        f"Department: {department} | "
        f"Action: {action}"
    )

    cur.execute("""
        INSERT INTO activity_log
        (acty_user_id,
         acty_user_group_id,
         acty_department,
         acty_email,
         acty_date,
         acty_time,
         acty_action)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        user_id,
        user_group_id,
        department,
        email,
        datetime.now().date(),
        datetime.now().time(),
        action_message
    ))

    conn.commit()
    cur.close()
    conn.close()
