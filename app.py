import sentry_sdk
from sanic import Sanic
from sanic_redis import SanicRedis
from sentry_sdk.integrations.sanic import SanicIntegration
from resources import user, record, merchant, industries
from loading_settings import load_variables
from redis_create_structure import *

configs = load_variables()
sentry_sdk.init(dsn='https://1fbbe56fa8f24ff89f69a99066177a0b@sentry.io/1320269',integrations=[SanicIntegration()])
app = Sanic(__name__)
app.config.LOGO = None
app.config.REQUEST_MAX_SIZE = configs['SANIC_REQUEST_MAX_SIZE']
app.config.KEEP_ALIVE_TIMEOUT = configs['SANIC_KEEP_ALIVE_TIMEOUT']
app.config.update(
    {
        'REDIS': {
            'address': (configs['REDIS_HOST'], configs['REDIS_PORT']),
            'db': configs['REDIS_DB'],
            # 'password': 'password',
            # 'ssl': None,
             'encoding': 'utf-8',
            # 'minsize': 1,
        }
    }
)

redis_database = SanicRedis(app)


@app.listener('after_server_start')
async def create_db_structure(app, loop):
    await setup_db(app.redis)

if __name__ == '__main__':
    app.add_route(record.RecordCreateView.as_view(), '/record/<attribute:string>/add')
    app.add_route(record.RecordView.as_view(), 'record/<attribute:string>/<id:int>')
    app.add_route(record.RecordListView.as_view(), '/record/<attribute:string>/list')
    app.add_route(record.RecordListAddView.as_view(), '/record/<attribute:string>')
    app.add_route(record.RecordPaymentView.as_view(), '/payment')
    app.add_route(record.RecordSearchView.as_view(), '/record/<attribute:string>/search')

    # User
    app.add_route(user.UserView.as_view(),  '/user/<id:int>')
    app.add_route(user.UserListView.as_view(), '/user/list')
    app.add_route(user.UserCreateView.as_view(), '/user/add')


    # Merchant
    app.add_route(merchant.MerchantCreateView.as_view(), 'merchant/add')
    app.add_route(merchant.MerchantView.as_view(), 'merchant/<id:int>')
    app.add_route(merchant.MerchantListView.as_view(), 'merchant/list')

    # Industries
    app.add_route(industries.IndustrieListView.as_view(), '/industries')



    app.run(host="0.0.0.0", port=configs['SANIC_PORT'], auto_reload=True)
