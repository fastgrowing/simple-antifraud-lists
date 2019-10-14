from sanic.response import json
from extensions.sanic_validation_decorators import *
from models.record  import *
from models.merchant import *
from datetime import datetime
from resources import auth
from sanic.views import HTTPMethodView
from sentry_sdk import capture_exception


schema_record = {
                'merchant_id': {
                    'type': 'integer',
                    'required': True,
                    'nullable': True
                },
                'value': {
                    'type': 'string',
                    'required': True
                },
                'list': {
                   'type': 'string',
                   'allowed': ['blacklist', 'whitelist', 'greylist'],
                   'required': True
                },
                'ttl': {
                   'type': 'integer',
                    'required': True,
                    'nullable': True
                }
}


schema_payment_put = {
               'email': {
                   'type': 'dict',
                   'empty': False,
                   'schema': {
                        'value': {'type': 'string', 'required': True},
                        'list': {'type': 'string', 'allowed': ['blacklist', 'whitelist', 'greylist'], 'required': True},
                        'ttl': {'type': 'integer', 'required': True, 'nullable': True}
                   }
               },
               'hash': {
                   'type': 'dict',
                   'schema': {
                        'value': {'type': 'string', 'required': True},
                        'list': {'type': 'string', 'allowed': ['blacklist', 'whitelist', 'greylist'], 'required': True},
                        'ttl': {'type': 'integer', 'required': True, 'nullable': True}
                   }
               }
}

schema_payment = {
               'order_id': {'type': 'string', 'required': True},
               'email': {'type': 'string', 'required': True},
               'hash': {'type': 'string', 'required': True},
               'ip': {'type': 'string', 'required': True},
               'bin': {'type': 'string', 'required': True}
}

schema_search = {
               'value': {'type': 'string', 'required': True, 'nullable': True},
               'merchant_id': {'type': 'integer', 'required': True, 'nullable': True}
}

schema_list = {
               'merchant_id': {'type': 'integer', 'required': True, 'nullable': True}
}


schema_listadd = {
              'merchant_id': {
                    'type': 'integer',
                    'required': True,
                    'nullable': True
               },
               'batch': {
                   'type': 'list',
                   'empty': False,
                   'schema': {
                        'type': 'dict',
                        'empty': False,
                        'schema': {
                                    'value': {'type': 'string', 'required': True},
                                    'list': {'type': 'string', 'allowed': ['blacklist', 'whitelist', 'greylist'],
                                             'required': True},
                                    'ttl': {'type': 'integer', 'required': True, 'nullable': True}
                        }
                   }
               }
}


# record/<attribute:string>/<id:int>
class RecordView(HTTPMethodView):
    decorators = [auth.authorized()]

    async def get(self, request, attribute, id, technical):
        try:
            with await request.app.redis as redis:
                curr_record = Record(attribute, merchant=technical['merchant'], industry=technical['industry'],
                                     id=id, redis_conn=redis)
                data = await curr_record.get_record()
            if data['created_at'] is None:
                return json({
                    "message": "Record with such value is not existed."
                }, status=404)
            else:
                return json(data, status=200)
        except Exception:
            capture_exception()
            return json({"message": "Internal Server error"
                         }, status=500)

    async def delete(self, request, attribute, id, technical):
        try:
            with await request.app.redis as redis:
                curr_record = Record(attribute, merchant=technical['merchant'], industry=technical['industry'],
                                     id=id, redis_conn=redis)
                await curr_record.delete_record()
            return json(
                {"message": "Item was deleted from the list"}, status=204)
        except Exception:
            capture_exception()
            return json({"message": "Internal Server error"
                     }, status=500)


# record/<attribute:string>/add
class RecordCreateView(HTTPMethodView):
    decorators = [auth.authorized(), validate_json(schema_record)]

    async def post(self, request, attribute, technical):
        try:
            if request.json['merchant_id'] is None and technical['role'] in ['global', 'admin']:
                return json({"message": "User with role global should include merchant id in request body."
                         }, status=400)
            body = request.json
            data = dict()
            data['list'] = body['list']
            data['ttl'] = body['ttl']
            data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['added_by'] = technical['role']
            with await request.app.redis as redis:
                if technical['role'] == 'global':
                    merch_search = Merchant(id=body['merchant_id'], redis_conn=redis)
                    id, merch_info = await merch_search.get_merchant()
                    if id is None:
                        return json({
                                     "message": "No such merchant."
                                    }, status=400)
                    merchant_name = merch_info['name']
                    merchant_industry = merch_info['industry']
                else:
                    merchant_name = technical['merchant']
                    merchant_industry = technical['industry']
                new_record = Record(attribute, industry=merchant_industry, merchant=merchant_name,
                                    value=body["value"], redis_conn=redis)
                result = await new_record.create_record(data)
            if result is not None:
                return json(result, status=201)
            else:
                return json({
                    "message": "Record with such value is already existed."
                }, status=409)
        except Exception as e:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                     }, status=500)


# /record/<attribute:string>/search
class RecordSearchView(HTTPMethodView):
    decorators = [auth.authorized(), validate_json(schema_search)]

    async def post(self, request, attribute, technical):
        try:
            if request.json['merchant_id'] is None and technical['role'] in ['global', 'admin']:
                return json({"message": "User with role global should include merchant id in request body."
                         }, status=400)
            search_value = request.json['value']
            merchant_id = request.json['merchant_id']
            with await request.app.redis as redis:
                if technical['role'] == 'global':
                    merch_search = Merchant(id=merchant_id, redis_conn=redis)
                    id, merch_info = await merch_search.get_merchant()
                    if id is None:
                        return json({
                                    "message": "No such merchant."
                                    }, status=400)
                    merchant_name = merch_info['name']
                    merchant_industry = merch_info['industry']
                else:
                    merchant_name = technical['merchant']
                    merchant_industry = technical['industry']
                result = []
                if search_value is None:
                    record_list = RecordList(attribute=attribute, industry=merchant_industry,
                                             merchant=merchant_name, redis_conn=redis)
                    result = await record_list.list_records()
                    result = sorted(result, key=lambda x: x['record_id'], reverse=True)
                else:
                    check_record = Record(attribute, industry=merchant_industry, merchant=merchant_name,
                                          value=search_value, redis_conn=redis)
                    result[0] = await check_record.get_record()
            if result[0]['record_id'] is not None:
                return json(result, status=200)
            else:
                return json([], status=200)
        except Exception:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                     }, status=500)


# /record/<attribute:string>/list
class RecordListView(HTTPMethodView):
    decorators = [auth.authorized(), validate_json(schema_list)]

    async def post(self, request, attribute, technical):
        try:
            if request.json['merchant_id'] is None and technical['role'] in ['global', 'admin']:
                return json({"message": "User with role global should include merchant id in request body."
                         }, status=400)
            else:
                merchant_id = request.json['merchant_id']
            with await request.app.redis as redis:
                if technical['role'] == 'global':
                    merch_search = Merchant(id=merchant_id, redis_conn=redis)
                    id, merch_info = await merch_search.get_merchant()
                    if id is None:
                        return json({
                                     "message": "No such merchant."
                                    }, status=400)
                    merchant_name = merch_info['name']
                    merchant_industry = merch_info['industry']
                else:
                    merchant_name = technical['merchant']
                    merchant_industry = technical['industry']
                record_list = RecordList(attribute=attribute, industry=merchant_industry,
                                         merchant=merchant_name, redis_conn=redis)
                data = await record_list.list_records()
                data = sorted(data, key=lambda x: x['record_id'], reverse=True)
            return json({
                "attribute": attribute,
                "records": data
            }, status=201)
        except Exception:
            capture_exception()
            return json({"message": "Internal Server error"
                         }, status=500)


# /record/<attribute:string>
class RecordListAddView(HTTPMethodView):
    decorators = [auth.authorized(), validate_json(schema_listadd, methods=['POST'])]

    async def post(self, request, attribute, technical):
        try:
            if request.json['merchant_id'] is None and technical['role'] in ['global', 'admin']:
                return json({"message": "User with role global should include merchant id in request body."
                         }, status=400)
            data = request.json
            merchant_id = data.pop('merchant_id')

            for rec in data['batch']:
                rec['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rec['added_by'] = technical['role']
            with await request.app.redis as redis:
                if technical['role'] == 'global':
                    merch_search = Merchant(id=merchant_id, redis_conn=redis)
                    id, merch_info = await merch_search.get_merchant()
                    if id is None:
                        return json({
                                     "message": "No such merchant."
                                    }, status=400)
                    merchant_name = merch_info['name']
                    merchant_industry = merch_info['industry']
                else:
                    merchant_name = technical['merchant']
                    merchant_industry = technical['industry']
                new_record_list = RecordList(attribute=attribute, industry=merchant_industry,
                                             merchant=merchant_name, redis_conn=redis)
                result = await new_record_list.add_records(data)
            return json({
                "attribute": attribute,
                "records": result
            }, status=201)
        except Exception:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                     }, status=500)


# /payment
class RecordPaymentView(HTTPMethodView):
    decorators = [auth.authorized(), validate_json(schema_payment_put, methods=['PUT']), validate_json(schema_payment, methods=['POST'])]

    async def post(self, request, technical):
        try:
            values = request.json
            order_id = values.pop('order_id')
            with await request.app.redis as redis:
                if technical['list_level'] == 'Local':
                    payment_check = Payment(industry=technical['industry'], merchant=technical['merchant'], redis_conn=redis)
                    result = await payment_check.find_payment(values)
                elif technical['list_level'] == 'Industry':
                    payment_check = Payment(industry=technical['industry'], merchant='*', redis_conn=redis)
                    result = await payment_check.find_payment(values)
                else:
                    payment_check = Payment(industry='*', merchant='*', redis_conn=redis)
                    result = await payment_check.find_payment(values)
            if 'whitelist' in result.values():
                return json({
                        "order_id": order_id,
                        "score": 100,
                        "group": "positive",
                        "description": result
                }, status=200)
            elif 'greylist' in result.values():
                return json({
                        "order_id": order_id,
                        "score": -20,
                        "group": "low",
                        "description": result
                }, status=200)
            elif 'blacklist' in result.values():
                return json({
                        "order_id": order_id,
                        "score": -100,
                        "group": "high",
                        "description": result
                }, status=200)
            else:
                return json({
                    "order_id": order_id,
                    "score": 0,
                    "group": "neutral",
                    "description": result
                }, status=200)
        except Exception:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                         }, status=500)

    async def put(self, request, technical):
        try:
            data = request.json
            for key in data.keys():
                data[key]['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data[key]['added_by'] = technical['role']
            with await request.app.redis as redis:
                payment_data = Payment(industry=technical['industry'], merchant=technical['merchant'], redis_conn=redis)
                result = await payment_data.add_payment(data)
            return json(result, status=201)
        except Exception:
            capture_exception(data=request.json)
            return json({"message": "Internal Server error"
                         }, status=500)
