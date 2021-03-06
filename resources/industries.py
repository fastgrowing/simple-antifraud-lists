from sanic.response import json
from models.industries import *
from datetime import datetime
from resources import auth
from sanic.views import HTTPMethodView
from sentry_sdk import capture_exception


# /industries
class IndustrieListView(HTTPMethodView):
    decorators = [auth.authorized()]

    async def get(self, request, technical):
        try:
            with await request.app.redis as redis:
                ind_list = await Industry.list_industries(redis_conn=redis)
                print(ind_list)
                return json({"industries": ind_list}, status=200)
        except Exception as e:
            capture_exception()
            return json({"message": "Internal Server error"
                         }, status=500)
