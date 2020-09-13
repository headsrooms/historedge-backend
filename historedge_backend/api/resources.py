from aredis import StrictRedis

from historedge_backend import settings

redis = StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
