from flask import Blueprint, request, jsonify, session
import csv
import io

assessment_bp = Blueprint("assessment_bp", __name__, url_prefix="/assessment")

USER_TOTALS = {}


def process_csv(file):
    total = 0
    yes_count = 0

    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    for row in reader:
        total += 1
        if row.get("Answer", "").strip().lower() == "yes":
            yes_count += 1

    return total, yes_count


@assessment_bp.route("/upload", methods=["POST"])
def upload_assessment():
    user_id = session.get("user_id")
    file = request.files.get("file")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if not file:
        return jsonify({"error": "file required"}), 400

    total, yes_count = process_csv(file)

    USER_TOTALS.setdefault(user_id, {"total": 0, "yes": 0})
    USER_TOTALS[user_id]["total"] += total
    USER_TOTALS[user_id]["yes"] += yes_count

    score = round(
        (USER_TOTALS[user_id]["yes"] / USER_TOTALS[user_id]["total"]) * 100,
        2
    )

    return jsonify({
        "message": "Assessment uploaded successfully",
        "overall_score": score
    }), 200


@assessment_bp.route("/score", methods=["GET"])
def get_overall_score():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = USER_TOTALS.get(user_id)

    if not data or data["total"] == 0:
        return jsonify({"overall_score": None}), 200

    score = round((data["yes"] / data["total"]) * 100, 2)

    return jsonify({"overall_score": score}), 200
