from flask import Blueprint, request, jsonify
from database import get_db_connection
from dateutil import parser

form_bp = Blueprint('form', __name__)

@form_bp.route('/submit', methods=['POST'])
def submit_form():
    data = request.get_json()

    company_name = data.get('company_name')
    govt_document = data.get('govt_document')
    cin = data.get('cin')
    subscribers = data.get('subscribers', 2)
    end_of_subscription = data.get('end_of_subscription')

    # Validate required fields
    if not company_name or not govt_document or not cin:
        return jsonify({"error": "Company Name, Govt Document, and CIN are required"}), 400

    # Parse end_of_subscription if provided
    if end_of_subscription:
        try:
            end_of_subscription = parser.parse(end_of_subscription).strftime('%Y-%m-%d')
        except Exception:
            return jsonify({"error": "Invalid date format for end_of_subscription"}), 400
    else:
        end_of_subscription = None

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if CIN already exists
        cursor.execute("SELECT * FROM user_group WHERE usgrp_cin = %s", (cin,))
        existing_company = cursor.fetchone()
        if existing_company:
            return jsonify({"error": "Company already registered with this CIN"}), 400

        # Insert new record
        cursor.execute("""
            INSERT INTO user_group 
            (usgrp_company_name, usgrp_govt_document, usgrp_cin, usgrp_subscribers, usgrp_end_of_subscription)
            VALUES (%s, %s, %s, %s, %s)
        """, (company_name, govt_document, cin, subscribers, end_of_subscription))
        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Company details submitted successfully"}), 201


@form_bp.route('/all', methods=['GET'])
def get_forms():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            usgrp_id,
            usgrp_company_name,
            usgrp_govt_document,
            usgrp_cin,
            usgrp_subscribers,
            usgrp_last_updated,
            usgrp_end_of_subscription
        FROM user_group
        ORDER BY usgrp_id DESC
    """)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(results), 200
