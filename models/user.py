import secrets


class User:

    def __init__(self, redis_conn, id='*', token='*'):
            self.id = id
            self.token = token
            self.key = str(id) + ':user:' + str(token)
            self.redis = redis_conn

    async def build_key(self):
        search_key_result = await self.redis.keys(self.key)
        if len(search_key_result) == 1:
            self.key = search_key_result[0]
            self.token = self.key.split(':')[2]

    async def get_user(self):
        await self.build_key()
        if await self.redis.exists(self.key):
            return await self.redis.hgetall(self.key)
        else:
            return None

    async def create_user(self, data):
        self.token = secrets.token_urlsafe(20)
        user_max_id = await self.redis.get('user_max_id')
        # increase user_max_id by one
        self.id = int(user_max_id) + 1
        self.key = str(self.id) + ':user:' + str(self.token)
        await self.redis.set('user_max_id', self.id)
        await self.redis.hmset_dict(self.key, data)
        return self.id, self.token

    async def delete_user(self):
        await self.build_key()
        await self.redis.delete(self.key)

    async def update_user(self, data):
        await self.build_key()
        if await self.redis.exists(self.key) is not None:
            await self.redis.delete(self.key)
            await self.redis.hmset_dict(self.key, data)
            return self.id, self.token
        else:
            return None, None

    async def refresh(self):
        """Refresh the user token."""
        await self.build_key()
        if await self.redis.exists(self.key) is not None:
            self.token = secrets.token_urlsafe(20)
            await self.redis.rename(self.key, str(self.id) + ':user:' + self.token)
            self.key = str(self.id) + ':user:' + self.token
            return self.token
        else:
            return None

    @classmethod
    async def list_users(cls, redis_conn):
        key = '*:user:*'
        data = []
        for item in await redis_conn.keys(key):
            d = await redis_conn.hgetall(item)
            d['user_id'] = int(item.split(':')[0])
            d['merchant_id'] = int(d['merchant_id'])
            d.pop('password')
            data.append(d)
        return data
