from sanic.response import json
from models import merchant, industries
from datetime import datetime
from extensions.sanic_validation_decorators import *
from resources import auth
from sanic.views import HTTPMethodView
from sentry_sdk import capture_exception


schema_merchant = {
               'name': {
                   'type': 'string',
                   'required': True
               },
               'industry': {
                   'type': 'string',
                   'required': True
                   #'allowed': industries.Industry.list_industries()
               },
               'list_level': {
                   'type': 'string',
                   'required': True,
                   'allowed': ['global', 'industry', 'local']
               }
}


# /merchant/add
class MerchantCreateView(HTTPMethodView):
    decorators = [auth.authorized(roles=['global', 'admin']), validate_json(schema_merchant, methods=['POST'])]

    async def post(self, request, technical):
        try:
            merchant_names = [x['name'] for x in await merchant.Merchant.list_merchants(redis_conn=request.app.redis)]
            data = request.json
            if data['name'] not in merchant_names:
                data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with await request.app.redis as redis:
                    new_merchant = merchant.Merchant(redis_conn=redis)
                    merchant_id, data = await new_merchant.create_merchant(data)
                data['merchant_id'] = int(merchant_id)
                return json(data, status=201)
            else:
                return json({"message": "Merchant with the name {0} already exists.".format(data['name'])}, status=409)
        except Exception:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                         }, status=500)


# /merchant/<id:int>/
class MerchantView(HTTPMethodView):
    decorators = [auth.authorized(roles=['global', 'admin']), validate_json(schema_merchant, methods=['POST'])]

    async def get(self, request, id, technical):
        try:
            with await request.app.redis as redis:
                curr_merchant = merchant.Merchant(id=id, redis_conn=redis)
                curr_merchant_id, data = await curr_merchant.get_merchant()
            if data is not None:
                data['merchant_id'] = curr_merchant_id
                return json(data, status=200)
            else:
                return json({
                    "message": "Merchant is not existed yet."
                }, status=404)
        except Exception as e:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                         }, status=500)

    async def post(self, request, id, technical):
        try:
            with await request.app.redis as redis:
                curr_merchant = merchant.Merchant(id=id, redis_conn=redis)
                data = request.json
                id, old_data = await curr_merchant.get_merchant()
                data['created_at'] = old_data['created_at']
                merchant_id, upd_merchant_data = await curr_merchant.update_merchant(data)
                data['merchant_id'] = merchant_id
            if upd_merchant_data is not None:
                return json(upd_merchant_data, status=200)
            else:
                return json({
                    "message": "Merchant is not existed yet."
                }, status=404)
        except Exception:
            capture_exception()
            return json({"message": "Internal Server error"
                         }, status=500)

    async def delete(self, request, id, technical):
        try:
            with await request.app.redis as redis:
                curr_merchant = merchant.Merchant(id=id, redis_conn=redis)
                await curr_merchant.delete_merchant()
            return json({
                "message": "There is no such merchant anymore."
            }, status=204)
        except Exception:
            capture_exception()
            return json({"message": "Internal Server error"
                     }, status=500)


# /merchant/list
class MerchantListView(HTTPMethodView):
    decorators = [auth.authorized(roles=['global', 'admin'])]

    async def get(self, request, technical):
        try:
            with await request.app.redis as redis:
                data = await merchant.Merchant.list_merchants(redis_conn=redis)
                data = sorted(data, key=lambda x: x['merchant_id'], reverse=True)
            return json(data, status=200)
        except Exception:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                         }, status=500)

















