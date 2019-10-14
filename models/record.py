class Record:
    def __init__(self, attribute, redis_conn, industry="default", merchant='default', id='*', value='*'):
        self.id = str(id)
        if industry is not None:
            self.industry = industry
        else:
            self.industry = "default"
        if merchant is not None:
            self.merchant = merchant
        else:
            self.merchant = "default"
        self.attribute = attribute
        self.value = value
        self.key = self.update_key()
        self.redis = redis_conn

    def update_key(self):
        return str(self.id) + ':' + self.industry + ':' + self.merchant + ':' + self.attribute + ':' \
                   + str(self.value)

    async def build_key(self):
        """Build the object key"""
        self.key = self.update_key()
        search_key_result = await self.redis.keys(self.key)
        if len(search_key_result) == 1:
            self.key = search_key_result[0]
            if self.id == "*":
                self.id = self.key.split(':')[0]
            if self.value == "*":
                self.value = self.key.split(':')[-1]
            return True

    async def get_record(self):
        await self.build_key()
        result = await self.redis.hmget(self.key, 'list', 'created_at', 'ttl')

        if result[0] is not None:
            return dict({'record_id': int(self.id), 'attribute': self.attribute, 'value': self.value, 'list': result[0],
                        'created_at': result[1], 'ttl': result[2]})
        else:
            return dict({'record_id': None, 'attribute': self.attribute, 'value': self.value,
                        'list': None, 'created_at': None})

    async def create_record(self, data):
        if await self.build_key() is not True:
            record_max_id = int(await self.redis.get('record_max_id')) + 1
            self.id = record_max_id
            await self.build_key()
            ttl = data['ttl']
            if ttl is None:
                data['ttl'] = -1
            await self.redis.set('record_max_id', record_max_id)
            await self.redis.hmset_dict(self.key, data)
            if ttl is not None:
                await self.redis.expire(self.key, int(ttl)*3600)
            data['record_id'] = int(self.id)
            data['value'] = self.value
            return data
        else:
            return None

    async def delete_record(self):
        await self.build_key()
        await self.redis.delete(self.key)


class Payment:

    def __init__(self, redis_conn, industry='default', merchant='default'):
        if industry is not None:
            self.industry = industry
        else:
            self.industry = "default"
        if merchant is not None:
            self.merchant = merchant
        else:
            self.merchant = "default"
        self.key = '*:' + self.industry + ':' + self.merchant + ':*' + ':*'
        self.redis = redis_conn

    async def build_key(self, attribute, value, record_id='*'):
        """Building the object key"""
        self.key = '{var1}:{var2}:{var3}:{var4}:{var5}'.format(var1=record_id, var2=self.industry, var3=self.merchant,
                                                               var4=attribute, var5=value)

    async def add_payment(self, values):
        """Adding payments attributes to the merchant lists."""
        pipe = self.redis.pipeline()
        result = dict()
        record_max_id = int(await self.redis.get('record_max_id'))
        for item in values:
            record_max_id += 1
            value_data = values[item]
            await self.build_key(attribute=item, value=value_data['value'])
            value = value_data.pop('value')
            search_key_result = await self.redis.keys(self.key)
            if len(search_key_result) == 0:
                await self.build_key(attribute=item, value=value, record_id=record_max_id)
                ttl = value_data.pop('ttl')
                pipe.hmset_dict(self.key, values[item])
                result[item] = value_data
                if ttl is not None:
                    pipe.expire(self.key, int(ttl)*3600)
                result[item]['value'] = value
                result[item]['record_id'] = record_max_id
            else:
                result[item] = {'message': "Item with this value is already existed"}
        pipe.set('record_max_id', record_max_id)
        await pipe.execute()
        return result

    async def find_payment(self, values):
        """Check the attribute in the merchant list."""
        pipe = self.redis.pipeline()
        for item in values:
            value_data = values[item]
            await self.build_key(attribute=item, value=value_data)
            search_key_result = await self.redis.keys(self.key)
            if len(search_key_result) == 1:
                self.key = search_key_result[0]
            pipe.hget(self.key, 'list')
        data = await pipe.execute()
        return dict(zip(values.keys(), data))


class RecordList:

    def __init__(self, attribute, redis_conn, industry='default', merchant='default'):
        if industry is not None:
            self.industry = industry
        else:
            self.industry = "default"
        if merchant is not None:
            self.merchant = merchant
        else:
            self.merchant = "default"
        self.attribute = attribute
        self.key = '*:' + self.industry + ':' + self.merchant + ':' + self.attribute + ':*'
        self.redis = redis_conn

    async def rebuild_key(self, value='*', record_id='*'):
        self.key = '{var1}:{var2}:{var3}:{var4}:{var5}'.format(var1=record_id, var2=self.industry, var3=self.merchant,
                                                               var4=self.attribute, var5=value)

    async def list_records(self):
        data = []
        for item in await self.redis.keys(self.key):
            t = dict()
            t['list'], t['created_at'], t['ttl'] = await self.redis.hmget(item, 'list', 'created_at', 'ttl')
            t['ttl'] = int(t['ttl'])
            t['value'] = item.split(':')[-1]
            t['record_id'] = int(item.split(':')[0])
            data.append(t)
        return data

    async def add_records(self, data):
        result = []
        record_max_id = int(await self.redis.get('record_max_id'))
        for item in data['batch']:
            await self.rebuild_key(value=item['value'])
            search_key_result = await self.redis.keys(self.key)
            if len(search_key_result) == 0:
                record_max_id += 1
                await self.rebuild_key(record_id=record_max_id, value=item['value'])
                ttl = item['ttl']
                if ttl is None:
                    item['ttl'] = -1
                self.redis.hmset_dict(self.key, item)
                if ttl is not None:
                    await self.redis.expire(self.key, int(ttl)*3600)
                item['record_id'] = record_max_id
                self.redis.set('record_max_id', record_max_id)
                result.append(item)
            else:
                result.append({item['value']: "Item with this value is already existed"})
        return result
