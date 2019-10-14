from sanic.response import json
from models import auth
from functools import wraps
from sentry_sdk import capture_exception



async def check_request_for_authorization_status(request):
    """Check the request token."""
    token = request.token
    with await request.app.redis as redis:
        data = await auth.Auth.find_merchant_by_token(token, redis_conn=redis)
    if data is not None:
        return True, data
    else:
        return False, None

def authorized(roles=['merchant', 'admin', 'global']):
    """Simple authorization"""
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            try:
                is_authorized, data = await check_request_for_authorization_status(request)
                if is_authorized and data['role'] in roles:
                    response = await f(request, technical=data, *args, **kwargs)
                    return response
                else:
                    return json({'message': 'Not Authorized. Check your token.'}, 403)
            except Exception:
                capture_exception()
                return json({"message": "Internal Server error"
                             }, status=500)
        return decorated_function
    return decorator


def authorized_global():
    """Authorization for the users with the special role."""
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            try:
                is_authorized, data = await check_request_for_authorization_status(request)
                if is_authorized and data['role'] == 'global':
                    response = await f(request, technical=data, *args, **kwargs)
                    return response
                else:
                    return json({'message': 'Not Authorized. Check your token.'}, 403)
            except Exception:
                capture_exception()
        return decorated_function
    return decorator

