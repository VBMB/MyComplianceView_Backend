# from flask import Blueprint, jsonify
# from flask_jwt_extended import jwt_required, get_jwt
# from database import get_db_connection

# report_bp = Blueprint("report_bp", __name__, url_prefix="/report")


# @report_bp.route("/compliance", methods=["GET"])
# @jwt_required()
# def compliance_report():
#     try:
#         claims = get_jwt()
#         user_group_id = claims.get("user_group_id")

#         conn = get_db_connection()
#         cursor = conn.cursor()

#         regulatory_sql = """
#         SELECT
#             rc.regcmp_compliance_id           AS report_id,
#             rc.regcmp_act                     AS act,
#             rc.regcmp_particular              AS name,
#             rc.regcmp_description             AS description,
#             rc.regcmp_start_date              AS start_date,
#             rc.regcmp_action_date             AS action_date,
#             rc.regcmp_end_date                AS end_date,
#             rc.regcmp_original_action_date    AS original_date,
#             rc.regcmp_status                  AS status,
#             rc.regcmp_requested_date          AS request_date,
#             rc.regcmp_response_date           AS response_date
#         FROM regulatory_compliance rc
#         JOIN user_group ug
#           ON ug.usgrp_id = rc.regcmp_user_group_id
#         WHERE rc.regcmp_user_group_id = %s
#         """

#         cursor.execute(regulatory_sql, (user_group_id,))
#         regulatory_rows = cursor.fetchall()

#         self_sql = """
#         SELECT
#             sc.slfcmp_compliance_id           AS report_id,
#             'self'                            AS act,
#             sc.slfcmp_particular              AS name,
#             sc.slfcmp_description             AS description,
#             sc.slfcmp_start_date              AS start_date,
#             sc.slfcmp_action_date             AS action_date,
#             sc.slfcmp_end_date                AS end_date,
#             sc.slfcmp_original_action_date    AS original_date,
#             sc.slfcmp_status                  AS status,
#             sc.slfcmp_requested_date          AS request_date,
#             sc.slfcmp_response_date           AS response_date
#         FROM self_compliance sc
#         JOIN user_group ug
#           ON ug.usgrp_id = sc.slfcmp_user_group_id
#         WHERE sc.slfcmp_user_group_id = %s
#         """

#         cursor.execute(self_sql, (user_group_id,))
#         self_rows = cursor.fetchall()

#         cursor.close()
#         conn.close()

#         """
#         ----------------------------------------------------
#         MERGE + SORT (BY ACTION DATE)
#         ----------------------------------------------------
#         """
#         all_rows = regulatory_rows + self_rows
#         all_rows.sort(key=lambda x: (x["action_date"] or ""))

#         return jsonify({
#             "group_id": user_group_id,
#             "total_records": len(all_rows),
#             "data": all_rows
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
import pymysql
from database import get_db_connection
from datetime import date

report_bp = Blueprint("report_bp", __name__, url_prefix="/report")


@report_bp.route("/admin/compliance", methods=["GET"])
@jwt_required()
def compliance_report():
    try:
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")

        conn = get_db_connection()
        # cursor = conn.cursor(dictionary=True)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        regulatory_sql = """
        SELECT
            rc.regcmp_compliance_id           AS report_id,
            rc.regcmp_act                     AS act,
            rc.regcmp_particular              AS name,
            rc.regcmp_description             AS description,
            rc.regcmp_start_date              AS start_date,
            rc.regcmp_action_date             AS action_date,
            rc.regcmp_end_date                AS end_date,
            rc.regcmp_original_action_date    AS original_date,
            rc.regcmp_status                  AS status,
            rc.regcmp_requested_date          AS request_date,
            rc.regcmp_response_date           AS response_date,
            rc.regcmp_user_id                 AS user_id,
            ul.usrlst_name                    AS user_name,
            ud.usrdept_department_name        AS dept_name,
            bu.usrbu_business_unit_name       AS bu_name
        FROM regulatory_compliance rc
        JOIN user_group ug
            ON ug.usgrp_id = rc.regcmp_user_group_id
        JOIN user_list ul
            ON ul.usrlst_id = rc.regcmp_user_id
        JOIN user_business_unit bu
            ON bu.usrbu_id = ul.usrlst_business_unit_id
        JOIN user_departments ud
            ON ud.usrdept_id = ul.usrlst_department_id
        WHERE rc.regcmp_user_group_id = %s
        """

        cursor.execute(regulatory_sql, (user_group_id,))
        regulatory_rows = cursor.fetchall()

        self_sql = """
        SELECT
            sc.slfcmp_compliance_id           AS report_id,
            'self'                            AS act,
            sc.slfcmp_particular              AS name,
            sc.slfcmp_description             AS description,
            sc.slfcmp_start_date              AS start_date,
            sc.slfcmp_action_date             AS action_date,
            sc.slfcmp_end_date                AS end_date,
            sc.slfcmp_original_action_date    AS original_date,
            sc.slfcmp_status                  AS status,
            sc.slfcmp_requested_date          AS request_date,
            sc.slfcmp_response_date           AS response_date,
            sc.slfcmp_user_id                 AS user_id,
            ul.usrlst_name                    AS user_name,
            ud.usrdept_department_name        AS dept_name,
            bu.usrbu_business_unit_name       AS bu_name
        FROM self_compliance sc
        JOIN user_group ug
            ON ug.usgrp_id = sc.slfcmp_user_group_id
        JOIN user_list ul
            ON ul.usrlst_id = sc.slfcmp_user_id
        JOIN user_business_unit bu
            ON bu.usrbu_id = ul.usrlst_business_unit_id
        JOIN user_departments ud
            ON ud.usrdept_id = ul.usrlst_department_id
        WHERE sc.slfcmp_user_group_id = %s
        """

        cursor.execute(self_sql, (user_group_id,))
        self_rows = cursor.fetchall()

        cursor.close()
        conn.close()

        all_rows = regulatory_rows + self_rows
        all_rows.sort(
            key=lambda x: x["action_date"] if x["action_date"] else date.max
        )

        return jsonify({
            "group_id": user_group_id,
            "total_records": len(all_rows),
            "data": all_rows
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@report_bp.route("/user/compliance", methods=["GET"])
@jwt_required()
def user_compliance_report():
    try:
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")
        user_id = claims.get("sub")  

        if not user_group_id or not user_id:
            return jsonify({"error": "Invalid token"}), 401

        user_group_id = int(user_group_id)
        user_id = int(user_id)

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        regulatory_sql = """
        SELECT
            rc.regcmp_compliance_id           AS report_id,
            rc.regcmp_act                     AS act,
            rc.regcmp_particular              AS name,
            rc.regcmp_description             AS description,
            rc.regcmp_start_date              AS start_date,
            rc.regcmp_action_date             AS action_date,
            rc.regcmp_end_date                AS end_date,
            rc.regcmp_original_action_date    AS original_date,
            rc.regcmp_status                  AS status,
            rc.regcmp_requested_date          AS request_date,
            rc.regcmp_response_date           AS response_date,
            rc.regcmp_user_id                 AS user_id,
            ul.usrlst_name                    AS user_name,
            ud.usrdept_department_name        AS dept_name,
            bu.usrbu_business_unit_name       AS bu_name
        FROM regulatory_compliance rc
        JOIN user_list ul
            ON ul.usrlst_id = rc.regcmp_user_id
        JOIN user_business_unit bu
            ON bu.usrbu_id = ul.usrlst_business_unit_id
        JOIN user_departments ud
            ON ud.usrdept_id = ul.usrlst_department_id
        WHERE rc.regcmp_user_group_id = %s
          AND rc.regcmp_user_id = %s
        """

        cursor.execute(regulatory_sql, (user_group_id, user_id))
        regulatory_rows = cursor.fetchall()

        self_sql = """
        SELECT
            sc.slfcmp_compliance_id           AS report_id,
            'self'                            AS act,
            sc.slfcmp_particular              AS name,
            sc.slfcmp_description             AS description,
            sc.slfcmp_start_date              AS start_date,
            sc.slfcmp_action_date             AS action_date,
            sc.slfcmp_end_date                AS end_date,
            sc.slfcmp_original_action_date    AS original_date,
            sc.slfcmp_status                  AS status,
            sc.slfcmp_requested_date          AS request_date,
            sc.slfcmp_response_date           AS response_date,
            sc.slfcmp_user_id                 AS user_id,
            ul.usrlst_name                    AS user_name,
            ud.usrdept_department_name        AS dept_name,
            bu.usrbu_business_unit_name       AS bu_name
        FROM self_compliance sc
        JOIN user_list ul
            ON ul.usrlst_id = sc.slfcmp_user_id
        JOIN user_business_unit bu
            ON bu.usrbu_id = ul.usrlst_business_unit_id
        JOIN user_departments ud
            ON ud.usrdept_id = ul.usrlst_department_id
        WHERE sc.slfcmp_user_group_id = %s
          AND sc.slfcmp_user_id = %s
        """

        cursor.execute(self_sql, (user_group_id, user_id))
        self_rows = cursor.fetchall()

        cursor.close()
        conn.close()

        all_rows = regulatory_rows + self_rows
        all_rows.sort(
            key=lambda x: x["action_date"] if x["action_date"] else date.max
        )

        return jsonify({
            "group_id": user_group_id,
            "user_id": user_id,
            "total_records": len(all_rows),
            "data": all_rows
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500