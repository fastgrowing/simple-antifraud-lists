class Industry:
    industries = ['social', 'financial', 'gaming', 'commercial']
    key = 'industry'

    @classmethod
    async def create_industries(cls, redis_conn):
        """Create the base list of all available industries."""
        for value in sorted(cls.industries):
            await redis_conn.rpush(cls.key, value)

    @classmethod
    async def list_industries(cls, redis_conn):
        """Return the list of all available industries."""
        list = await redis_conn.lrange('industry', 0, -1)
        return list
