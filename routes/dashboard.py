from unittest import result
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import get_db_connection
import pymysql

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix="/dashboard")

# @dashboard_bp.route('/summary', methods=['GET'])
# @jwt_required()
# def dashboard_summary():
#     try:
#         # JWT identity is stored as STRING → convert to int
#         claims = get_jwt()
#         user_group_id = claims.get("user_group_id")
#         user_id = get_jwt_identity()

#         if not user_id:
#             return jsonify({"error": "Unauthorized"}), 401
        
#         if not user_group_id:
#             return jsonify({"error": "User group not found"}), 401

#         try:
#             user_id = int(user_id)
#         except ValueError:
#             return jsonify({"error": "Invalid user identity"}), 401

#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # Total compliances
#         # cursor.execute("""
#         #     SELECT COUNT(*) AS total_compliances
#         #     FROM compliance_list
#         #     WHERE cmplst_user_id = %s
#         # """, (user_id,))
#         # total_compliances = cursor.fetchone()["total_compliances"]

#         #Added by Sanskar Sharma to include both regulatory and self compliances
#         cursor.execute("""
#         SELECT 
#         (
#             SELECT COUNT(DISTINCT regcmp_compliance_id)
#             FROM regulatory_compliance
#             WHERE regcmp_user_id = %s
#         ) +
#         (
#         SELECT COUNT(DISTINCT slfcmp_compliance_id)
#         FROM self_compliance
#         WHERE slfcmp_user_id = %s
#         ) AS total_compliances
#         """, (user_id, user_id))

#         total_compliances = cursor.fetchone()["total_compliances"]

#         # Total departments
#         # cursor.execute("""
#         #     SELECT COUNT(*) AS total_departments
#         #     FROM user_departments
#         #     WHERE usrdept_user_group_id = %s
#         # """, (user_id,))
#         # total_departments = cursor.fetchone()["total_departments"]

#         cursor.execute("""
#             SELECT COUNT(*) AS total_departments
#             FROM user_departments
#             WHERE usrdept_user_group_id = %s
#         """, (user_group_id,))
#         total_departments = cursor.fetchone()["total_departments"]

#         # Pending actions
#         # cursor.execute("""
#         #     SELECT 
#         #         COALESCE(SUM(
#         #             (TIMESTAMPDIFF(MONTH, cmplst_start_date, cmplst_end_date) + 1)
#         #             - COALESCE(cmplst_actions_completed, 0)
#         #         ), 0) AS total_pending_actions
#         #     FROM compliance_list
#         #     WHERE cmplst_user_id = %s
#         # """, (user_id,))
#         # total_pending_actions = cursor.fetchone()["total_pending_actions"]

#         # Subscription end date
#         cursor.execute("""
#             SELECT usgrp_end_of_subscription
#             FROM user_group
#             WHERE usgrp_id = %s
#         """, (user_group_id,))

#         cursor.execute("""
#             SELECT
#                 COUNT(*) AS total_compliances,
#                 SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved_compliances
#             FROM (
#                 SELECT regcmp_status AS status
#                 FROM regulatory_compliance
#                 WHERE regcmp_user_group_id = %s

#                 UNION ALL

#                 SELECT slfcmp_status AS status
#                 FROM self_compliance
#                 WHERE slfcmp_user_group_id = %s
#             ) AS all_compliances
#         """, (user_group_id, user_group_id))
        
#         row = cursor.fetchone()


#         total = row["total_compliances"] or 0
#         approved = row["approved_compliances"] or 0

#         compliance_score = round((approved / total) * 100, 2) if total > 0 else 0

#         subscription_end_date = (
#             row["usgrp_end_of_subscription"].strftime("%d-%m-%Y")
#                 if row and row.get("usgrp_end_of_subscription")
#                     else None
#         )

#         cursor.close()
#         conn.close()

#         return jsonify({
#             "compliance_score_percent" : compliance_score,
#             "total_compliances": total_compliances,
#             "total_departments": total_departments,
#             "subscription_end_date": subscription_end_date
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    
# @dashboard_bp.route('/summary', methods=['GET'])
# @jwt_required()
# def dashboard_summary():
#     try:
#         claims = get_jwt()
#         user_group_id = claims.get("user_group_id")
#         user_id = get_jwt_identity()

#         if not user_id:
#             return jsonify({"error": "Unauthorized"}), 401

#         if not user_group_id:
#             return jsonify({"error": "User group not found"}), 401

#         try:
#             user_id = int(user_id)
#             user_group_id = int(user_group_id)
#         except ValueError:
#             return jsonify({"error": "Invalid JWT data"}), 401

#         conn = get_db_connection()
#         # cursor = conn.cursor(dictionary=True)
#         cursor = conn.cursor(pymysql.cursors.DictCursor)

#         cursor.execute("""
#             SELECT 
#             (
#                 SELECT COUNT(DISTINCT regcmp_compliance_id)
#                 FROM regulatory_compliance
#                 WHERE regcmp_user_id = %s
#             ) +
#             (
#                 SELECT COUNT(DISTINCT slfcmp_compliance_id)
#                 FROM self_compliance
#                 WHERE slfcmp_user_id = %s
#             ) AS total_compliances
#         """, (user_id, user_id))

#         total_compliances = cursor.fetchone()["total_compliances"] or 0

#         cursor.execute("""
#             SELECT
#                 (
#                     SELECT COUNT(*)
#                     FROM regulatory_compliance
#                     WHERE regcmp_user_id = %s
#                       AND regcmp_user_group_id = %s
#                 ) AS regulatory_instances,
#                 (
#                     SELECT COUNT(*)
#                     FROM self_compliance
#                     WHERE slfcmp_user_id = %s
#                       AND slfcmp_user_group_id = %s
#                 ) AS self_instances
#         """, (user_id, user_group_id, user_id, user_group_id))

#         cursor.execute("""
#             SELECT
#                 (
#                     SELECT COUNT(*)
#                     FROM regulatory_compliance
#                     WHERE regcmp_user_id = %s
#                       AND regcmp_user_group_id = %s
#                 ) AS regulatory_instances,
#                 (
#                     SELECT COUNT(*)
#                     FROM self_compliance
#                     WHERE slfcmp_user_id = %s
#                       AND slfcmp_user_group_id = %s
#                 ) AS self_instances
#         """, (user_id, user_group_id, user_id, user_group_id))

#         cursor.execute("""
#             SELECT COUNT(*) AS total_departments
#             FROM user_departments
#             WHERE usrdept_user_group_id = %s
#         """, (user_group_id,))

#         total_departments = cursor.fetchone()["total_departments"] or 0

#         cursor.execute("""
#             SELECT usgrp_end_of_subscription
#             FROM user_group
#             WHERE usgrp_id = %s
#         """, (user_group_id,))

#         sub_row = cursor.fetchone()

#         subscription_end_date = (
#             sub_row["usgrp_end_of_subscription"].strftime("%d-%m-%Y")
#             if sub_row and sub_row["usgrp_end_of_subscription"]
#             else None
#         )

#         cursor.execute("""
#             SELECT
#                 COUNT(*) AS total_compliances,
#                 SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved_compliances
#             FROM (
#                 SELECT regcmp_status AS status
#                 FROM regulatory_compliance
#                 WHERE regcmp_user_id = %s
#                   AND regcmp_user_group_id = %s

#                 UNION ALL

#                 SELECT slfcmp_status AS status
#                 FROM self_compliance
#                 WHERE slfcmp_user_id = %s
#                   AND slfcmp_user_group_id = %s
#             ) AS all_compliances
#         """, (user_id, user_group_id, user_id, user_group_id))

#         score_row = cursor.fetchone()

#         total = score_row["total_compliances"] or 0
#         approved = score_row["approved_compliances"] or 0

#         compliance_score = round((approved / total) * 100, 2) if total > 0 else 0

#         cursor.close()
#         conn.close()

#         return jsonify({
#             "compliance_score_percent": compliance_score,
#             "total_compliances": total_compliances,
#             "total_departments": total_departments,
#             "subscription_end_date": subscription_end_date
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def dashboard_summary():
    try:
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")
        user_id = get_jwt_identity()

        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        if not user_group_id:
            return jsonify({"error": "User group not found"}), 401

        try:
            user_id = int(user_id)
            user_group_id = int(user_group_id)
        except ValueError:
            return jsonify({"error": "Invalid JWT data"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT 
            (
                SELECT COUNT(DISTINCT regcmp_compliance_id)
                FROM regulatory_compliance
                WHERE regcmp_user_id = %s
            ) +
            (
                SELECT COUNT(DISTINCT slfcmp_compliance_id)
                FROM self_compliance
                WHERE slfcmp_user_id = %s
            ) AS total_compliances
        """, (user_id, user_id))

        total_compliances = cursor.fetchone()["total_compliances"] or 0

        cursor.execute("""
            SELECT
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                ) AS regulatory_instances,
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                ) AS self_instances
        """, (user_id, user_group_id, user_id, user_group_id))

        instance_row = cursor.fetchone()

        regulatory_instances = instance_row["regulatory_instances"] or 0
        self_instances = instance_row["self_instances"] or 0
        total_instances = regulatory_instances + self_instances

        cursor.execute("""
            SELECT COUNT(*) AS total_departments
            FROM user_departments
            WHERE usrdept_user_group_id = %s
        """, (user_group_id,))

        total_departments = cursor.fetchone()["total_departments"] or 0

        cursor.execute("""
            SELECT usgrp_end_of_subscription
            FROM user_group
            WHERE usgrp_id = %s
        """, (user_group_id,))

        sub_row = cursor.fetchone()

        subscription_end_date = (
            sub_row["usgrp_end_of_subscription"].strftime("%d-%m-%Y")
            if sub_row and sub_row["usgrp_end_of_subscription"]
            else None
        )

        cursor.execute("""
            SELECT
                COUNT(*) AS total_compliances,
                SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved_compliances
            FROM (
                SELECT regcmp_status AS status
                FROM regulatory_compliance
                WHERE regcmp_user_id = %s
                  AND regcmp_user_group_id = %s

                UNION ALL

                SELECT slfcmp_status AS status
                FROM self_compliance
                WHERE slfcmp_user_id = %s
                  AND slfcmp_user_group_id = %s
            ) AS all_compliances
        """, (user_id, user_group_id, user_id, user_group_id))

        score_row = cursor.fetchone()

        total = score_row["total_compliances"] or 0
        approved = score_row["approved_compliances"] or 0

        compliance_score = round((approved / total) * 100, 2) if total > 0 else 0

        cursor.close()
        conn.close()

        return jsonify({
            "compliance_score_percent": compliance_score,
            "total_compliances": total_compliances,

            "total_instances": total_instances,
            "regulatory_instances": regulatory_instances,
            "self_instances": self_instances,

            "total_departments": total_departments,
            "subscription_end_date": subscription_end_date
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/admin', methods=['GET'])
@jwt_required()
def dashboard_admin():
    try:
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT
                COUNT(*) AS total_compliances,
                SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved_compliances
            FROM (
                SELECT regcmp_status AS status
                FROM regulatory_compliance
                WHERE regcmp_user_group_id = %s

                UNION ALL

                SELECT slfcmp_status AS status
                FROM self_compliance
                WHERE slfcmp_user_group_id = %s
            ) AS all_compliances
        """, (user_group_id, user_group_id))

        result = cursor.fetchone()

        total = result["total_compliances"] or 0
        approved = result["approved_compliances"] or 0
        compliance_score = round((approved / total) * 100, 2) if total > 0 else 0

        cursor.execute("""
            SELECT *
            FROM (
                SELECT
                    regcmp_id AS id,
                    regcmp_act AS title,
                    regcmp_start_date AS start_date,
                    regcmp_end_date AS end_date,
                    'regulatory' AS type
                FROM regulatory_compliance
                WHERE regcmp_user_group_id = %s
                ORDER BY regcmp_id DESC
                LIMIT 5

                UNION ALL

                SELECT
                    slfcmp_id AS id,
                    'Self Compliance' AS title,
                    slfcmp_start_date AS start_date,
                    slfcmp_end_date AS end_date,
                    'self' AS type
                FROM self_compliance
                WHERE slfcmp_user_group_id = %s
                ORDER BY slfcmp_id DESC
                LIMIT 5
            ) combined
            ORDER BY id DESC
            LIMIT 5
        """, (user_group_id, user_group_id))

        recent_rows = cursor.fetchall()

        recent_compliances = [
            {
                "id": row["id"],
                "title": row["title"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "type": row["type"]
            }
            for row in recent_rows
        ]

        cursor.close()
        conn.close()

        return jsonify({
            "group_id": user_group_id,
            "total_compliances": total,
            "approved_compliances": approved,
            "compliance_score_percent": compliance_score,
            "recent_compliances": recent_compliances
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
