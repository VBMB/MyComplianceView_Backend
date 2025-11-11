from flask import Blueprint, request, jsonify, session
from database import get_db_connection

compliance_bp = Blueprint('compliance_bp', __name__, url_prefix="/compliance")

@compliance_bp.route("/countries", methods=["GET"])
def get_countries():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT cmplst_country
            FROM compliance_list
            WHERE cmplst_country IS NOT NULL
            ORDER BY cmplst_country
        """)
        countries = [row["cmplst_country"] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify({"countries": countries}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@compliance_bp.route("/acts", methods=["GET"])
def get_acts_by_country():
    try:
        country = request.args.get("country")
        if not country:
            return jsonify({"error": "country parameter is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT cmplst_act
            FROM compliance_list
            WHERE cmplst_country = %s AND cmplst_act IS NOT NULL
            ORDER BY cmplst_act
        """, (country,))
        acts = [row["cmplst_act"] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify({"country": country, "acts": acts}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@compliance_bp.route("/filter", methods=["GET"])
def get_compliance_by_act_and_country():
    try:
        country = request.args.get("country")
        act = request.args.get("act")
        if not country or not act:
            return jsonify({"error": "country and act parameters are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cmplst_particular, cmplst_description
            FROM compliance_list
            WHERE cmplst_country = %s AND cmplst_act = %s
        """, (country, act))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"country": country, "act": act, "records": records}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🟢 Add new compliance for logged-in user
@compliance_bp.route("/add", methods=["POST"])
def add_compliance():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json()
        required_fields = [
            "cmplst_compliance_key", "cmplst_country", "cmplst_act",
            "cmplst_particular", "cmplst_start_date", "cmplst_end_date",
            "cmplst_action_date", "cmplst_description"
        ]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO compliance_list (
                cmplst_user_id, cmplst_compliance_key, cmplst_country,
                cmplst_act, cmplst_particular, cmplst_start_date,
                cmplst_end_date, cmplst_action_date, cmplst_description
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id,
            data["cmplst_compliance_key"],
            data["cmplst_country"],
            data["cmplst_act"],
            data["cmplst_particular"],
            data["cmplst_start_date"],
            data["cmplst_end_date"],
            data["cmplst_action_date"],
            data["cmplst_description"]
        ))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Compliance added successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@compliance_bp.route("/list", methods=["GET"])
def list_compliances():
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cmplst_id, cmplst_country, cmplst_act, cmplst_particular,
                   cmplst_start_date, cmplst_end_date, cmplst_action_date, cmplst_description
            FROM compliance_list
            WHERE cmplst_user_id = %s
            ORDER BY cmplst_end_date DESC
        """, (user_id,))
        compliances = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"compliances": compliances}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
