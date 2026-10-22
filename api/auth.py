import secrets
from django.contrib.auth.models import User
from .models import ApiToken

def issue_token(user):
    token = secrets.token_hex(32)
    ApiToken.objects.create(user=user, token=token)
    return token

def user_from_token(header_value):
    """header_value is the raw 'Authorization' header, e.g. 'Bearer abc123'."""
    if not header_value:
        return None
    parts = header_value.split(' ', 1)
    raw = parts[1] if len(parts) == 2 and parts[0].lower() == 'bearer' else header_value
    try:
        t = ApiToken.objects.select_related('user').get(token=raw)
    except ApiToken.DoesNotExist:
        return None
    return t.user