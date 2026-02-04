from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app


def generate_action_token(data):
    """
    Generate secure token for approve/decline
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(data, salt="compliance-approval")


def verify_action_token(token, max_age=86400):
    """
    Verify token (valid for 24 hours)
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    try:
        data = s.loads(
            token,
            salt="compliance-approval",
            max_age=max_age
        )
        return data

    except SignatureExpired:
        print("❌ Token expired")
        return None

    except BadSignature:
        print("❌ Invalid token signature")
        return None

    except Exception as e:
        print("❌ Token error:", str(e))
        return None
