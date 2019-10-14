class Auth:

    @classmethod
    async def find_merchant_by_token(cls, token, redis_conn):
        """Находим и возвращаем информацию требуюмую для авторизационной функции."""
        search_key_result = await redis_conn.keys('*:user:' + str(token))
        if len(search_key_result) == 1:
            key = search_key_result[0]
            merch_id, role = await redis_conn.hmget(key, 'merchant_id', 'role')
            key_merchant = '{id}:merchant'.format(id=merch_id)
            values = await redis_conn.hmget(key_merchant, 'name', 'industry', 'list_level')
            return {'role': role, 'merchant': values[0],
                    'industry': values[1], 'list_level': values[2]}
        else:
            return None
