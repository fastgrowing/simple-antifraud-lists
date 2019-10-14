from models.user import *
from models.merchant import *
from models.industries import *
from datetime import datetime


async def merchant_index(r):
    await r.set('merchant_max_id', 0)


async def record_index(r):
    await r.set('record_max_id', 0)


async def user_index(r):
    await r.set('user_max_id', 0)


user_admin = {
               'login': 'admin',
               'password': 'admin',
               'merchant_id': 0,
               'role': 'admin'
}

user_base = {
               'login': 'base',
               'password': 'base',
               'merchant_id': 0,
               'role': 'global'
}

merchant_data = {
               'name': 'admin',
               'industry': '*',
               'list_level': 'global'
}


async def setup_db(redis_conn):
    logins = [x['login'] for x in await User.list_users(redis_conn=redis_conn)]
    if 'admin' not in logins:
        await merchant_index(r=redis_conn)
        await record_index(r=redis_conn)
        await user_index(r=redis_conn)
        await Industry.create_industries(redis_conn = redis_conn)
        # создание базового и юзера
        merchant_admin = Merchant(redis_conn=redis_conn)
        merchant_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        merchant_id, merc_data = await merchant_admin.create_merchant(merchant_data)
        admin = User(redis_conn=redis_conn)
        user_admin['merchant_id'] = int(merchant_id)
        user_admin['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_id, token = await admin.create_user(user_admin)
        print('User token for admin account is {0}'.format(token))
        base = User(redis_conn=redis_conn)
        user_base['merchant_id'] = int(merchant_id)
        user_base['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_id, token = await base.create_user(user_base)
        print('User token for base account is {0}'.format(token))
    else:
        print('Structure has been already created.')

