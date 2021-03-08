import redis
import json


class Cache:
    cache = redis.Redis(host='redis.backtory', port=6379, db=0)

    @classmethod
    def get(cls, cache_group, cache_key):
        redis_key = f'gitlabci:{cache_group}:{cache_key}'
        value = cls.cache.get(redis_key)
        if value is not None:
            return value.decode('utf-8')

    @classmethod
    def set(cls, cache_group, cache_key, value, ttl=60, no_exp=False):
        redis_key = f'gitlabci:{cache_group}:{cache_key}'
        if no_exp:
            cls.cache.set(redis_key, value)
        else:
            cls.cache.set(redis_key, value, ex=ttl)

    @classmethod
    def hash_get(cls, cache_group, cache_key, hash_key):
        redis_key = f'gitlabci:{cache_group}:{cache_key}'
        value = cls.cache.hget(redis_key, hash_key)
        return value

    @classmethod
    def hash_set(cls, cache_group, cache_key, hash_key, value, ttl=60):
        redis_key = f'gitlabci:{cache_group}:{cache_key}'
        cls.cache.hset(redis_key, hash_key, value)
        cls.cache.expire(name=redis_key, time=ttl)

    @classmethod
    def hash_get_all(cls, cache_group, cache_key):
        redis_key = f'gitlabci:{cache_group}:{cache_key}'
        result = cls.cache.hgetall(redis_key)
        return result

    @classmethod
    def hash_set_all(cls, cache_group, cache_key, input_dict, ttl=60):
        redis_key = f'gitlabci:{cache_group}:{cache_key}'
        cls.cache.hmset(redis_key, input_dict)
        cls.cache.expire(redis_key, time=ttl)

    @classmethod
    def get_list(cls, cache_group, cache_key):
        redis_key = f'gitlabci:{cache_group}:{cache_key}'
        elements = cls.cache.lrange(redis_key, 0, -1)
        output_list = list(map(lambda x: json.loads(x), elements))
        return output_list

    @classmethod
    def set_list(cls, cache_group, cache_key, input_list, ttl=60):
        redis_key = f'gitlabci:{cache_group}:{cache_key}'
        input_list = list(map(lambda x: json.dumps(x), input_list)) or []
        if len(input_list) > 0:
            cls.cache.rpush(redis_key, *input_list)
            cls.cache.expire(redis_key, time=ttl)

    @classmethod
    def add_to_list(cls, cache_group, cache_key, item):
        redis_key = f'gitlabci:{cache_group}:{cache_key}'
        serialized_object = json.dumps(item)
        cls.cache.rpush(redis_key, serialized_object)

    @classmethod
    def delete_cache(cls, cache_group, cache_key):
        redis_key = f'gitlabci:{cache_group}:{cache_key}'
        cls.cache.delete(redis_key)

    @classmethod
    def delete_cache_by_key_prefix(cls, redis_key):
        redis_key_pattern = f'gitlabci:{redis_key}*'
        for key in cls.cache.scan_iter(match=redis_key_pattern):
            cls.cache.delete(key)

    @classmethod
    def increment_key(cls, cache_group, cache_key):
        redis_key = f'gitlabci:{cache_group}:{cache_key}'
        cls.cache.incr(redis_key, 1)
