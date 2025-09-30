from flask import Blueprint, request, jsonify
from database import get_db_connection
import datetime

form_bp = Blueprint('form', __name__)


@form_bp.route('/submit', methods=['POST'])
def submit_form():
    data = request.get_json()

    company_name = data.get('company_name')
    govt_document = data.get('govt_document')
    cin = data.get('cin')

    if not company_name or not govt_document or not cin:
        return jsonify({"error": "Company Name, Govt Document, and CIN are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("SELECT * FROM user_group WHERE usgrp_cin = %s", (cin,))
    existing_company = cursor.fetchone()
    if existing_company:
        cursor.close()
        conn.close()
        return jsonify({"error": "Company already registered with this CIN"}), 400


    cursor.execute(
        "INSERT INTO user_group (usgrp_company_name, usgrp_last_updated, usgrp_govt_document, usgrp_cin) VALUES (%s, %s, %s, %s)",
        (company_name, datetime.datetime.now(), govt_document, cin)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Company details submitted successfully"})



@form_bp.route('/all', methods=['GET'])
def get_forms():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_group ORDER BY usgrp_id DESC")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)
