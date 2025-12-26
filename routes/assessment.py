from flask import Blueprint, request, jsonify, session, Response
import csv
import io
from database import get_db_connection

assessment_bp = Blueprint("assessment_bp", __name__, url_prefix="/assessment")


# assessments
@assessment_bp.route("/list", methods=["GET"])
def list_assessments():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT dpdpas_id, dpdp_sheet
        FROM dpdp_assessment_sheets
    """)
    assessments = cur.fetchall()

    return jsonify(assessments), 200


# download csv
@assessment_bp.route("/download/<int:dpdpas_id>", methods=["GET"])
def download_assessment(dpdpas_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get assessment details
    cur.execute("""
        SELECT dpdp_sheet, dpdp_answer_column_name
        FROM dpdp_assessment_sheets
        WHERE dpdpas_id = %s
    """, (dpdpas_id,))
    assessment = cur.fetchone()

    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404

    # Get questions
    cur.execute("""
        SELECT question
        FROM dpdp_assessment_questions
        WHERE dpdpas_id = %s
    """, (dpdpas_id,))
    questions = cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Question", assessment["dpdp_answer_column_name"]])

    for q in questions:
        writer.writerow([q["question"], ""])

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            f"attachment; filename={assessment['dpdp_sheet']}.csv"
        }
    )



@assessment_bp.route("/upload/<int:dpdpas_id>", methods=["POST"])
def upload_assessment(dpdpas_id):
    user_id = session.get("user_id")
    user_group_id = session.get("user_group_id")
    file = request.files.get("file")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if not file:
        return jsonify({"error": "CSV file required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Get answer column name
    cur.execute("""
        SELECT dpdp_answer_column_name
        FROM dpdp_assessment_sheets
        WHERE dpdpas_id = %s
    """, (dpdpas_id,))
    sheet = cur.fetchone()

    if not sheet:
        return jsonify({"error": "Assessment not found"}), 404

    answer_col = sheet["dpdp_answer_column_name"]

    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    total = 0
    yes_count = 0


    cur.execute("""
        DELETE FROM dpdp_assessment_answers
        WHERE dpdpans_user_id = %s
        AND dpdpans_dpdpas_id = %s
    """, (user_id, dpdpas_id))

    for row in reader:
        total += 1
        answer = row[answer_col].strip().lower()

        if answer == "yes":
            yes_count += 1

        cur.execute("""
            INSERT INTO dpdp_assessment_answers
            (dpdpans_user_id, dpdpans_dpdpas_id, dpdpans_question, dpdpans_answer)
            VALUES (%s, %s, %s, %s)
        """, (
            user_id,
            dpdpas_id,
            row["Question"],
            answer
        ))

    score = round((yes_count / total) * 100, 2)


    cur.execute("""
        DELETE FROM dpdp_assessment_upload
        WHERE dpdpau_user_id = %s
        AND dpdpau_dpdpas_key = %s
    """, (user_id, dpdpas_id))


    cur.execute("""
        INSERT INTO dpdp_assessment_upload
        (dpdpau_user_id,
         dpdpau_user_group_id,
         dpdpau_dpdpas_key,
         dpdpau_uploaded_sheet,
         dpdpau_score)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        user_id,
        user_group_id,
        dpdpas_id,
        file.filename,
        score
    ))

    conn.commit()

    return jsonify({
        "assessment_id": dpdpas_id,
        "total_questions": total,
        "yes_answers": yes_count,
        "score": score
    }), 200



@assessment_bp.route("/overall-score", methods=["GET"])
def overall_score():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT AVG(dpdpau_score) AS overall_score
        FROM dpdp_assessment_upload
        WHERE dpdpau_user_id = %s
    """, (user_id,))

    result = cur.fetchone()

    return jsonify({
        "overall_score": round(result["overall_score"], 2)
        if result["overall_score"] else None
    }), 200
