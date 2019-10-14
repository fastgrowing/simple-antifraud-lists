class Industry:
    industries = ['dating', 'herbs and diets', 'gambling', 'gaming', 'commercial']
    key = 'industry'

    @classmethod
    async def create_industries(cls, redis_conn):
        """Создаем базовый список всех индустрий."""
        for value in sorted(cls.industries):
            await redis_conn.rpush(cls.key, value)

    @classmethod
    async def list_industries(cls, redis_conn):
        """Вовращаем список доступных индустрий."""
        list = await redis_conn.lrange('industry', 0, -1)
        return list
