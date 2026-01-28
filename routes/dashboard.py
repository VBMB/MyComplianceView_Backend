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

#         instance_row = cursor.fetchone()

#         regulatory_instances = instance_row["regulatory_instances"] or 0
#         self_instances = instance_row["self_instances"] or 0
#         total_instances = regulatory_instances + self_instances

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

#             "total_instances": total_instances,
#             "regulatory_instances": regulatory_instances,
#             "self_instances": self_instances,

#             "total_departments": total_departments,
#             "subscription_end_date": subscription_end_date
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

#chnages made here
@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def dashboard_summary():
    try:
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")
        user_id = get_jwt_identity()

        if not user_id or not user_group_id:
            return jsonify({"error": "Unauthorized"}), 401

        user_id = int(user_id)
        user_group_id = int(user_group_id)

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # --------------------------------------------------
        # TOTAL UNIQUE COMPLIANCES
        # --------------------------------------------------
        cursor.execute("""
            SELECT 
            (
                SELECT COUNT(DISTINCT regcmp_compliance_id)
                FROM regulatory_compliance
                WHERE regcmp_user_id = %s
                  AND regcmp_user_group_id = %s
            ) +
            (
                SELECT COUNT(DISTINCT slfcmp_compliance_id)
                FROM self_compliance
                WHERE slfcmp_user_id = %s
                  AND slfcmp_user_group_id = %s
            ) AS total_compliances
        """, (user_id, user_group_id, user_id, user_group_id))

        total_compliances = cursor.fetchone()["total_compliances"] or 0

        # --------------------------------------------------
        # TOTAL INSTANCES
        # --------------------------------------------------
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

        row = cursor.fetchone()
        regulatory_instances = row["regulatory_instances"] or 0
        self_instances = row["self_instances"] or 0
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
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved
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
            ) t
        """, (user_id, user_group_id, user_id, user_group_id))

        score = cursor.fetchone()
        compliance_score_percent = round(
            (score["approved"] / score["total"]) * 100, 2
        ) if score["total"] else 0

        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND regcmp_status IN ('Pending', 'Requested')
                      AND regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND slfcmp_status IN ('Pending', 'Requested')
                      AND slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                ),
                0
            ) * 100 AS at_risk_percent
        """, (
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id
        ))

        at_risk_percent = round(cursor.fetchone()["at_risk_percent"] or 0, 2)
        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND regcmp_status = 'Approved'
                      AND regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND slfcmp_status = 'Approved'
                      AND slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                ),
                0
            ) * 100 AS low_risk_percent
        """, (
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id
        ))

        low_risk_percent = round(cursor.fetchone()["low_risk_percent"] or 0, 2)

        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
                      AND regcmp_status = 'Approved'
                      AND regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
                      AND slfcmp_status = 'Approved'
                      AND slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE regcmp_user_id = %s
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE slfcmp_user_id = %s
                      AND slfcmp_user_group_id = %s
                ),
                0
            ) * 100 AS no_risk_percent
        """, (
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id,
            user_id, user_group_id
        ))

        no_risk_percent = round(cursor.fetchone()["no_risk_percent"] or 0, 2)

        cursor.close()
        conn.close()

        return jsonify({
            "compliance_score_percent": compliance_score_percent,

            "at_risk_percent": at_risk_percent,
            "low_risk_percent": low_risk_percent,
            "no_risk_percent": no_risk_percent,

            "total_compliances": total_compliances,
            "total_instances": total_instances,
            "regulatory_instances": regulatory_instances,
            "self_instances": self_instances,

            "total_departments": total_departments,
            "subscription_end_date": subscription_end_date
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# @dashboard_bp.route('/admin', methods=['GET'])
# @jwt_required()
# def dashboard_admin():
#     try:
#         claims = get_jwt()
#         user_group_id = claims.get("user_group_id")

#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)

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

#         result = cursor.fetchone()

#         total = result["total_compliances"] or 0
#         approved = result["approved_compliances"] or 0
#         compliance_score = round((approved / total) * 100, 2) if total > 0 else 0

#         cursor.execute("""
#             SELECT *

# FROM (

#     SELECT

#         regcmp_id AS id,

#         regcmp_act AS title,

#         regcmp_start_date AS start_date,

#         regcmp_end_date AS end_date,

#         'regulatory' AS type

#     FROM regulatory_compliance

#     WHERE regcmp_user_group_id = %s
 
#     UNION ALL
 
#     SELECT

#         slfcmp_id AS id,

#         slfcmp_act AS title,

#         slfcmp_start_date AS start_date,

#         slfcmp_end_date AS end_date,

#         'self' AS type

#     FROM self_compliance

#     WHERE slfcmp_user_group_id = %s

# ) combined

# ORDER BY id DESC

# LIMIT 5;

 
#         """, (user_group_id, user_group_id))

#         recent_rows = cursor.fetchall()

#         recent_compliances = [
#             {
#                 "id": row["id"],
#                 "title": row["title"],
#                 "start_date": row["start_date"],
#                 "end_date": row["end_date"],
#                 "type": row["type"]
#             }
#             for row in recent_rows
#         ]

#         cursor.close()
#         conn.close()

#         return jsonify({
#             "group_id": user_group_id,
#             "total_compliances": total,
#             "approved_compliances": approved,
#             "compliance_score_percent": compliance_score,
#             "recent_compliances": recent_compliances
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# @dashboard_bp.route('/admin', methods=['GET'])
# @jwt_required()
# def dashboard_admin():
#     try:
#         claims = get_jwt()
#         user_group_id = claims.get("user_group_id")

#         if not user_group_id:
#             return jsonify({"error": "Unauthorized"}), 401

#         user_group_id = int(user_group_id)

#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)

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
#             ) t
#         """, (user_group_id, user_group_id))

#         result = cursor.fetchone()
#         total = result["total_compliances"] or 0
#         approved = result["approved_compliances"] or 0
#         compliance_score = round((approved / total) * 100, 2) if total > 0 else 0
#         cursor.execute("""
#             SELECT
#             (
#                 (
#                     SELECT COUNT(*)
#                     FROM regulatory_compliance
#                     WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
#                       AND regcmp_status IN ('Pending', 'Requested')
#                       AND regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*)
#                     FROM self_compliance
#                     WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
#                       AND slfcmp_status IN ('Pending', 'Requested')
#                       AND slfcmp_user_group_id = %s
#                 )
#             )
#             /
#             NULLIF(
#                 (
#                     SELECT COUNT(*) FROM regulatory_compliance
#                     WHERE regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*) FROM self_compliance
#                     WHERE slfcmp_user_group_id = %s
#                 ),
#                 0
#             ) * 100 AS at_risk_percent
#         """, (
#             user_group_id, user_group_id,
#             user_group_id, user_group_id
#         ))

#         at_risk_percent = round(cursor.fetchone()["at_risk_percent"] or 0, 2)

#         cursor.execute("""
#             SELECT
#             (
#                 (
#                     SELECT COUNT(*)
#                     FROM regulatory_compliance
#                     WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
#                       AND regcmp_status = 'Approved'
#                       AND regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*)
#                     FROM self_compliance
#                     WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
#                       AND slfcmp_status = 'Approved'
#                       AND slfcmp_user_group_id = %s
#                 )
#             )
#             /
#             NULLIF(
#                 (
#                     SELECT COUNT(*) FROM regulatory_compliance
#                     WHERE regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*) FROM self_compliance
#                     WHERE slfcmp_user_group_id = %s
#                 ),
#                 0
#             ) * 100 AS low_risk_percent
#         """, (
#             user_group_id, user_group_id,
#             user_group_id, user_group_id
#         ))

#         low_risk_percent = round(cursor.fetchone()["low_risk_percent"] or 0, 2)
#         cursor.execute("""
#             SELECT
#             (
#                 (
#                     SELECT COUNT(*)
#                     FROM regulatory_compliance
#                     WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
#                       AND regcmp_status = 'Approved'
#                       AND regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*)
#                     FROM self_compliance
#                     WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
#                       AND slfcmp_status = 'Approved'
#                       AND slfcmp_user_group_id = %s
#                 )
#             )
#             /
#             NULLIF(
#                 (
#                     SELECT COUNT(*) FROM regulatory_compliance
#                     WHERE regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*) FROM self_compliance
#                     WHERE slfcmp_user_group_id = %s
#                 ),
#                 0
#             ) * 100 AS no_risk_percent
#         """, (
#             user_group_id, user_group_id,
#             user_group_id, user_group_id
#         ))

#         no_risk_percent = round(cursor.fetchone()["no_risk_percent"] or 0, 2)

#         cursor.execute("""
#             SELECT *
#             FROM (
#                 SELECT
#                     regcmp_id AS id,
#                     regcmp_act AS title,
#                     regcmp_start_date AS start_date,
#                     regcmp_end_date AS end_date,
#                     'regulatory' AS type
#                 FROM regulatory_compliance
#                 WHERE regcmp_user_group_id = %s

#                 UNION ALL

#                 SELECT
#                     slfcmp_id AS id,
#                     slfcmp_act AS title,
#                     slfcmp_start_date AS start_date,
#                     slfcmp_end_date AS end_date,
#                     'self' AS type
#                 FROM self_compliance
#                 WHERE slfcmp_user_group_id = %s
#             ) combined
#             ORDER BY id DESC
#             LIMIT 5
#         """, (user_group_id, user_group_id))

#         recent_rows = cursor.fetchall()

#         recent_compliances = [
#             {
#                 "id": row["id"],
#                 "title": row["title"],
#                 "start_date": row["start_date"],
#                 "end_date": row["end_date"],
#                 "type": row["type"]
#             }
#             for row in recent_rows
#         ]

#         cursor.close()
#         conn.close()

#         return jsonify({
#             "group_id": user_group_id,

#             "total_compliances": total,
#             "approved_compliances": approved,
#             "compliance_score_percent": compliance_score,

#             "at_risk_percent": at_risk_percent,
#             "low_risk_percent": low_risk_percent,
#             "no_risk_percent": no_risk_percent,

#             "recent_compliances": recent_compliances
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @dashboard_bp.route('/admin', methods=['GET'])
# @jwt_required()
# def dashboard_admin():
#     try:
#         claims = get_jwt()
#         user_group_id = claims.get("user_group_id")

#         if not user_group_id:
#             return jsonify({"error": "Unauthorized"}), 401

#         user_group_id = int(user_group_id)

#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)

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
#             ) t
#         """, (user_group_id, user_group_id))

#         result = cursor.fetchone()
#         total = result["total_compliances"] or 0
#         approved = result["approved_compliances"] or 0
#         compliance_score = round((approved / total) * 100, 2) if total > 0 else 0

#         cursor.execute("""
#             SELECT
#             (
#                 (
#                     SELECT COUNT(*)
#                     FROM regulatory_compliance
#                     WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
#                       AND regcmp_status IN ('Pending', 'Requested')
#                       AND regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*)
#                     FROM self_compliance
#                     WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
#                       AND slfcmp_status IN ('Pending', 'Requested')
#                       AND slfcmp_user_group_id = %s
#                 )
#             )
#             /
#             NULLIF(
#                 (
#                     SELECT COUNT(*) FROM regulatory_compliance
#                     WHERE regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*) FROM self_compliance
#                     WHERE slfcmp_user_group_id = %s
#                 ),
#                 0
#             ) * 100 AS at_risk_percent
#         """, (
#             user_group_id, user_group_id,
#             user_group_id, user_group_id
#         ))

#         at_risk_percent = round(cursor.fetchone()["at_risk_percent"] or 0, 2)
#         cursor.execute("""
#             SELECT
#             (
#                 (
#                     SELECT COUNT(*)
#                     FROM regulatory_compliance
#                     WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
#                       AND regcmp_status = 'Approved'
#                       AND regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*)
#                     FROM self_compliance
#                     WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
#                       AND slfcmp_status = 'Approved'
#                       AND slfcmp_user_group_id = %s
#                 )
#             )
#             /
#             NULLIF(
#                 (
#                     SELECT COUNT(*) FROM regulatory_compliance
#                     WHERE regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*) FROM self_compliance
#                     WHERE slfcmp_user_group_id = %s
#                 ),
#                 0
#             ) * 100 AS low_risk_percent
#         """, (
#             user_group_id, user_group_id,
#             user_group_id, user_group_id
#         ))

#         low_risk_percent = round(cursor.fetchone()["low_risk_percent"] or 0, 2)

#         cursor.execute("""
#             SELECT
#             (
#                 (
#                     SELECT COUNT(*)
#                     FROM regulatory_compliance
#                     WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
#                       AND regcmp_status = 'Approved'
#                       AND regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*)
#                     FROM self_compliance
#                     WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
#                       AND slfcmp_status = 'Approved'
#                       AND slfcmp_user_group_id = %s
#                 )
#             )
#             /
#             NULLIF(
#                 (
#                     SELECT COUNT(*) FROM regulatory_compliance
#                     WHERE regcmp_user_group_id = %s
#                 )
#                 +
#                 (
#                     SELECT COUNT(*) FROM self_compliance
#                     WHERE slfcmp_user_group_id = %s
#                 ),
#                 0
#             ) * 100 AS no_risk_percent
#         """, (
#             user_group_id, user_group_id,
#             user_group_id, user_group_id
#         ))

#         no_risk_percent = round(cursor.fetchone()["no_risk_percent"] or 0, 2)

#         cursor.execute("""
#             SELECT *
#             FROM (
#                 SELECT
#                     regcmp_id AS id,
#                     regcmp_act AS title,
#                     regcmp_start_date AS start_date,
#                     regcmp_end_date AS end_date,
#                     'regulatory' AS type
#                 FROM regulatory_compliance
#                 WHERE regcmp_user_group_id = %s

#                 UNION ALL

#                 SELECT
#                     slfcmp_id AS id,
#                     slfcmp_act AS title,
#                     slfcmp_start_date AS start_date,
#                     slfcmp_end_date AS end_date,
#                     'self' AS type
#                 FROM self_compliance
#                 WHERE slfcmp_user_group_id = %s
#             ) combined
#             ORDER BY id DESC
#             LIMIT 5
#         """, (user_group_id, user_group_id))

#         recent_compliances = cursor.fetchall()

#         # cursor.execute("""
#         #     SELECT
#         #         DATE_FORMAT(action_date, '%Y-%m') AS month,
#         #         COUNT(CASE WHEN status = 'Approved' THEN 1 END) AS approved_count,
#         #         COUNT(
#         #             CASE 
#         #                 WHEN status <> 'Approved'
#         #                  AND action_date < CURDATE()
#         #             THEN 1 END
#         #         ) AS overdue_count
#         #     FROM (
#         #         SELECT
#         #             STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') AS action_date,
#         #             regcmp_status AS status
#         #         FROM regulatory_compliance
#         #         WHERE regcmp_user_group_id = %s
#         #           AND STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y')
#         #               BETWEEN
#         #               (
#         #                   CASE 
#         #                       WHEN MONTH(CURDATE()) >= 4
#         #                       THEN CONCAT(YEAR(CURDATE()), '-04-01')
#         #                       ELSE CONCAT(YEAR(CURDATE()) - 1, '-04-01')
#         #                   END
#         #               )
#         #               AND DATE_ADD(
#         #                   (
#         #                       CASE 
#         #                           WHEN MONTH(CURDATE()) >= 4
#         #                           THEN CONCAT(YEAR(CURDATE()), '-04-01')
#         #                           ELSE CONCAT(YEAR(CURDATE()) - 1, '-04-01')
#         #                       END
#         #                   ),
#         #                   INTERVAL 1 YEAR
#         #               )

#         #         UNION ALL

#         #         SELECT
#         #             STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') AS action_date,
#         #             slfcmp_status AS status
#         #         FROM self_compliance
#         #         WHERE slfcmp_user_group_id = %s
#         #           AND STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y')
#         #               BETWEEN
#         #               (
#         #                   CASE 
#         #                       WHEN MONTH(CURDATE()) >= 4
#         #                       THEN CONCAT(YEAR(CURDATE()), '-04-01')
#         #                       ELSE CONCAT(YEAR(CURDATE()) - 1, '-04-01')
#         #                   END
#         #               )
#         #               AND DATE_ADD(
#         #                   (
#         #                       CASE 
#         #                           WHEN MONTH(CURDATE()) >= 4
#         #                           THEN CONCAT(YEAR(CURDATE()), '-04-01')
#         #                           ELSE CONCAT(YEAR(CURDATE()) - 1, '-04-01')
#         #                       END
#         #                   ),
#         #                   INTERVAL 1 YEAR
#         #               )
#         #     ) combined
#         #     GROUP BY DATE_FORMAT(action_date, '%Y-%m')
#         #     ORDER BY month
#         # """, (user_group_id, user_group_id))

#         cursor.execute("""
#     SELECT
#         DATE_FORMAT(action_date, '%%Y-%%m') AS month,
#         COUNT(CASE WHEN status = 'Approved' THEN 1 END) AS approved_count,
#         COUNT(
#             CASE 
#                 WHEN status <> 'Approved'
#                  AND action_date < CURDATE()
#             THEN 1 END
#         ) AS overdue_count
#     FROM (
#         SELECT
#             STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') AS action_date,
#             regcmp_status AS status
#         FROM regulatory_compliance
#         WHERE regcmp_user_group_id = %s
#           AND STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y')
#               BETWEEN
#               (
#                   CASE 
#                       WHEN MONTH(CURDATE()) >= 4
#                       THEN CONCAT(YEAR(CURDATE()), '-04-01')
#                       ELSE CONCAT(YEAR(CURDATE()) - 1, '-04-01')
#                   END
#               )
#               AND DATE_ADD(
#                   (
#                       CASE 
#                           WHEN MONTH(CURDATE()) >= 4
#                           THEN CONCAT(YEAR(CURDATE()), '-04-01')
#                           ELSE CONCAT(YEAR(CURDATE()) - 1, '-04-01')
#                       END
#                   ),
#                   INTERVAL 1 YEAR
#               )

#         UNION ALL

#         SELECT
#             STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') AS action_date,
#             slfcmp_status AS status
#         FROM self_compliance
#         WHERE slfcmp_user_group_id = %s
#           AND STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y')
#               BETWEEN
#               (
#                   CASE 
#                       WHEN MONTH(CURDATE()) >= 4
#                       THEN CONCAT(YEAR(CURDATE()), '-04-01')
#                       ELSE CONCAT(YEAR(CURDATE()) - 1, '-04-01')
#                   END
#               )
#               AND DATE_ADD(
#                   (
#                       CASE 
#                           WHEN MONTH(CURDATE()) >= 4
#                           THEN CONCAT(YEAR(CURDATE()), '-04-01')
#                           ELSE CONCAT(YEAR(CURDATE()) - 1, '-04-01')
#                       END
#                   ),
#                   INTERVAL 1 YEAR
#               )
#     ) combined
#     GROUP BY DATE_FORMAT(action_date, '%%Y-%%m')
#     ORDER BY month
# """, (user_group_id, user_group_id))


#         compliance_track = cursor.fetchall()

#         cursor.close()
#         conn.close()

#         return jsonify({
#             "group_id": user_group_id,

#             "total_compliances": total,
#             "approved_compliances": approved,
#             "compliance_score_percent": compliance_score,

#             "at_risk_percent": at_risk_percent,
#             "low_risk_percent": low_risk_percent,
#             "no_risk_percent": no_risk_percent,

#             "recent_compliances": recent_compliances,

#             "compliance_track": compliance_track
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


#2step (up)
@dashboard_bp.route('/admin', methods=['GET'])
@jwt_required()
def dashboard_admin():
    try:
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")

        if not user_group_id:
            return jsonify({"error": "Unauthorized"}), 401

        user_group_id = int(user_group_id)

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
            ) t
        """, (user_group_id, user_group_id))

        result = cursor.fetchone()
        total = result["total_compliances"] or 0
        approved = result["approved_compliances"] or 0
        compliance_score = round((approved / total) * 100, 2) if total > 0 else 0

        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND regcmp_status IN ('Pending','Requested')
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND slfcmp_status IN ('Pending','Requested')
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*) FROM regulatory_compliance WHERE regcmp_user_group_id = %s
                ) +
                (
                    SELECT COUNT(*) FROM self_compliance WHERE slfcmp_user_group_id = %s
                ), 0
            ) * 100 AS at_risk_percent
        """, (user_group_id, user_group_id, user_group_id, user_group_id))

        at_risk_percent = round(cursor.fetchone()["at_risk_percent"] or 0, 2)

        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND regcmp_status = 'Approved'
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') < CURDATE()
                      AND slfcmp_status = 'Approved'
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*) FROM regulatory_compliance WHERE regcmp_user_group_id = %s
                ) +
                (
                    SELECT COUNT(*) FROM self_compliance WHERE slfcmp_user_group_id = %s
                ), 0
            ) * 100 AS low_risk_percent
        """, (user_group_id, user_group_id, user_group_id, user_group_id))

        low_risk_percent = round(cursor.fetchone()["low_risk_percent"] or 0, 2)

        cursor.execute("""
            SELECT
            (
                (
                    SELECT COUNT(*)
                    FROM regulatory_compliance
                    WHERE STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
                      AND regcmp_status = 'Approved'
                      AND regcmp_user_group_id = %s
                )
                +
                (
                    SELECT COUNT(*)
                    FROM self_compliance
                    WHERE STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') >= CURDATE()
                      AND slfcmp_status = 'Approved'
                      AND slfcmp_user_group_id = %s
                )
            )
            /
            NULLIF(
                (
                    SELECT COUNT(*) FROM regulatory_compliance WHERE regcmp_user_group_id = %s
                ) +
                (
                    SELECT COUNT(*) FROM self_compliance WHERE slfcmp_user_group_id = %s
                ), 0
            ) * 100 AS no_risk_percent
        """, (user_group_id, user_group_id, user_group_id, user_group_id))

        no_risk_percent = round(cursor.fetchone()["no_risk_percent"] or 0, 2)

        cursor.execute("""
            SELECT *
            FROM (
                SELECT regcmp_id AS id, regcmp_act AS title,
                       regcmp_start_date AS start_date,
                       regcmp_end_date AS end_date,
                       'regulatory' AS type
                FROM regulatory_compliance
                WHERE regcmp_user_group_id = %s
                UNION ALL
                SELECT slfcmp_id AS id, slfcmp_act AS title,
                       slfcmp_start_date AS start_date,
                       slfcmp_end_date AS end_date,
                       'self' AS type
                FROM self_compliance
                WHERE slfcmp_user_group_id = %s
            ) t
            ORDER BY id DESC
            LIMIT 5
        """, (user_group_id, user_group_id))

        recent_compliances = cursor.fetchall()

        cursor.execute("""
            SELECT
                quarter_label,
                SUM(approved_count) OVER (ORDER BY quarter_num) AS approved_count,
                SUM(overdue_count) OVER (ORDER BY quarter_num) AS overdue_count
            FROM (
                SELECT
                    quarter_num,
                    CONCAT('Q', quarter_num) AS quarter_label,
                    COUNT(CASE WHEN status = 'Approved' THEN 1 END) AS approved_count,
                    COUNT(
                        CASE
                            WHEN status <> 'Approved'
                             AND action_date < CURDATE()
                        THEN 1 END
                    ) AS overdue_count
                FROM (
                    SELECT
                        STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y') AS action_date,
                        regcmp_status AS status,
                        CASE
                            WHEN MONTH(STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 4 AND 6 THEN 1
                            WHEN MONTH(STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 7 AND 9 THEN 2
                            WHEN MONTH(STR_TO_DATE(regcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 10 AND 12 THEN 3
                            ELSE 4
                        END AS quarter_num
                    FROM regulatory_compliance
                    WHERE regcmp_user_group_id = %s

                    UNION ALL

                    SELECT
                        STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y') AS action_date,
                        slfcmp_status AS status,
                        CASE
                            WHEN MONTH(STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 4 AND 6 THEN 1
                            WHEN MONTH(STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 7 AND 9 THEN 2
                            WHEN MONTH(STR_TO_DATE(slfcmp_action_date, '%%d-%%m-%%Y')) BETWEEN 10 AND 12 THEN 3
                            ELSE 4
                        END AS quarter_num
                    FROM self_compliance
                    WHERE slfcmp_user_group_id = %s
                ) base
                GROUP BY quarter_num
            ) q
            ORDER BY quarter_num
        """, (user_group_id, user_group_id))

        quarterly_compliance_track = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "group_id": user_group_id,
            "total_compliances": total,
            "approved_compliances": approved,
            "compliance_score_percent": compliance_score,
            "at_risk_percent": at_risk_percent,
            "low_risk_percent": low_risk_percent,
            "no_risk_percent": no_risk_percent,
            "recent_compliances": recent_compliances,
            "quarterly_compliance_track": quarterly_compliance_track
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#impact assessment
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import get_db_connection
import pymysql

dashboard_bp = Blueprint(
    "dashboard_bp",
    __name__,
    url_prefix="/dashboard"
)



@dashboard_bp.route("/impact_assessment", methods=["GET"])
@jwt_required()
def impact_assessment():

    try:
        claims = get_jwt()
        user_group_id = claims.get("user_group_id")
        selected_act = request.args.get("act")

        if not user_group_id:
            return jsonify({"error": "User group not found in token"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        query = """
        SELECT
            act,
            particular,
            COUNT(*) AS total_instances,

            SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved_count,
            SUM(CASE WHEN status = 'Requested' THEN 1 ELSE 0 END) AS requested_count,
            SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending_count,

            CASE
                WHEN SUM(CASE WHEN status != 'Approved' THEN 1 ELSE 0 END) = 0
                    THEN 'Completed'
                WHEN SUM(CASE WHEN status = 'Requested' THEN 1 ELSE 0 END) > 0
                    THEN 'In Progress'
                ELSE 'Not Started'
            END AS particular_status

        FROM (
            SELECT
                regcmp_act AS act,
                regcmp_particular AS particular,
                regcmp_status AS status
            FROM regulatory_compliance
            WHERE regcmp_user_group_id = %s

            UNION ALL

            SELECT
                slfcmp_act AS act,
                slfcmp_particular AS particular,
                slfcmp_status AS status
            FROM self_compliance
            WHERE slfcmp_user_group_id = %s
        ) 
        """

        params = [user_group_id, user_group_id]

        if selected_act:
            query += " WHERE act = %s"
            params.append(selected_act)

        query += " GROUP BY act, particular ORDER BY act, particular"

        cursor.execute(query, params)
        rows = cursor.fetchall()


        summary = {
            "Completed": 0,
            "In Progress": 0,
            "Not Started": 0
        }

        for row in rows:
            summary[row["particular_status"]] += 1

        total_particulars = sum(summary.values())


        score_percentage = {
            "Completed": round((summary["Completed"] / total_particulars) * 100, 2) if total_particulars else 0,
            "In Progress": round((summary["In Progress"] / total_particulars) * 100, 2) if total_particulars else 0,
            "Not Started": round((summary["Not Started"] / total_particulars) * 100, 2) if total_particulars else 0
        }

        return jsonify({
            "selected_act": selected_act,
            "impact_assessment": rows,
            "summary": summary,
            "score_percentage": score_percentage
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()