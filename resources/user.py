from sanic.response import json
from models import user, merchant
from extensions.sanic_validation_decorators import *
from datetime import datetime
from resources import auth
from sanic.views import HTTPMethodView
from sentry_sdk import capture_exception



schema_user = {
               'login': {
                   'type': 'string',
                   'required': True
               },
               'password': {
                   'type': 'string',
                   'required': True
               },
               'merchant_id': {
                   'type': 'integer',
                   'required': True
               },
               'role': {
                   'type': 'string',
                   'required': True,
                   'allowed': ['global', 'merchant']
               }
}


# /user/add
class UserCreateView(HTTPMethodView):
    decorators = [auth.authorized(roles=['global', 'admin']), validate_json(schema_user)]

    async def post(self, request, technical):
        try:
            data = request.json
            logins = [x['login'] for x in await user.User.list_users(redis_conn=request.app.redis)]
            if data['login'] not in logins:
                data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with await request.app.redis as redis:
                    curr_merchant = merchant.Merchant(id=data['merchant_id'], redis_conn=redis)
                    curr_merchant_id, result = await curr_merchant.get_merchant()
                    if curr_merchant_id is not None:
                        new_user = user.User(redis_conn=redis)
                        data['user_id'], data['token'] = await new_user.create_user(data=data)
                        return json(data, status=201)
                    else:
                        return json({"message": "There is no such merchant."
                             }, status=400)
            else:
                return json({"message": "User with the login {0} already exists.".format(data['login'])
                             }, status=409)
        except Exception:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                     }, status=500)


# /user/<id:int>
class UserView(HTTPMethodView):
    decorators = [auth.authorized(roles=['global', 'admin']),  validate_json(schema_user, methods=['PUT'])]

    async def get(self, request, id, technical):
        try:
            with await request.app.redis as redis:
                curr_user = user.User(id=id, redis_conn=redis)
                data = await curr_user.get_user()
            if data is not None:
                data.pop('password')
                data['user_id'] = int(id)
                data['merchant_id'] = int(data['merchant_id'])
                return json(data, status=200)
            else:
                return json({
                    "message": "User is not existed yet."
                }, status=404)
        except Exception:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                         }, status=500)

    async def put(self, request, id, technical):
        try:
            data = request.json
            with await request.app.redis as redis:
                curr_user = user.User(id=id, redis_conn=redis)
                old_data = await curr_user.get_user()
                data['created_at'] = old_data['created_at']
                data['user_id'], data['token'] = await curr_user.update_user(data)
            if data['user_id'] is not None:
                return json(data, status=201)
            else:
                return json({
                    "message": "User is not existed yet."
                }, status=404)
        except Exception:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                         }, status=500)

    async def delete(self, request, id, technical):
        try:
            with await request.app.redis as redis:
                curr_user = user.User(id=id, redis_conn=redis)
                await curr_user.delete_user()
            return json({
                "message": "There is no such user anymore."
            }, status=204)
        except Exception:
            capture_exception()
            return json({"message": "Internal Server error"
                         }, status=500)

    async def patch(self, request, id, technical):
        try:
            with await request.app.redis as redis:
                curr_user = user.User(id=id, redis_conn=redis)
                token = await curr_user.refresh()
            if token is not None:
                return json({
                    "user_id": int(id),
                    "token": token
                }, status=200)
            else:
                return json({
                    "message": "User is not existed yet."
                }, status=404)
        except Exception:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                         }, status=500)


#  /user/list
class UserListView(HTTPMethodView):
    decorators = [auth.authorized(roles=['global', 'admin'])]

    async def get(self, request, technical):
        try:
            with await request.app.redis as redis:
                data = await user.User.list_users(redis_conn=redis)
                data = sorted(data, key=lambda x: x['user_id'], reverse=True)
            return json(data, status=200)
        except Exception:
            capture_exception(data=request.json)
            return json({
                    "message": "Internal Server error"
                }, status=500)

