from itsdangerous import URLSafeTimedSerializer
from flask import current_app


def generate_action_token(data):
    """
    Generate secure token for approval links
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(data, salt="compliance-approval")


def verify_action_token(token, max_age=86400):
    """
    Verify token (24 hours expiry)
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    return s.loads(
        token,
        salt="compliance-approval",
        max_age=max_age
    )
