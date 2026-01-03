from flask import Blueprint, request, jsonify, session, Response
import csv
import io
from database import get_db_connection

assessment_bp = Blueprint("assessment_bp", __name__, url_prefix="/assessment")

@assessment_bp.route("/list", methods=["GET"])
def list_assessments():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT
            dpdpas_assessment_key,
            dpdpas_assessment_name
        FROM dpdp_assessment_sheets
    """)

    return jsonify(cur.fetchall()), 200



@assessment_bp.route("/download/<assessment_key>", methods=["GET"])
def download_assessment(assessment_key):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT dpdpas_question
        FROM dpdp_assessment_sheets
        WHERE dpdpas_assessment_key = %s
    """, (assessment_key,))

    questions = cur.fetchall()
    if not questions:
        return jsonify({"error": "Assessment not found"}), 404

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Question", "Answer"])

    for q in questions:
        writer.writerow([q["dpdpas_question"], ""])

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            f"attachment; filename={assessment_key}.csv"
        }
    )



@assessment_bp.route("/upload/<assessment_key>", methods=["POST"])
def upload_assessment(assessment_key):
    user_id = session.get("user_id")
    user_group_id = session.get("user_group_id")
    queue_id = session.get("queue_id")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "CSV file required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()


    cur.execute("""
        SELECT dpdps_id
        FROM dpdp_assessment_score
        WHERE dpdps_user_id = %s
          AND dpdps_queue_id = %s
    """, (user_id, queue_id))

    if cur.fetchone():
        return jsonify({
            "error": "Assessment already submitted. Re-upload is not allowed."
        }), 403

    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    total = 0
    yes_count = 0

    for row in reader:
        if "Question" not in row or "Answer" not in row:
            return jsonify({"error": "Invalid CSV format"}), 400

        answer = row["Answer"].strip().lower()
        total += 1

        if answer == "yes":
            yes_count += 1

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
            assessment_key,
            row["Question"],
            answer,
            user_group_id,
            user_id,
            queue_id,
            answer,
            assessment_key
        ))

    score = round((yes_count / total) * 100, 2) if total else 0


    cur.execute("""
        INSERT INTO dpdp_assessment_score
        (dpdps_queue_id,
         dpdps_user_id,
         dpdps_user_group_id,
         dpdps_score)
        VALUES (%s,%s,%s,%s)
    """, (
        queue_id,
        user_id,
        user_group_id,
        score
    ))

    conn.commit()

    return jsonify({
        "assessment_key": assessment_key,
        "total_questions": total,
        "yes_answers": yes_count,
        "score": score,
        "message": "Assessment submitted successfully"
    }), 200



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

    return jsonify({
        "overall_score": round(result["overall_score"], 2)
        if result and result["overall_score"] is not None else None
    }), 200
