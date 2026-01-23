from flask import Blueprint, request, jsonify, session, Response
import csv
import io
from datetime import datetime
from database import get_db_connection

assessment_bp = Blueprint("assessment_bp", __name__, url_prefix="/assessment")



@assessment_bp.route("/list", methods=["GET"])
def list_assessments():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            dpdpas_assessment_name,
            MAX(dpdpas_assessment_key) AS dpdpas_assessment_key
        FROM dpdp_assessment_sheets
        GROUP BY dpdpas_assessment_name
        ORDER BY dpdpas_assessment_name
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data), 200



@assessment_bp.route("/download/<assessment_name>", methods=["GET"])
def download_assessment(assessment_name):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT MAX(dpdpas_assessment_key) AS assessment_key
        FROM dpdp_assessment_sheets
        WHERE dpdpas_assessment_name = %s
    """, (assessment_name,))
    row = cur.fetchone()

    if not row or not row["assessment_key"]:
        cur.close()
        conn.close()
        return jsonify({"error": "Assessment not found"}), 404

    assessment_key = row["assessment_key"]

    cur.execute("""
        SELECT dpdpas_id, dpdpas_question
        FROM dpdp_assessment_sheets
        WHERE dpdpas_assessment_key = %s
    """, (assessment_key,))
    questions = cur.fetchall()

    if not questions:
        cur.close()
        conn.close()
        return jsonify({"error": "Assessment not found"}), 404

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["question_id", "question", "answer"])

    for q in questions:
        writer.writerow([q["dpdpas_id"], q["dpdpas_question"], ""])

    output.seek(0)
    cur.close()
    conn.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={assessment_name}.csv"}
    )


@assessment_bp.route("/upload/<assessment_name>", methods=["POST"])
def upload_assessment(assessment_name):
    user_id = session.get("user_id")
    user_group_id = session.get("user_group_id")

    if not user_id or not user_group_id:
        return jsonify({"error": "Unauthorized"}), 401

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "CSV file required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # latest assessment key
        cur.execute("""
            SELECT MAX(dpdpas_assessment_key) AS assessment_key
            FROM dpdp_assessment_sheets
            WHERE dpdpas_assessment_name = %s
        """, (assessment_name,))
        row = cur.fetchone()

        if not row or not row["assessment_key"]:
            return jsonify({"error": "Assessment not found"}), 404

        assessment_key = row["assessment_key"]

        # 🔑 YEAR + USER_ID QUEUE ID
        current_year = datetime.now().year
        queue_id = int(f"{current_year}{user_id}")

        # prevent duplicate yearly attempt
        cur.execute("""
            SELECT dpdps_id
            FROM dpdp_assessment_score
            WHERE dpdps_queue_id = %s
        """, (queue_id,))

        if cur.fetchone():
            return jsonify({
                "error": "Assessment already submitted for this year"
            }), 403

        # create score row
        cur.execute("""
            INSERT INTO dpdp_assessment_score
            (dpdps_queue_id, dpdps_user_id, dpdps_user_group_id, dpdps_score)
            VALUES (%s, %s, %s, %s)
        """, (queue_id, user_id, user_group_id, 0))

        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)

        total = 0
        yes_count = 0

        for r in reader:
            question_id = r.get("question_id")
            answer = r.get("answer")

            if not question_id or not answer:
                conn.rollback()
                return jsonify({"error": "Invalid CSV format"}), 400

            cur.execute("""
                SELECT dpdpas_question
                FROM dpdp_assessment_sheets
                WHERE dpdpas_id = %s
                  AND dpdpas_assessment_key = %s
            """, (question_id, assessment_key))
            qrow = cur.fetchone()

            if not qrow:
                conn.rollback()
                return jsonify({
                    "error": f"Invalid question_id {question_id}"
                }), 400

            answer = answer.strip().lower()

            if answer in ("y", "yes"):
                normalized_answer = "yes"
                yes_count += 1
            elif answer in ("n", "no"):
                normalized_answer = "no"
            else:
                conn.rollback()
                return jsonify({
                    "error": f"Invalid answer '{answer}'. Allowed: yes / no"
                }), 400

            total += 1

            cur.execute("""
                INSERT INTO dpdp_assessment_upload
                (dpdpau_assessment_name,
                 dpdpau_question,
                 dpdpau_answer,
                 dpdpau_user_group_id,
                 dpdpau_user_id,
                 dpdpau_queue_id,
                 dpdpau_result,
                 dpdpas_assessment_key)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                assessment_name,
                qrow["dpdpas_question"],
                normalized_answer,
                user_group_id,
                user_id,
                queue_id,
                normalized_answer,
                assessment_key
            ))

        score = round((yes_count / total) * 100, 2) if total else 0

        cur.execute("""
            UPDATE dpdp_assessment_score
            SET dpdps_score = %s
            WHERE dpdps_queue_id = %s
        """, (score, queue_id))

        conn.commit()

        return jsonify({
            "assessment_name": assessment_name,
            "assessment_key": assessment_key,
            "queue_id": queue_id,
            "total_questions": total,
            "yes_answers": yes_count,
            "score": score
        }), 200

    finally:
        cur.close()
        conn.close()



@assessment_bp.route("/overall-score", methods=["GET"])
def overall_score():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT AVG(dpdps_score) AS overall_score
        FROM dpdp_assessment_score
        WHERE dpdps_user_id = %s
    """, (user_id,))
    result = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify({
        "overall_score": result["overall_score"] if result else None
    }), 200
