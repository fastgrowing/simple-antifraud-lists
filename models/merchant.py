class Merchant:

    def __init__(self, redis_conn, id='*'):
        self.id = id
        self.key = str(self.id) + ':merchant'
        self.redis = redis_conn

    async def build_key(self):
        """Строим ключ обьекта"""
        search_key_result = await self.redis.keys(self.key)
        if len(search_key_result) == 1:
            self.key = search_key_result[0]

    async def get_merchant(self):
        """Получаем информацию о мерчанте"""
        await self.build_key()
        if await self.redis.exists(self.key):
            return self.id, await self.redis.hgetall(self.key)
        else:
            return None, None

    async def create_merchant(self, data):
        """Создает хэш-запись о новом мерчанте в базе."""
        merchant_max_id = await self.redis.get('merchant_max_id')
        # increase merchant_max_id by one
        self.id = int(merchant_max_id) + 1
        self.key = str(self.id) + ':merchant'
        await self.redis.set('merchant_max_id', self.id)
        await self.redis.hmset_dict(self.key, data)
        return self.id, data

    async def delete_merchant(self):
        """Удаляет мерчанта из базы."""
        await self.build_key()
        await self.redis.delete(self.key)

    async def update_merchant(self, data):
        """Обновляет информацию о мерчанте в базе."""
        await self.build_key()
        if await self.redis.exists(self.key) is not None:
            await self.redis.delete(self.key)
            await self.redis.hmset_dict(self.key, data)
            return self.id, data
        else:
            return None, None

    @classmethod
    async def list_merchants(cls, redis_conn):
        """Возвращает список всех мерчантов"""
        key = '*:merchant'
        data = []
        for item in await redis_conn.keys(key):
            d = await redis_conn.hgetall(item)
            d['merchant_id'] = int(item.split(':')[0])
            data.append(d)
        return data
