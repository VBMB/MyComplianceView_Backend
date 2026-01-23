from flask import Blueprint, request, jsonify
from database import get_db_connection
from datetime import datetime

#
regulcompli_report_bp = Blueprint('regulcompli_report_bp', __name__, url_prefix="/regulcompliance")



def decode_bytes(row):
    """Convert bytes to string for JSON serialization."""
    return {k: (v.decode('utf-8') if isinstance(v, bytes) else v) for k, v in row.items()}



@regulcompli_report_bp.route('/add', methods=['POST'])
def add_regulatory_compliance():
    try:
        data = request.get_json()

        regcmp_compliance_id = data.get('regcmp_compliance_id')
        regcmp_compliance_key = data.get('regcmp_compliance_key')
        regcmp_remind_before_days = data.get('regcmp_remind_before_days')
        regcmp_status = data.get('regcmp_status', 'Upcoming')
        regcmp_approver_email = data.get('regcmp_approver_email')
        regcmp_compliance_document = data.get('regcmp_compliance_document')
        regcmp_escalation_email = data.get('regcmp_escalation_email')
        regcmp_requested_date = data.get('regcmp_requested_date') or datetime.now().strftime('%Y-%m-%d')
        regcmp_completed_date = data.get('regcmp_completed_date')
        regcmp_user_id = data.get('regcmp_user_id')
        regcmp_user_group_id = data.get('regcmp_user_group_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO regulatory_compliance (
                regcmp_compliance_id,
                regcmp_compliance_key,
                regcmp_remind_before_days,
                regcmp_status,
                regcmp_approver_email,
                regcmp_compliance_document,
                regcmp_escalation_email,
                regcmp_requested_date,
                regcmp_completed_date,
                regcmp_user_id,
                regcmp_user_group_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            regcmp_compliance_id,
            regcmp_compliance_key,
            regcmp_remind_before_days,
            regcmp_status,
            regcmp_approver_email,
            regcmp_compliance_document,
            regcmp_escalation_email,
            regcmp_requested_date,
            regcmp_completed_date,
            regcmp_user_id,
            regcmp_user_group_id
        ))

        conn.commit()
        return jsonify({"message": "Regulatory compliance added"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()



@regulcompli_report_bp.route('/all', methods=['GET'])
def get_all_regulatory_compliances():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM regulatory_compliance ORDER BY regcmp_requested_date ASC")
        compliances = [decode_bytes(row) for row in cursor.fetchall()]
        return jsonify(compliances), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



@regulcompli_report_bp.route('/upcoming', methods=['GET'])
def get_upcoming_regulatory_compliances():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM regulatory_compliance
            WHERE regcmp_status='Upcoming'
            ORDER BY regcmp_requested_date ASC
        """)
        compliances = [decode_bytes(row) for row in cursor.fetchall()]
        return jsonify(compliances), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



@regulcompli_report_bp.route('/approved', methods=['GET'])
def get_approved_regulatory_compliances():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM regulatory_compliance
            WHERE regcmp_status='Approved'
            ORDER BY regcmp_requested_date ASC
        """)
        compliances = [decode_bytes(row) for row in cursor.fetchall()]
        return jsonify(compliances), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()