from flask import Blueprint, request, jsonify
from database import get_db_connection
from datetime import datetime

report_bp = Blueprint('report_bp', __name__, url_prefix="/report")



def decode_bytes(row):
    return {k: (v.decode('utf-8') if isinstance(v, bytes) else v) for k, v in row.items()}



@report_bp.route('/add', methods=['POST'])
def add_compliance():
    try:
        data = request.get_json()

        slfcmp_compliance_key = data.get('slfcmp_compliance_key')
        slfcmp_remind_before_days = data.get('slfcmp_remind_before_days')
        slfcmp_status = data.get('slfcmp_status', 'Upcoming')
        slfcmp_approver_email = data.get('slfcmp_approver_email')
        slfcmp_compliance_document = data.get('slfcmp_compliance_document')
        slfcmp_escalation_email = data.get('slfcmp_escalation_email')
        slfcmp_requested_date = data.get('slfcmp_requested_date') or datetime.now().strftime('%Y-%m-%d')
        slfcmp_completed_date = data.get('slfcmp_completed_date')
        slfcmp_user_id = data.get('slfcmp_user_id')
        slfcmp_user_group_id = data.get('slfcmp_user_group_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO self_compliance (
                slfcmp_compliance_key,
                slfcmp_remind_before_days,
                slfcmp_status,
                slfcmp_approver_email,
                slfcmp_compliance_document,
                slfcmp_escalation_email,
                slfcmp_requested_date,
                slfcmp_completed_date,
                slfcmp_user_id,
                slfcmp_user_group_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            slfcmp_compliance_key,
            slfcmp_remind_before_days,
            slfcmp_status,
            slfcmp_approver_email,
            slfcmp_compliance_document,
            slfcmp_escalation_email,
            slfcmp_requested_date,
            slfcmp_completed_date,
            slfcmp_user_id,
            slfcmp_user_group_id
        ))

        conn.commit()
        return jsonify({"message": "Compliance added"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()



@report_bp.route('/all', methods=['GET'])
def get_all_compliances():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM self_compliance ORDER BY slfcmp_requested_date ASC")
        compliances = [decode_bytes(row) for row in cursor.fetchall()]
        return jsonify(compliances), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



@report_bp.route('/upcoming', methods=['GET'])
def get_upcoming_compliances():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM self_compliance
            WHERE slfcmp_status='Upcoming'
            ORDER BY slfcmp_requested_date ASC
        """)
        compliances = [decode_bytes(row) for row in cursor.fetchall()]
        return jsonify(compliances), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



@report_bp.route('/approved', methods=['GET'])
def get_approved_compliances():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM self_compliance
            WHERE slfcmp_status='Approved'
            ORDER BY slfcmp_requested_date ASC
        """)
        compliances = [decode_bytes(row) for row in cursor.fetchall()]
        return jsonify(compliances), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
